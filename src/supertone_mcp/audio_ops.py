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


def _build_filter_complex(n_inputs: int, gap_ms: int, crossfade_ms: int) -> str:
    """Build the ffmpeg `-filter_complex` graph for the requested merge mode.

    Every input audio stream is first normalized to the canonical sample
    rate / channel layout / sample format (`[a{i}]` labels) so the downstream
    `concat`/`acrossfade` filters do not fail on heterogeneous inputs.

    - crossfade_ms > 0: chain `acrossfade` across consecutive normalized inputs.
    - gap_ms > 0: interleave normalized `aevalsrc` silence segments, then concat.
    - otherwise: plain `concat` of all normalized input audio streams.

    The final output stream is always labelled `[out]`.
    """
    # Normalize each raw input stream: [i:a] -> [a{i}].
    norm_filters = [f"[{i}:a]{_NORMALIZE}[a{i}]" for i in range(n_inputs)]

    if crossfade_ms > 0:
        duration = crossfade_ms / 1000.0
        parts: list[str] = []
        prev = "a0"
        for i in range(1, n_inputs):
            out = "out" if i == n_inputs - 1 else f"acf{i}"
            parts.append(f"[{prev}][a{i}]acrossfade=d={duration}[{out}]")
            prev = out
        return ";".join([*norm_filters, *parts])

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
) -> tuple[bytes, str]:
    """Concatenate audio files via ffmpeg and return (audio_bytes, ext).

    Args:
        input_paths: Two or more audio file paths (already validated and
            existence-checked by the caller).
        gap_ms: Silence (ms) inserted at each junction. Mutually exclusive
            with `crossfade_ms` (the caller enforces this).
        crossfade_ms: Crossfade blend (ms) at each junction.
        output_format: Resolved output extension ("mp3" or "wav").

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

    filter_complex = _build_filter_complex(len(input_paths), gap_ms, crossfade_ms)
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-f",
        _pipe_format(output_format),
        "pipe:1",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
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

    return stdout, output_format
