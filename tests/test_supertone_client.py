"""Tests for SupertoneClient SDK wrapper."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from supertone.errors.forbiddenerrorresponse import ForbiddenErrorResponse
from supertone.errors.internalservererrorresponse import InternalServerErrorResponse
from supertone.errors.no_response_error import NoResponseError
from supertone.errors.toomanyrequestserrorresponse import TooManyRequestsErrorResponse
from supertone.errors.unauthorizederrorresponse import UnauthorizedErrorResponse
from supertone.models import GetAPICharacterResponseData

from supertone_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_mcp.supertone_client import SupertoneClient


@pytest.fixture
def client():
    with patch("supertone_mcp.supertone_client.Supertone") as MockSDK:
        sdk_instance = MockSDK.return_value
        sdk_instance.text_to_speech = MagicMock()
        sdk_instance.voices = MagicMock()
        sdk_instance.usage = MagicMock()
        c = SupertoneClient(api_key="test-key")
        yield c


def _make_httpx_response(content: bytes = b"audio-data", headers: dict | None = None):
    """Create a mock httpx.Response for SDK result."""
    resp = httpx.Response(
        status_code=200,
        content=content,
        headers=headers or {"content-type": "audio/mpeg"},
        request=httpx.Request("POST", "https://api.test.com"),
    )
    return resp


def _make_create_speech_response(result):
    """Create a mock CreateSpeechResponse wrapping the given result."""
    mock = MagicMock()
    mock.result = result
    mock.headers = {}
    return mock


def _make_list_voices_response(items, next_page_token=None):
    """Create a mock GetAPICharacterListResponse."""
    mock = MagicMock()
    mock.items = items
    mock.next_page_token = next_page_token
    return mock


def _make_voice_data(voice_id, name, language, styles):
    """Create a mock GetAPICharacterResponseData."""
    mock = MagicMock(spec=GetAPICharacterResponseData)
    mock.voice_id = voice_id
    mock.name = name
    mock.language = language
    mock.styles = styles
    return mock


def _sdk_error(error_cls):
    """Create a SDK error with mock raw_response."""
    raw_response = httpx.Response(
        status_code=500,
        content=b"error",
        request=httpx.Request("POST", "https://api.test.com"),
    )
    return error_cls("error", raw_response)


class TestSynthesize:
    @pytest.mark.asyncio
    async def test_returns_bytes_from_httpx_response(self, client):
        audio_data = b"\xff\xfb\x90\x00" * 100
        httpx_resp = _make_httpx_response(content=audio_data)
        sdk_resp = _make_create_speech_response(httpx_resp)

        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            return_value=sdk_resp
        )

        result_bytes, content_type, duration = await client.synthesize(
            voice_id="v1",
            text="Hello",
            language="en",
            output_format="mp3",
            model="sona_speech_2_flash",
            speed=1.0,
            pitch_shift=0,
        )

        assert result_bytes == audio_data
        assert content_type == "audio/mp3"
        assert duration is None

    @pytest.mark.asyncio
    async def test_returns_duration_from_header(self, client):
        httpx_resp = _make_httpx_response(
            content=b"audio",
            headers={"content-type": "audio/mpeg", "x-audio-length": "3.45"},
        )
        sdk_resp = _make_create_speech_response(httpx_resp)
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            return_value=sdk_resp
        )

        _, _, duration = await client.synthesize(
            voice_id="v1",
            text="Hello",
            language="en",
            output_format="mp3",
            model="sona_speech_2_flash",
            speed=1.0,
            pitch_shift=0,
        )

        assert duration == 3.45

    @pytest.mark.asyncio
    async def test_returns_bytes_from_base64_response(self, client):
        audio_data = b"\xff\xfb\x90\x00" * 10
        encoded = base64.b64encode(audio_data).decode()

        body_mock = MagicMock()
        body_mock.audio_base64 = encoded
        # Make it not an instance of httpx.Response
        sdk_resp = _make_create_speech_response(body_mock)
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            return_value=sdk_resp
        )

        result_bytes, content_type, duration = await client.synthesize(
            voice_id="v1",
            text="Hello",
            language="en",
            output_format="wav",
            model="sona_speech_2_flash",
            speed=1.0,
            pitch_shift=0,
        )

        assert result_bytes == audio_data
        assert content_type == "audio/wav"
        assert duration is None

    @pytest.mark.asyncio
    async def test_passes_correct_params_to_sdk(self, client):
        httpx_resp = _make_httpx_response()
        sdk_resp = _make_create_speech_response(httpx_resp)
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            return_value=sdk_resp
        )

        await client.synthesize(
            voice_id="v1",
            text="Hello",
            language="ko",
            output_format="mp3",
            model="sona_speech_2_flash",
            speed=1.5,
            pitch_shift=-3,
            style="happy",
        )

        call_kwargs = client._sdk.text_to_speech.create_speech_async.call_args[1]
        assert call_kwargs["voice_id"] == "v1"
        assert call_kwargs["text"] == "Hello"
        assert call_kwargs["style"] == "happy"
        assert call_kwargs["voice_settings"].speed == 1.5
        assert call_kwargs["voice_settings"].pitch_shift == -3.0

    @pytest.mark.asyncio
    async def test_omits_style_when_none(self, client):
        httpx_resp = _make_httpx_response()
        sdk_resp = _make_create_speech_response(httpx_resp)
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            return_value=sdk_resp
        )

        await client.synthesize(
            voice_id="v1",
            text="Hello",
            language="en",
            output_format="mp3",
            model="sona_speech_2_flash",
            speed=1.0,
            pitch_shift=0,
            style=None,
        )

        call_kwargs = client._sdk.text_to_speech.create_speech_async.call_args[1]
        assert call_kwargs["style"] is None

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_too_many_requests_raises_rate_limit(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_server_error_raises(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=NoResponseError("No response")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, client):
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            side_effect=httpx.ReadTimeout("Timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.synthesize(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_2_flash",
                speed=1.0,
                pitch_shift=0,
            )


class TestGetVoices:
    @pytest.mark.asyncio
    async def test_returns_parsed_list(self, client):
        voices_data = [
            _make_voice_data("v1", "Voice1", ["ko"], ["neutral"]),
            _make_voice_data("v2", "Voice2", ["en"], ["happy"]),
        ]
        resp = _make_list_voices_response(voices_data)
        client._sdk.voices.list_voices_async = AsyncMock(return_value=resp)

        result = await client.get_voices()

        assert len(result) == 2
        assert result[0]["voice_id"] == "v1"
        assert result[0]["supported_languages"] == ["ko"]
        assert result[0]["supported_styles"] == ["neutral"]

    @pytest.mark.asyncio
    async def test_handles_pagination(self, client):
        page1_voices = [_make_voice_data("v1", "V1", ["ko"], [])]
        page2_voices = [_make_voice_data("v2", "V2", ["en"], [])]

        resp1 = _make_list_voices_response(page1_voices, next_page_token="token123")
        resp2 = _make_list_voices_response(page2_voices)

        client._sdk.voices.list_voices_async = AsyncMock(side_effect=[resp1, resp2])

        result = await client.get_voices()

        assert len(result) == 2
        assert result[0]["voice_id"] == "v1"
        assert result[1]["voice_id"] == "v2"

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        client._sdk.voices.list_voices_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await client.get_voices()

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.voices.list_voices_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.get_voices()


class TestSynthesizeStream:
    """Tests for the streaming synthesize_stream method."""

    @pytest.mark.asyncio
    async def test_yields_chunks_from_httpx_stream(self, client):
        """Streaming response yields audio chunks."""
        chunks = [b"\xff\xfb" * 10, b"\x90\x00" * 10]

        async def mock_aiter_bytes():
            for c in chunks:
                yield c

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.aiter_bytes = mock_aiter_bytes

        stream_resp = MagicMock()
        stream_resp.result = mock_resp

        client._sdk.text_to_speech.stream_speech_async = AsyncMock(
            return_value=stream_resp
        )

        received = []
        async for chunk in client.synthesize_stream(
            voice_id="v1",
            text="Hello",
            language="en",
            output_format="mp3",
            model="sona_speech_1",
            speed=1.0,
            pitch_shift=0,
        ):
            received.append(chunk)

        assert received == chunks

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.text_to_speech.stream_speech_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            async for _ in client.synthesize_stream(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            ):
                pass

    @pytest.mark.asyncio
    async def test_rate_limit_raises(self, client):
        client._sdk.text_to_speech.stream_speech_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            async for _ in client.synthesize_stream(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            ):
                pass

    @pytest.mark.asyncio
    async def test_server_error_raises(self, client):
        client._sdk.text_to_speech.stream_speech_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            async for _ in client.synthesize_stream(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            ):
                pass

    @pytest.mark.asyncio
    async def test_connection_error_raises(self, client):
        client._sdk.text_to_speech.stream_speech_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            async for _ in client.synthesize_stream(
                voice_id="v1",
                text="Hello",
                language="en",
                output_format="mp3",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            ):
                pass

    @pytest.mark.asyncio
    async def test_string_result_yields_bytes(self, client):
        """NDJSON string result is encoded to bytes."""
        stream_resp = MagicMock()
        stream_resp.result = "ndjson-data"

        client._sdk.text_to_speech.stream_speech_async = AsyncMock(
            return_value=stream_resp
        )

        received = []
        async for chunk in client.synthesize_stream(
            voice_id="v1",
            text="Hello",
            language="en",
            output_format="mp3",
            model="sona_speech_1",
            speed=1.0,
            pitch_shift=0,
        ):
            received.append(chunk)

        assert received == [b"ndjson-data"]


class TestAclose:
    @pytest.mark.asyncio
    async def test_closes_sdk_client(self, client):
        mock_http_client = AsyncMock()
        client._sdk._client = mock_http_client
        await client.aclose()
        mock_http_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_error_when_no_internal_client(self, client):
        if hasattr(client._sdk, "_client"):
            del client._sdk._client
        await client.aclose()


# ---------------------------------------------------------------------------
# ISSUE-014: Voice discovery methods (search_voices, get_voice, get_credit_balance)
# ---------------------------------------------------------------------------


def _make_voice_detail(
    *,
    voice_id="v1",
    name="Voice One",
    description="A test voice",
    age="adult",
    gender="female",
    use_case="narration",
    use_cases=None,
    language=None,
    styles=None,
    models=None,
    samples: list | None = None,
    thumbnail_image_url: str | None = "https://cdn.test/v1.png",
):
    """Build a mock GetCharacterByIDResponse with all required fields populated."""
    mock = MagicMock()
    mock.voice_id = voice_id
    mock.name = name
    mock.description = description
    mock.age = age
    mock.gender = gender
    mock.use_case = use_case
    mock.use_cases = use_cases if use_cases is not None else ["narration"]
    mock.language = language if language is not None else ["en", "ko"]
    mock.styles = styles if styles is not None else ["neutral", "happy"]
    mock.models = models if models is not None else ["sona_speech_1"]
    mock.samples = samples
    mock.thumbnail_image_url = thumbnail_image_url
    return mock


def _make_sample(
    language="en",
    style="neutral",
    model="sona_speech_1",
    url="https://cdn.test/sample.mp3",
):
    """Build a mock APISampleData."""
    mock = MagicMock()
    mock.language = language
    mock.style = style
    mock.model = model
    mock.url = url
    return mock


def _make_credit_balance(balance: float | None = 100.5):
    """Build a mock GetCreditBalanceResponse."""
    mock = MagicMock()
    mock.balance = balance
    return mock


class TestSearchVoices:
    @pytest.mark.asyncio
    async def test_returns_parsed_list(self, client):
        voices_data = [
            _make_voice_data("v1", "Voice1", ["ko"], ["neutral"]),
            _make_voice_data("v2", "Voice2", ["en"], ["happy"]),
        ]
        resp = _make_list_voices_response(voices_data)
        client._sdk.voices.search_voices_async = AsyncMock(return_value=resp)

        result = await client.search_voices(gender="female")

        assert len(result) == 2
        assert result[0]["voice_id"] == "v1"
        assert result[0]["name"] == "Voice1"
        assert result[0]["supported_languages"] == ["ko"]
        assert result[0]["supported_styles"] == ["neutral"]
        assert result[1]["voice_id"] == "v2"

    @pytest.mark.asyncio
    async def test_handles_pagination(self, client):
        page1_voices = [_make_voice_data("v1", "V1", ["ko"], [])]
        page2_voices = [_make_voice_data("v2", "V2", ["en"], [])]
        page3_voices = [_make_voice_data("v3", "V3", ["ja"], [])]

        resp1 = _make_list_voices_response(page1_voices, next_page_token="t1")
        resp2 = _make_list_voices_response(page2_voices, next_page_token="t2")
        resp3 = _make_list_voices_response(page3_voices)

        client._sdk.voices.search_voices_async = AsyncMock(
            side_effect=[resp1, resp2, resp3]
        )

        result = await client.search_voices(gender="female")

        assert len(result) == 3
        assert [v["voice_id"] for v in result] == ["v1", "v2", "v3"]
        # Confirm next_page_token threaded through subsequent calls
        calls = client._sdk.voices.search_voices_async.call_args_list
        assert calls[0].kwargs.get("next_page_token") is None
        assert calls[1].kwargs.get("next_page_token") == "t1"
        assert calls[2].kwargs.get("next_page_token") == "t2"

    @pytest.mark.asyncio
    async def test_passes_all_filter_params_to_sdk(self, client):
        resp = _make_list_voices_response([])
        client._sdk.voices.search_voices_async = AsyncMock(return_value=resp)

        await client.search_voices(
            name="alice",
            description="warm",
            language="ko",
            gender="female",
            age="adult",
            use_case="narration",
            style="happy",
            model="sona_speech_1",
        )

        call_kwargs = client._sdk.voices.search_voices_async.call_args.kwargs
        assert call_kwargs["name"] == "alice"
        assert call_kwargs["description"] == "warm"
        assert call_kwargs["language"] == "ko"
        assert call_kwargs["gender"] == "female"
        assert call_kwargs["age"] == "adult"
        assert call_kwargs["use_case"] == "narration"
        assert call_kwargs["style"] == "happy"
        assert call_kwargs["model"] == "sona_speech_1"

    @pytest.mark.asyncio
    async def test_no_filters_returns_all(self, client):
        voices_data = [_make_voice_data("v1", "V1", ["en"], [])]
        resp = _make_list_voices_response(voices_data)
        client._sdk.voices.search_voices_async = AsyncMock(return_value=resp)

        result = await client.search_voices()

        assert len(result) == 1
        call_kwargs = client._sdk.voices.search_voices_async.call_args.kwargs
        assert call_kwargs.get("name") is None
        assert call_kwargs.get("gender") is None

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.voices.search_voices_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.search_voices(gender="female")

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, client):
        client._sdk.voices.search_voices_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.search_voices()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        client._sdk.voices.search_voices_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await client.search_voices()

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, client):
        client._sdk.voices.search_voices_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await client.search_voices()

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, client):
        client._sdk.voices.search_voices_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.search_voices()


class TestGetVoice:
    @pytest.mark.asyncio
    async def test_returns_full_voice_detail(self, client):
        samples = [
            _make_sample(
                language="en",
                style="neutral",
                model="sona_speech_1",
                url="https://cdn.test/s1.mp3",
            ),
            _make_sample(
                language="ko",
                style="happy",
                model="sona_speech_2",
                url="https://cdn.test/s2.mp3",
            ),
        ]
        detail = _make_voice_detail(
            voice_id="v1",
            name="Alice",
            description="A warm narrator",
            age="adult",
            gender="female",
            use_case="narration",
            use_cases=["narration", "audiobook"],
            language=["en", "ko"],
            styles=["neutral", "happy"],
            models=["sona_speech_1", "sona_speech_2"],
            samples=samples,
            thumbnail_image_url="https://cdn.test/v1.png",
        )
        client._sdk.voices.get_voice_async = AsyncMock(return_value=detail)

        result = await client.get_voice("v1")

        assert result["voice_id"] == "v1"
        assert result["name"] == "Alice"
        assert result["description"] == "A warm narrator"
        assert result["age"] == "adult"
        assert result["gender"] == "female"
        assert result["use_case"] == "narration"
        assert result["use_cases"] == ["narration", "audiobook"]
        assert result["supported_languages"] == ["en", "ko"]
        assert result["styles"] == ["neutral", "happy"]
        assert result["models"] == ["sona_speech_1", "sona_speech_2"]
        assert result["thumbnail_image_url"] == "https://cdn.test/v1.png"
        assert len(result["samples"]) == 2
        assert result["samples"][0] == {
            "language": "en",
            "style": "neutral",
            "model": "sona_speech_1",
            "url": "https://cdn.test/s1.mp3",
        }

    @pytest.mark.asyncio
    async def test_passes_voice_id_to_sdk(self, client):
        detail = _make_voice_detail(voice_id="v99")
        client._sdk.voices.get_voice_async = AsyncMock(return_value=detail)

        await client.get_voice("v99")

        call_kwargs = client._sdk.voices.get_voice_async.call_args.kwargs
        assert call_kwargs["voice_id"] == "v99"

    @pytest.mark.asyncio
    async def test_handles_missing_samples_and_thumbnail(self, client):
        detail = _make_voice_detail(samples=None, thumbnail_image_url=None)
        client._sdk.voices.get_voice_async = AsyncMock(return_value=detail)

        result = await client.get_voice("v1")

        # samples/thumbnail are optional in the TypedDict.
        assert "samples" not in result or result.get("samples") in (None, [])
        assert (
            "thumbnail_image_url" not in result
            or result.get("thumbnail_image_url") is None
        )

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.voices.get_voice_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.get_voice("v1")

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, client):
        client._sdk.voices.get_voice_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.get_voice("v1")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        client._sdk.voices.get_voice_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await client.get_voice("v1")

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, client):
        client._sdk.voices.get_voice_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await client.get_voice("v1")

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, client):
        client._sdk.voices.get_voice_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.get_voice("v1")

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, client):
        client._sdk.voices.get_voice_async = AsyncMock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.get_voice("v1")


class TestGetCreditBalance:
    @pytest.mark.asyncio
    async def test_returns_balance_dict(self, client):
        resp = _make_credit_balance(balance=250.75)
        client._sdk.usage.get_credit_balance_async = AsyncMock(return_value=resp)

        result = await client.get_credit_balance()

        assert result["balance"] == 250.75

    @pytest.mark.asyncio
    async def test_handles_null_balance(self, client):
        resp = _make_credit_balance(balance=None)
        client._sdk.usage.get_credit_balance_async = AsyncMock(return_value=resp)

        result = await client.get_credit_balance()

        assert result["balance"] is None

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.usage.get_credit_balance_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.get_credit_balance()

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, client):
        client._sdk.usage.get_credit_balance_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.get_credit_balance()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        client._sdk.usage.get_credit_balance_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await client.get_credit_balance()

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, client):
        client._sdk.usage.get_credit_balance_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await client.get_credit_balance()

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, client):
        client._sdk.usage.get_credit_balance_async = AsyncMock(
            side_effect=NoResponseError("no response")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.get_credit_balance()

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, client):
        client._sdk.usage.get_credit_balance_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.get_credit_balance()


class TestVoiceDetailDictShape:
    """ISSUE-014 AC5: VoiceDetailDict / SampleDict / CreditBalanceDict are importable
    and match the SDK GetCharacterByIDResponse / GetCreditBalanceResponse shapes."""

    def test_voice_detail_dict_importable(self):
        from supertone_mcp.models import VoiceDetailDict

        # TypedDict instances are dicts at runtime; verify required keys can be set.
        sample_value: VoiceDetailDict = {
            "voice_id": "v1",
            "name": "Alice",
            "description": "desc",
            "age": "adult",
            "gender": "female",
            "use_case": "narration",
            "use_cases": ["narration"],
            "supported_languages": ["en"],
            "styles": ["neutral"],
            "models": ["sona_speech_1"],
        }
        assert sample_value["voice_id"] == "v1"
        assert sample_value["supported_languages"] == ["en"]

    def test_sample_dict_importable(self):
        from supertone_mcp.models import SampleDict

        s: SampleDict = {
            "language": "en",
            "style": "neutral",
            "model": "sona_speech_1",
            "url": "https://cdn.test/s.mp3",
        }
        assert s["language"] == "en"
        assert s["url"].startswith("https://")

    def test_credit_balance_dict_importable(self):
        from supertone_mcp.models import CreditBalanceDict

        c: CreditBalanceDict = {"balance": 100.0}
        assert c["balance"] == 100.0


# ---------------------------------------------------------------------------
# ISSUE-018: predict_duration SDK wrapper
# ---------------------------------------------------------------------------


def _make_predict_duration_response(duration: float | None = 2.34):
    """Build a mock PredictDurationResponse."""
    mock = MagicMock()
    mock.duration = duration
    return mock


class TestPredictDuration:
    @pytest.mark.asyncio
    async def test_returns_duration_float(self, client):
        """Happy path: wrapper extracts the `duration` field from the SDK response."""
        resp = _make_predict_duration_response(duration=2.34)
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(return_value=resp)

        result = await client.predict_duration(
            voice_id="v1",
            text="hello",
            language="en",
            output_format="wav",
            model="sona_speech_1",
            speed=1.0,
            pitch_shift=0,
        )

        assert result == 2.34

    @pytest.mark.asyncio
    async def test_returns_none_when_duration_missing(self, client):
        """SDK schema marks `duration` Optional; the wrapper passes `None` through."""
        resp = _make_predict_duration_response(duration=None)
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(return_value=resp)

        result = await client.predict_duration(
            voice_id="v1",
            text="hello",
            language="en",
            output_format="wav",
            model="sona_speech_1",
            speed=1.0,
            pitch_shift=0,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_passes_all_params_to_sdk(self, client):
        """All parameters (incl. style) are forwarded to predict_duration_async."""
        resp = _make_predict_duration_response(duration=1.0)
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(return_value=resp)

        await client.predict_duration(
            voice_id="alice-01",
            text="hello there",
            language="ko",
            output_format="mp3",
            model="sona_speech_2",
            speed=1.25,
            pitch_shift=-3,
            style="happy",
        )

        call_kwargs = client._sdk.text_to_speech.predict_duration_async.call_args.kwargs
        assert call_kwargs["voice_id"] == "alice-01"
        assert call_kwargs["text"] == "hello there"
        # language / model / output_format must be the SDK enum values
        assert call_kwargs["language"].value == "ko"
        assert call_kwargs["model"].value == "sona_speech_2"
        assert call_kwargs["output_format"].value == "mp3"
        # style is a plain pass-through string
        assert call_kwargs["style"] == "happy"
        # voice_settings carries speed + pitch_shift
        vs = call_kwargs["voice_settings"]
        assert vs.speed == 1.25
        assert vs.pitch_shift == -3.0

    @pytest.mark.asyncio
    async def test_style_defaults_to_none(self, client):
        """When the caller omits `style`, the SDK receives `style=None`."""
        resp = _make_predict_duration_response(duration=1.0)
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(return_value=resp)

        await client.predict_duration(
            voice_id="v1",
            text="hi",
            language="en",
            output_format="wav",
            model="sona_speech_1",
            speed=1.0,
            pitch_shift=0,
        )

        call_kwargs = client._sdk.text_to_speech.predict_duration_async.call_args.kwargs
        assert call_kwargs["style"] is None

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, client):
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, client):
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, client):
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, client):
        """RL-002: symmetric coverage of NoResponseError."""
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=NoResponseError("no response")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, client):
        """RL-002: symmetric coverage of httpx.ConnectError."""
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, client):
        """RL-002: symmetric coverage of httpx.TimeoutException."""
        client._sdk.text_to_speech.predict_duration_async = AsyncMock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await client.predict_duration(
                voice_id="v1",
                text="hi",
                language="en",
                output_format="wav",
                model="sona_speech_1",
                speed=1.0,
                pitch_shift=0,
            )


# ---------------------------------------------------------------------------
# ISSUE-019: create_cloned_voice SDK wrapper
# ---------------------------------------------------------------------------


def _make_create_cloned_voice_response(voice_id: str = "cv_abc123"):
    """Build a mock CreateCustomVoiceResponse."""
    mock = MagicMock()
    mock.voice_id = voice_id
    return mock


class TestCreateClonedVoice:
    """Tests for SupertoneClient.create_cloned_voice (ISSUE-019)."""

    @pytest.fixture
    def cv_client(self):
        with patch("supertone_mcp.supertone_client.Supertone") as MockSDK:
            sdk_instance = MockSDK.return_value
            sdk_instance.text_to_speech = MagicMock()
            sdk_instance.voices = MagicMock()
            sdk_instance.usage = MagicMock()
            sdk_instance.custom_voices = MagicMock()
            c = SupertoneClient(api_key="test-key")
            yield c

    @pytest.mark.asyncio
    async def test_returns_voice_id_dict(self, cv_client):
        """Happy path: wrapper extracts the `voice_id` field from the SDK response."""
        resp = _make_create_cloned_voice_response(voice_id="cv_abc123")
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            return_value=resp
        )

        result = await cv_client.create_cloned_voice(
            name="MyVoice",
            audio_bytes=b"RIFF....WAVEfmt ",
            file_name="my-voice.wav",
            content_type="audio/wav",
        )

        assert result == {"voice_id": "cv_abc123"}

    @pytest.mark.asyncio
    async def test_passes_files_payload_and_name_to_sdk(self, cv_client):
        """The SDK is invoked with a Files payload built from the supplied bytes
        and the caller's name (per architecture.md §SDK)."""
        resp = _make_create_cloned_voice_response()
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            return_value=resp
        )

        await cv_client.create_cloned_voice(
            name="Alpha",
            audio_bytes=b"\x00\x01\x02",
            file_name="alpha.mp3",
            content_type="audio/mpeg",
            description="alpha description",
        )

        call_kwargs = (
            cv_client._sdk.custom_voices.create_cloned_voice_async.call_args.kwargs
        )
        assert call_kwargs["name"] == "Alpha"
        assert call_kwargs["description"] == "alpha description"
        files = call_kwargs["files"]
        # The SDK accepts a Files BaseModel OR a FilesTypedDict (mapping).
        # Either way, the three fields must be present and accurate.
        if isinstance(files, dict):
            assert files["file_name"] == "alpha.mp3"
            assert files["content"] == b"\x00\x01\x02"
            assert files["content_type"] == "audio/mpeg"
        else:
            assert files.file_name == "alpha.mp3"
            assert files.content == b"\x00\x01\x02"
            assert files.content_type == "audio/mpeg"

    @pytest.mark.asyncio
    async def test_description_defaults_to_none(self, cv_client):
        """When the caller omits `description`, the SDK receives `description=None`."""
        resp = _make_create_cloned_voice_response()
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            return_value=resp
        )

        await cv_client.create_cloned_voice(
            name="NoDesc",
            audio_bytes=b"x",
            file_name="x.wav",
            content_type="audio/wav",
        )

        call_kwargs = (
            cv_client._sdk.custom_voices.create_cloned_voice_async.call_args.kwargs
        )
        assert call_kwargs["description"] is None

    # --- RL-002: symmetric error-branch coverage ---

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, cv_client):
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, cv_client):
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, cv_client):
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, cv_client):
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, cv_client):
        """RL-002: symmetric coverage of NoResponseError."""
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=NoResponseError("no response")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, cv_client):
        """RL-002: symmetric coverage of httpx.ConnectError."""
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, cv_client):
        """RL-002: symmetric coverage of httpx.TimeoutException."""
        cv_client._sdk.custom_voices.create_cloned_voice_async = AsyncMock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_client.create_cloned_voice(
                name="MyVoice",
                audio_bytes=b"x",
                file_name="x.wav",
                content_type="audio/wav",
            )


# ---------------------------------------------------------------------------
# ISSUE-020: Custom voice CRUD (search / edit / delete)
# ---------------------------------------------------------------------------


def _make_custom_voice_item(
    voice_id: str = "cv_1",
    name: str = "MyVoice",
    description: str | None = "warm narrator",
):
    """Build a mock GetCustomVoiceResponse item."""
    mock = MagicMock()
    mock.voice_id = voice_id
    mock.name = name
    mock.description = description
    return mock


def _make_custom_voice_list_response(
    items: list,
    next_page_token: str | None = None,
):
    """Build a mock GetCustomVoiceListResponse."""
    mock = MagicMock()
    mock.items = items
    mock.next_page_token = next_page_token
    return mock


def _make_update_custom_voice_response(
    voice_id: str = "cv_1",
    name: str = "MyVoice",
    description: str | None = "warm narrator",
):
    """Build a mock UpdateCustomVoiceResponse."""
    mock = MagicMock()
    mock.voice_id = voice_id
    mock.name = name
    mock.description = description
    return mock


@pytest.fixture
def cv_crud_client():
    """A SupertoneClient fixture that mocks the custom_voices namespace."""
    with patch("supertone_mcp.supertone_client.Supertone") as MockSDK:
        sdk_instance = MockSDK.return_value
        sdk_instance.text_to_speech = MagicMock()
        sdk_instance.voices = MagicMock()
        sdk_instance.usage = MagicMock()
        sdk_instance.custom_voices = MagicMock()
        c = SupertoneClient(api_key="test-key")
        yield c


class TestSearchCustomVoices:
    """Tests for SupertoneClient.search_custom_voices (ISSUE-020)."""

    @pytest.mark.asyncio
    async def test_returns_parsed_list(self, cv_crud_client):
        items = [
            _make_custom_voice_item("cv_1", "Voice1", "first"),
            _make_custom_voice_item("cv_2", "Voice2", "second"),
        ]
        resp = _make_custom_voice_list_response(items)
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            return_value=resp
        )

        result = await cv_crud_client.search_custom_voices()

        assert len(result) == 2
        assert result[0] == {
            "voice_id": "cv_1",
            "name": "Voice1",
            "description": "first",
        }
        assert result[1]["voice_id"] == "cv_2"

    @pytest.mark.asyncio
    async def test_omits_description_when_none(self, cv_crud_client):
        """`description` is NotRequired in CustomVoiceDict; omit when None."""
        items = [_make_custom_voice_item("cv_1", "Voice1", description=None)]
        resp = _make_custom_voice_list_response(items)
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            return_value=resp
        )

        result = await cv_crud_client.search_custom_voices()

        assert result[0]["voice_id"] == "cv_1"
        assert result[0]["name"] == "Voice1"
        assert "description" not in result[0]

    @pytest.mark.asyncio
    async def test_handles_pagination(self, cv_crud_client):
        """RL-003: multi-page pagination with token threading."""
        page1_items = [_make_custom_voice_item("cv_1", "V1", "d1")]
        page2_items = [_make_custom_voice_item("cv_2", "V2", "d2")]
        page3_items = [_make_custom_voice_item("cv_3", "V3", "d3")]

        resp1 = _make_custom_voice_list_response(page1_items, next_page_token="t1")
        resp2 = _make_custom_voice_list_response(page2_items, next_page_token="t2")
        resp3 = _make_custom_voice_list_response(page3_items)

        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=[resp1, resp2, resp3]
        )

        result = await cv_crud_client.search_custom_voices()

        assert len(result) == 3
        assert [v["voice_id"] for v in result] == ["cv_1", "cv_2", "cv_3"]
        # Confirm next_page_token threaded through subsequent calls.
        calls = (
            cv_crud_client._sdk.custom_voices.search_custom_voices_async.call_args_list
        )
        assert calls[0].kwargs.get("next_page_token") is None
        assert calls[1].kwargs.get("next_page_token") == "t1"
        assert calls[2].kwargs.get("next_page_token") == "t2"

    @pytest.mark.asyncio
    async def test_passes_filters_to_sdk(self, cv_crud_client):
        resp = _make_custom_voice_list_response([])
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            return_value=resp
        )

        await cv_crud_client.search_custom_voices(name="my", description="warm")

        mock_search = cv_crud_client._sdk.custom_voices.search_custom_voices_async
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["name"] == "my"
        assert call_kwargs["description"] == "warm"

    @pytest.mark.asyncio
    async def test_no_filters_passes_none(self, cv_crud_client):
        resp = _make_custom_voice_list_response([])
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            return_value=resp
        )

        await cv_crud_client.search_custom_voices()

        mock_search = cv_crud_client._sdk.custom_voices.search_custom_voices_async
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs.get("name") is None
        assert call_kwargs.get("description") is None

    # --- RL-002: symmetric error-branch coverage ---

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_crud_client.search_custom_voices()

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_crud_client.search_custom_voices()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await cv_crud_client.search_custom_voices()

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await cv_crud_client.search_custom_voices()

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of NoResponseError."""
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=NoResponseError("no response")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.search_custom_voices()

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of httpx.ConnectError."""
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.search_custom_voices()

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of httpx.TimeoutException."""
        cv_crud_client._sdk.custom_voices.search_custom_voices_async = AsyncMock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.search_custom_voices()


class TestEditCustomVoice:
    """Tests for SupertoneClient.edit_custom_voice (ISSUE-020)."""

    @pytest.mark.asyncio
    async def test_returns_updated_voice_dict(self, cv_crud_client):
        resp = _make_update_custom_voice_response(
            voice_id="cv_1", name="NewName", description="updated"
        )
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            return_value=resp
        )

        result = await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="NewName")

        assert result["voice_id"] == "cv_1"
        assert result["name"] == "NewName"
        assert result["description"] == "updated"

    @pytest.mark.asyncio
    async def test_omits_name_when_none(self, cv_crud_client):
        """Partial update: only the non-None kwargs are forwarded."""
        resp = _make_update_custom_voice_response()
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            return_value=resp
        )

        await cv_crud_client.edit_custom_voice(voice_id="cv_1", description="only-desc")

        call_kwargs = (
            cv_crud_client._sdk.custom_voices.edit_custom_voice_async.call_args.kwargs
        )
        assert call_kwargs["voice_id"] == "cv_1"
        assert "name" not in call_kwargs
        assert call_kwargs["description"] == "only-desc"

    @pytest.mark.asyncio
    async def test_omits_description_when_none(self, cv_crud_client):
        """Partial update: only the non-None kwargs are forwarded."""
        resp = _make_update_custom_voice_response()
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            return_value=resp
        )

        await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="OnlyName")

        call_kwargs = (
            cv_crud_client._sdk.custom_voices.edit_custom_voice_async.call_args.kwargs
        )
        assert call_kwargs["voice_id"] == "cv_1"
        assert call_kwargs["name"] == "OnlyName"
        assert "description" not in call_kwargs

    @pytest.mark.asyncio
    async def test_forwards_both_fields(self, cv_crud_client):
        resp = _make_update_custom_voice_response()
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            return_value=resp
        )

        await cv_crud_client.edit_custom_voice(
            voice_id="cv_1", name="N", description="D"
        )

        call_kwargs = (
            cv_crud_client._sdk.custom_voices.edit_custom_voice_async.call_args.kwargs
        )
        assert call_kwargs["voice_id"] == "cv_1"
        assert call_kwargs["name"] == "N"
        assert call_kwargs["description"] == "D"

    @pytest.mark.asyncio
    async def test_omits_description_in_result_when_sdk_returns_none(
        self, cv_crud_client
    ):
        resp = _make_update_custom_voice_response(description=None)
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            return_value=resp
        )

        result = await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

        assert "description" not in result

    # --- RL-002: symmetric error-branch coverage ---

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of NoResponseError."""
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=NoResponseError("no response")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of httpx.ConnectError."""
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of httpx.TimeoutException."""
        cv_crud_client._sdk.custom_voices.edit_custom_voice_async = AsyncMock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.edit_custom_voice(voice_id="cv_1", name="N")


class TestDeleteCustomVoice:
    """Tests for SupertoneClient.delete_custom_voice (ISSUE-020)."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_none(self, cv_crud_client):
        """SDK returns None on 204/200 — wrapper returns None."""
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            return_value=None
        )

        result = await cv_crud_client.delete_custom_voice(voice_id="cv_1")

        assert result is None

    @pytest.mark.asyncio
    async def test_passes_voice_id_to_sdk(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            return_value=None
        )

        await cv_crud_client.delete_custom_voice(voice_id="cv_42")

        call_kwargs = (
            cv_crud_client._sdk.custom_voices.delete_custom_voice_async.call_args.kwargs
        )
        assert call_kwargs["voice_id"] == "cv_42"

    # --- RL-002: symmetric error-branch coverage ---

    @pytest.mark.asyncio
    async def test_unauthorized_raises_auth_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(UnauthorizedErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")

    @pytest.mark.asyncio
    async def test_forbidden_raises_auth_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(ForbiddenErrorResponse)
        )
        with pytest.raises(SupertoneAuthError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(TooManyRequestsErrorResponse)
        )
        with pytest.raises(SupertoneRateLimitError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, cv_crud_client):
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=_sdk_error(InternalServerErrorResponse)
        )
        with pytest.raises(SupertoneServerError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")

    @pytest.mark.asyncio
    async def test_no_response_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of NoResponseError."""
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=NoResponseError("no response")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")

    @pytest.mark.asyncio
    async def test_connect_error_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of httpx.ConnectError."""
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, cv_crud_client):
        """RL-002: symmetric coverage of httpx.TimeoutException."""
        cv_crud_client._sdk.custom_voices.delete_custom_voice_async = AsyncMock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(SupertoneConnectionError):
            await cv_crud_client.delete_custom_voice(voice_id="cv_1")


class TestModelMapResolution:
    """ISSUE-021: confirm the dynamically-built model maps resolve the 2 new
    SDK 0.2.3 models (`sona_speech_3t`, `supertonic_api_3`)."""

    @pytest.mark.parametrize("model", ["sona_speech_3t", "supertonic_api_3"])
    def test_synthesize_model_map_contains_new_models(self, model):
        from supertone_mcp.supertone_client import _MODEL_MAP

        assert model in _MODEL_MAP
        assert _MODEL_MAP[model].value == model

    @pytest.mark.parametrize("model", ["sona_speech_3t", "supertonic_api_3"])
    def test_predict_model_map_contains_new_models(self, model):
        from supertone_mcp.supertone_client import _PREDICT_MODEL_MAP

        assert model in _PREDICT_MODEL_MAP
        assert _PREDICT_MODEL_MAP[model].value == model

    def test_model_maps_have_all_seven_models(self):
        from supertone_mcp.supertone_client import _MODEL_MAP, _PREDICT_MODEL_MAP

        expected = {
            "sona_speech_1",
            "sona_speech_2",
            "sona_speech_2_flash",
            "sona_speech_2t",
            "sona_speech_3t",
            "supertonic_api_1",
            "supertonic_api_3",
        }
        assert expected <= set(_MODEL_MAP)
        assert expected <= set(_PREDICT_MODEL_MAP)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("model", ["sona_speech_3t", "supertonic_api_3"])
    async def test_synthesize_passes_new_model_enum_to_sdk(self, client, model):
        httpx_resp = _make_httpx_response()
        sdk_resp = _make_create_speech_response(httpx_resp)
        client._sdk.text_to_speech.create_speech_async = AsyncMock(
            return_value=sdk_resp
        )

        await client.synthesize(
            voice_id="v1",
            text="hi",
            language="en",
            output_format="mp3",
            model=model,
            speed=1.0,
            pitch_shift=0,
        )

        call_kwargs = client._sdk.text_to_speech.create_speech_async.call_args[1]
        assert call_kwargs["model"].value == model
