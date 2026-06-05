"""Constants and literal types for the Supertone TTS MCP server."""

from typing import Literal

Language = Literal[
    "ko",
    "en",
    "ja",
    "bg",
    "cs",
    "da",
    "de",
    "el",
    "es",
    "et",
    "fi",
    "fr",
    "hi",
    "hu",
    "id",
    "it",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "vi",
    "ar",
]
OutputFormat = Literal["mp3", "wav"]
Model = Literal[
    "sona_speech_1",
    "sona_speech_2",
    "sona_speech_2_flash",
    "sona_speech_2t",
    "sona_speech_3t",
    "supertonic_api_1",
    "supertonic_api_3",
]

SUPPORTED_LANGUAGES: list[str] = [
    "ko",
    "en",
    "ja",
    "bg",
    "cs",
    "da",
    "de",
    "el",
    "es",
    "et",
    "fi",
    "fr",
    "hi",
    "hu",
    "id",
    "it",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "vi",
    "ar",
]
SUPPORTED_FORMATS: list[str] = ["mp3", "wav"]
SUPPORTED_MODELS: list[str] = [
    "sona_speech_1",
    "sona_speech_2",
    "sona_speech_2_flash",
    "sona_speech_2t",
    "sona_speech_3t",
    "supertonic_api_1",
    "supertonic_api_3",
]

SPEED_MIN: float = 0.5
SPEED_MAX: float = 2.0
PITCH_SHIFT_MIN: int = -24
PITCH_SHIFT_MAX: int = 24
TEXT_MAX_LENGTH: int = 300

DEFAULT_LANGUAGE: str = "ko"
DEFAULT_FORMAT: str = "mp3"
DEFAULT_MODEL: str = "sona_speech_2_flash"
DEFAULT_SPEED: float = 1.0
DEFAULT_PITCH_SHIFT: int = 0
DEFAULT_VOICE_ID: str = (
    "2d5a380030e78fcab0c82a"  # Aiden (all languages, multiple styles)
)

HTTP_TIMEOUT: float = 30.0
SUPERTONE_BASE_URL: str = "https://supertoneapi.com"
DEFAULT_OUTPUT_DIR: str = "~/supertone-tts-output/"

OUTPUT_MODE_FILES: str = "files"
OUTPUT_MODE_RESOURCES: str = "resources"
OUTPUT_MODE_BOTH: str = "both"
VALID_OUTPUT_MODES: list[str] = [
    OUTPUT_MODE_FILES,
    OUTPUT_MODE_RESOURCES,
    OUTPUT_MODE_BOTH,
]
DEFAULT_OUTPUT_MODE: str = OUTPUT_MODE_FILES
DEFAULT_AUTOPLAY: bool = True

# --- ISSUE-019: clone_voice constraints ---
# Per FR-017 / UX spec §2.8: WAV/MP3 only, exactly one file, ≤3MB.
MAX_AUDIO_FILE_BYTES: int = 3 * 1024 * 1024
SUPPORTED_CLONE_FORMATS: dict[str, str] = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
}
