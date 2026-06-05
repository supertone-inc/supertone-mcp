"""MCP tool handlers, input validation, and output formatting."""

import base64
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.types import AudioContent, TextContent
from mutagen import File as MutagenFile

from supertone_mcp.constants import (
    DEFAULT_FORMAT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_MODE,
    DEFAULT_PITCH_SHIFT,
    DEFAULT_SPEED,
    DEFAULT_VOICE_ID,
    MAX_AUDIO_FILE_BYTES,
    OUTPUT_MODE_BOTH,
    OUTPUT_MODE_FILES,
    OUTPUT_MODE_RESOURCES,
    PITCH_SHIFT_MAX,
    PITCH_SHIFT_MIN,
    SPEED_MAX,
    SPEED_MIN,
    SUPPORTED_CLONE_FORMATS,
    SUPPORTED_FORMATS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_MODELS,
    TEXT_MAX_LENGTH,
    VALID_OUTPUT_MODES,
)
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
    TTSResponse,
    VoiceDetailDict,
    VoiceInfo,
    generate_output_path,
)
from supertone_mcp.supertone_client import SupertoneClient


def _format_int_with_commas(value: int | float) -> str:
    """Format a numeric value with thousands separators (e.g., 12345 -> 12,345)."""
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    return f"{int(value):,}"


# --- Input Validation ---


def validate_text(text: str) -> None:
    """Validate text input for TTS."""
    if not text:
        raise ValueError("Text must not be empty.")


def validate_text_max_length(text: str) -> None:
    """Validate text against the 300-character SDK limit.

    Used by handlers (e.g., `predict_duration`) where the SDK does NOT
    auto-chunk long inputs and a >300-char payload would be rejected by
    the API. The `text_to_speech` handler intentionally skips this check
    because the synthesize SDK splits chunks transparently.
    """
    n = len(text)
    if n > TEXT_MAX_LENGTH:
        raise ValueError(
            f"Text exceeds the maximum length of {TEXT_MAX_LENGTH} characters "
            f"(received: {n}). Please shorten or split the text manually."
        )


def validate_language(language: str) -> None:
    """Validate language code."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f'Invalid language: "{language}". '
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
        )


def validate_output_format(fmt: str) -> None:
    """Validate output format."""
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f'Invalid output format: "{fmt}". Supported formats: mp3, wav.'
        )


def validate_speed(speed: float) -> None:
    """Validate speed parameter."""
    if speed < SPEED_MIN or speed > SPEED_MAX:
        raise ValueError(
            f"Speed must be between {SPEED_MIN} and {SPEED_MAX} (received: {speed})."
        )


def validate_pitch_shift(pitch_shift: int) -> None:
    """Validate pitch shift parameter."""
    if pitch_shift < PITCH_SHIFT_MIN or pitch_shift > PITCH_SHIFT_MAX:
        raise ValueError(
            f"Pitch shift must be between {PITCH_SHIFT_MIN} and +{PITCH_SHIFT_MAX} "
            f"semitones (received: {pitch_shift})."
        )


def validate_model(model: str) -> None:
    """Validate model parameter."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f'Invalid model: "{model}". '
            f"Supported models: {', '.join(SUPPORTED_MODELS)}."
        )


def validate_output_mode(mode: str) -> str:
    """Validate the per-call `output_mode` argument (ISSUE-022).

    Replaces the former `resolve_output_mode()` env read. The output mode is
    now decided per call via the `text_to_speech` `output_mode` parameter;
    the `SUPERTONE_MCP_OUTPUT_MODE` environment variable is no longer
    consulted for behavior control.

    Returns the case-normalized mode on success; raises `ValueError` with the
    UX-spec wording for an unknown mode.
    """
    normalized = mode.lower()
    if normalized not in VALID_OUTPUT_MODES:
        raise ValueError(
            f'Invalid output mode: "{mode}". '
            f"Valid modes: {', '.join(VALID_OUTPUT_MODES)}."
        )
    return normalized


def validate_audio_path(audio_path: str) -> None:
    """Validate the audio path for `clone_voice` (ISSUE-019).

    Performs fail-fast checks in this order:
      1. File must exist (after `~` expansion).
      2. Extension (case-insensitive) must be in `SUPPORTED_CLONE_FORMATS`.

    Per UX spec §4.8, the user-facing error wording is:
      - missing → `Audio file not found: {path}`
      - bad ext → `Unsupported audio format. Supported: WAV, MP3.`

    Note: size validation is performed by `validate_audio_file_size` against
    the resolved `Path` object so callers can fail-fast on `stat().st_size`
    before calling `read_bytes()`.
    """
    p = Path(audio_path).expanduser()
    if not p.is_file():
        raise ValueError(f"Audio file not found: {p}")
    ext = p.suffix.lower()
    if ext not in SUPPORTED_CLONE_FORMATS:
        raise ValueError("Unsupported audio format. Supported: WAV, MP3.")


def validate_audio_file_size(path: Path) -> None:
    """Validate the audio file size against `MAX_AUDIO_FILE_BYTES` (3MB).

    Uses `stat().st_size` so callers can fail fast WITHOUT reading the file
    contents. Raises with the UX-spec wording `Audio file too large:
    {size_mb:.2f}MB. Maximum: 3MB.` per the ISSUE-019 AC.
    """
    size = path.stat().st_size
    if size > MAX_AUDIO_FILE_BYTES:
        size_mb = size / (1024 * 1024)
        raise ValueError(f"Audio file too large: {size_mb:.2f}MB. Maximum: 3MB.")


# --- Configuration Resolution ---


def resolve_api_key() -> str:
    """Resolve the Supertone API key from environment."""
    key = os.environ.get("SUPERTONE_API_KEY", "")
    if not key:
        raise ValueError(
            "SUPERTONE_API_KEY environment variable is not set. "
            "Please configure it in your MCP client settings."
        )
    return key


def resolve_voice_id() -> str:
    """Resolve the default voice ID from environment or constant."""
    return os.environ.get("SUPERTONE_MCP_VOICE_ID", DEFAULT_VOICE_ID)


def resolve_output_dir() -> str:
    """Resolve the output directory from environment or default."""
    output_dir = os.environ.get("SUPERTONE_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    return str(Path(output_dir).expanduser().resolve())


def ensure_output_dir(path: str) -> None:
    """Create the output directory if it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError:
        raise ValueError(
            f"Cannot write to output directory: {path}. "
            "Please check directory permissions or set SUPERTONE_OUTPUT_DIR "
            "to a writable location."
        )


# --- Migration warning (ISSUE-022) ---

# Behavior-control env vars removed in ISSUE-022. If a user still has them set,
# emit a one-time stderr warning (per process) to aid migration. These vars are
# NO LONGER read for behavior — output mode and autoplay are per-call params.
_REMOVED_BEHAVIOR_ENV_VARS = (
    "SUPERTONE_MCP_OUTPUT_MODE",
    "SUPERTONE_MCP_AUTOPLAY",
)
_migration_warning_emitted = False


def _warn_removed_behavior_env_vars() -> None:
    """Emit a one-time stderr warning if removed behavior env vars are set.

    Does NOT change behavior (the vars are ignored regardless). Fires at most
    once per process. Logging goes to stderr only — stdout is reserved for the
    MCP stdio protocol.
    """
    global _migration_warning_emitted
    if _migration_warning_emitted:
        return
    present = [v for v in _REMOVED_BEHAVIOR_ENV_VARS if os.environ.get(v)]
    if present:
        _migration_warning_emitted = True
        print(
            f"[supertone-mcp] WARNING: {', '.join(present)} is set but no longer "
            "read. Output mode and autoplay are now per-call parameters of "
            "text_to_speech (output_mode, autoplay). autoplay now defaults to "
            "false. See the migration guide.",
            file=sys.stderr,
        )


# --- Autoplay ---


def _autoplay(
    file_path: str | None, audio_bytes: bytes | None, output_format: str
) -> None:
    """Play audio via macOS afplay (fire-and-forget, non-blocking)."""
    if sys.platform != "darwin":
        return
    try:
        if file_path:
            subprocess.Popen(
                ["/usr/bin/afplay", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif audio_bytes:
            tmp = tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False)
            tmp.write(audio_bytes)
            tmp.close()
            subprocess.Popen(
                f'/usr/bin/afplay "{tmp.name}" && rm -f "{tmp.name}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except OSError:
        pass


# --- Output Formatting ---


def format_tts_response(response: TTSResponse) -> str:
    """Format a TTSResponse as plain text per UX spec."""
    return (
        f"Audio file saved: {response.file_path}\n"
        f"Duration: {response.duration_seconds} seconds\n"
        f"Voice: {response.voice_id}\n"
        f"Language: {response.language}\n"
        f"Format: {response.output_format}"
    )


def format_tts_metadata(
    duration: float,
    voice_id: str,
    language: str,
    output_format: str,
    file_path: str | None = None,
) -> str:
    """Format TTS metadata as concise text for resources/both modes."""
    parts = [
        f"Duration: {duration}s",
        f"Voice: {voice_id}",
        f"Language: {language}",
        f"Format: {output_format}",
    ]
    if file_path:
        parts.insert(0, f"Saved: {file_path}")
    return " | ".join(parts)


def format_voice_list(
    voices: list[VoiceInfo],
    language_filter: str | None = None,
    filters: dict[str, str | None] | None = None,
) -> str:
    """Format a list of VoiceInfo as plain text per UX spec.

    When `filters` is provided (the v0.2 path used by `search_voice`), any
    non-None entries are rendered as a "Filters applied: k=v, ..." prefix line
    above the standard list. An empty result with active filters returns
    "No voices found matching the filters." per the v0.2 UX spec.

    The legacy `language_filter` argument is retained for backward-compatible
    callers (none remain after ISSUE-015, kept for safety/test coverage).
    """
    active_filters: dict[str, str] = {}
    if filters:
        active_filters = {k: v for k, v in filters.items() if v is not None}

    if not voices:
        if active_filters:
            return "No voices found matching the filters."
        if language_filter:
            return f"No voices found matching language: {language_filter}."
        return "No voices found."

    if active_filters:
        filter_line = "Filters applied: " + ", ".join(
            f"{k}={v}" for k, v in active_filters.items()
        )
        header = f"{filter_line}\nFound {len(voices)} voices:"
    elif language_filter:
        header = f"Found {len(voices)} voices matching language: {language_filter}"
    else:
        header = f"Found {len(voices)} voices:"

    entries = []
    for i, voice in enumerate(voices, 1):
        entry = (
            f"{i}. Name: {voice.name}\n"
            f"   Voice ID: {voice.voice_id}\n"
            f"   Languages: {', '.join(voice.supported_languages)}\n"
            f"   Styles: {', '.join(voice.supported_styles)}"
        )
        entries.append(entry)

    return header + "\n\n" + "\n\n".join(entries)


def calculate_duration(file_path: str) -> float:
    """Calculate the duration of an audio file in seconds using mutagen."""
    try:
        audio = MutagenFile(file_path)
        if audio is not None and audio.info is not None:
            return round(audio.info.length, 1)
    except Exception:
        pass
    return 0.0


# --- Tool Handlers ---


async def text_to_speech(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    output_format: str | None = None,
    model: str | None = None,
    speed: float | None = None,
    pitch_shift: int | None = None,
    style: str | None = None,
    output_mode: str | None = None,
    autoplay: bool = False,
    streaming: bool = False,
) -> str | list:
    """Convert text to speech using Supertone TTS API.

    Output mode and autoplay are decided PER CALL (ISSUE-022):
      - `output_mode`: "files" (default), "resources", or "both". Resolved to
        `DEFAULT_OUTPUT_MODE` when None. The removed `SUPERTONE_MCP_OUTPUT_MODE`
        env var is NO LONGER read.
      - `autoplay`: defaults to False. The removed `SUPERTONE_MCP_AUTOPLAY`
        env var is NO LONGER read.

    Synthesis routing is decided PER CALL (ISSUE-023):
      - `streaming`: defaults to False. When False, the one-shot
        `client.synthesize` path is used. When True, the
        `client.synthesize_stream` chunked path is used. Streaming is only
        supported by `model="sona_speech_1"`; any other model with
        `streaming=True` fails fast BEFORE any SDK call.

    Returns a plain-text response string ("files" mode) or a list of Content
    objects ("resources"/"both" modes).
    """
    # Migration aid: warn once if the removed behavior env vars are set.
    _warn_removed_behavior_env_vars()

    # Apply defaults
    voice_id = voice_id or resolve_voice_id()
    language = language or DEFAULT_LANGUAGE
    output_format = output_format or DEFAULT_FORMAT
    model = model or DEFAULT_MODEL
    speed = speed if speed is not None else DEFAULT_SPEED
    pitch_shift = pitch_shift if pitch_shift is not None else DEFAULT_PITCH_SHIFT
    output_mode_arg = output_mode if output_mode is not None else DEFAULT_OUTPUT_MODE

    # Validate inputs
    try:
        api_key = resolve_api_key()
        output_mode = validate_output_mode(output_mode_arg)
        validate_text(text)
        validate_language(language)
        validate_output_format(output_format)
        validate_model(model)
        validate_speed(speed)
        validate_pitch_shift(pitch_shift)
    except ValueError as e:
        return str(e)

    # Cross-field validation (ISSUE-023): streaming requires sona_speech_1.
    # Fail fast BEFORE constructing/calling the client.
    if streaming and model != "sona_speech_1":
        return (
            f'Streaming is only supported by model "sona_speech_1" '
            f'(received: "{model}"). Set streaming=false or use sona_speech_1.'
        )

    # Resolve output directory (only needed for files/both modes)
    needs_file = output_mode in (OUTPUT_MODE_FILES, OUTPUT_MODE_BOTH)
    if needs_file:
        try:
            output_dir = resolve_output_dir()
            ensure_output_dir(output_dir)
        except ValueError as e:
            return str(e)

    # Synthesize audio from SDK (one-shot by default; streaming when requested)
    client = SupertoneClient(api_key=api_key)
    file_path_str: str | None = None
    output_path: Path | None = None
    sdk_duration: float | None = None

    try:
        # Prepare file output path if needed
        if needs_file:
            output_path = generate_output_path(output_dir, output_format)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file and/or collect in memory
        memory_buffer = io.BytesIO()
        collect_in_memory = output_mode in (OUTPUT_MODE_RESOURCES, OUTPUT_MODE_BOTH)

        if streaming:
            # Streaming path: consume chunks from synthesize_stream.
            file_handle = None
            try:
                if output_path is not None:
                    file_handle = open(output_path, "wb")

                async for chunk in client.synthesize_stream(
                    voice_id=voice_id,
                    text=text,
                    language=language,
                    output_format=output_format,
                    model=model,
                    speed=speed,
                    pitch_shift=pitch_shift,
                    style=style,
                ):
                    if file_handle is not None:
                        file_handle.write(chunk)
                    if collect_in_memory:
                        memory_buffer.write(chunk)

            except (
                SupertoneAuthError,
                SupertoneRateLimitError,
                SupertoneServerError,
                SupertoneConnectionError,
            ):
                raise
            except Exception as exc:
                # Unexpected error mid-stream: clean up partial file
                if output_path is not None and output_path.exists():
                    output_path.unlink(missing_ok=True)
                return f"Streaming error: {exc}"
            finally:
                if file_handle is not None:
                    file_handle.close()
        else:
            # One-shot path: a single synthesize() call returns all bytes plus
            # an optional SDK-reported duration.
            audio_bytes_oneshot, _content_type, sdk_duration = await client.synthesize(
                voice_id=voice_id,
                text=text,
                language=language,
                output_format=output_format,
                model=model,
                speed=speed,
                pitch_shift=pitch_shift,
                style=style,
            )
            if output_path is not None:
                with open(output_path, "wb") as fh:
                    fh.write(audio_bytes_oneshot)
            if collect_in_memory:
                memory_buffer.write(audio_bytes_oneshot)

        if output_path is not None:
            file_path_str = str(output_path)

    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        # Clean up partial file on API error
        if output_path is not None and output_path.exists():
            output_path.unlink(missing_ok=True)
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        # Clean up partial file on connection error
        if output_path is not None and output_path.exists():
            output_path.unlink(missing_ok=True)
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    except PermissionError:
        return (
            f"Cannot write to output directory: {output_path.parent}. "
            "Please check directory permissions or set SUPERTONE_OUTPUT_DIR "
            "to a writable location."
        )
    except OSError:
        return "Cannot write audio file. Please check available disk space."
    finally:
        await client.aclose()

    # Determine duration. The one-shot path may return an SDK-reported
    # duration (ISSUE-023) — prefer it over the mutagen-derived value when
    # present. Otherwise fall back to reading the completed file with mutagen.
    if sdk_duration is not None:
        duration = round(sdk_duration, 1)
    elif file_path_str:
        duration = calculate_duration(file_path_str)
    else:
        duration = 0.0

    audio_bytes = memory_buffer.getvalue() if collect_in_memory else None

    # Autoplay after streaming completes — driven by the per-call argument
    # (default False). The removed SUPERTONE_MCP_AUTOPLAY env var is not read.
    if autoplay:
        _autoplay(file_path_str, audio_bytes, output_format)

    # Format response based on output mode
    if output_mode == OUTPUT_MODE_FILES:
        response = TTSResponse(
            file_path=file_path_str,
            duration_seconds=duration,
            voice_id=voice_id,
            language=language,
            output_format=output_format,
        )
        return format_tts_response(response)

    # resources or both mode: return AudioContent + TextContent
    mime_type = "audio/mpeg" if output_format == "mp3" else "audio/wav"
    audio_base64 = base64.b64encode(audio_bytes).decode()
    meta_text = format_tts_metadata(
        duration=duration,
        voice_id=voice_id,
        language=language,
        output_format=output_format,
        file_path=file_path_str,
    )
    return [
        AudioContent(type="audio", data=audio_base64, mimeType=mime_type),
        TextContent(type="text", text=meta_text),
    ]


async def search_voice(
    language: str | None = None,
    gender: str | None = None,
    age: str | None = None,
    use_case: str | None = None,
    style: str | None = None,
    model: str | None = None,
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Search the Supertone voice catalog with optional server-side filters.

    All filters are AND-combined and forwarded to the SDK; enum membership is
    validated server-side (per ISSUE-015 Implementation Notes). The single
    exception is `language`, which we still validate client-side against
    `SUPPORTED_LANGUAGES` to give the LLM/user a precise error message.

    With no filters this is equivalent to the legacy `list_voices` behavior.

    Returns a plain-text response string (never raises to the caller).
    """
    # Client-side validation: language only (enum-style filters are passed
    # through; the SDK / API is authoritative).
    if language is not None:
        try:
            validate_language(language)
        except ValueError as e:
            return str(e)

    # Resolve API key
    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    # Call API
    client = SupertoneClient(api_key=api_key)
    try:
        voice_dicts = await client.search_voices(
            name=name,
            description=description,
            language=language,
            gender=gender,
            age=age,
            use_case=use_case,
            style=style,
            model=model,
        )
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    # Convert to VoiceInfo objects
    voices = [
        VoiceInfo(
            voice_id=v["voice_id"],
            name=v["name"],
            supported_languages=v["supported_languages"],
            supported_styles=v["supported_styles"],
        )
        for v in voice_dicts
    ]

    filters: dict[str, str | None] = {
        "name": name,
        "description": description,
        "language": language,
        "gender": gender,
        "age": age,
        "use_case": use_case,
        "style": style,
        "model": model,
    }

    return format_voice_list(voices, filters=filters)


# --- get_voice / get_credit_balance (ISSUE-016) ---


def format_voice_detail(detail: VoiceDetailDict) -> str:
    """Format a `VoiceDetailDict` as a multi-line plain-text response.

    Per UX spec §4.4, sample audio URLs are intentionally NOT rendered here —
    that surface belongs to `preview_voice` (ISSUE-017). We only expose the
    sample COUNT.

    Optional fields (per `VoiceDetailDict`) are rendered with sensible
    fallbacks: missing strings collapse to "-", missing list fields render
    as an empty joined value. Required fields are accessed directly.
    """
    voice_id = detail["voice_id"]
    name = detail["name"]
    description = detail.get("description") or "-"
    age = detail.get("age") or "-"
    gender = detail.get("gender") or "-"

    use_cases_list = detail.get("use_cases") or []
    # Some SDK payloads only populate the singular `use_case` field; fall back.
    if not use_cases_list and detail.get("use_case"):
        use_cases_list = [detail["use_case"]]
    use_cases_str = ", ".join(use_cases_list) if use_cases_list else "-"

    languages = detail.get("supported_languages") or []
    languages_str = ", ".join(languages) if languages else "-"

    styles = detail.get("styles") or []
    styles_str = ", ".join(styles) if styles else "-"

    models = detail.get("models") or []
    models_str = ", ".join(models) if models else "-"

    samples = detail.get("samples")
    sample_count = len(samples) if samples is not None else 0

    lines = [
        f"Voice ID: {voice_id}",
        f"Name: {name}",
        f"Description: {description}",
        f"Age: {age}",
        f"Gender: {gender}",
        f"Use cases: {use_cases_str}",
        f"Languages: {languages_str}",
        f"Styles: {styles_str}",
        f"Models: {models_str}",
        f"Samples: {sample_count}",
    ]

    thumbnail = detail.get("thumbnail_image_url")
    if thumbnail:
        lines.append(f"Thumbnail: {thumbnail}")

    lines.append("")
    lines.append("Use preview_voice to fetch sample URLs.")
    return "\n".join(lines)


def format_credit_balance(balance: CreditBalanceDict) -> str:
    """Format a `CreditBalanceDict` as a single-line plain-text response.

    Per UX spec §4.5, the canonical line is:
      `Credit balance: 12,345 credits remaining.`

    The SDK schema currently exposes only `balance` (nullable float). If the
    upstream payload one day grows `plan` / `expires_at` fields (the spec
    leaves room for them), we render them on subsequent lines without
    breaking the single-line guarantee for the minimal case. `balance=None`
    is treated as unknown.
    """
    raw_balance = balance.get("balance")
    if raw_balance is None:
        balance_str = "unknown"
    else:
        balance_str = _format_int_with_commas(raw_balance)

    lines = [f"Credit balance: {balance_str} credits remaining."]

    # Forward-compat: render optional `plan` / `expires_at` if the SDK starts
    # returning them. The current TypedDict only declares `balance`, so use
    # `.get(...)` against the runtime dict — TypedDicts ARE dicts at runtime,
    # so this is safe without an isinstance ladder.
    plan = balance.get("plan")  # type: ignore[typeddict-item]
    if plan:
        lines.append(f"Plan: {plan}")
    expires = balance.get("expires_at")  # type: ignore[typeddict-item]
    if expires:
        lines.append(f"Expires: {expires}")

    return "\n".join(lines)


async def get_voice(voice_id: str) -> str:
    """Return formatted detail for a single voice by ID.

    Validates that `voice_id` is a non-empty (post-strip) string before
    issuing any API call. Errors from the SDK are mapped to the same
    plain-text strings used elsewhere in this module.
    """
    # Fail-fast input validation — no API call when voice_id is empty/whitespace.
    if not isinstance(voice_id, str) or not voice_id.strip():
        return "voice_id must not be empty."

    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        detail = await client.get_voice(voice_id=voice_id)
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    return format_voice_detail(detail)


async def get_credit_balance() -> str:
    """Return the formatted current credit balance for the API key.

    No input parameters. Errors from the SDK are mapped to the same plain
    text strings used elsewhere in this module.
    """
    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        balance = await client.get_credit_balance()
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    return format_credit_balance(balance)


# --- preview_voice (ISSUE-017) ---


def format_voice_samples(
    samples: list[SampleDict] | None,
    filters: dict[str, str | None],
) -> str:
    """Format a voice's sample list as a numbered plain-text response.

    Per UX spec §4.6:
      - One line per matching sample.
      - Format: `N. [language=ko, style=happy, model=sona_speech_1] <url>`
      - If `samples` is None or empty: `"This voice has no preview samples."`
      - If samples exist but filters match none:
        `"No matching samples for the given filters."`

    `filters` is a mapping with keys "language", "style", "model"; any
    non-None value is applied as an exact-match filter (AND-combined).
    Numbering restarts at 1 across the FILTERED subset (not the source list).
    """
    if not samples:
        return "This voice has no preview samples."

    language_filter = filters.get("language")
    style_filter = filters.get("style")
    model_filter = filters.get("model")

    matched = [
        s
        for s in samples
        if (language_filter is None or s.get("language") == language_filter)
        and (style_filter is None or s.get("style") == style_filter)
        and (model_filter is None or s.get("model") == model_filter)
    ]

    if not matched:
        return "No matching samples for the given filters."

    lines = []
    for i, sample in enumerate(matched, 1):
        lines.append(
            f"{i}. [language={sample['language']}, "
            f"style={sample['style']}, "
            f"model={sample['model']}] "
            f"{sample['url']}"
        )
    return "\n".join(lines)


async def preview_voice(
    voice_id: str,
    language: str | None = None,
    style: str | None = None,
    model: str | None = None,
) -> str:
    """Return formatted sample audio URLs for a single voice.

    Calls `SupertoneClient.get_voice(voice_id)` to fetch the voice detail,
    then filters its `samples` list by the optional language/style/model
    parameters. The output is plain text suitable for an LLM to relay to
    the user.

    Errors from the SDK are mapped to the same plain-text strings used
    elsewhere in this module.
    """
    # Fail-fast input validation — no API call when voice_id is empty/whitespace.
    if not isinstance(voice_id, str) or not voice_id.strip():
        return "voice_id must not be empty."

    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        detail = await client.get_voice(voice_id=voice_id)
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    samples = detail.get("samples")
    filters: dict[str, str | None] = {
        "language": language,
        "style": style,
        "model": model,
    }
    return format_voice_samples(samples, filters)


# --- predict_duration (ISSUE-018) ---


def format_predicted_duration(duration: float | None) -> str:
    """Format the predicted duration as a single-line UX response.

    Per UX spec §4.7 the canonical line is:
      `Predicted duration: 2.34s (credit usage is proportional to duration).`

    The SDK marks `duration` as Optional[float], so when the upstream API
    omits the field we render a defensive "unknown" line that still keeps
    the UX-spec phrasing about credit proportionality. This avoids
    surfacing a Python `None` (or raising) when the schema gap is hit.
    """
    if duration is None:
        return "Predicted duration: unknown (credit usage is proportional to duration)."
    return (
        f"Predicted duration: {duration:.2f}s "
        "(credit usage is proportional to duration)."
    )


async def predict_duration(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    output_format: str | None = None,
    model: str | None = None,
    speed: float | None = None,
    pitch_shift: int | None = None,
    style: str | None = None,
) -> str:
    """Predict the output audio length for a TTS request WITHOUT synthesizing.

    Mirrors the parameter surface of `text_to_speech`, runs the same
    client-side validation (with the addition of the 300-character text
    cap — predict_duration does not chunk), and maps SDK errors to the
    same plain-text strings used elsewhere in this module.

    Returns the formatted single-line response per UX spec §4.7.
    """
    # Apply defaults — same resolution as text_to_speech.
    voice_id = voice_id or resolve_voice_id()
    language = language or DEFAULT_LANGUAGE
    # SDK default for predict_duration is "wav"; match that (UX §2.7 note).
    output_format = output_format or "wav"
    model = model or DEFAULT_MODEL
    speed = speed if speed is not None else DEFAULT_SPEED
    pitch_shift = pitch_shift if pitch_shift is not None else DEFAULT_PITCH_SHIFT

    # Validate inputs — fail-fast, no API call on any validation failure.
    try:
        api_key = resolve_api_key()
        validate_text(text)
        validate_text_max_length(text)
        validate_language(language)
        validate_output_format(output_format)
        validate_model(model)
        validate_speed(speed)
        validate_pitch_shift(pitch_shift)
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        duration = await client.predict_duration(
            voice_id=voice_id,
            text=text,
            language=language,
            output_format=output_format,
            model=model,
            speed=speed,
            pitch_shift=pitch_shift,
            style=style,
        )
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    return format_predicted_duration(duration)


# --- clone_voice (ISSUE-019) ---


async def clone_voice(
    name: str,
    audio_path: str,
    description: str | None = None,
) -> str:
    """Create a custom (cloned) voice from a single local audio file.

    Workflow (fail-fast, per UX spec §4.8):
      1. Validate `name` is non-empty (after strip).
      2. Resolve the API key from env.
      3. Validate `audio_path` (existence, supported extension).
      4. Validate file size (≤3MB) via `stat().st_size`.
      5. Read bytes from disk.
      6. Resolve content_type from extension.
      7. Call `SupertoneClient.create_cloned_voice`.
      8. Format the response per UX spec §4.8.

    Errors from the SDK are mapped to the same plain-text strings used
    elsewhere in this module (auth / rate-limit / 5xx / connection).
    """
    # Fail-fast: empty / whitespace-only name is rejected before any API call.
    if not isinstance(name, str) or not name.strip():
        return "Voice name must not be empty."

    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    # Path + size validation BEFORE constructing the client / reading bytes.
    try:
        validate_audio_path(audio_path)
    except ValueError as e:
        return str(e)

    resolved = Path(audio_path).expanduser()

    try:
        validate_audio_file_size(resolved)
    except ValueError as e:
        return str(e)

    # Read bytes only after size has been confirmed.
    try:
        audio_bytes = resolved.read_bytes()
    except PermissionError:
        return f"Cannot read audio file: {resolved}. Please check file permissions."
    except OSError as e:
        return f"Cannot read audio file: {resolved}. {e}"

    content_type = SUPPORTED_CLONE_FORMATS[resolved.suffix.lower()]
    file_name = resolved.name

    client = SupertoneClient(api_key=api_key)
    try:
        result = await client.create_cloned_voice(
            name=name,
            audio_bytes=audio_bytes,
            file_name=file_name,
            content_type=content_type,
            description=description,
        )
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    voice_id = result["voice_id"]
    return (
        f"Custom voice created. voice_id: {voice_id}. "
        "Use this voice_id in text_to_speech."
    )


# --- search_custom_voice / edit_custom_voice / delete_custom_voice (ISSUE-020) ---


def format_custom_voice_list(voices: list[CustomVoiceDict]) -> str:
    """Format a list of `CustomVoiceDict` as a numbered plain-text response.

    Per UX spec §4.9: a header "Found N custom voices:" (or
    "No custom voices found." when empty) followed by one entry per
    voice with `Name`, `Voice ID`, and `Description` fields.

    Description renders as "-" when missing/empty per the UX spec
    placeholder convention used elsewhere (see `format_voice_detail`).
    Note: the UX spec illustrative example also includes a `Created`
    line; the SDK schema does NOT expose a created-at field for custom
    voices in v0.2, so that line is intentionally omitted to keep
    output truthful to the source data. This is documented as a
    docs-vs-SDK drift in review notes.
    """
    if not voices:
        return "No custom voices found."

    header = f"Found {len(voices)} custom voices:"
    entries = []
    for i, voice in enumerate(voices, 1):
        description = voice.get("description") or "-"
        entry = (
            f"{i}. Name: {voice['name']}\n"
            f"   Voice ID: {voice['voice_id']}\n"
            f"   Description: {description}"
        )
        entries.append(entry)
    return header + "\n\n" + "\n\n".join(entries)


async def search_custom_voice(
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Return a numbered list of the API key's custom (cloned) voices.

    Both `name` and `description` are optional partial-match filters
    delegated to the SDK. Errors from the SDK are mapped to the same
    plain-text strings used elsewhere in this module.
    """
    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        voices = await client.search_custom_voices(
            name=name,
            description=description,
        )
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    return format_custom_voice_list(voices)


async def edit_custom_voice(
    voice_id: str,
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Update name and/or description of an existing custom voice.

    Validates fail-fast that:
      1. `voice_id` is a non-empty (post-strip) string.
      2. At least one of `name` / `description` is provided.

    No API call is made if either guard fails. Errors from the SDK are
    mapped to the same plain-text strings used elsewhere in this module.

    Per UX spec §4.10, a 404 should surface as
      `Custom voice not found: "{voice_id}".`
    but the shared `_handle_sdk_errors` does NOT yet map 404 (RL-006).
    This handler intentionally mirrors the existing `get_voice` /
    `preview_voice` behavior (no 404 mapping) and the gap is logged for
    a future tech-debt issue.
    """
    if not isinstance(voice_id, str) or not voice_id.strip():
        return "voice_id must not be empty."

    if name is None and description is None:
        return "Provide at least one of: name, description."

    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        await client.edit_custom_voice(
            voice_id=voice_id,
            name=name,
            description=description,
        )
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    return f"Custom voice updated. voice_id: {voice_id}."


async def delete_custom_voice(voice_id: str) -> str:
    """Permanently delete a custom (cloned) voice by ID.

    Validates fail-fast that `voice_id` is a non-empty (post-strip)
    string. No API call is made if validation fails. Per UX spec §4.11
    this action is irreversible; the user-facing warning lives in the
    tool description text (no in-tool confirmation gate in v0.2).

    Per UX spec §4.11, a 404 should surface as
      `Custom voice not found: "{voice_id}".`
    but the shared `_handle_sdk_errors` does NOT yet map 404 (RL-006).
    This handler intentionally mirrors the existing `get_voice` /
    `preview_voice` behavior (no 404 mapping) and the gap is logged for
    a future tech-debt issue.
    """
    if not isinstance(voice_id, str) or not voice_id.strip():
        return "voice_id must not be empty."

    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    client = SupertoneClient(api_key=api_key)
    try:
        await client.delete_custom_voice(voice_id=voice_id)
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return (
            "Failed to connect to Supertone API. Please check your network connection."
        )
    finally:
        await client.aclose()

    return f"Custom voice deleted. voice_id: {voice_id}."
