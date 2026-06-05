# supertone-mcp

<!-- mcp-name: io.github.supertone-inc/supertone-mcp -->

A **composable MCP toolkit** for the [Supertone](https://supertone.ai) TTS API. Rather than a single "speak this text" command, it exposes Supertone's SDK as a set of building-block tools — synthesis, voice discovery, preview, duration/credit prediction, usage tracking, and full voice-cloning CRUD — that an LLM assembles to fulfill a request. Works in Claude Desktop, Cursor, or any MCP-compatible client.

[![supertone-inc/supertone-mcp MCP server](https://glama.ai/mcp/servers/supertone-inc/supertone-mcp/badges/score.svg)](https://glama.ai/mcp/servers/supertone-inc/supertone-mcp)

Covers Korean, English, Japanese, and **31 languages** total. Speed (0.5x–2.0x), pitch shift (-24 to +24 semitones), emotion styles, per-call output mode, streaming, and model selection.

## Features

**Synthesis**
- **`text_to_speech`** — Convert text to audio. Per-call control of `output_mode` (files / resources / both), `autoplay`, `streaming`, `model`, plus `include_phonemes` / `normalized_text`. Long text is auto-chunked by the SDK.
- **`predict_duration`** — Estimate audio length (and credit cost) without synthesizing.

**Voice discovery (preset)**
- **`search_voice`** — Filter the catalog by language, gender, age, use_case, style, model, name, or description.
- **`get_voice`** — Full detail for one voice.
- **`preview_voice`** — Sample audio URLs for a voice (filterable by language/style/model).

**Custom voice cloning**
- **`clone_voice`** — Create a cloned voice from a local WAV/MP3 (≤3MB).
- **`search_custom_voice`** — List/filter cloned voices.
- **`get_custom_voice`** — Full detail for one cloned voice.
- **`edit_custom_voice`** — Update name and/or description.
- **`delete_custom_voice`** — Permanently delete (irreversible).

**Usage & credits**
- **`get_credit_balance`** — Remaining credits.
- **`get_usage_history`** — Usage over a time window.
- **`get_voice_usage`** — Usage for a specific voice.

## Breaking changes & migration (0.2.0)

0.2.0 moves behavior control **out of environment variables and into per-call tool parameters** — so the LLM decides per request, not the server config.

| Before (env var) | After (per-call parameter) | Note |
|------------------|----------------------------|------|
| `SUPERTONE_MCP_OUTPUT_MODE=files\|resources\|both` | `text_to_speech(output_mode=...)` | Default still `files` |
| `SUPERTONE_MCP_AUTOPLAY=true` | `text_to_speech(autoplay=...)` | **Default changed `true` → `false`** (playback is now explicit) |
| *(always streamed)* | `text_to_speech(streaming=...)` | **New, default `false`** (one-shot). `streaming=true` requires `model="sona_speech_1"` |

Other changes:
- **Default model** changed `sona_speech_1` → **`sona_speech_2_flash`**.
- **`list_voices` was removed** (since the discovery release) and replaced by `search_voice` — call it with no arguments to reproduce the old "list everything" behavior.
- No more hard 300-character limit — longer text is auto-chunked by the SDK (credit/latency scale with length).

If you previously set `SUPERTONE_MCP_OUTPUT_MODE` or `SUPERTONE_MCP_AUTOPLAY`, remove them from your client config and pass `output_mode` / `autoplay` per call instead. (The server prints a one-time stderr notice if it sees the removed vars.)

## Installation

```bash
# Using uvx (recommended)
uvx supertone-mcp

# Using pip
pip install supertone-mcp
```

## Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-mcp"],
      "env": {
        "SUPERTONE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings (same JSON shape as above).

## Environment Variables

Only authentication and stable defaults are configured via the environment — all behavior is controlled per call.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPERTONE_API_KEY` | Yes | — | Your Supertone API key |
| `SUPERTONE_MCP_VOICE_ID` | No | preset voice (Aiden, multilingual) | Default `voice_id` for `text_to_speech` / `predict_duration` (override per call) |
| `SUPERTONE_OUTPUT_DIR` | No | `~/supertone-tts-output/` | Directory where audio files are saved (used by `output_mode=files`/`both`) |

> Removed in 0.2.0: `SUPERTONE_MCP_OUTPUT_MODE` and `SUPERTONE_MCP_AUTOPLAY` — see [Migration](#breaking-changes--migration-020).

### Output modes (`text_to_speech` `output_mode`)

| Mode | Returns | Use when |
|------|---------|----------|
| `files` *(default)* | Plain text with the saved file path + metadata | You want the file on disk |
| `resources` | MCP `AudioContent` + `TextContent` (no file written) | The client renders audio inline (e.g., Claude.ai chat) |
| `both` | File on disk **and** `AudioContent`/`TextContent` | You want both — preview inline, keep the file |

## Usage Examples

The MCP client routes natural-language requests across these tools — the value of the toolkit is **composition**: the LLM chains several tools to satisfy one request.

### Example 1 — Discover → preview → estimate cost → synthesize

> "Find a calm Korean female voice, let me hear a sample, check the cost, then make this announcement as an mp3."

The LLM assembles:
```
search_voice(language="ko", gender="female", style="neutral")   # find candidates
  → preview_voice(voice_id)                                       # sample URLs to confirm the voice
  → predict_duration(text, voice_id) + get_credit_balance()       # gauge cost before spending
  → text_to_speech(text, voice_id, output_format="mp3",
                   output_mode="files")                           # synthesize
```

### Example 2 — Clone my voice → use it right away

> "Make a cloned voice from ~/recordings/sample.wav named MyVoice, then read this greeting with it and play it for me."

The LLM assembles:
```
clone_voice(name="MyVoice", audio_path="~/recordings/sample.wav")   # create the cloned voice
  → get_custom_voice(voice_id)                                       # confirm it was created
  → text_to_speech(text, voice_id=<cloned>, autoplay=true)           # synthesize, then play immediately
```

> `autoplay` is a per-call parameter (default `false`), so playback happens only when explicitly requested.

## Tool Parameters

### `text_to_speech`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | — | Text to convert (long text is auto-chunked by the SDK) |
| `voice_id` | string | No | env or preset | Voice identifier (browse via `search_voice`) |
| `language` | string | No | `ko` | Language code — one of 31 (`ko`, `en`, `ja`, …) |
| `output_format` | string | No | `mp3` | `mp3` or `wav` |
| `model` | string | No | `sona_speech_2_flash` | `sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `sona_speech_3t`, `supertonic_api_1`, `supertonic_api_3` |
| `speed` | float | No | `1.0` | 0.5–2.0 |
| `pitch_shift` | int | No | `0` | -24 to +24 semitones |
| `style` | string | No | — | Emotion style (varies by voice) |
| `output_mode` | string | No | `files` | `files`, `resources`, or `both` (see [Output modes](#output-modes-text_to_speech-output_mode)) |
| `autoplay` | bool | No | `false` | Play the audio locally after synthesis (macOS `afplay`) |
| `streaming` | bool | No | `false` | Stream synthesis. Only supported by `model="sona_speech_1"` |
| `include_phonemes` | bool | No | `false` | Return phoneme timing data alongside the audio |
| `normalized_text` | string | No | — | Pre-normalized text (only used by `sona_speech_2` / `sona_speech_2_flash`) |

### `predict_duration`

Same core parameter schema as `text_to_speech` (long text auto-chunked). Returns `"Predicted duration: 2.34s (credit usage is proportional to duration)."`.

### `search_voice`

All parameters optional. With no filters → full catalog. With any filter → first response line is `Filters applied: ...`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `language` | string | e.g., `ko`, `en`, `ja` |
| `gender` | string | e.g., `male`, `female` |
| `age` | string | e.g., `young_adult`, `child` |
| `use_case` | string | e.g., `narration`, `advertisement` |
| `style` | string | e.g., `neutral`, `happy` |
| `model` | string | e.g., `sona_speech_2_flash` |
| `name` | string | partial match |
| `description` | string | partial match |

### `get_voice` / `preview_voice`

| Tool | Required | Optional |
|------|----------|----------|
| `get_voice` | `voice_id` | — |
| `preview_voice` | `voice_id` | `language`, `style`, `model` (filter samples) |

### `clone_voice`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Display name (non-empty) |
| `audio_path` | string | Yes | Local WAV or MP3 path (≤3MB). Supports `~` expansion |
| `description` | string | No | Optional note |

### Custom voice CRUD

| Tool | Required | Optional |
|------|----------|----------|
| `search_custom_voice` | — | `name`, `description` (partial match) |
| `get_custom_voice` | `voice_id` | — |
| `edit_custom_voice` | `voice_id` | `name`, `description` (at least one required) |
| `delete_custom_voice` | `voice_id` | — *(IRREVERSIBLE)* |

### Usage & credits

| Tool | Required | Optional |
|------|----------|----------|
| `get_credit_balance` | — | — |
| `get_usage_history` | — | — (reports a recent default window) |
| `get_voice_usage` | `voice_id` | — |

## Development

```bash
# Clone and install
git clone https://github.com/supertone-inc/supertone-mcp.git
cd supertone-mcp
uv sync

# Run tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

## License

MIT
