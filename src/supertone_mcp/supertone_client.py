"""SDK wrapper for the Supertone TTS API."""

import base64
from collections.abc import AsyncIterator

import httpx
from supertone import Supertone, models
from supertone.errors.forbiddenerrorresponse import ForbiddenErrorResponse
from supertone.errors.internalservererrorresponse import InternalServerErrorResponse
from supertone.errors.no_response_error import NoResponseError
from supertone.errors.toomanyrequestserrorresponse import TooManyRequestsErrorResponse
from supertone.errors.unauthorizederrorresponse import UnauthorizedErrorResponse

from supertone_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_mcp.models import (
    CreditBalanceDict,
    CustomVoiceDict,
    SampleDict,
    VoiceDetailDict,
    VoiceDict,
)

# Map string language codes to SDK enum values
_LANGUAGE_MAP = {
    member.value: member
    for member in models.APIConvertTextToSpeechUsingCharacterRequestLanguage
}

# Map string model names to SDK enum values
_MODEL_MAP = {
    member.value: member
    for member in models.APIConvertTextToSpeechUsingCharacterRequestModel
}

# Map string format names to SDK enum values
_FORMAT_MAP = {
    member.value: member
    for member in models.APIConvertTextToSpeechUsingCharacterRequestOutputFormat
}

# Maps for the predict-duration endpoint. The SDK declares parallel enum
# types whose `.value` strings match the synthesize maps above, but we
# resolve via the dedicated enum classes to stay future-proof if the SDK
# ever diverges them.
_PREDICT_LANGUAGE_MAP = {
    member.value: member for member in models.PredictTTSDurationRequestLanguage
}
_PREDICT_MODEL_MAP = {
    member.value: member for member in models.PredictTTSDurationRequestModel
}
_PREDICT_FORMAT_MAP = {
    member.value: member for member in models.PredictTTSDurationRequestOutputFormat
}


def _handle_sdk_errors(exc: Exception) -> None:
    """Map SDK exceptions to domain exceptions. Always raises."""
    if isinstance(exc, (UnauthorizedErrorResponse, ForbiddenErrorResponse)):
        raise SupertoneAuthError() from exc
    if isinstance(exc, TooManyRequestsErrorResponse):
        raise SupertoneRateLimitError() from exc
    if isinstance(exc, InternalServerErrorResponse):
        status = exc.raw_response.status_code if hasattr(exc, "raw_response") else 500
        raise SupertoneServerError(status) from exc
    if isinstance(exc, NoResponseError):
        raise SupertoneConnectionError(str(exc)) from exc
    if isinstance(exc, httpx.ConnectError):
        raise SupertoneConnectionError(str(exc)) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise SupertoneConnectionError(str(exc)) from exc
    raise exc


class SupertoneClient:
    """Async client for the Supertone TTS API using the official SDK."""

    def __init__(self, api_key: str) -> None:
        self._sdk = Supertone(api_key=api_key)

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        language: str,
        output_format: str,
        model: str,
        speed: float,
        pitch_shift: int,
        style: str | None = None,
        include_phonemes: bool = False,
        normalized_text: str | None = None,
    ) -> tuple[bytes, str, float | None]:
        """Synthesize speech using the Supertone SDK (batch mode).

        The SDK automatically splits text longer than 300 characters into chunks,
        processes them in parallel, and concatenates the audio.

        `include_phonemes` and `normalized_text` (SDK 0.2.3, ISSUE-025) are
        forwarded to the SDK as-is. `normalized_text` is only honored by the
        `sona_speech_2` / `sona_speech_2_flash` models per the SDK; other models
        ignore it (no client-side rejection).

        Returns a tuple of (audio_bytes, content_type, duration_seconds).
        """
        lang_enum = _LANGUAGE_MAP[language]
        model_enum = _MODEL_MAP[model]
        fmt_enum = _FORMAT_MAP[output_format]

        voice_settings = models.ConvertTextToSpeechParameters(
            speed=speed,
            pitch_shift=float(pitch_shift),
        )

        try:
            response = await self._sdk.text_to_speech.create_speech_async(
                voice_id=voice_id,
                text=text,
                language=lang_enum,
                model=model_enum,
                output_format=fmt_enum,
                voice_settings=voice_settings,
                style=style,
                include_phonemes=include_phonemes,
                normalized_text=normalized_text,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        # Determine content type
        content_type = f"audio/{output_format}"

        # Extract audio bytes from response
        result = response.result
        if isinstance(result, httpx.Response):
            audio_bytes = result.content
            # Try to get duration from X-Audio-Length header
            duration: float | None = None
            audio_length = result.headers.get("x-audio-length")
            if audio_length:
                try:
                    duration = float(audio_length)
                except ValueError:
                    pass
            return audio_bytes, content_type, duration
        else:
            # CreateSpeechResponseBody with audio_base64
            audio_bytes = base64.b64decode(result.audio_base64)
            return audio_bytes, content_type, None

    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        language: str,
        output_format: str,
        model: str,
        speed: float,
        pitch_shift: int,
        style: str | None = None,
        include_phonemes: bool = False,
        normalized_text: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Synthesize speech using the Supertone SDK streaming API.

        Yields audio data chunks as they are received from the API.
        This reduces time-to-first-audio compared to the batch synthesize() method.

        `include_phonemes` and `normalized_text` (SDK 0.2.3, ISSUE-025) are
        forwarded to the SDK as-is. `normalized_text` is only honored by the
        `sona_speech_2` / `sona_speech_2_flash` models per the SDK; other models
        ignore it (no client-side rejection).
        """
        lang_enum = _LANGUAGE_MAP[language]
        model_enum = _MODEL_MAP[model]
        fmt_enum = _FORMAT_MAP[output_format]

        voice_settings = models.ConvertTextToSpeechParameters(
            speed=speed,
            pitch_shift=float(pitch_shift),
        )

        try:
            response = await self._sdk.text_to_speech.stream_speech_async(
                voice_id=voice_id,
                text=text,
                language=lang_enum,
                model=model_enum,
                output_format=fmt_enum,
                voice_settings=voice_settings,
                style=style,
                include_phonemes=include_phonemes,
                normalized_text=normalized_text,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        result = response.result
        if hasattr(result, "aiter_bytes"):
            async for chunk in result.aiter_bytes():
                yield chunk
        elif isinstance(result, str):
            yield result.encode("utf-8")
        else:
            yield result

    async def get_voices(self) -> list[VoiceDict]:
        """Fetch all available voices from the Supertone API (handles pagination)."""
        all_voices: list[VoiceDict] = []
        next_page_token: str | None = None

        while True:
            try:
                response = await self._sdk.voices.list_voices_async(
                    page_size=100,
                    next_page_token=next_page_token,
                )
            except (
                UnauthorizedErrorResponse,
                ForbiddenErrorResponse,
                TooManyRequestsErrorResponse,
                InternalServerErrorResponse,
                NoResponseError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                _handle_sdk_errors(exc)

            for item in response.items:
                voice: VoiceDict = {
                    "voice_id": item.voice_id,
                    "name": item.name,
                    "supported_languages": item.language,
                    "supported_styles": item.styles,
                }
                all_voices.append(voice)

            next_page_token = response.next_page_token
            if not next_page_token:
                break

        return all_voices

    async def search_voices(
        self,
        name: str | None = None,
        description: str | None = None,
        language: str | None = None,
        gender: str | None = None,
        age: str | None = None,
        use_case: str | None = None,
        use_cases: str | None = None,
        style: str | None = None,
        model: str | None = None,
    ) -> list[VoiceDict]:
        """Search voices on the Supertone API with optional filters.

        All filter params are pass-through strings (per SDK signature); enum
        validation is delegated to the API. Auto-paginates and returns the
        full concatenated list as `VoiceDict` entries (same shape as
        `get_voices()`).
        """
        all_voices: list[VoiceDict] = []
        next_page_token: str | None = None

        while True:
            try:
                response = await self._sdk.voices.search_voices_async(
                    page_size=100,
                    next_page_token=next_page_token,
                    name=name,
                    description=description,
                    language=language,
                    gender=gender,
                    age=age,
                    use_case=use_case,
                    use_cases=use_cases,
                    style=style,
                    model=model,
                )
            except (
                UnauthorizedErrorResponse,
                ForbiddenErrorResponse,
                TooManyRequestsErrorResponse,
                InternalServerErrorResponse,
                NoResponseError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                _handle_sdk_errors(exc)

            for item in response.items:
                voice: VoiceDict = {
                    "voice_id": item.voice_id,
                    "name": item.name,
                    "supported_languages": item.language,
                    "supported_styles": item.styles,
                }
                all_voices.append(voice)

            next_page_token = response.next_page_token
            if not next_page_token:
                break

        return all_voices

    async def get_voice(self, voice_id: str) -> VoiceDetailDict:
        """Fetch full detail for a single voice by ID.

        Maps the SDK `GetCharacterByIDResponse` into a `VoiceDetailDict`,
        renaming `language` to `supported_languages` for consistency with
        `VoiceDict`. Optional fields (`samples`, `thumbnail_image_url`) are
        only included when the SDK returned non-None values.
        """
        try:
            response = await self._sdk.voices.get_voice_async(voice_id=voice_id)
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        detail: VoiceDetailDict = {
            "voice_id": response.voice_id,
            "name": response.name,
            "description": response.description,
            "age": response.age,
            "gender": response.gender,
            "use_case": response.use_case,
            "use_cases": response.use_cases,
            "supported_languages": response.language,
            "styles": response.styles,
            "models": response.models,
        }

        samples = getattr(response, "samples", None)
        if samples is not None:
            detail["samples"] = [
                SampleDict(
                    language=s.language,
                    style=s.style,
                    model=s.model,
                    url=s.url,
                )
                for s in samples
            ]

        thumbnail = getattr(response, "thumbnail_image_url", None)
        if thumbnail is not None:
            detail["thumbnail_image_url"] = thumbnail

        return detail

    async def get_credit_balance(self) -> CreditBalanceDict:
        """Fetch the current credit balance for the authenticated user."""
        try:
            response = await self._sdk.usage.get_credit_balance_async()
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        return {"balance": response.balance}

    async def predict_duration(
        self,
        voice_id: str,
        text: str,
        language: str,
        output_format: str,
        model: str,
        speed: float,
        pitch_shift: int,
        style: str | None = None,
    ) -> float | None:
        """Predict the audio duration (seconds) for a TTS request WITHOUT
        synthesizing any audio.

        Mirrors the parameter shape of `synthesize()` so callers can preview
        the cost of a TTS call. Returns the SDK's `duration` field (a float
        in seconds), or `None` when the SDK does not populate it.
        """
        lang_enum = _PREDICT_LANGUAGE_MAP[language]
        model_enum = _PREDICT_MODEL_MAP[model]
        fmt_enum = _PREDICT_FORMAT_MAP[output_format]

        voice_settings = models.ConvertTextToSpeechParameters(
            speed=speed,
            pitch_shift=float(pitch_shift),
        )

        try:
            response = await self._sdk.text_to_speech.predict_duration_async(
                voice_id=voice_id,
                text=text,
                language=lang_enum,
                model=model_enum,
                output_format=fmt_enum,
                voice_settings=voice_settings,
                style=style,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        return response.duration

    async def create_cloned_voice(
        self,
        name: str,
        audio_bytes: bytes,
        file_name: str,
        content_type: str,
        description: str | None = None,
    ) -> dict:
        """Create a custom (cloned) voice from a single audio file.

        Wraps `custom_voices.create_cloned_voice_async` (ISSUE-019). The
        caller is responsible for validating the file (extension, size,
        existence) and supplying already-read bytes plus the matching
        MIME type. The wrapper does NOT touch the filesystem.

        Returns a dict with the new `voice_id` (per the SDK
        `CreateCustomVoiceResponse` shape).
        """
        files_payload: models.FilesTypedDict = {
            "file_name": file_name,
            "content": audio_bytes,
            "content_type": content_type,
        }

        try:
            response = await self._sdk.custom_voices.create_cloned_voice_async(
                files=files_payload,
                name=name,
                description=description,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        return {"voice_id": response.voice_id}

    async def search_custom_voices(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> list[CustomVoiceDict]:
        """List custom (cloned) voices for the current API key.

        Mirrors the pagination pattern of `search_voices`: loops on
        `next_page_token` until the SDK returns a terminal page (no
        token). Filters are pass-through; the SDK / API decides the
        match semantics (partial-match per UX spec §2.9 / §4.9).

        Returns a list of `CustomVoiceDict` entries (the SDK exposes
        `voice_id`, `name`, and nullable `description`).
        """
        all_voices: list[CustomVoiceDict] = []
        next_page_token: str | None = None

        while True:
            try:
                response = await self._sdk.custom_voices.search_custom_voices_async(
                    page_size=100,
                    next_page_token=next_page_token,
                    name=name,
                    description=description,
                )
            except (
                UnauthorizedErrorResponse,
                ForbiddenErrorResponse,
                TooManyRequestsErrorResponse,
                InternalServerErrorResponse,
                NoResponseError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                _handle_sdk_errors(exc)

            for item in response.items:
                voice: CustomVoiceDict = {
                    "voice_id": item.voice_id,
                    "name": item.name,
                }
                item_description = getattr(item, "description", None)
                if item_description is not None:
                    voice["description"] = item_description
                all_voices.append(voice)

            next_page_token = response.next_page_token
            if not next_page_token:
                break

        return all_voices

    async def edit_custom_voice(
        self,
        voice_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> CustomVoiceDict:
        """Update name and/or description of a custom voice.

        Partial update: only the non-None kwargs are forwarded to the
        SDK. The caller is responsible for enforcing the "at least one
        of name/description" rule before invoking this method.

        Returns a `CustomVoiceDict` reflecting the updated voice.
        """
        # Build kwargs dict so we only send fields the caller actually set.
        # The SDK accepts None for both, but explicit omission keeps the
        # wire payload aligned with the caller's intent.
        sdk_kwargs: dict = {"voice_id": voice_id}
        if name is not None:
            sdk_kwargs["name"] = name
        if description is not None:
            sdk_kwargs["description"] = description

        try:
            response = await self._sdk.custom_voices.edit_custom_voice_async(
                **sdk_kwargs,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        result: CustomVoiceDict = {
            "voice_id": response.voice_id,
            "name": response.name,
        }
        resp_description = getattr(response, "description", None)
        if resp_description is not None:
            result["description"] = resp_description
        return result

    async def delete_custom_voice(self, voice_id: str) -> None:
        """Delete a custom (cloned) voice by ID.

        The SDK returns nothing on a successful 204 / 200. Errors are
        mapped through `_handle_sdk_errors` like the other wrappers.
        Per UX spec §4.11 this is irreversible — callers (the MCP tool
        layer) are expected to surface the warning to the user.
        """
        try:
            await self._sdk.custom_voices.delete_custom_voice_async(
                voice_id=voice_id,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

    async def get_custom_voice(self, voice_id: str) -> CustomVoiceDict:
        """Fetch the detail of a single custom (cloned) voice by ID.

        Wraps `custom_voices.get_custom_voice_async` (ISSUE-026) and maps
        the SDK `GetCustomVoiceResponse` into a `CustomVoiceDict`. The SDK
        schema exposes `voice_id`, `name`, and a nullable `description`
        (there is NO `created_at` field — verified against the installed
        SDK `models/getcustomvoiceresponse.py`), so `description` is only
        included when the SDK returned a non-None value, matching the
        `search_custom_voices` / `edit_custom_voice` mapping convention.

        Errors are mapped through `_handle_sdk_errors` like the other
        wrappers.
        """
        try:
            response = await self._sdk.custom_voices.get_custom_voice_async(
                voice_id=voice_id,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        result: CustomVoiceDict = {
            "voice_id": response.voice_id,
            "name": response.name,
        }
        resp_description = getattr(response, "description", None)
        if resp_description is not None:
            result["description"] = resp_description
        return result

    async def aclose(self) -> None:
        """Close the underlying SDK HTTP client."""
        # The SDK uses httpx internally; close its async client if available
        if hasattr(self._sdk, "_client"):
            await self._sdk._client.aclose()
