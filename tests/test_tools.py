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
    format_credit_balance,
    format_tts_metadata,
    format_tts_response,
    format_voice_detail,
    format_voice_list,
    format_voice_samples,
    get_credit_balance,
    get_voice,
    preview_voice,
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


# --- ISSUE-016: format_voice_detail / format_credit_balance / handlers ---


def _make_voice_detail(
    *,
    voice_id: str = "v1",
    name: str = "Sujin",
    description: str | None = "A warm, professional female voice.",
    age: str | None = "young_adult",
    gender: str | None = "female",
    use_cases: list[str] | None = None,
    use_case: str | None = None,
    supported_languages: list[str] | None = None,
    styles: list[str] | None = None,
    models: list[str] | None = None,
    samples: list | None = None,
    thumbnail_image_url: str | None = "https://cdn.example.com/v1.png",
):
    """Build a VoiceDetailDict-shaped dict for tests.

    All optional/nullable fields are typed explicitly per RL-005 so callers
    can pass `None` to exercise null-handling branches without type errors.
    """
    detail: dict = {
        "voice_id": voice_id,
        "name": name,
    }
    if description is not None:
        detail["description"] = description
    if age is not None:
        detail["age"] = age
    if gender is not None:
        detail["gender"] = gender
    if use_cases is not None:
        detail["use_cases"] = use_cases
    if use_case is not None:
        detail["use_case"] = use_case
    if supported_languages is not None:
        detail["supported_languages"] = supported_languages
    if styles is not None:
        detail["styles"] = styles
    if models is not None:
        detail["models"] = models
    if samples is not None:
        detail["samples"] = samples
    if thumbnail_image_url is not None:
        detail["thumbnail_image_url"] = thumbnail_image_url
    return detail


def _make_credit_balance(*, balance: float | None = 12345.0):
    """Build a CreditBalanceDict-shaped dict for tests (per RL-005)."""
    return {"balance": balance}


class TestFormatVoiceDetail:
    """Pure formatter — no I/O — for VoiceDetailDict (ISSUE-016 AC #1)."""

    def test_renders_all_fields(self):
        detail = _make_voice_detail(
            use_cases=["narration", "advertisement"],
            supported_languages=["ko", "en"],
            styles=["neutral", "happy", "sad"],
            models=["sona_speech_1"],
            samples=[{"x": 1}, {"x": 2}, {"x": 3}],
        )
        result = format_voice_detail(detail)
        # Required fields rendered as labeled lines
        assert "Voice ID: v1" in result
        assert "Name: Sujin" in result
        assert "Description: A warm, professional female voice." in result
        assert "Age: young_adult" in result
        assert "Gender: female" in result
        # Joined list fields
        assert "Use cases: narration, advertisement" in result
        assert "Languages: ko, en" in result
        assert "Styles: neutral, happy, sad" in result
        assert "Models: sona_speech_1" in result
        # Sample COUNT, not URLs (URLs are preview_voice's domain)
        assert "Samples: 3" in result
        # No sample URLs leaked into the formatter output
        assert "https://" not in result.split("Thumbnail:")[0]
        # Thumbnail rendered when present
        assert "Thumbnail: https://cdn.example.com/v1.png" in result
        # Hint about preview_voice
        assert "preview_voice" in result

    def test_omits_thumbnail_when_missing(self):
        detail = _make_voice_detail(
            thumbnail_image_url=None,
            samples=[],
            use_cases=["narration"],
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
        )
        result = format_voice_detail(detail)
        assert "Thumbnail" not in result
        # Zero samples is still expressed (sanity)
        assert "Samples: 0" in result

    def test_zero_samples_when_field_missing(self):
        """`samples` may be absent entirely (NotRequired)."""
        detail = _make_voice_detail(
            samples=None,
            use_cases=["narration"],
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
        )
        result = format_voice_detail(detail)
        assert "Samples: 0" in result

    def test_falls_back_to_singular_use_case(self):
        """Some SDK payloads expose only `use_case` (singular)."""
        detail = _make_voice_detail(
            use_cases=None,
            use_case="narration",
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
            samples=[],
        )
        result = format_voice_detail(detail)
        assert "Use cases: narration" in result

    def test_collapses_missing_optional_strings_to_dash(self):
        detail = _make_voice_detail(
            description=None,
            age=None,
            gender=None,
            use_cases=None,
            use_case=None,
            supported_languages=None,
            styles=None,
            models=None,
            samples=None,
            thumbnail_image_url=None,
        )
        result = format_voice_detail(detail)
        assert "Description: -" in result
        assert "Age: -" in result
        assert "Gender: -" in result
        assert "Use cases: -" in result
        assert "Languages: -" in result
        assert "Styles: -" in result
        assert "Models: -" in result
        assert "Samples: 0" in result
        assert "Thumbnail" not in result

    def test_does_not_leak_sample_urls(self):
        """Per AC: sample URLs must not appear in this formatter's output."""
        detail = _make_voice_detail(
            samples=[
                {
                    "language": "ko",
                    "style": "happy",
                    "model": "sona_speech_1",
                    "url": "https://cdn.example.com/sujin-happy.wav",
                }
            ],
            supported_languages=["ko"],
            styles=["happy"],
            models=["sona_speech_1"],
            use_cases=["narration"],
        )
        result = format_voice_detail(detail)
        # The thumbnail URL is allowed but the sample URL must not appear.
        assert "sujin-happy.wav" not in result


class TestFormatCreditBalance:
    """Pure formatter — no I/O — for CreditBalanceDict (ISSUE-016 AC #4)."""

    def test_renders_integer_balance_with_thousands_separator(self):
        result = format_credit_balance(_make_credit_balance(balance=12345.0))
        # UX spec single-line canonical form
        assert result == "Credit balance: 12,345 chars remaining."

    def test_renders_large_balance(self):
        result = format_credit_balance(_make_credit_balance(balance=1_234_567.0))
        assert "1,234,567 chars" in result

    def test_renders_fractional_balance(self):
        result = format_credit_balance(_make_credit_balance(balance=12345.5))
        assert "12,345.50" in result or "12,345.5" in result

    def test_renders_none_balance_as_unknown(self):
        result = format_credit_balance(_make_credit_balance(balance=None))
        assert "unknown" in result
        assert "chars remaining" in result

    def test_renders_optional_plan_and_expiry_when_present(self):
        """Forward-compat path: SDK may add plan/expires_at."""
        payload: dict = {
            "balance": 12345.0,
            "plan": "pro",
            "expires_at": "2026-12-31",
        }
        result = format_credit_balance(payload)
        lines = result.splitlines()
        assert lines[0] == "Credit balance: 12,345 chars remaining."
        assert "Plan: pro" in lines
        assert "Expires: 2026-12-31" in lines


class TestGetVoiceHandler:
    """Tests for the `get_voice(voice_id)` handler."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_formatted_detail(self):
        """AC #1: returns voice_id, name, description, age, gender, use_cases,
        languages, styles, models, and sample count."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            name="Sujin",
            use_cases=["narration"],
            supported_languages=["ko", "en"],
            styles=["neutral", "happy"],
            models=["sona_speech_1"],
            samples=[{"x": 1}, {"x": 2}],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await get_voice("v1")

        inst.get_voice.assert_called_once_with(voice_id="v1")
        assert "Voice ID: v1" in result
        assert "Name: Sujin" in result
        assert "Description:" in result
        assert "Age:" in result
        assert "Gender:" in result
        assert "Use cases: narration" in result
        assert "Languages: ko, en" in result
        assert "Styles: neutral, happy" in result
        assert "Models: sona_speech_1" in result
        assert "Samples: 2" in result

    @pytest.mark.asyncio
    async def test_empty_voice_id_returns_validation_error_without_api_call(self):
        """AC #2: empty voice_id is rejected before any API call."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await get_voice("")

        assert "voice_id must not be empty" in result
        # No SDK or constructor call
        MC.assert_not_called()
        inst.get_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_voice_id_returns_validation_error_without_api_call(self):
        """AC #2: whitespace-only voice_id is rejected before any API call."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await get_voice("   ")

        assert "voice_id must not be empty" in result
        MC.assert_not_called()
        inst.get_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_error_returns_formatted_string(self):
        """AC #3: SupertoneAuthError -> auth error string."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await get_voice("v1")

        assert result == "Authentication failed. Please verify your SUPERTONE_API_KEY."

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await get_voice("v1")

        assert "Rate limit exceeded" in result

    @pytest.mark.asyncio
    async def test_server_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneServerError(503))
            inst.aclose = AsyncMock()

            result = await get_voice("v1")

        assert "server error (503)" in result

    @pytest.mark.asyncio
    async def test_connection_error_returns_formatted_string(self):
        """Per RL-002: each handler must cover the connection-error branch."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            result = await get_voice("v1")

        assert "Failed to connect" in result

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error_without_api_call(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("supertone_tts_mcp.tools.SupertoneClient") as MC:
                result = await get_voice("v1")
                MC.assert_not_called()
        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_success(self):
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            use_cases=["narration"],
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            await get_voice("v1")

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_error(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            await get_voice("v1")

        inst.aclose.assert_awaited_once()


class TestGetCreditBalanceHandler:
    """Tests for the `get_credit_balance()` handler (ISSUE-016 AC #4)."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_formatted_balance(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(
                return_value=_make_credit_balance(balance=12345.0)
            )
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        inst.get_credit_balance.assert_called_once_with()
        # Single-line canonical form
        assert result == "Credit balance: 12,345 chars remaining."

    @pytest.mark.asyncio
    async def test_happy_path_with_plan_and_expiry(self):
        env = {"SUPERTONE_API_KEY": "key"}
        payload = {
            "balance": 12345.0,
            "plan": "pro",
            "expires_at": "2026-12-31",
        }
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(return_value=payload)
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        lines = result.splitlines()
        assert lines[0] == "Credit balance: 12,345 chars remaining."
        assert "Plan: pro" in lines
        assert "Expires: 2026-12-31" in lines

    @pytest.mark.asyncio
    async def test_none_balance_renders_unknown(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(
                return_value=_make_credit_balance(balance=None)
            )
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        assert "unknown" in result

    @pytest.mark.asyncio
    async def test_auth_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        assert result == "Authentication failed. Please verify your SUPERTONE_API_KEY."

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        assert "Rate limit exceeded" in result

    @pytest.mark.asyncio
    async def test_server_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(side_effect=SupertoneServerError(502))
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        assert "server error (502)" in result

    @pytest.mark.asyncio
    async def test_connection_error_returns_formatted_string(self):
        """Per RL-002: each handler must cover the connection-error branch."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            result = await get_credit_balance()

        assert "Failed to connect" in result

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error_without_api_call(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("supertone_tts_mcp.tools.SupertoneClient") as MC:
                result = await get_credit_balance()
                MC.assert_not_called()
        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_success(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(
                return_value=_make_credit_balance(balance=12345.0)
            )
            inst.aclose = AsyncMock()

            await get_credit_balance()

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_error(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_credit_balance = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            await get_credit_balance()

        inst.aclose.assert_awaited_once()


# --- ISSUE-017: format_voice_samples / preview_voice handler ---


def _make_sample(
    *,
    language: str = "ko",
    style: str = "neutral",
    model: str = "sona_speech_1",
    url: str = "https://cdn.example.com/sujin-neutral.wav",
) -> dict:
    """Build a SampleDict-shaped dict for tests."""
    return {
        "language": language,
        "style": style,
        "model": model,
        "url": url,
    }


class TestFormatVoiceSamples:
    """Pure formatter — no I/O — for the samples list (ISSUE-017 AC #1)."""

    def test_renders_all_samples_with_no_filters(self):
        """Given 4 samples and no filters, all 4 lines are rendered with metadata."""
        samples = [
            _make_sample(
                language="ko",
                style="neutral",
                model="sona_speech_1",
                url="https://cdn.example.com/s1.wav",
            ),
            _make_sample(
                language="ko",
                style="happy",
                model="sona_speech_1",
                url="https://cdn.example.com/s2.wav",
            ),
            _make_sample(
                language="en",
                style="neutral",
                model="sona_speech_1",
                url="https://cdn.example.com/s3.wav",
            ),
            _make_sample(
                language="ja",
                style="sad",
                model="sona_speech_2",
                url="https://cdn.example.com/s4.wav",
            ),
        ]
        filters: dict[str, str | None] = {
            "language": None,
            "style": None,
            "model": None,
        }
        out = format_voice_samples(samples, filters)
        lines = out.splitlines()
        assert len(lines) == 4
        assert lines[0] == (
            "1. [language=ko, style=neutral, model=sona_speech_1] "
            "https://cdn.example.com/s1.wav"
        )
        assert lines[1].startswith("2. [language=ko, style=happy, model=sona_speech_1]")
        assert lines[1].endswith("https://cdn.example.com/s2.wav")
        assert lines[2].startswith(
            "3. [language=en, style=neutral, model=sona_speech_1]"
        )
        assert lines[3].startswith("4. [language=ja, style=sad, model=sona_speech_2]")

    def test_filter_by_language_only(self):
        samples = [
            _make_sample(language="ko", style="happy"),
            _make_sample(language="en", style="happy"),
            _make_sample(language="ko", style="neutral"),
        ]
        out = format_voice_samples(
            samples, {"language": "ko", "style": None, "model": None}
        )
        lines = out.splitlines()
        assert len(lines) == 2
        assert all("language=ko" in line for line in lines)
        assert "language=en" not in out

    def test_filter_by_style_only(self):
        samples = [
            _make_sample(language="ko", style="happy"),
            _make_sample(language="en", style="happy"),
            _make_sample(language="ko", style="neutral"),
        ]
        out = format_voice_samples(
            samples, {"language": None, "style": "happy", "model": None}
        )
        lines = out.splitlines()
        assert len(lines) == 2
        assert all("style=happy" in line for line in lines)

    def test_filter_by_model_only(self):
        samples = [
            _make_sample(model="sona_speech_1"),
            _make_sample(model="sona_speech_2"),
            _make_sample(model="sona_speech_2_flash"),
        ]
        out = format_voice_samples(
            samples, {"language": None, "style": None, "model": "sona_speech_2"}
        )
        lines = out.splitlines()
        # Exact-match filter must NOT include sona_speech_2_flash.
        assert len(lines) == 1
        assert "model=sona_speech_2]" in lines[0]

    def test_combined_filters_narrow_correctly(self):
        samples = [
            _make_sample(language="ko", style="happy", model="sona_speech_1"),
            _make_sample(language="ko", style="neutral", model="sona_speech_1"),
            _make_sample(language="en", style="happy", model="sona_speech_1"),
            _make_sample(language="ko", style="happy", model="sona_speech_2"),
        ]
        out = format_voice_samples(
            samples,
            {"language": "ko", "style": "happy", "model": "sona_speech_1"},
        )
        lines = out.splitlines()
        assert len(lines) == 1
        assert "[language=ko, style=happy, model=sona_speech_1]" in lines[0]

    def test_empty_samples_list_returns_no_preview_samples_message(self):
        """AC #5: zero samples => 'no preview samples' message."""
        out = format_voice_samples([], {"language": None, "style": None, "model": None})
        assert out == "This voice has no preview samples."

    def test_none_samples_returns_no_preview_samples_message(self):
        """AC #5: samples=None => 'no preview samples' message."""
        out = format_voice_samples(
            None, {"language": None, "style": None, "model": None}
        )
        assert out == "This voice has no preview samples."

    def test_no_match_returns_no_matching_samples_message(self):
        """AC #4: samples exist but filters match none."""
        samples = [
            _make_sample(language="ko"),
            _make_sample(language="en"),
        ]
        out = format_voice_samples(
            samples, {"language": "ja", "style": None, "model": None}
        )
        assert out == "No matching samples for the given filters."

    def test_numbering_resets_at_one_for_filtered_subset(self):
        """Per UX spec: numbering is 1..N over the FILTERED list, not the full list."""
        samples = [
            _make_sample(language="en"),
            _make_sample(language="ko", url="https://cdn.example.com/a.wav"),
            _make_sample(language="ko", url="https://cdn.example.com/b.wav"),
        ]
        out = format_voice_samples(
            samples, {"language": "ko", "style": None, "model": None}
        )
        lines = out.splitlines()
        assert lines[0].startswith("1. ")
        assert lines[1].startswith("2. ")


class TestPreviewVoiceHandler:
    """Tests for the `preview_voice(voice_id, ...)` handler."""

    @pytest.mark.asyncio
    async def test_happy_path_no_filters_returns_all_samples(self):
        """AC #1: 4 samples + no filters => 4 sample lines."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko", "en", "ja"],
            styles=["neutral", "happy", "sad"],
            models=["sona_speech_1", "sona_speech_2"],
            use_cases=["narration"],
            samples=[
                _make_sample(
                    language="ko",
                    style="neutral",
                    model="sona_speech_1",
                    url="https://cdn.example.com/s1.wav",
                ),
                _make_sample(
                    language="ko",
                    style="happy",
                    model="sona_speech_1",
                    url="https://cdn.example.com/s2.wav",
                ),
                _make_sample(
                    language="en",
                    style="neutral",
                    model="sona_speech_1",
                    url="https://cdn.example.com/s3.wav",
                ),
                _make_sample(
                    language="ja",
                    style="sad",
                    model="sona_speech_2",
                    url="https://cdn.example.com/s4.wav",
                ),
            ],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        inst.get_voice.assert_called_once_with(voice_id="v1")
        lines = result.splitlines()
        assert len(lines) == 4
        for n in (1, 2, 3, 4):
            assert any(line.startswith(f"{n}. [") for line in lines), (
                f"missing line {n}: {result}"
            )
        # All URLs present
        assert "s1.wav" in result
        assert "s4.wav" in result

    @pytest.mark.asyncio
    async def test_filter_by_language_narrows_results(self):
        """AC #2: language="ko" returns only Korean samples."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko", "en"],
            styles=["happy", "neutral"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=[
                _make_sample(language="ko", style="happy"),
                _make_sample(language="en", style="happy"),
                _make_sample(language="ko", style="neutral"),
            ],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1", language="ko")

        lines = result.splitlines()
        assert len(lines) == 2
        assert "language=en" not in result
        assert "language=ko" in result

    @pytest.mark.asyncio
    async def test_combined_filters_narrow_correctly(self):
        """AC #3: language="ko", style="happy" => only matches both."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko", "en"],
            styles=["happy", "neutral"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=[
                _make_sample(
                    language="ko",
                    style="happy",
                    url="https://cdn.example.com/match.wav",
                ),
                _make_sample(language="ko", style="neutral"),
                _make_sample(language="en", style="happy"),
            ],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1", language="ko", style="happy")

        lines = result.splitlines()
        assert len(lines) == 1
        assert "match.wav" in lines[0]
        assert "[language=ko, style=happy, model=sona_speech_1]" in lines[0]

    @pytest.mark.asyncio
    async def test_filter_by_model_narrows(self):
        """AC #2: model filter dimension narrows results."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko"],
            styles=["happy"],
            models=["sona_speech_1", "sona_speech_2"],
            use_cases=["narration"],
            samples=[
                _make_sample(model="sona_speech_1"),
                _make_sample(model="sona_speech_2"),
            ],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1", model="sona_speech_2")

        lines = result.splitlines()
        assert len(lines) == 1
        assert "model=sona_speech_2]" in lines[0]

    @pytest.mark.asyncio
    async def test_filter_by_style_narrows(self):
        """AC #2: style filter dimension narrows results."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko"],
            styles=["happy", "neutral"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=[
                _make_sample(style="happy"),
                _make_sample(style="neutral"),
            ],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1", style="neutral")

        lines = result.splitlines()
        assert len(lines) == 1
        assert "style=neutral" in lines[0]

    @pytest.mark.asyncio
    async def test_empty_samples_returns_no_preview_message(self):
        """AC #5: voice has no samples => 'This voice has no preview samples.'"""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=[],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        assert result == "This voice has no preview samples."

    @pytest.mark.asyncio
    async def test_samples_field_absent_returns_no_preview_message(self):
        """AC #5: samples field absent entirely (NotRequired) => same message."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=None,
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        assert result == "This voice has no preview samples."

    @pytest.mark.asyncio
    async def test_no_match_filters_returns_no_matching_message(self):
        """AC #4: samples exist but filters match none."""
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko", "en"],
            styles=["happy"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=[
                _make_sample(language="ko"),
                _make_sample(language="en"),
            ],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            result = await preview_voice("v1", language="ja")

        assert result == "No matching samples for the given filters."

    @pytest.mark.asyncio
    async def test_empty_voice_id_returns_validation_error_without_api_call(self):
        """AC #6: empty voice_id rejected before any API call."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await preview_voice("")

        assert "voice_id must not be empty" in result
        MC.assert_not_called()
        inst.get_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_voice_id_returns_validation_error_without_api_call(self):
        """AC #6: whitespace-only voice_id rejected before any API call."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await preview_voice("   ")

        assert "voice_id must not be empty" in result
        MC.assert_not_called()
        inst.get_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_error_returns_formatted_string(self):
        """AC #7: SupertoneAuthError -> formatted auth error."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        assert result == "Authentication failed. Please verify your SUPERTONE_API_KEY."

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        assert "Rate limit exceeded" in result

    @pytest.mark.asyncio
    async def test_server_error_returns_formatted_string(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneServerError(503))
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        assert "server error (503)" in result

    @pytest.mark.asyncio
    async def test_connection_error_returns_formatted_string(self):
        """Per RL-002: each handler must cover the connection-error branch."""
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            result = await preview_voice("v1")

        assert "Failed to connect" in result

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error_without_api_call(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("supertone_tts_mcp.tools.SupertoneClient") as MC:
                result = await preview_voice("v1")
                MC.assert_not_called()
        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_success(self):
        env = {"SUPERTONE_API_KEY": "key"}
        detail = _make_voice_detail(
            voice_id="v1",
            supported_languages=["ko"],
            styles=["neutral"],
            models=["sona_speech_1"],
            use_cases=["narration"],
            samples=[_make_sample()],
        )
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(return_value=detail)
            inst.aclose = AsyncMock()

            await preview_voice("v1")

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_error(self):
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.get_voice = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            await preview_voice("v1")

        inst.aclose.assert_awaited_once()


# --- ISSUE-018: predict_duration handler ---


class TestPredictDurationHandler:
    """Tests for the `predict_duration(text, ...)` handler."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_formatted_duration(self):
        """AC #1: mocked client returns 2.34 => exact UX spec output."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=2.34)
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi")

        assert result == (
            "Predicted duration: 2.34s (credit usage is proportional to duration)."
        )

    @pytest.mark.asyncio
    async def test_happy_path_uses_two_decimal_format(self):
        """Duration formatted to two decimals even when value is whole."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=3.0)
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hello world")

        # Per UX spec §4.7: "Predicted duration: 2.34s ..." — two decimals.
        assert result.startswith("Predicted duration: 3.00s")
        assert result.endswith("(credit usage is proportional to duration).")

    @pytest.mark.asyncio
    async def test_text_over_300_chars_returns_validation_error_without_api_call(self):
        """AC #2: text length >300 chars rejected before any API call."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        long_text = "a" * 301
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text=long_text)

        assert "exceeds the maximum length of 300 characters" in result
        assert "received: 301" in result
        MC.assert_not_called()
        inst.predict_duration.assert_not_called()

    @pytest.mark.asyncio
    async def test_text_exactly_300_chars_passes_validation(self):
        """Boundary: 300 chars is allowed (edge case per UX spec §4.1)."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        text_300 = "a" * 300
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=12.5)
            inst.aclose = AsyncMock()

            result = await predict_duration(text=text_300)

        # Validation passed and the API was invoked.
        inst.predict_duration.assert_awaited_once()
        assert result.startswith("Predicted duration: 12.50s")

    @pytest.mark.asyncio
    async def test_empty_text_returns_validation_error_without_api_call(self):
        """Empty text rejected before any API call (consistent with text_to_speech)."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text="")

        assert result == "Text must not be empty."
        MC.assert_not_called()
        inst.predict_duration.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_language_returns_validation_error(self):
        """AC #3: invalid language rejected before any API call."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi", language="zz")

        assert 'Invalid language: "zz"' in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_output_format_returns_validation_error(self):
        """AC #3: invalid output_format rejected before any API call."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi", output_format="flac")

        assert 'Invalid output format: "flac"' in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_speed_out_of_range_returns_validation_error(self):
        """AC #3: speed outside [0.5, 2.0] rejected before any API call."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi", speed=5.0)

        assert "Speed must be between 0.5 and 2.0" in result
        assert "received: 5.0" in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_pitch_shift_out_of_range_returns_validation_error(self):
        """AC #3: pitch_shift outside [-24, +24] rejected before any API call."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi", pitch_shift=99)

        assert "Pitch shift must be between" in result
        assert "received: 99" in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_model_returns_validation_error(self):
        """Invalid model is validated client-side (same as text_to_speech)."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock()
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi", model="bogus_model")

        assert 'Invalid model: "bogus_model"' in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_default_voice_id_resolves_from_env(self):
        """Default voice_id uses the same env-var resolution as text_to_speech."""
        from supertone_tts_mcp.tools import predict_duration

        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_VOICE_ID": "env-voice-99",
        }
        with (
            patch.dict(os.environ, env, clear=False),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=1.0)
            inst.aclose = AsyncMock()

            await predict_duration(text="hi")

        # The SDK wrapper was called with the env-resolved voice_id.
        call_kwargs = inst.predict_duration.call_args.kwargs
        assert call_kwargs["voice_id"] == "env-voice-99"

    @pytest.mark.asyncio
    async def test_default_voice_id_falls_back_to_constant(self):
        """When no env override, default voice_id is the project constant."""
        from supertone_tts_mcp.constants import DEFAULT_VOICE_ID
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env, clear=True),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=1.0)
            inst.aclose = AsyncMock()

            await predict_duration(text="hi")

        call_kwargs = inst.predict_duration.call_args.kwargs
        assert call_kwargs["voice_id"] == DEFAULT_VOICE_ID

    @pytest.mark.asyncio
    async def test_explicit_voice_id_overrides_env(self):
        """Caller-supplied voice_id wins over the env default."""
        from supertone_tts_mcp.tools import predict_duration

        env = {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_VOICE_ID": "env-voice",
        }
        with (
            patch.dict(os.environ, env, clear=False),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=1.0)
            inst.aclose = AsyncMock()

            await predict_duration(text="hi", voice_id="explicit-voice")

        call_kwargs = inst.predict_duration.call_args.kwargs
        assert call_kwargs["voice_id"] == "explicit-voice"

    @pytest.mark.asyncio
    async def test_defaults_propagate_to_sdk_call(self):
        """When optional params are omitted, project defaults flow to the SDK call."""
        from supertone_tts_mcp.constants import (
            DEFAULT_LANGUAGE,
            DEFAULT_MODEL,
            DEFAULT_PITCH_SHIFT,
            DEFAULT_SPEED,
        )
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env, clear=True),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=1.0)
            inst.aclose = AsyncMock()

            await predict_duration(text="hi")

        call_kwargs = inst.predict_duration.call_args.kwargs
        assert call_kwargs["language"] == DEFAULT_LANGUAGE
        assert call_kwargs["model"] == DEFAULT_MODEL
        assert call_kwargs["speed"] == DEFAULT_SPEED
        assert call_kwargs["pitch_shift"] == DEFAULT_PITCH_SHIFT
        # output_format default for predict_duration matches the SDK default (wav)
        assert call_kwargs["output_format"] == "wav"
        # style default is None
        assert call_kwargs["style"] is None

    @pytest.mark.asyncio
    async def test_explicit_params_pass_through(self):
        """All explicit params flow through to the SDK wrapper."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=1.0)
            inst.aclose = AsyncMock()

            await predict_duration(
                text="hello",
                voice_id="custom-voice",
                language="ja",
                output_format="mp3",
                model="sona_speech_2",
                speed=1.5,
                pitch_shift=-2,
                style="happy",
            )

        call_kwargs = inst.predict_duration.call_args.kwargs
        assert call_kwargs["text"] == "hello"
        assert call_kwargs["voice_id"] == "custom-voice"
        assert call_kwargs["language"] == "ja"
        assert call_kwargs["output_format"] == "mp3"
        assert call_kwargs["model"] == "sona_speech_2"
        assert call_kwargs["speed"] == 1.5
        assert call_kwargs["pitch_shift"] == -2
        assert call_kwargs["style"] == "happy"

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error_without_api_call(self):
        """API key validation runs before any client construction."""
        from supertone_tts_mcp.tools import predict_duration

        with patch.dict(os.environ, {}, clear=True):
            with patch("supertone_tts_mcp.tools.SupertoneClient") as MC:
                result = await predict_duration(text="hi")
                MC.assert_not_called()

        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_auth_error_returns_formatted_string(self):
        """AC #4: SDK 401/403 -> formatted auth error."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi")

        assert result == "Authentication failed. Please verify your SUPERTONE_API_KEY."

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_formatted_string(self):
        """AC #5: SDK 429 -> formatted rate-limit error."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi")

        assert result == "Rate limit exceeded. Please wait and try again."

    @pytest.mark.asyncio
    async def test_server_error_returns_formatted_string(self):
        """SDK 5xx -> formatted server error including the status code."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(side_effect=SupertoneServerError(503))
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi")

        assert result == ("Supertone API server error (503). Please try again later.")

    @pytest.mark.asyncio
    async def test_connection_error_returns_formatted_string(self):
        """Per RL-002: the handler covers the connection-error branch."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi")

        assert result == (
            "Failed to connect to Supertone API. Please check your network connection."
        )

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_success(self):
        """The client is always closed after a successful call."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=1.0)
            inst.aclose = AsyncMock()

            await predict_duration(text="hi")

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_error(self):
        """The client is always closed even when the SDK call fails."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            await predict_duration(text="hi")

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_duration_none_renders_unknown_safely(self):
        """If the SDK omits `duration` (it is Optional), handler does not crash."""
        from supertone_tts_mcp.tools import predict_duration

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.predict_duration = AsyncMock(return_value=None)
            inst.aclose = AsyncMock()

            result = await predict_duration(text="hi")

        # The exact wording is internal — but the response MUST be a string
        # and MUST mention duration somewhere, without raising.
        assert isinstance(result, str)
        assert "duration" in result.lower()


# ---------------------------------------------------------------------------
# ISSUE-019: clone_voice handler + validators
# ---------------------------------------------------------------------------


class TestValidateAudioPath:
    """Tests for `validate_audio_path` (ISSUE-019)."""

    def test_existing_wav_file_passes(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_path

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")
        # Should NOT raise.
        validate_audio_path(str(f))

    def test_existing_mp3_file_passes(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_path

        f = tmp_path / "sample.mp3"
        f.write_bytes(b"\xff\xfb\x90\x00")
        validate_audio_path(str(f))

    def test_missing_file_raises(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_path

        missing = str(tmp_path / "nope.wav")
        with pytest.raises(ValueError) as exc:
            validate_audio_path(missing)
        assert f"Audio file not found: {missing}" in str(exc.value)

    def test_unsupported_extension_raises(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_path

        f = tmp_path / "sample.ogg"
        f.write_bytes(b"OggS")
        with pytest.raises(ValueError) as exc:
            validate_audio_path(str(f))
        msg = str(exc.value)
        assert "Unsupported audio format" in msg
        assert "WAV" in msg and "MP3" in msg

    def test_extension_check_is_case_insensitive(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_path

        f = tmp_path / "SAMPLE.WAV"
        f.write_bytes(b"RIFF....WAVEfmt ")
        # Should NOT raise — `.WAV` is the same as `.wav` for the purposes of
        # cloning extension validation.
        validate_audio_path(str(f))

    def test_expanduser_path(self, tmp_path, monkeypatch):
        """`~` in the path is expanded to the user's home before any check."""
        from supertone_tts_mcp.tools import validate_audio_path

        monkeypatch.setenv("HOME", str(tmp_path))
        f = tmp_path / "audio.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")
        # Use the `~`-prefixed form — must resolve to tmp_path/audio.wav.
        validate_audio_path("~/audio.wav")


class TestValidateAudioFileSize:
    """Tests for `validate_audio_file_size` (ISSUE-019)."""

    def test_small_file_passes(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_file_size

        f = tmp_path / "tiny.wav"
        f.write_bytes(b"x" * 1024)  # 1 KB
        validate_audio_file_size(f)

    def test_exactly_3mb_passes(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_file_size

        f = tmp_path / "exact.wav"
        # Simulate via mocked stat to avoid writing 3MB to disk
        with patch.object(Path, "stat") as mstat:
            stat_mock = MagicMock()
            stat_mock.st_size = 3 * 1024 * 1024  # exactly 3MB
            mstat.return_value = stat_mock
            validate_audio_file_size(f)

    def test_oversize_file_raises(self, tmp_path):
        from supertone_tts_mcp.tools import validate_audio_file_size

        f = tmp_path / "big.wav"
        with patch.object(Path, "stat") as mstat:
            stat_mock = MagicMock()
            stat_mock.st_size = 3 * 1024 * 1024 + 1  # 3MB + 1 byte
            mstat.return_value = stat_mock
            with pytest.raises(ValueError) as exc:
                validate_audio_file_size(f)
        msg = str(exc.value)
        assert "Audio file too large" in msg
        assert "Maximum: 3MB" in msg


class TestCloneVoiceHandler:
    """Tests for the `clone_voice(name, audio_path, description?)` handler."""

    @pytest.mark.asyncio
    async def test_happy_path_with_wav(self, tmp_path):
        """AC #1: valid WAV ≤3MB → SDK returns voice_id → formatted response."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(return_value={"voice_id": "cv_xyz999"})
            inst.aclose = AsyncMock()

            result = await clone_voice(name="MyVoice", audio_path=str(f))

        assert result == (
            "Custom voice created. voice_id: cv_xyz999. "
            "Use this voice_id in text_to_speech."
        )

    @pytest.mark.asyncio
    async def test_happy_path_with_mp3(self, tmp_path):
        """Happy path with MP3 — content_type maps to audio/mpeg."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.mp3"
        f.write_bytes(b"\xff\xfb\x90\x00")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(return_value={"voice_id": "cv_mp3_42"})
            inst.aclose = AsyncMock()

            result = await clone_voice(name="MP3Voice", audio_path=str(f))

        # Output format check
        assert "cv_mp3_42" in result
        # SDK got the right content_type + file_name + bytes.
        call_kwargs = inst.create_cloned_voice.call_args.kwargs
        assert call_kwargs["content_type"] == "audio/mpeg"
        assert call_kwargs["file_name"] == "sample.mp3"
        assert call_kwargs["audio_bytes"] == b"\xff\xfb\x90\x00"
        assert call_kwargs["name"] == "MP3Voice"

    @pytest.mark.asyncio
    async def test_wav_content_type_mapping(self, tmp_path):
        """WAV extension maps to `audio/wav` content_type."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(return_value={"voice_id": "cv_wav_1"})
            inst.aclose = AsyncMock()

            await clone_voice(name="WavVoice", audio_path=str(f))

        call_kwargs = inst.create_cloned_voice.call_args.kwargs
        assert call_kwargs["content_type"] == "audio/wav"
        assert call_kwargs["file_name"] == "sample.wav"

    @pytest.mark.asyncio
    async def test_description_passed_through(self, tmp_path):
        """Optional description is forwarded to the SDK."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(
                return_value={"voice_id": "cv_with_desc"}
            )
            inst.aclose = AsyncMock()

            await clone_voice(
                name="Desc",
                audio_path=str(f),
                description="warm narration voice",
            )

        call_kwargs = inst.create_cloned_voice.call_args.kwargs
        assert call_kwargs["description"] == "warm narration voice"

    @pytest.mark.asyncio
    async def test_missing_file_returns_error_without_api_call(self, tmp_path):
        """AC #2: missing file returns error without invoking the SDK."""
        from supertone_tts_mcp.tools import clone_voice

        missing = str(tmp_path / "ghost.wav")
        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=missing)

        assert f"Audio file not found: {missing}" in result
        MC.assert_not_called()
        inst.create_cloned_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_unsupported_extension_returns_error_without_api_call(self, tmp_path):
        """AC #3: unsupported extension rejected before any API call."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.ogg"
        f.write_bytes(b"OggS")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=str(f))

        assert "Unsupported audio format" in result
        assert "WAV" in result and "MP3" in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_oversize_file_returns_error_without_api_call(self, tmp_path):
        """AC #4: file >3MB rejected before any API call (mocked size).

        We patch `validate_audio_file_size` rather than `Path.stat` globally
        because `Path.is_file()` itself calls `stat()` internally — a global
        mock would break the prior existence check.
        """
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "big.wav"
        f.write_bytes(b"RIFF")  # actual file is tiny

        env = {"SUPERTONE_API_KEY": "key"}

        def _raise_oversize(_path):
            # 3.0009765625 MB
            raise ValueError("Audio file too large: 3.00MB. Maximum: 3MB.")

        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
            patch(
                "supertone_tts_mcp.tools.validate_audio_file_size",
                side_effect=_raise_oversize,
            ),
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=str(f))

        assert "Audio file too large" in result
        assert "Maximum: 3MB" in result
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_name_returns_error_without_api_call(self, tmp_path):
        """AC #5: empty name rejected before any API call."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await clone_voice(name="", audio_path=str(f))

        assert result == "Voice name must not be empty."
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_only_name_returns_error_without_api_call(self, tmp_path):
        """AC #5 (extended): whitespace-only name rejected before any API call."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock()
            inst.aclose = AsyncMock()

            result = await clone_voice(name="   ", audio_path=str(f))

        assert result == "Voice name must not be empty."
        MC.assert_not_called()

    @pytest.mark.asyncio
    async def test_expands_tilde_in_path(self, tmp_path, monkeypatch):
        """AC: `~` in audio_path expands to user's home dir before any check."""
        from supertone_tts_mcp.tools import clone_voice

        # Pretend tmp_path IS the user's home.
        monkeypatch.setenv("HOME", str(tmp_path))
        f = tmp_path / "audio.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env, clear=False),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(return_value={"voice_id": "cv_tilde"})
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path="~/audio.wav")

        assert "cv_tilde" in result
        # The SDK got the actual bytes (proving file was read after expansion).
        call_kwargs = inst.create_cloned_voice.call_args.kwargs
        assert call_kwargs["audio_bytes"] == b"RIFF....WAVEfmt "
        assert call_kwargs["file_name"] == "audio.wav"

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error_without_api_call(self, tmp_path):
        """API key validation runs before any client construction."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        with patch.dict(os.environ, {}, clear=True):
            with patch("supertone_tts_mcp.tools.SupertoneClient") as MC:
                result = await clone_voice(name="V", audio_path=str(f))
                MC.assert_not_called()

        assert "SUPERTONE_API_KEY" in result

    @pytest.mark.asyncio
    async def test_auth_error_returns_formatted_string(self, tmp_path):
        """AC #6: SDK 401/403 -> formatted auth error."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(side_effect=SupertoneAuthError())
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=str(f))

        assert result == (
            "Authentication failed. Please verify your SUPERTONE_API_KEY."
        )

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_formatted_string(self, tmp_path):
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(side_effect=SupertoneRateLimitError())
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=str(f))

        assert result == "Rate limit exceeded. Please wait and try again."

    @pytest.mark.asyncio
    async def test_server_error_returns_formatted_string(self, tmp_path):
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(side_effect=SupertoneServerError(503))
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=str(f))

        assert result == ("Supertone API server error (503). Please try again later.")

    @pytest.mark.asyncio
    async def test_connection_error_returns_formatted_string(self, tmp_path):
        """Per RL-002: the handler covers the connection-error branch."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            result = await clone_voice(name="V", audio_path=str(f))

        assert result == (
            "Failed to connect to Supertone API. Please check your network connection."
        )

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_success(self, tmp_path):
        """The client is always closed after a successful call."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(return_value={"voice_id": "cv_close"})
            inst.aclose = AsyncMock()

            await clone_voice(name="V", audio_path=str(f))

        inst.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_client_aclose_called_on_error(self, tmp_path):
        """The client is always closed even when the SDK call fails."""
        from supertone_tts_mcp.tools import clone_voice

        f = tmp_path / "sample.wav"
        f.write_bytes(b"RIFF....WAVEfmt ")

        env = {"SUPERTONE_API_KEY": "key"}
        with (
            patch.dict(os.environ, env),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MC,
        ):
            inst = MC.return_value
            inst.create_cloned_voice = AsyncMock(side_effect=SupertoneConnectionError())
            inst.aclose = AsyncMock()

            await clone_voice(name="V", audio_path=str(f))

        inst.aclose.assert_awaited_once()
