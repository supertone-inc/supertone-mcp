"""Tests for input validation, output formatting, and tool handlers."""

import base64
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import AudioContent, TextContent
from supertone_tts_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.models import TTSResponse, VoiceInfo
from supertone_tts_mcp.tools import (
    _autoplay,
    calculate_duration,
    format_tts_metadata,
    format_tts_response,
    format_voice_list,
    resolve_api_key,
    resolve_autoplay,
    resolve_output_dir,
    resolve_output_mode,
    resolve_voice_id,
    search_voice,
    text_to_speech,
    validate_language,
    validate_model,
    validate_output_format,
    validate_pitch_shift,
    validate_speed,
    validate_text,
)


class TestValidateText:
    def test_empty_string(self):
        with pytest.raises(ValueError, match="Text must not be empty."):
            validate_text("")

    def test_long_text_passes(self):
        """SDK handles chunking, so long text should pass."""
        validate_text("a" * 1000)

    def test_1_char_passes(self):
        validate_text("a")


class TestValidateLanguage:
    @pytest.mark.parametrize("lang", ["ko", "en", "ja", "de", "fr", "es"])
    def test_valid_languages(self, lang):
        validate_language(lang)

    def test_invalid_language(self):
        with pytest.raises(ValueError, match=r'Invalid language: "zz"'):
            validate_language("zz")


class TestValidateOutputFormat:
    @pytest.mark.parametrize("fmt", ["mp3", "wav"])
    def test_valid_formats(self, fmt):
        validate_output_format(fmt)

    def test_invalid_format(self):
        with pytest.raises(
            ValueError,
            match=(
                r'Invalid output format: "ogg"\.'
                r" Supported formats: mp3, wav\."
            ),
        ):
            validate_output_format("ogg")


class TestValidateSpeed:
    @pytest.mark.parametrize("speed", [0.5, 1.0, 2.0])
    def test_valid_speeds(self, speed):
        validate_speed(speed)

    def test_too_low(self):
        with pytest.raises(
            ValueError,
            match=r"Speed must be between 0\.5 and 2\.0",
        ):
            validate_speed(0.4)

    def test_too_high(self):
        with pytest.raises(
            ValueError,
            match=r"Speed must be between 0\.5 and 2\.0",
        ):
            validate_speed(2.1)


class TestValidatePitchShift:
    @pytest.mark.parametrize("pitch", [-24, 0, 24])
    def test_valid_pitches(self, pitch):
        validate_pitch_shift(pitch)

    def test_too_low(self):
        with pytest.raises(
            ValueError,
            match=r"Pitch shift must be between -24",
        ):
            validate_pitch_shift(-25)

    def test_too_high(self):
        with pytest.raises(
            ValueError,
            match=r"Pitch shift must be between -24",
        ):
            validate_pitch_shift(25)


class TestValidateModel:
    @pytest.mark.parametrize("model", ["sona_speech_1", "sona_speech_2_flash"])
    def test_valid_models(self, model):
        validate_model(model)

    def test_invalid_model(self):
        with pytest.raises(ValueError, match=r'Invalid model: "bad_model"'):
            validate_model("bad_model")


class TestResolveApiKey:
    def test_returns_key_when_set(self):
        env = {"SUPERTONE_API_KEY": "test-key-123"}
        with patch.dict(os.environ, env):
            assert resolve_api_key() == "test-key-123"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="SUPERTONE_API_KEY environment variable",
            ):
                resolve_api_key()

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"SUPERTONE_API_KEY": ""}):
            with pytest.raises(
                ValueError,
                match="SUPERTONE_API_KEY environment variable",
            ):
                resolve_api_key()


class TestResolveOutputDir:
    def test_returns_default_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_output_dir()
            assert "~" not in result
            assert os.path.isabs(result)
            assert "supertone-tts-output" in result

    def test_returns_custom_when_set(self):
        env = {"SUPERTONE_OUTPUT_DIR": "/custom/dir"}
        with patch.dict(os.environ, env):
            result = resolve_output_dir()
            assert "custom" in result


class TestResolveOutputMode:
    def test_default_is_files(self):
        with patch.dict(os.environ, {}, clear=True):
            assert resolve_output_mode() == "files"

    @pytest.mark.parametrize("mode", ["files", "resources", "both"])
    def test_valid_modes(self, mode):
        env = {"SUPERTONE_MCP_OUTPUT_MODE": mode}
        with patch.dict(os.environ, env):
            assert resolve_output_mode() == mode

    def test_case_insensitive(self):
        env = {"SUPERTONE_MCP_OUTPUT_MODE": "RESOURCES"}
        with patch.dict(os.environ, env):
            assert resolve_output_mode() == "resources"

    def test_invalid_mode_raises(self):
        env = {"SUPERTONE_MCP_OUTPUT_MODE": "invalid"}
        with patch.dict(os.environ, env):
            with pytest.raises(
                ValueError,
                match='Invalid output mode: "invalid"',
            ):
                resolve_output_mode()


class TestResolveVoiceId:
    def test_default_voice(self):
        with patch.dict(os.environ, {}, clear=True):
            assert resolve_voice_id() == "2d5a380030e78fcab0c82a"

    def test_custom_voice_from_env(self):
        env = {"SUPERTONE_MCP_VOICE_ID": "my-custom-voice"}
        with patch.dict(os.environ, env):
            assert resolve_voice_id() == "my-custom-voice"


class TestResolveAutoplay:
    def test_default_is_true(self):
        with patch.dict(os.environ, {}, clear=True):
            assert resolve_autoplay() is True

    @pytest.mark.parametrize("val", ["true", "1", "yes", ""])
    def test_truthy_values(self, val):
        env = {"SUPERTONE_MCP_AUTOPLAY": val}
        with patch.dict(os.environ, env):
            assert resolve_autoplay() is True

    @pytest.mark.parametrize("val", ["false", "0", "no"])
    def test_falsy_values(self, val):
        env = {"SUPERTONE_MCP_AUTOPLAY": val}
        with patch.dict(os.environ, env):
            assert resolve_autoplay() is False

    def test_case_insensitive_disable(self):
        env = {"SUPERTONE_MCP_AUTOPLAY": "FALSE"}
        with patch.dict(os.environ, env):
            assert resolve_autoplay() is False


class TestAutoplay:
    def test_calls_afplay_with_file_path(self):
        with (
            patch("supertone_tts_mcp.tools.sys") as mock_sys,
            patch("supertone_tts_mcp.tools.subprocess.Popen") as mock_popen,
        ):
            mock_sys.platform = "darwin"
            _autoplay("/tmp/test.mp3", None, "mp3")
            mock_popen.assert_called_once_with(
                ["/usr/bin/afplay", "/tmp/test.mp3"],
                stdout=-3,
                stderr=-3,
            )

    def test_resources_mode_creates_temp_file(self):
        with (
            patch("supertone_tts_mcp.tools.sys") as mock_sys,
            patch("supertone_tts_mcp.tools.subprocess.Popen") as mock_popen,
        ):
            mock_sys.platform = "darwin"
            _autoplay(None, b"\xff\xfb\x90\x00", "mp3")
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert call_args[1]["shell"] is True
            assert "afplay" in call_args[0][0]
            assert ".mp3" in call_args[0][0]

    def test_noop_on_non_darwin(self):
        with (
            patch("supertone_tts_mcp.tools.sys") as mock_sys,
            patch("supertone_tts_mcp.tools.subprocess.Popen") as mock_popen,
        ):
            mock_sys.platform = "linux"
            _autoplay("/tmp/test.mp3", None, "mp3")
            mock_popen.assert_not_called()

    def test_oserror_suppressed(self):
        with (
            patch("supertone_tts_mcp.tools.sys") as mock_sys,
            patch(
                "supertone_tts_mcp.tools.subprocess.Popen",
                side_effect=OSError,
            ),
        ):
            mock_sys.platform = "darwin"
            _autoplay("/tmp/test.mp3", None, "mp3")


class TestFormatTtsMetadata:
    def test_without_file_path(self):
        result = format_tts_metadata(
            duration=2.3,
            voice_id="v1",
            language="ko",
            output_format="mp3",
        )
        expected = "Duration: 2.3s | Voice: v1 | Language: ko | Format: mp3"
        assert result == expected

    def test_with_file_path(self):
        result = format_tts_metadata(
            duration=1.0,
            voice_id="v1",
            language="en",
            output_format="wav",
            file_path="/tmp/out.wav",
        )
        expected = (
            "Saved: /tmp/out.wav | Duration: 1.0s"
            " | Voice: v1 | Language: en | Format: wav"
        )
        assert result == expected


class TestFormatTtsResponse:
    def test_produces_exact_format(self):
        resp = TTSResponse(
            file_path="/Users/test/output/2026-03-13_abc123.mp3",
            duration_seconds=2.3,
            voice_id="yuki-01",
            language="en",
            output_format="mp3",
        )
        result = format_tts_response(resp)
        expected = (
            "Audio file saved:"
            " /Users/test/output/2026-03-13_abc123.mp3\n"
            "Duration: 2.3 seconds\n"
            "Voice: yuki-01\n"
            "Language: en\n"
            "Format: mp3"
        )
        assert result == expected


class TestFormatVoiceList:
    def test_with_voices(self):
        voices = [
            VoiceInfo(
                voice_id="sujin-01",
                name="Sujin",
                supported_languages=["ko", "en"],
                supported_styles=["neutral", "happy"],
            ),
            VoiceInfo(
                voice_id="minho-01",
                name="Minho",
                supported_languages=["ko"],
                supported_styles=["neutral"],
            ),
        ]
        result = format_voice_list(voices)
        assert "Found 2 voices:" in result
        assert "1. Name: Sujin" in result
        assert "2. Name: Minho" in result
        assert "Voice ID: sujin-01" in result
        assert "Languages: ko, en" in result
        assert "Styles: neutral, happy" in result

    def test_empty_with_filter(self):
        result = format_voice_list([], language_filter="ja")
        assert result == "No voices found matching language: ja."

    def test_empty_no_filter(self):
        result = format_voice_list([])
        assert result == "No voices found."

    def test_with_language_filter(self):
        voices = [
            VoiceInfo(
                voice_id="v1",
                name="V1",
                supported_languages=["ko"],
                supported_styles=["neutral"],
            ),
        ]
        result = format_voice_list(voices, language_filter="ko")
        assert "Found 1 voices matching language: ko" in result

    def test_filters_prepended_when_any_filter_active(self):
        """v0.2: any non-None filter triggers a 'Filters applied:' header line."""
        voices = [
            VoiceInfo(
                voice_id="v1",
                name="V1",
                supported_languages=["ko"],
                supported_styles=["neutral"],
            ),
        ]
        result = format_voice_list(
            voices, filters={"gender": "female", "language": "ko", "age": None}
        )
        first_line = result.splitlines()[0]
        assert first_line.startswith("Filters applied:")
        assert "gender=female" in first_line
        assert "language=ko" in first_line
        # None values must NOT appear (use the filter prefix to avoid the
        # accidental substring match against `language=`).
        assert " age=" not in first_line
        assert "age=None" not in first_line
        # Numbered list still follows
        assert "Found 1 voices:" in result
        assert "1. Name: V1" in result

    def test_filters_all_none_does_not_render_header(self):
        """All-None filters dict is treated as no filters."""
        voices = [
            VoiceInfo(
                voice_id="v1",
                name="V1",
                supported_languages=["ko"],
                supported_styles=["neutral"],
            ),
        ]
        result = format_voice_list(voices, filters={"gender": None, "language": None})
        assert "Filters applied" not in result
        assert "Found 1 voices:" in result

    def test_filters_empty_result_message(self):
        """v0.2: empty result with active filters returns the filters-empty msg."""
        result = format_voice_list([], filters={"gender": "zzz"})
        assert result == "No voices found matching the filters."


class TestCalculateDuration:
    def test_returns_float_for_valid_file(self, tmp_path):
        mock_audio = MagicMock()
        mock_audio.info.length = 2.345

        with patch(
            "supertone_tts_mcp.tools.MutagenFile",
            return_value=mock_audio,
        ):
            duration = calculate_duration("/tmp/test.mp3")

        assert duration == 2.3

    def test_returns_zero_for_unrecognized(self, tmp_path):
        with patch(
            "supertone_tts_mcp.tools.MutagenFile",
            return_value=None,
        ):
            duration = calculate_duration("/tmp/test.mp3")
        assert duration == 0.0


# --- Tool Handler Tests ---

_AUDIO_CHUNK_A = b"\xff\xfb\x90\x00" * 5
_AUDIO_CHUNK_B = b"\xff\xfb\x90\x00" * 5
_AUDIO_DATA = _AUDIO_CHUNK_A + _AUDIO_CHUNK_B


async def _async_gen_chunks(chunks):
    """Async generator yielding the given chunks."""
    for chunk in chunks:
        yield chunk


def _mock_stream(chunks=None, side_effect=None):
    """Mock for SupertoneClient.synthesize_stream.

    Returns a callable that produces an async generator.
    If side_effect is set, it will be raised on iteration.
    """
    if side_effect is not None:

        async def _error_gen(*args, **kwargs):
            raise side_effect
            yield  # noqa: F841

        return _error_gen

    if chunks is None:
        chunks = [_AUDIO_CHUNK_A, _AUDIO_CHUNK_B]

    def _gen(*args, **kwargs):
        return _async_gen_chunks(chunks)

    return _gen


def _mock_get_voices(voices=None):
    """Mock for SupertoneClient.get_voices."""
    if voices is None:
        voices = [
            {
                "voice_id": "sujin-01",
                "name": "Sujin",
                "supported_languages": ["ko", "en"],
                "supported_styles": ["neutral", "happy"],
            },
            {
                "voice_id": "yuki-01",
                "name": "Yuki",
                "supported_languages": ["ja"],
                "supported_styles": ["neutral"],
            },
            {
                "voice_id": "minho-01",
                "name": "Minho",
                "supported_languages": ["ko"],
                "supported_styles": ["neutral", "sad"],
            },
        ]
    return AsyncMock(return_value=voices)


def _env_files(tmp_path):
    """Standard env dict for files mode tests."""
    return {
        "SUPERTONE_API_KEY": "test-key",
        "SUPERTONE_OUTPUT_DIR": str(tmp_path),
    }


class TestTextToSpeechHandler:
    """Tests for the text_to_speech streaming handler."""

    @pytest.mark.asyncio
    async def test_happy_path(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello world")

        assert "Audio file saved:" in result
        assert str(tmp_path) in result

    @pytest.mark.asyncio
    async def test_streaming_writes_chunks_to_file(self, tmp_path):
        """Verify file contains concatenated chunks."""
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        path = result.split("Audio file saved: ")[1].split("\n")[0]
        assert Path(path).read_bytes() == _AUDIO_DATA

    @pytest.mark.asyncio
    async def test_default_model_is_sona_speech_1(self):
        """DEFAULT_MODEL constant changed to sona_speech_1."""
        from supertone_tts_mcp.constants import DEFAULT_MODEL

        assert DEFAULT_MODEL == "sona_speech_1"

    @pytest.mark.asyncio
    async def test_mutagen_duration(self, tmp_path):
        """Duration calculated via mutagen on file."""
        mock_audio = MagicMock()
        mock_audio.info.length = 3.456

        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
            patch(
                "supertone_tts_mcp.tools.MutagenFile",
                return_value=mock_audio,
            ),
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Duration: 3.5 seconds" in result

    @pytest.mark.asyncio
    async def test_default_voice_id(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Voice: 2d5a380030e78fcab0c82a" in result

    @pytest.mark.asyncio
    async def test_env_voice_id_used(self, tmp_path):
        env = {
            **_env_files(tmp_path),
            "SUPERTONE_MCP_VOICE_ID": "custom-voice-99",
            "SUPERTONE_MCP_AUTOPLAY": "false",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Voice: custom-voice-99" in result

    @pytest.mark.asyncio
    async def test_default_language(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Language: ko" in result

    @pytest.mark.asyncio
    async def test_empty_text_returns_error(self):
        env = {"SUPERTONE_API_KEY": "test-key"}
        with patch.dict(os.environ, env):
            result = await text_to_speech(text="")
        assert result == "Text must not be empty."

    @pytest.mark.asyncio
    async def test_invalid_language_returns_error(self):
        env = {"SUPERTONE_API_KEY": "test-key"}
        with patch.dict(os.environ, env):
            result = await text_to_speech(text="Hello", language="zz")
        assert 'Invalid language: "zz"' in result

    @pytest.mark.asyncio
    async def test_auth_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        expected = "Authentication failed. Please verify your SUPERTONE_API_KEY."
        assert result == expected

    @pytest.mark.asyncio
    async def test_rate_limit_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        expected = "Rate limit exceeded. Please wait and try again."
        assert result == expected

    @pytest.mark.asyncio
    async def test_server_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream(side_effect=SupertoneServerError(503))
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        expected = "Supertone API server error (503). Please try again later."
        assert result == expected

    @pytest.mark.asyncio
    async def test_server_error_cleans_partial_file(self, tmp_path):
        """Mid-stream server error should clean up partial."""
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream(side_effect=SupertoneServerError(500))
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "server error" in result.lower()
        # No partial files should remain
        files = list(tmp_path.iterdir())
        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_connection_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream(
                side_effect=SupertoneConnectionError()
            )
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Failed to connect" in result

    @pytest.mark.asyncio
    async def test_file_written_with_correct_bytes(self, tmp_path):
        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        fpath = result.split("Audio file saved: ")[1].split("\n")[0]
        assert Path(fpath).read_bytes() == _AUDIO_DATA

    @pytest.mark.asyncio
    async def test_api_key_missing_returns_error(self):
        with patch.dict(os.environ, {}, clear=True):
            result = await text_to_speech(text="Hello")
        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_resources_mode_returns_audio_content(self):
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "resources",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], AudioContent)
        assert result[0].mimeType == "audio/mpeg"
        assert isinstance(result[1], TextContent)
        assert "Saved:" not in result[1].text

    @pytest.mark.asyncio
    async def test_resources_mode_no_file_written(self, tmp_path):
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "resources",
            "SUPERTONE_OUTPUT_DIR": str(tmp_path),
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            await text_to_speech(text="Hello")

        assert list(tmp_path.iterdir()) == []

    @pytest.mark.asyncio
    async def test_resources_mode_collects_in_memory(self):
        """Resources mode collects all chunks in memory."""
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "resources",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        decoded = base64.b64decode(result[0].data)
        assert decoded == _AUDIO_DATA

    @pytest.mark.asyncio
    async def test_both_mode_returns_audio_and_saves(self, tmp_path):
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "both",
            "SUPERTONE_OUTPUT_DIR": str(tmp_path),
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], AudioContent)
        assert isinstance(result[1], TextContent)
        assert "Saved:" in result[1].text
        # File written
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].read_bytes() == _AUDIO_DATA

    @pytest.mark.asyncio
    async def test_resources_mode_wav_mime_type(self):
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "resources",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream(chunks=[b"\x00" * 10])
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello", output_format="wav")

        assert result[0].mimeType == "audio/wav"

    @pytest.mark.asyncio
    async def test_invalid_output_mode_returns_error(self):
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "invalid",
        }
        with patch.dict(os.environ, env):
            result = await text_to_speech(text="Hello")
        assert 'Invalid output mode: "invalid"' in result

    @pytest.mark.asyncio
    async def test_resources_mode_base64_encoding(self):
        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "resources",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        decoded = base64.b64decode(result[0].data)
        assert decoded == _AUDIO_DATA

    @pytest.mark.asyncio
    async def test_autoplay_called_after_streaming(self, tmp_path):
        env = {
            **_env_files(tmp_path),
            "SUPERTONE_MCP_AUTOPLAY": "true",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
            patch("supertone_tts_mcp.tools._autoplay") as mock_ap,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            await text_to_speech(text="Hello")

        mock_ap.assert_called_once()
        call_args = mock_ap.call_args
        assert call_args[0][2] == "mp3"

    @pytest.mark.asyncio
    async def test_autoplay_not_called_when_disabled(self, tmp_path):
        env = {
            **_env_files(tmp_path),
            "SUPERTONE_MCP_AUTOPLAY": "false",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
            patch("supertone_tts_mcp.tools._autoplay") as mock_ap,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _mock_stream()
            inst.aclose = AsyncMock()

            await text_to_speech(text="Hello")

        mock_ap.assert_not_called()

    @pytest.mark.asyncio
    async def test_mid_stream_error_cleans_partial(self, tmp_path):
        """Unexpected error during streaming cleans up."""

        async def _failing_gen(*args, **kwargs):
            yield b"\xff" * 10
            raise RuntimeError("network glitch")

        with (
            patch.dict(os.environ, _env_files(tmp_path)),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.synthesize_stream = _failing_gen
            inst.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Streaming error" in result
        # Partial file should be cleaned up
        files = list(tmp_path.iterdir())
        assert len(files) == 0


def _mock_search_voices(voices=None):
    """Mock for SupertoneClient.search_voices."""
    if voices is None:
        voices = [
            {
                "voice_id": "sujin-01",
                "name": "Sujin",
                "supported_languages": ["ko", "en"],
                "supported_styles": ["neutral", "happy"],
            },
            {
                "voice_id": "yuki-01",
                "name": "Yuki",
                "supported_languages": ["ja"],
                "supported_styles": ["neutral"],
            },
            {
                "voice_id": "minho-01",
                "name": "Minho",
                "supported_languages": ["ko"],
                "supported_styles": ["neutral", "sad"],
            },
        ]
    return AsyncMock(return_value=voices)


class TestSearchVoiceHandler:
    """Tests for the search_voice handler (replaces list_voices in v0.2)."""

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self):
        """AC: search_voice() with no parameters returns all voices in numbered list."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices()
            inst.aclose = AsyncMock()

            result = await search_voice()

        # Header should NOT include "Filters applied:" when no filters set
        assert "Filters applied" not in result
        assert "Found 3 voices:" in result
        assert "1. Name: Sujin" in result
        assert "2. Name: Yuki" in result
        assert "3. Name: Minho" in result
        # Mock called with all None filters
        inst.search_voices.assert_called_once_with(
            name=None,
            description=None,
            language=None,
            gender=None,
            age=None,
            use_case=None,
            style=None,
            model=None,
        )

    @pytest.mark.asyncio
    async def test_single_filter_passes_through(self):
        """AC: a single filter is forwarded to the SDK call."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices(
                voices=[
                    {
                        "voice_id": "v1",
                        "name": "V1",
                        "supported_languages": ["ko"],
                        "supported_styles": ["neutral"],
                    }
                ]
            )
            inst.aclose = AsyncMock()

            result = await search_voice(gender="female")

        inst.search_voices.assert_called_once_with(
            name=None,
            description=None,
            language=None,
            gender="female",
            age=None,
            use_case=None,
            style=None,
            model=None,
        )
        assert "Filters applied: gender=female" in result
        assert "Found 1 voices" in result

    @pytest.mark.asyncio
    async def test_multiple_filters_pass_through_and_show_in_header(self):
        """AC: multiple filters reach the SDK and appear in the header line."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices()
            inst.aclose = AsyncMock()

            result = await search_voice(gender="female", language="ko")

        inst.search_voices.assert_called_once_with(
            name=None,
            description=None,
            language="ko",
            gender="female",
            age=None,
            use_case=None,
            style=None,
            model=None,
        )
        # Both filters must appear in the header (order independent)
        first_line = result.splitlines()[0]
        assert first_line.startswith("Filters applied:")
        assert "gender=female" in first_line
        assert "language=ko" in first_line

    @pytest.mark.asyncio
    async def test_all_filters_pass_through(self):
        """All eight filters are forwarded with the correct keyword names."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices(voices=[])
            inst.aclose = AsyncMock()

            await search_voice(
                language="ko",
                gender="female",
                age="young_adult",
                use_case="narration",
                style="happy",
                model="sona_speech_1",
                name="Su",
                description="warm",
            )

        inst.search_voices.assert_called_once_with(
            name="Su",
            description="warm",
            language="ko",
            gender="female",
            age="young_adult",
            use_case="narration",
            style="happy",
            model="sona_speech_1",
        )

    @pytest.mark.asyncio
    async def test_empty_result_with_filter(self):
        """AC: with filters and 0 results returns the filtered empty string."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices(voices=[])
            inst.aclose = AsyncMock()

            result = await search_voice(gender="zzz")

        assert result == "No voices found matching the filters."

    @pytest.mark.asyncio
    async def test_empty_result_without_filter(self):
        """No filters + 0 results falls back to plain 'No voices found.'"""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices(voices=[])
            inst.aclose = AsyncMock()

            result = await search_voice()

        assert result == "No voices found."

    @pytest.mark.asyncio
    async def test_invalid_language_filter_short_circuits(self):
        """validate_language is still applied when a language filter is provided."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices()
            inst.aclose = AsyncMock()

            result = await search_voice(language="zz")

        assert 'Invalid language: "zz"' in result
        # SDK must NOT be called when language validation fails
        inst.search_voices.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_error_caught(self):
        """AC: API 401 returns the standard auth error string."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = AsyncMock(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await search_voice()

        expected = "Authentication failed. Please verify your SUPERTONE_API_KEY."
        assert result == expected

    @pytest.mark.asyncio
    async def test_rate_limit_error_caught(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = AsyncMock(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await search_voice()

        assert "Rate limit exceeded" in result

    @pytest.mark.asyncio
    async def test_server_error_caught(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = AsyncMock(side_effect=SupertoneServerError(502))
            inst.aclose = AsyncMock()

            result = await search_voice()

        assert "server error (502)" in result

    @pytest.mark.asyncio
    async def test_connection_error_caught(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            result = await search_voice()

        assert "Failed to connect" in result

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error(self):
        """Without SUPERTONE_API_KEY, return the validation msg without hitting SDK."""
        with patch.dict(os.environ, {}, clear=True):
            result = await search_voice()
        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_success(self):
        """aclose() is invoked on the happy path (no SDK leaks)."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = _mock_search_voices()
            inst.aclose = AsyncMock()

            await search_voice()

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_error(self):
        """aclose() is invoked even when the SDK raises."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.search_voices = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            await search_voice()

        inst.aclose.assert_awaited_once()
