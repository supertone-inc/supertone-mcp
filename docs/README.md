# Supertone TTS MCP Server

A Model Context Protocol (MCP) server that wraps the Supertone TTS API, enabling high-quality text-to-speech conversion directly from MCP-compatible clients like Claude Desktop and Cursor.

## Prerequisites

- **Python 3.11+**
- **uv** package manager ([install guide](https://docs.astral.sh/uv/))
- **Supertone API Key** ([get one here](https://supertoneapi.com))

## Setup

### Install Dependencies

```bash
uv sync
```

### Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Set your Supertone API key:

```
SUPERTONE_API_KEY=your-api-key-here
SUPERTONE_OUTPUT_DIR=~/supertone-tts-output/   # optional
```

### Run the MCP Server

```bash
uv run supertone-tts-mcp
```

Or via PyPI (after publish):

```bash
uvx supertone-tts-mcp
pip install supertone-tts-mcp
```

### MCP Client Configuration

**Claude Desktop** (`claude_desktop_config.json`):

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

## Test

```bash
uv run pytest -q
uv run pytest --cov=src --cov-report=term-missing
```

## Tools

| Tool | Description |
|------|-------------|
| `text_to_speech` | Convert text to audio. Per-call control of model, output mode, streaming, autoplay. Long text is auto-chunked. |
| `predict_duration` | Estimate audio length and credit cost without synthesizing. |
| `search_voice` | Filter the voice catalog by language, gender, age, use_case, style, model, name, or description. |
| `get_voice` | Full detail for one voice (samples, styles, thumbnail). |
| `preview_voice` | Sample audio URLs for a voice, filterable by language/style/model. |
| `get_credit_balance` | Remaining API credits. |
| `clone_voice` | Create a cloned voice from a local WAV/MP3 (≤3MB). |
| `search_custom_voice` | List/filter cloned voices. |
| `get_custom_voice` | Full detail for one cloned voice. |
| `edit_custom_voice` | Update name and/or description of a cloned voice. |
| `delete_custom_voice` | Permanently delete a cloned voice (irreversible). |
| `get_usage_history` | Usage over a recent time window. |
| `get_voice_usage` | Usage for a specific voice. |
| `merge_audio_files` | Concatenate two or more local mp3/wav files into one. Supports plain concat, silence gaps (`gap_ms`), or crossfade (`crossfade_ms`). Uses a **bundled ffmpeg** — no system ffmpeg required. |

### Supported Languages

`ko` (Korean, default), `en` (English), `ja` (Japanese), and 28 additional languages supported by the Supertone API.

### Parameters (text_to_speech)

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| text | string | (required) | Long text is auto-chunked by the SDK |
| voice_id | string | preset voice | Browse with `search_voice` |
| language | string | `ko` | One of 31 supported language codes |
| output_format | string | `mp3` | `mp3` or `wav` |
| model | string | `sona_speech_2_flash` | One of 7 SDK models |
| speed | number | `1.0` | 0.5–2.0 |
| pitch_shift | number | `0` | -24 to +24 semitones |
| style | string | voice default | Varies by voice |
| output_mode | string | `files` | `files`, `resources`, or `both` |
| autoplay | bool | `false` | Play locally after synthesis (macOS `afplay`) |
| streaming | bool | `false` | `true` requires `model="sona_speech_1"` |
| include_phonemes | bool | `false` | Return phoneme timing data |
| normalized_text | string | — | Pre-normalized text (sona_speech_2/2_flash only) |

### Parameters (merge_audio_files)

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| input_paths | string[] | (required) | Two or more local mp3/wav paths. `~` expansion supported. A single path is returned as-is. |
| gap_ms | int | `0` | Silence (ms) inserted at each junction. Mutually exclusive with `crossfade_ms`. |
| crossfade_ms | int | `0` | Crossfade blend (ms) at each junction. Mutually exclusive with `gap_ms`. |
| output_format | string | auto | Force `mp3` or `wav`. If omitted: all-same-ext → that ext; mixed → `mp3`. |

## Architecture

See `docs/architecture.md` for full architecture documentation.

**Tech Stack:** Python 3.12+, MCP Python SDK, Supertone SDK, httpx (async), mutagen, imageio-ffmpeg, uv

**Modules:**
- `server.py` — MCP entry point, tool registration
- `tools.py` — Input validation, output formatting, tool handlers
- `supertone_client.py` — Supertone SDK wrapper
- `audio_ops.py` — ffmpeg subprocess wrapper for `merge_audio_files` (uses bundled binary via `imageio-ffmpeg`; no system ffmpeg dependency)
