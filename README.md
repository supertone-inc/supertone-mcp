# supertone-tts-mcp

MCP server for [Supertone](https://supertone.ai) TTS API. Generate high-quality speech, browse the voice catalog, predict synthesis cost, and create cloned voices — directly from Claude Desktop, Cursor, or any MCP-compatible client.

## Features

**Synthesis**
- **`text_to_speech`** — Convert text (≤300 chars) to audio. Output as files, MCP resources, or both.
- **`predict_duration`** — Estimate audio length (and credit cost) without synthesizing.

**Voice discovery (preset)**
- **`search_voice`** — Filter the catalog by language, gender, age, use_case, style, model, name, or description.
- **`get_voice`** — Full detail for one voice.
- **`preview_voice`** — Sample audio URLs for a voice (filterable by language/style/model).
- **`get_credit_balance`** — Check remaining credits.

**Custom voice cloning**
- **`clone_voice`** — Create a cloned voice from a local WAV/MP3 (≤3MB).
- **`search_custom_voice`** — List/filter cloned voices.
- **`edit_custom_voice`** — Update name and/or description.
- **`delete_custom_voice`** — Permanently delete (irreversible).

Supports Korean, English, Japanese, and 20+ other languages. Speed (0.5x–2.0x), pitch shift (-24 to +24 semitones), and emotion styles.

> **Breaking change in v0.2:** `list_voices` was removed and replaced by `search_voice`. To reproduce the old behavior, call `search_voice` with no arguments.

## Installation

```bash
# Using uvx (recommended)
uvx supertone-tts-mcp

# Using pip
pip install supertone-tts-mcp
```

## Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

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

Add to your Cursor MCP settings (same JSON shape as above).

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPERTONE_API_KEY` | Yes | — | Your Supertone API key |
| `SUPERTONE_MCP_VOICE_ID` | No | preset voice (Aiden, multilingual) | Default `voice_id` for `text_to_speech` / `predict_duration` |
| `SUPERTONE_OUTPUT_DIR` | No | `~/supertone-tts-output/` | Directory where audio files are saved |
| `SUPERTONE_MCP_OUTPUT_MODE` | No | `files` | One of `files`, `resources`, `both`. Controls how `text_to_speech` returns audio (see below) |
| `SUPERTONE_MCP_AUTOPLAY` | No | `true` | Auto-play generated audio on macOS via `afplay` (enabled by default). Set `false`/`0`/`no` to disable |

### Output modes (`text_to_speech`)

| Mode | Returns | Use when |
|------|---------|----------|
| `files` *(default)* | Plain text with the saved file path + metadata | You want the file on disk |
| `resources` | MCP `AudioContent` + `TextContent` (no file written) | The client renders audio inline (e.g., Claude.ai chat) |
| `both` | File on disk **and** `AudioContent`/`TextContent` | You want both — preview inline, keep the file |

## Usage Examples

Natural language phrasing — the MCP client routes these to the right tool automatically.

**Synthesis**
> "Read this aloud: Hello, how are you today?"
> "한국어로 '안녕하세요' 천천히 읽어줘"

**Estimate before synthesizing**
> "이 문단 합성하면 몇 초쯤 나와?"
> → calls `predict_duration`

**Browse / pick a voice**
> "Find me a female Korean voice for narration"
> → calls `search_voice(language="ko", gender="female", use_case="narration")`
>
> "그 중에 첫 번째 목소리 샘플 들어보자"
> → calls `preview_voice(voice_id=...)` and returns sample URLs

**Check credits**
> "내 크레딧 얼마 남았어?"
> → calls `get_credit_balance`

**Clone a voice from a local file**
> "이 파일로 클론 만들어줘: ~/recordings/sample.wav, 이름은 MyVoice"
> → calls `clone_voice(name="MyVoice", audio_path="~/recordings/sample.wav")`

**Manage cloned voices**
> "내가 만든 커스텀 보이스 목록 보여줘" → `search_custom_voice`
> "MyVoice 이름을 NarratorA로 바꿔" → `edit_custom_voice`
> "MyVoice 삭제해" → `delete_custom_voice` *(prompts for confirmation; irreversible)*

## Tool Parameters

### `text_to_speech`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | — | Text to convert (≤300 chars; longer text is auto-chunked) |
| `voice_id` | string | No | env or preset | Voice identifier (browse via `search_voice`) |
| `language` | string | No | `ko` | Language code (`ko`, `en`, `ja`, …) |
| `output_format` | string | No | `mp3` | `mp3` or `wav` |
| `model` | string | No | `sona_speech_1` | TTS model |
| `speed` | float | No | `1.0` | 0.5–2.0 |
| `pitch_shift` | int | No | `0` | -24 to +24 semitones |
| `style` | string | No | — | Emotion style (varies by voice) |

### `predict_duration`

Same parameter schema as `text_to_speech` (no auto-chunking — hard 300-char limit). Returns `"Predicted duration: 2.34s (credit usage is proportional to duration)."`.

### `search_voice`

All parameters optional. With no filters → full catalog. With any filter → first response line is `Filters applied: ...`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `language` | string | e.g., `ko`, `en`, `ja` |
| `gender` | string | e.g., `male`, `female` |
| `age` | string | e.g., `young_adult`, `child` |
| `use_case` | string | e.g., `narration`, `advertisement` |
| `style` | string | e.g., `neutral`, `happy` |
| `model` | string | e.g., `sona_speech_1` |
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
| `edit_custom_voice` | `voice_id` | `name`, `description` (at least one required) |
| `delete_custom_voice` | `voice_id` | — *(IRREVERSIBLE)* |

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
