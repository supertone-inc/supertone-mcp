"""Real-ffmpeg regression tests for the merge bug fixes (ISSUE-032 / ISSUE-033).

These run the *bundled* ffmpeg for real, so they are env-gated and skipped by
default (CI stays binary-free, per ISSUE-030 / docs/test_plan.md Flow 13). Run
with:

    SUPERTONE_RUN_FFMPEG_TESTS=1 uv run pytest tests/test_audio_ops_real_ffmpeg.py

They pin the two behaviours that the mocked unit tests cannot observe:

- ISSUE-032: a merged WAV reports its true duration (not the ~24347s that a
  pipe-corrupted RIFF header produced), and the on-disk file is parseable.
- ISSUE-033: `crossfade_ms` on short / similar-length clips is deterministic and
  the correct length — the old `acrossfade` truncated ~1-in-2 runs to a single
  clip minus the crossfade.
"""

import os
import subprocess
import tempfile

import imageio_ffmpeg
import pytest
from mutagen import File as MutagenFile

from supertone_mcp.audio_ops import merge_audio

pytestmark = pytest.mark.skipif(
    os.environ.get("SUPERTONE_RUN_FFMPEG_TESTS") != "1",
    reason="real-ffmpeg test; set SUPERTONE_RUN_FFMPEG_TESTS=1 to run",
)


def _make_sine(path: str, duration: float, freq: int) -> None:
    """Render a stereo 44100Hz sine WAV via the bundled ffmpeg."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq}:duration={duration}",
            "-ar",
            "44100",
            "-ac",
            "2",
            path,
        ],
        check=True,
        capture_output=True,
    )


def _duration(path: str) -> float:
    audio = MutagenFile(path)
    return audio.info.length


async def test_merged_wav_reports_true_duration(tmp_path):
    """ISSUE-032: WAV merge duration is the real sum, not the pipe placeholder."""
    a, b = str(tmp_path / "a.wav"), str(tmp_path / "b.wav")
    _make_sine(a, 1.6, 440)
    _make_sine(b, 1.6, 660)

    audio_bytes, ext = await merge_audio(
        [a, b], gap_ms=0, crossfade_ms=0, output_format="wav"
    )
    assert ext == "wav"

    out = str(tmp_path / "out.wav")
    with open(out, "wb") as fh:
        fh.write(audio_bytes)

    dur = _duration(out)
    # True sum is ~3.2s; the bug reported ~24347s.
    assert abs(dur - 3.2) < 0.2, f"expected ~3.2s, got {dur}"


async def test_crossfade_short_clips_is_deterministic(tmp_path):
    """ISSUE-033: short-clip crossfade is stable and correct across repeats."""
    a, b = str(tmp_path / "a.wav"), str(tmp_path / "b.wav")
    _make_sine(a, 1.36, 440)
    _make_sine(b, 1.36, 660)
    # 1.36 + 1.36 - 0.5 crossfade = 2.22s
    expected = 2.22

    for i in range(10):
        audio_bytes, _ = await merge_audio(
            [a, b],
            gap_ms=0,
            crossfade_ms=500,
            output_format="wav",
            input_durations=[1.36, 1.36],
        )
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            fh.write(audio_bytes)
            out = fh.name
        try:
            dur = _duration(out)
        finally:
            os.unlink(out)
        # The old acrossfade truncated to ~0.86s on a fraction of runs.
        assert abs(dur - expected) < 0.15, f"run {i}: expected ~{expected}s, got {dur}"


async def test_crossfade_three_input_chain_length(tmp_path):
    """ISSUE-033: an N-input crossfade chain totals Σdur − (n−1)·crossfade."""
    paths = []
    for i, freq in enumerate((440, 660, 880)):
        p = str(tmp_path / f"in{i}.wav")
        _make_sine(p, 1.36, freq)
        paths.append(p)
    # 3*1.36 - 2*0.5 = 3.08s
    expected = 3.08

    audio_bytes, _ = await merge_audio(
        paths,
        gap_ms=0,
        crossfade_ms=500,
        output_format="wav",
        input_durations=[1.36, 1.36, 1.36],
    )
    out = str(tmp_path / "out.wav")
    with open(out, "wb") as fh:
        fh.write(audio_bytes)
    dur = _duration(out)
    assert abs(dur - expected) < 0.15, f"expected ~{expected}s, got {dur}"
