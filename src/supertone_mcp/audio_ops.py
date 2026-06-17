"""Low-level ffmpeg subprocess wrapper for audio merge operations (ISSUE-029).

Keeps all ffmpeg-specific logic isolated from the tool handler in `tools.py`.
The ffmpeg binary is resolved via `imageio_ffmpeg.get_ffmpeg_exe()` (a bundled
binary, per SPEC-029 / NFR-001) rather than relying on a system `ffmpeg` on
PATH. Audio is rendered to stdout (`pipe:1`) and returned as bytes so the
handler owns all file-system concerns (naming, output dir).

This module has NO Supertone SDK dependency.
"""

from __future__ import annotations

import asyncio
import os
import tempfile

import imageio_ffmpeg

# Max stderr characters surfaced in the RuntimeError on a failed merge. The
# handler turns this into the user-facing "Audio merge failed: ..." string.
_STDERR_EXCERPT_LIMIT = 500

# Hard ceiling on a single ffmpeg invocation. A pathological input or a stalled
# bundled binary would otherwise hang the (single-process, stdio) MCP server
# indefinitely. Audio assembly of typical TTS clips completes in seconds.
_FFMPEG_TIMEOUT_SECONDS = 120.0

# Canonical intermediate audio parameters. ffmpeg's `concat`/`acrossfade`
# filters require every segment to share sample rate, channel layout, and
# sample format; raw mp3/wav inputs (and the silence source) routinely differ.
# Every input stream — and any generated silence — is normalized to these
# before merging so heterogeneous inputs work at runtime (the mocked tests
# cannot catch this; see RL-007). The final muxer/encoder converts as needed.
_TARGET_SAMPLE_RATE = 44100
_TARGET_SAMPLE_FMT = "fltp"
_TARGET_CHANNEL_LAYOUT = "stereo"

# Per-stream normalization applied to every input before concat/crossfade.
_NORMALIZE = (
    f"aresample={_TARGET_SAMPLE_RATE},"
    f"aformat=sample_fmts={_TARGET_SAMPLE_FMT}:"
    f"channel_layouts={_TARGET_CHANNEL_LAYOUT}"
)


def _pipe_format(output_format: str) -> str:
    """Map an output extension to the ffmpeg muxer name for `-f`."""
    # mp3 and wav share their extension with the muxer name; this indirection
    # keeps the mapping explicit and future-proof for new formats.
    return "wav" if output_format == "wav" else "mp3"


def _build_crossfade_filters(
    n_inputs: int, crossfade_ms: int, input_durations: list[float]
) -> list[str]:
    """Build a deterministic manual crossfade graph (afade + adelay + amix).

    ffmpeg's `acrossfade` filter is non-deterministic on short inputs: it
    occasionally drops a whole stream, truncating the result to roughly
    `one_clip - crossfade` (see ISSUE-033). We reconstruct an equivalent
    equal-gain (linear) crossfade ourselves, which is exact and stable:

    - Each clip is laid on a shared timeline at a cumulative offset; each
      junction overlaps by `crossfade` seconds, so clip `i` starts at
      `offset[i] = offset[i-1] + dur[i-1] - crossfade`.
    - The tail of every non-final clip fades out over `crossfade`; the head of
      every non-first clip fades in over `crossfade`. With linear fades the two
      overlapping clips sum to unity gain (matching acrossfade's default `tri`
      curve).
    - `adelay` places each faded clip at its offset; `amix=normalize=0` sums
      them without the implicit averaging that would otherwise halve the level.

    Requires `input_durations` (seconds) for every input. The per-junction
    crossfade is clamped to the shorter neighbouring clip so a `crossfade_ms`
    larger than a clip cannot push a fade start negative.
    """
    cf = crossfade_ms / 1000.0
    # Cumulative timeline offset of each clip. Clamp the overlap at each
    # junction to the shorter neighbour so offsets stay monotonic and fade
    # starts stay non-negative even for clips shorter than the crossfade.
    offsets = [0.0]
    for i in range(1, n_inputs):
        overlap = min(cf, input_durations[i - 1], input_durations[i])
        offsets.append(offsets[i - 1] + input_durations[i - 1] - overlap)

    branches: list[str] = []
    for i in range(n_inputs):
        chain: list[str] = []
        if i > 0:  # fade in the head of every non-first clip
            fade_in = min(cf, input_durations[i])
            chain.append(f"afade=t=in:st=0:d={fade_in}")
        if i < n_inputs - 1:  # fade out the tail of every non-final clip
            fade_out = min(cf, input_durations[i])
            chain.append(f"afade=t=out:st={input_durations[i] - fade_out}:d={fade_out}")
        delay_ms = int(round(offsets[i] * 1000))
        if delay_ms > 0:
            chain.append(f"adelay={delay_ms}|{delay_ms}")
        # `anull` guarantees a filter body so the [a{i}]->[f{i}] relabel is valid
        # even for a clip that needs neither fade nor delay (only i==0 with n==1,
        # which the caller never reaches, but keep the graph well-formed).
        body = ",".join(chain) if chain else "anull"
        branches.append(f"[a{i}]{body}[f{i}]")

    mix_labels = "".join(f"[f{i}]" for i in range(n_inputs))
    branches.append(
        f"{mix_labels}amix=inputs={n_inputs}:dropout_transition=0:normalize=0[out]"
    )
    return branches


def _build_filter_complex(
    n_inputs: int,
    gap_ms: int,
    crossfade_ms: int,
    input_durations: list[float] | None = None,
) -> str:
    """Build the ffmpeg `-filter_complex` graph for the requested merge mode.

    Every input audio stream is first normalized to the canonical sample
    rate / channel layout / sample format (`[a{i}]` labels) so the downstream
    filters do not fail on heterogeneous inputs.

    - crossfade_ms > 0: deterministic manual crossfade (afade/adelay/amix);
      requires `input_durations` (one per input, seconds).
    - gap_ms > 0: interleave normalized `aevalsrc` silence segments, then concat.
    - otherwise: plain `concat` of all normalized input audio streams.

    The final output stream is always labelled `[out]`.
    """
    # Normalize each raw input stream: [i:a] -> [a{i}].
    norm_filters = [f"[{i}:a]{_NORMALIZE}[a{i}]" for i in range(n_inputs)]

    if crossfade_ms > 0:
        if input_durations is None or len(input_durations) != n_inputs:
            raise ValueError("crossfade requires one input duration per input stream")
        return ";".join(
            [
                *norm_filters,
                *_build_crossfade_filters(n_inputs, crossfade_ms, input_durations),
            ]
        )

    if gap_ms > 0:
        duration = gap_ms / 1000.0
        silence_filters: list[str] = []
        labels: list[str] = []
        sil_idx = 0
        for i in range(n_inputs):
            labels.append(f"[a{i}]")
            if i < n_inputs - 1:
                lbl = f"sil{sil_idx}"
                # Match the silence source to the canonical parameters so the
                # concat segment boundaries line up.
                silence_filters.append(
                    f"aevalsrc=0:d={duration}:s={_TARGET_SAMPLE_RATE}:"
                    f"c={_TARGET_CHANNEL_LAYOUT},"
                    f"aformat=sample_fmts={_TARGET_SAMPLE_FMT}[{lbl}]"
                )
                labels.append(f"[{lbl}]")
                sil_idx += 1
        concat_n = len(labels)
        concat = "".join(labels) + f"concat=n={concat_n}:v=0:a=1[out]"
        return ";".join([*norm_filters, *silence_filters, concat])

    concat_labels = "".join(f"[a{i}]" for i in range(n_inputs))
    return ";".join([*norm_filters, f"{concat_labels}concat=n={n_inputs}:v=0:a=1[out]"])


async def merge_audio(
    input_paths: list[str],
    gap_ms: int,
    crossfade_ms: int,
    output_format: str,
    input_durations: list[float] | None = None,
) -> tuple[bytes, str]:
    """Concatenate audio files via ffmpeg and return (audio_bytes, ext).

    Args:
        input_paths: Two or more audio file paths (already validated and
            existence-checked by the caller).
        gap_ms: Silence (ms) inserted at each junction. Mutually exclusive
            with `crossfade_ms` (the caller enforces this).
        crossfade_ms: Crossfade blend (ms) at each junction.
        output_format: Resolved output extension ("mp3" or "wav").
        input_durations: One duration (seconds) per input, required only when
            `crossfade_ms > 0` (the deterministic crossfade graph lays clips on
            a shared timeline by offset). Ignored for concat/gap modes.

    Returns:
        A tuple of the rendered audio bytes and the output extension.

    Raises:
        RuntimeError: ffmpeg exited non-zero; the message carries an excerpt
            of stderr for the handler to surface.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd: list[str] = [ffmpeg_exe, "-y"]
    for path in input_paths:
        cmd += ["-i", path]

    filter_complex = _build_filter_complex(
        len(input_paths), gap_ms, crossfade_ms, input_durations
    )

    # Render to a seekable temp file rather than `pipe:1`. ffmpeg cannot rewind
    # a pipe to patch the WAV RIFF/`data` chunk size headers, so a piped WAV
    # carries the `0xFFFFFFFF` size placeholder — which mutagen reads as
    # ~24347s and which strict parsers reject (ISSUE-032). A real file lets
    # ffmpeg finalize the header; mp3 is unaffected but uses the same path.
    suffix = f".{output_format}"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="supertone-merge-")
    os.close(fd)
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-f",
        _pipe_format(output_format),
        tmp_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=_FFMPEG_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            # Kill the stalled process and surface a clear error rather than
            # hanging the MCP server forever.
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"ffmpeg timed out after {_FFMPEG_TIMEOUT_SECONDS:.0f}s")

        if proc.returncode != 0:
            excerpt = stderr.decode(errors="replace")[:_STDERR_EXCERPT_LIMIT].strip()
            # Fall back to the exit code when ffmpeg produced no stderr, so the
            # handler never surfaces a bare "Audio merge failed: ." message.
            raise RuntimeError(excerpt or f"ffmpeg exited with code {proc.returncode}")

        with open(tmp_path, "rb") as fh:
            audio_bytes = fh.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return audio_bytes, output_format
