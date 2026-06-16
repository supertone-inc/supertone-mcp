"""Tests for the ffmpeg-backed audio merge module (ISSUE-029).

All ffmpeg invocations are mocked: `asyncio.create_subprocess_exec` is patched
to return a fake process, and `imageio_ffmpeg.get_ffmpeg_exe` is patched so no
real binary is ever resolved or executed (per docs/test_plan.md Flow 13 — no
real ffmpeg/process in CI).
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from supertone_mcp.audio_ops import merge_audio

FAKE_FFMPEG = "/fake/bin/ffmpeg"


class _FakeProc:
    """Minimal stand-in for an asyncio subprocess."""

    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


def _patch_ffmpeg(proc: _FakeProc):
    """Return (get_exe_mock, create_proc_mock) context managers as a tuple."""
    get_exe = patch(
        "supertone_mcp.audio_ops.imageio_ffmpeg.get_ffmpeg_exe",
        return_value=FAKE_FFMPEG,
    )
    create_proc = patch(
        "asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=proc),
    )
    return get_exe, create_proc


class TestMergeAudio:
    async def test_resolves_binary_via_imageio_ffmpeg(self):
        """TC-152: the ffmpeg binary is resolved via imageio_ffmpeg, not PATH."""
        proc = _FakeProc(stdout=b"MERGED", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe as gx, create_proc as cp:
            data, ext = await merge_audio(
                ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=0, output_format="mp3"
            )
        gx.assert_called_once()
        # The resolved binary must be the first element of the command.
        args = cp.call_args.args
        assert args[0] == FAKE_FFMPEG
        assert data == b"MERGED"
        assert ext == "mp3"

    async def test_plain_concat_uses_concat_filter(self):
        """TC-140-ish: no gap/crossfade → a concat filter, no silence/crossfade."""
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=0, output_format="mp3"
            )
        cmd = " ".join(cp.call_args.args)
        assert "concat" in cmd
        assert "aevalsrc" not in cmd
        assert "acrossfade" not in cmd

    async def test_gap_inserts_silence(self):
        """TC-148: gap_ms>0 → a silence source is added to the filter graph."""
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.mp3", "b.mp3"], gap_ms=500, crossfade_ms=0, output_format="mp3"
            )
        cmd = " ".join(cp.call_args.args)
        assert "aevalsrc" in cmd
        # 500ms -> 0.5s
        assert "0.5" in cmd

    async def test_crossfade_uses_acrossfade(self):
        """TC-149: crossfade_ms>0 → the acrossfade filter is used."""
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=200, output_format="mp3"
            )
        cmd = " ".join(cp.call_args.args)
        assert "acrossfade" in cmd
        # 200ms -> 0.2s
        assert "0.2" in cmd

    async def test_output_format_wav_sets_pipe_format(self):
        """output_format='wav' is reflected in the ffmpeg output args + return."""
        proc = _FakeProc(stdout=b"WAVDATA", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            data, ext = await merge_audio(
                ["a.wav", "b.wav"], gap_ms=0, crossfade_ms=0, output_format="wav"
            )
        cmd = " ".join(cp.call_args.args)
        assert "wav" in cmd
        assert ext == "wav"
        assert data == b"WAVDATA"

    async def test_nonzero_exit_raises_runtimeerror_with_stderr(self):
        """TC-151: a nonzero ffmpeg exit raises RuntimeError carrying stderr."""
        proc = _FakeProc(stdout=b"", stderr=b"boom: bad codec", returncode=1)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc:
            with pytest.raises(RuntimeError, match="boom: bad codec"):
                await merge_audio(
                    ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=0, output_format="mp3"
                )

    async def test_three_inputs_concat_count(self):
        """TC-141: 3 inputs → concat n reflects all three streams."""
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.wav", "b.wav", "c.wav"],
                gap_ms=0,
                crossfade_ms=0,
                output_format="wav",
            )
        cmd = " ".join(cp.call_args.args)
        assert "concat=n=3" in cmd


class TestMergeAudioNormalization:
    """C1/C2: streams + silence are normalized so concat works on
    heterogeneous inputs (different sample rate / channel layout / format)."""

    async def test_inputs_are_normalized_before_concat(self):
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.mp3", "b.wav"], gap_ms=0, crossfade_ms=0, output_format="mp3"
            )
        cmd = " ".join(cp.call_args.args)
        # Every raw input stream is run through aresample + aformat.
        assert "aresample=44100" in cmd
        assert "aformat=sample_fmts=fltp" in cmd
        assert "channel_layouts=stereo" in cmd

    async def test_gap_silence_matches_target_params(self):
        """The aevalsrc silence must carry the same sample rate + channel
        layout as the normalized inputs, or concat fails at runtime."""
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.mp3", "b.mp3"], gap_ms=500, crossfade_ms=0, output_format="mp3"
            )
        cmd = " ".join(cp.call_args.args)
        assert "aevalsrc=0:d=0.5:s=44100:c=stereo" in cmd

    async def test_crossfade_inputs_are_normalized(self):
        proc = _FakeProc(stdout=b"X", returncode=0)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc as cp:
            await merge_audio(
                ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=200, output_format="mp3"
            )
        cmd = " ".join(cp.call_args.args)
        assert "aresample=44100" in cmd
        assert "acrossfade=d=0.2" in cmd

    async def test_timeout_kills_process_and_raises(self):
        """H1: a hung ffmpeg is killed and surfaced as a clear error."""

        class _HangingProc:
            def __init__(self):
                self.returncode = None
                self.killed = False

            async def communicate(self):
                raise asyncio.TimeoutError

            def kill(self):
                self.killed = True

            async def wait(self):
                return 0

        proc = _HangingProc()
        get_exe = patch(
            "supertone_mcp.audio_ops.imageio_ffmpeg.get_ffmpeg_exe",
            return_value=FAKE_FFMPEG,
        )
        create_proc = patch(
            "asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)
        )
        with get_exe, create_proc:
            with pytest.raises(RuntimeError, match="timed out"):
                await merge_audio(
                    ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=0, output_format="mp3"
                )
        assert proc.killed is True

    async def test_empty_stderr_falls_back_to_exit_code(self):
        """M1: nonzero exit with empty stderr surfaces the exit code, not ''."""
        proc = _FakeProc(stdout=b"", stderr=b"", returncode=1)
        get_exe, create_proc = _patch_ffmpeg(proc)
        with get_exe, create_proc:
            with pytest.raises(RuntimeError, match="exited with code 1"):
                await merge_audio(
                    ["a.mp3", "b.mp3"], gap_ms=0, crossfade_ms=0, output_format="mp3"
                )
