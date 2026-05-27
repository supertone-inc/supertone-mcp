# supertone-tts-mcp

MCP server for [Supertone](https://supertone.ai) TTS API. Convert text to speech with high-quality Korean, English, and Japanese voices directly from Claude Desktop, Cursor, or any MCP-compatible client.

## Features

- **text_to_speech** -- Convert text (up to 300 characters) to audio files (MP3/WAV)
- **search_voice** -- Search the voice catalog with filters (language, gender, age, use_case, style, model, name, description)
- Speed control (0.5x - 2.0x), pitch adjustment (-12 to +12 semitones), emotion styles
- Supports Korean, English, and Japanese

> **Breaking change in v0.2:** `list_voices` has been removed and replaced by `search_voice`. To reproduce the old behavior, call `search_voice` with no arguments.

## Installation

```bash
# Using uvx (recommended)
uvx supertone-tts-mcp

# Using pip
pip install supertone-tts-mcp
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-tts-mcp"],
      "env": {
        "SUPERTONE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-tts-mcp"],
      "env": {
        "SUPERTONE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPERTONE_API_KEY` | Yes | -- | Your Supertone API key |
| `SUPERTONE_OUTPUT_DIR` | No | `~/supertone-tts-output/` | Directory where audio files are saved |

## Usage Examples

Once configured, you can use natural language in your MCP client:

**Generate speech:**
> "Read this aloud: Hello, how are you today?"

The server will generate an audio file and return:
```
Audio file saved: /Users/you/supertone-tts-output/2026-03-13_a1b2c3d4.mp3
Duration: 2.3 seconds
Voice: sujin-01
Language: en
Format: mp3
```

**Search voices:**
> "Find me a female Korean voice for narration."

This calls `search_voice(language="ko", gender="female", use_case="narration")` and returns a numbered list whose first line is `Filters applied: language=ko, gender=female, use_case=narration`.

**Adjust parameters:**
> "Say 'good morning' in Japanese, slower and with a happy tone"

## Parameters

### text_to_speech

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | -- | Text to convert (max 300 characters) |
| `voice_id` | string | No | default voice | Voice identifier (use `search_voice` to browse) |
| `language` | string | No | `ko` | Language: `ko`, `en`, or `ja` |
| `output_format` | string | No | `mp3` | Format: `mp3` or `wav` |
| `speed` | float | No | `1.0` | Speed: 0.5 to 2.0 |
| `pitch_shift` | int | No | `0` | Pitch: -12 to +12 semitones |
| `style` | string | No | -- | Emotion style (e.g., `neutral`, `happy`) |

### search_voice

All parameters are optional. When all are omitted the full voice catalog is returned (equivalent to the removed `list_voices`). When any parameter is set, the response starts with a `Filters applied: ...` line.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `language` | string | No | -- | Language code (e.g., `ko`, `en`, `ja`) |
| `gender` | string | No | -- | Voice gender (e.g., `male`, `female`) |
| `age` | string | No | -- | Age bracket (e.g., `young_adult`, `child`) |
| `use_case` | string | No | -- | Use case keyword (e.g., `narration`, `advertisement`) |
| `style` | string | No | -- | Emotion style (e.g., `neutral`, `happy`) |
| `model` | string | No | -- | TTS model identifier (e.g., `sona_speech_1`) |
| `name` | string | No | -- | Voice name (partial match) |
| `description` | string | No | -- | Voice description (partial match) |

## Development

```bash
# Clone and install
git clone https://github.com/pillip/supertone-mcp.git
cd supertone-mcp
uv sync

# Run tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

## License

MIT
