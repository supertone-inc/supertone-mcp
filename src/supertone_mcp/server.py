"""MCP server entry point for Supertone TTS."""

from mcp.server.fastmcp import FastMCP

from supertone_mcp import tools

mcp = FastMCP("supertone-tts")


@mcp.tool(
    name="text_to_speech",
    description=(
        "Generate natural-sounding speech audio from text. "
        "Use this when the user wants to: "
        "hear text read aloud, create narration or voiceover, "
        "generate voice audio, preview how text sounds when spoken, "
        "or convert any writing into spoken audio. "
        "Supports 23 languages including Korean, English, and Japanese. "
        "Audio is automatically played back on macOS. "
        "A default voice is already configured -- just call this tool directly. "
        "Only call search_voice if the user explicitly asks to change or browse voices."
    ),
)
async def text_to_speech(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    output_format: str | None = None,
    model: str | None = None,
    speed: float | None = None,
    pitch_shift: int | None = None,
    style: str | None = None,
) -> str | list:
    """Generate natural-sounding speech audio from text.

    Args:
        text: The text to speak aloud. Required.
            Can be a sentence, paragraph, or any text content.
            Long text is automatically split and processed.
        voice_id: Voice to use (e.g., "sujin-01", "minho-01").
            Run search_voice to browse available voices.
            If omitted, a default Korean voice is used.
        language: Language code for the speech output.
            "ko" (Korean, default), "en" (English), "ja" (Japanese),
            and 20+ more. Must match the text language for best results.
        output_format: Audio file format: "mp3" (default) or "wav".
            Use "wav" for higher quality, "mp3" for smaller files.
        model: TTS model: "sona_speech_1" (default, streaming),
            "sona_speech_2", "sona_speech_2_flash" (fastest),
            "sona_speech_2t", "supertonic_api_1".
        speed: Speech speed. 0.5 (slow) to 2.0 (fast). Default: 1.0.
        pitch_shift: Voice pitch adjustment in semitones.
            -24 (deeper) to +24 (higher). Default: 0.
        style: Emotion or tone of the voice (e.g., "neutral", "happy",
            "sad", "angry"). Available styles vary by voice --
            call search_voice to see what each voice supports.
    """
    return await tools.text_to_speech(
        text=text,
        voice_id=voice_id,
        language=language,
        output_format=output_format,
        model=model,
        speed=speed,
        pitch_shift=pitch_shift,
        style=style,
    )


@mcp.tool(
    name="search_voice",
    description=(
        "Search the Supertone voice catalog. "
        "Filters are optional and combined with AND semantics: "
        "name, description, language, gender, age, use_case, style, model. "
        "With no filters, returns the full catalog "
        "(the v0.1 list_voices behavior). "
        "The output is a numbered plain-text list; when any filter is set, "
        'the first line shows "Filters applied: ...".'
    ),
)
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
    """Search the Supertone voice catalog with optional filters.

    Args:
        language: Language code (e.g., "ko", "en", "ja").
        gender: Voice gender (e.g., "male", "female").
        age: Age bracket (e.g., "young_adult", "child").
        use_case: Single use case keyword (e.g., "narration", "advertisement").
        style: Emotion style (e.g., "neutral", "happy").
        model: TTS model identifier (e.g., "sona_speech_1").
        name: Voice name (partial match).
        description: Voice description (partial match).
    """
    return await tools.search_voice(
        language=language,
        gender=gender,
        age=age,
        use_case=use_case,
        style=style,
        model=model,
        name=name,
        description=description,
    )


@mcp.tool(
    name="get_voice",
    description=(
        "Fetch full detail for a single voice by voice_id. "
        "Returns name, description, age, gender, use_cases, languages, "
        "styles, supported models, sample count, and thumbnail URL. "
        "Use preview_voice to get the actual sample audio URLs."
    ),
)
async def get_voice(voice_id: str) -> str:
    """Fetch full detail for a single voice by voice_id.

    Args:
        voice_id: Voice identifier returned by search_voice. Required.
    """
    return await tools.get_voice(voice_id=voice_id)


@mcp.tool(
    name="get_credit_balance",
    description=(
        "Returns the remaining Supertone credit balance for the current "
        "API key. Use this before long TTS calls to confirm you have enough "
        "characters left."
    ),
)
async def get_credit_balance() -> str:
    """Return the remaining Supertone credit balance for the current API key."""
    return await tools.get_credit_balance()


@mcp.tool(
    name="preview_voice",
    description=(
        "Fetch sample audio URLs for a voice. "
        "Optionally filter samples by language, style, and model. "
        "Returns one URL per matching sample. "
        "v0.2 does NOT play the audio locally; "
        "pass the URL to your client to listen."
    ),
)
async def preview_voice(
    voice_id: str,
    language: str | None = None,
    style: str | None = None,
    model: str | None = None,
) -> str:
    """Fetch sample audio URLs for a voice.

    Args:
        voice_id: Voice identifier. Required.
        language: Filter samples by language code (e.g., "ko", "en", "ja").
        style: Filter samples by emotion style (e.g., "neutral", "happy").
        model: Filter samples by TTS model identifier (e.g., "sona_speech_1").
    """
    return await tools.preview_voice(
        voice_id=voice_id,
        language=language,
        style=style,
        model=model,
    )


@mcp.tool(
    name="predict_duration",
    description=(
        "Predict the expected output audio duration in seconds for a given "
        "text WITHOUT producing any audio file. "
        "Accepts the same parameters as text_to_speech and applies the "
        "same 300-character limit. "
        "Use this to estimate credit cost before synthesizing — "
        "credit usage is proportional to the predicted duration."
    ),
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
    """Predict audio duration for a TTS request without synthesizing audio.

    Args:
        text: The text to estimate duration for. Required.
            Maximum 300 characters (no auto-chunking, unlike text_to_speech).
        voice_id: Voice to estimate for. If omitted, the configured default
            voice is used (same env-var resolution as text_to_speech).
        language: Language code (e.g., "ko" default, "en", "ja").
        output_format: Audio format the estimate corresponds to: "wav"
            (default; matches the SDK default) or "mp3".
        model: TTS model identifier (default: "sona_speech_1").
        speed: Speech speed. 0.5 (slow) to 2.0 (fast). Default: 1.0.
        pitch_shift: Pitch adjustment in semitones. -24 to +24. Default: 0.
        style: Emotion or tone of the voice (optional, voice-dependent).
    """
    return await tools.predict_duration(
        text=text,
        voice_id=voice_id,
        language=language,
        output_format=output_format,
        model=model,
        speed=speed,
        pitch_shift=pitch_shift,
        style=style,
    )


@mcp.tool(
    name="clone_voice",
    description=(
        "Create a custom voice from a single local audio file. "
        "Constraints: WAV or MP3 only, max 3MB, exactly one file. "
        "The returned voice_id can be used immediately in text_to_speech. "
        'Path supports ~ expansion (e.g., "~/sample.wav").'
    ),
)
async def clone_voice(
    name: str,
    audio_path: str,
    description: str | None = None,
) -> str:
    """Create a custom (cloned) voice from a local audio file.

    Args:
        name: Display name for the new voice. Required, non-empty.
        audio_path: Absolute or ~-prefixed local path to a WAV or MP3 file
            (≤ 3MB). Required.
        description: Optional note/description for the new voice.
    """
    return await tools.clone_voice(
        name=name,
        audio_path=audio_path,
        description=description,
    )


@mcp.tool(
    name="search_custom_voice",
    description=(
        "List custom (cloned) voices created by this API key. "
        "Optional name and description filters perform partial matching. "
        "Pagination is handled internally; v0.2 returns the SDK default page."
    ),
)
async def search_custom_voice(
    name: str | None = None,
    description: str | None = None,
) -> str:
    """List the API key's custom (cloned) voices.

    Args:
        name: Partial-match filter on custom voice name.
        description: Partial-match filter on custom voice description.
    """
    return await tools.search_custom_voice(
        name=name,
        description=description,
    )


@mcp.tool(
    name="edit_custom_voice",
    description=(
        "Update the name and/or description of an existing custom voice. "
        "At least one of name or description must be provided."
    ),
)
async def edit_custom_voice(
    voice_id: str,
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Update name and/or description of a custom voice.

    Args:
        voice_id: Custom voice identifier. Required.
        name: New name. Optional, but one of name/description must be set.
        description: New description. Optional, but one of name/description
            must be set.
    """
    return await tools.edit_custom_voice(
        voice_id=voice_id,
        name=name,
        description=description,
    )


@mcp.tool(
    name="delete_custom_voice",
    description=(
        "Permanently delete a custom (cloned) voice. "
        "THIS IS IRREVERSIBLE — once deleted, the voice cannot be recovered "
        "and any saved voice_id referencing it will stop working. "
        "Confirm with the user before calling."
    ),
)
async def delete_custom_voice(voice_id: str) -> str:
    """Permanently delete a custom (cloned) voice by ID.

    Args:
        voice_id: Custom voice identifier to delete. Required.
    """
    return await tools.delete_custom_voice(voice_id=voice_id)


def main() -> None:
    """Start the Supertone TTS MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
