"""Domain types and data models for the Supertone TTS MCP server."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NotRequired, TypedDict
from uuid import uuid4


@dataclass(frozen=True)
class TTSRequest:
    """Validated TTS request parameters. Immutable after construction."""

    text: str
    voice_id: str
    language: str
    output_format: str
    model: str
    speed: float
    pitch_shift: int
    style: str | None


@dataclass(frozen=True)
class TTSResponse:
    """Result of a successful TTS synthesis."""

    file_path: str
    duration_seconds: float
    voice_id: str
    language: str
    output_format: str


@dataclass(frozen=True)
class VoiceInfo:
    """A single voice from the Supertone voice catalog."""

    voice_id: str
    name: str
    supported_languages: list[str]
    supported_styles: list[str]


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration resolved from environment."""

    api_key: str
    output_dir: str
    base_url: str


class VoiceSettingsBody(TypedDict, total=False):
    """voice_settings object nested in the synthesize request."""

    pitch_shift: int
    speed: float


class SynthesizeRequestBody(TypedDict, total=False):
    """Request body for the Supertone synthesize API."""

    text: str
    language: str
    output_format: str
    model: str
    style: str
    voice_settings: VoiceSettingsBody


class VoiceDict(TypedDict):
    """Voice entry from the Supertone API response (mapped from raw API)."""

    voice_id: str
    name: str
    supported_languages: list[str]
    supported_styles: list[str]


class SampleDict(TypedDict):
    """Sample audio entry for a voice (mirrors SDK `APISampleData`)."""

    language: str
    style: str
    model: str
    url: str


class VoiceDetailDict(TypedDict):
    """Detailed voice entry (mirrors SDK `GetCharacterByIDResponse`).

    Per RL-001: only `samples` and `thumbnail_image_url` are nullable in the
    SDK schema. All other fields are required, so we default to `total=True`
    and explicitly mark just those two as `NotRequired`. This restores type
    safety for downstream consumers (`format_voice_detail`, `preview_voice`)
    that read required fields without `.get()` guards.

    `language` from the SDK is exposed here as `supported_languages` for
    consistency with the existing `VoiceDict`.
    """

    voice_id: str
    name: str
    description: str
    age: str
    gender: str
    use_case: str
    use_cases: list[str]
    supported_languages: list[str]
    styles: list[str]
    models: list[str]
    samples: NotRequired[list[SampleDict]]
    thumbnail_image_url: NotRequired[str]


class CreditBalanceDict(TypedDict):
    """Credit balance entry (mirrors SDK `GetCreditBalanceResponse`).

    `balance` is nullable per the SDK schema.
    """

    balance: float | None


class CustomVoiceDict(TypedDict):
    """Custom (cloned) voice entry (mirrors SDK `GetCustomVoiceResponse`).

    Per RL-001: only `description` is nullable in the SDK schema. The
    required fields default to `total=True` so downstream consumers can
    read them without `.get()` guards.
    """

    voice_id: str
    name: str
    description: NotRequired[str | None]


def generate_output_path(output_dir: str, output_format: str) -> Path:
    """Generate a unique output file path for an audio file.

    Returns a Path like: /absolute/path/2026-03-13_a1b2c3d4.mp3
    """
    today = date.today().isoformat()
    unique_id = uuid4().hex[:8]
    filename = f"{today}_{unique_id}.{output_format}"
    return Path(output_dir).expanduser().resolve() / filename
