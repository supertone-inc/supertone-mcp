# Data Model

## Storage Strategy

- **Primary storage:** None (stateless). All data structures are ephemeral, living only for the duration of a single MCP tool call.
- **Choice rationale:** The architecture is a single-process CLI tool spawned as a subprocess by MCP clients (NFR-001, NFR-003). There is no multi-user state, no session persistence, no query history. Adding a database would be over-engineering with zero user benefit.
- **Secondary storage:**
  - **File system:** Audio output files persisted to `SUPERTONE_OUTPUT_DIR` (default `~/supertone-tts-output/`). These are write-once artifacts, never read back by the server.
  - **No cache, no search index.** Voice list results are not cached in v1 (architecture decision: stateless simplicity over API call savings).

---

## Access Patterns

| Pattern | Source | Operation | Frequency | Latency Target |
|---------|--------|-----------|-----------|----------------|
| Synthesize speech | `text_to_speech` tool | Write (API call + file write) | High (primary use case) | < 100ms server overhead (NFR-003), API time dominant |
| List voices | `list_voices` tool | Read (API call) | Low (discovery, typically once per session) | < 100ms server overhead (NFR-003) |
| Validate TTS parameters | `text_to_speech` tool | Read (in-memory check) | High (every TTS call) | < 1ms |
| Validate list_voices parameters | `list_voices` tool | Read (in-memory check) | Low | < 1ms |
| Resolve output directory | `text_to_speech` tool | Read env var + mkdir | High (every TTS call) | < 10ms |
| Resolve API key | Both tools | Read env var | High (every tool call) | < 1ms |
| Generate output filename | `text_to_speech` tool | Compute (date + uuid4) | High (every TTS call) | < 1ms |
| Calculate audio duration | `text_to_speech` tool | Read (parse saved file) | High (every TTS call) | < 50ms |

---

## Type Definitions

All types below are Python dataclasses or TypedDicts intended for use in `tools.py` and `supertone_client.py`. They provide type safety without any ORM or database coupling.

### Enums and Literal Types

```python
from typing import Literal

Language = Literal["ko", "en", "ja"]
OutputFormat = Literal["mp3", "wav"]

SUPPORTED_LANGUAGES: list[str] = ["ko", "en", "ja"]
SUPPORTED_FORMATS: list[str] = ["mp3", "wav"]

SPEED_MIN: float = 0.5
SPEED_MAX: float = 2.0
PITCH_SHIFT_MIN: int = -12
PITCH_SHIFT_MAX: int = 12
TEXT_MAX_LENGTH: int = 300

DEFAULT_LANGUAGE: Language = "ko"
DEFAULT_FORMAT: OutputFormat = "mp3"
DEFAULT_SPEED: float = 1.0
DEFAULT_PITCH_SHIFT: int = 0
DEFAULT_VOICE_ID: str = "TBD"  # Assumption A4: verify with stakeholder
```

### Entity: TTSRequest

Validated parameters for a single `text_to_speech` tool call. Constructed in `tools.py` after all validation passes.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TTSRequest:
    """Validated TTS request parameters. Immutable after construction."""
    text: str                  # 1-300 characters, NOT NULL
    voice_id: str              # Resolved (default applied if omitted by user)
    language: Language          # "ko" | "en" | "ja", default "ko"
    output_format: OutputFormat # "mp3" | "wav", default "mp3"
    speed: float               # 0.5-2.0, default 1.0
    pitch_shift: int           # -12 to +12, default 0
    style: str | None          # None means voice default; pass-through to API
```

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| text | str | NOT NULL, len 1-300 (Unicode codepoints) | -- (required) | Text to synthesize |
| voice_id | str | NOT NULL after resolution | DEFAULT_VOICE_ID | Supertone voice identifier |
| language | Literal["ko","en","ja"] | NOT NULL, enum check | "ko" | Speech language |
| output_format | Literal["mp3","wav"] | NOT NULL, enum check | "mp3" | Audio file format |
| speed | float | NOT NULL, range [0.5, 2.0] | 1.0 | Playback speed multiplier |
| pitch_shift | int | NOT NULL, range [-12, +12] | 0 | Pitch adjustment in semitones |
| style | str or None | Nullable (pass-through to API) | None | Emotion style, validated per-voice when possible |

### Entity: TTSResponse

Result of a successful `text_to_speech` call. Constructed in `tools.py` after file write and duration calculation.

```python
@dataclass(frozen=True)
class TTSResponse:
    """Result of a successful TTS synthesis."""
    file_path: str           # Absolute path, ~ expanded, forward slashes
    duration_seconds: float  # Computed from saved audio file
    voice_id: str            # Echo back for user transparency
    language: str            # Echo back
    output_format: str       # Echo back ("mp3" or "wav")
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| file_path | str | NOT NULL, absolute path | Full path to saved audio file |
| duration_seconds | float | NOT NULL, >= 0.0 | Audio duration computed via mutagen |
| voice_id | str | NOT NULL | Voice used (including resolved default) |
| language | str | NOT NULL | Language used |
| output_format | str | NOT NULL | Format of saved file |

**Plain-text serialization** (per UX spec Section 6.1):
```
Audio file saved: {file_path}
Duration: {duration_seconds} seconds
Voice: {voice_id}
Language: {language}
Format: {output_format}
```

### Entity: VoiceInfo

A single voice entry from the Supertone API `GET /v1/voices` response.

```python
@dataclass(frozen=True)
class VoiceInfo:
    """A single voice from the Supertone voice catalog."""
    voice_id: str                    # Unique identifier
    name: str                        # Display name
    supported_languages: list[str]   # e.g., ["ko", "en"]
    supported_styles: list[str]      # e.g., ["neutral", "happy", "sad"]
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| voice_id | str | NOT NULL, unique within response | Supertone voice identifier |
| name | str | NOT NULL | Human-readable voice name |
| supported_languages | list[str] | NOT NULL, non-empty | Language codes this voice supports |
| supported_styles | list[str] | NOT NULL (may be empty) | Available emotion styles |

**Plain-text serialization** (per UX spec Section 4.2):
```
{N}. Name: {name}
   Voice ID: {voice_id}
   Languages: {', '.join(supported_languages)}
   Styles: {', '.join(supported_styles)}
```

### Entity: AppConfig

Configuration resolved from environment variables at tool-call time (not at startup, per FR-003).

```python
@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration resolved from environment."""
    api_key: str        # From SUPERTONE_API_KEY; checked per tool call
    output_dir: str     # From SUPERTONE_OUTPUT_DIR or default
    base_url: str       # Hardcoded: https://api.supertoneapi.com
```

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| api_key | str | NOT NULL, non-empty | -- (env var required) | Supertone API key, never logged (NFR-007) |
| output_dir | str | NOT NULL, valid directory path | ~/supertone-tts-output/ | Resolved and expanded absolute path |
| base_url | str | NOT NULL, HTTPS URL | https://api.supertoneapi.com | Hardcoded, not user-configurable (SSRF prevention) |

### v0.3 additions (concept pivot)

The v0.3 pivot adds per-call parameters to the `text_to_speech` request surface and two usage response shapes. No persistent storage is introduced.

**`text_to_speech` parameter additions** (request-shape only; not persisted):

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| output_mode | Literal["files","resources","both"] | enum check; replaces env var | "files" | How audio is returned (per-call) |
| autoplay | bool | — | False | Play locally after synthesis (per-call; default flipped from old env default) |
| streaming | bool | requires model=="sona_speech_1" when True | False | One-shot (`create_speech_async`) vs streaming (`stream_speech_async`) |
| model | str | one of 7 SDK 0.2.3 models | "sona_speech_2_flash" | TTS model (default changed from sona_speech_1) |
| include_phonemes | bool | — | False | Return phoneme timing data (SDK 0.2.3) |
| normalized_text | str or None | effective only for sona_speech_2/2_flash | None | Pre-normalized text (SDK 0.2.3) |

> **Note:** `text` no longer carries a 300-char hard cap in v0.3 (FR-005 relaxed). The only retained constraint is non-empty. Long text is delegated to the SDK auto-chunk.

**Usage response shapes** (mapped from SDK `usage.get_usage_async` / `usage.get_voice_usage_async`; in-memory only, formatted to plain text):

```python
from typing import TypedDict, NotRequired

class UsageHistoryDict(TypedDict):
    # Shape mirrors the SDK 0.2.3 usage payload; modeled loosely because
    # the exact period/paging fields are SDK-defined. Formatter is tolerant
    # of missing optional fields (renders "-" / "0" fallbacks).
    items: list[dict]            # per-period usage entries (period, characters, requests, ...)
    next_page_token: NotRequired[str | None]

class VoiceUsageDict(TypedDict):
    voice_id: str
    characters: NotRequired[int]
    requests: NotRequired[int]
```

> The existing `CustomVoiceDict` (voice_id, name, optional description) is reused by `get_custom_voice`; if the SDK exposes a `created_at` field it is added as an optional key (`created_at: NotRequired[str]`).

---

## File Storage Schema

### Output Directory Structure

```
{SUPERTONE_OUTPUT_DIR}/          # Default: ~/supertone-tts-output/
  2026-03-13_a1b2c3d4.mp3
  2026-03-13_e5f6g7h8.wav
  2026-03-14_i9j0k1l2.mp3
```

- **Directory:** Flat structure (no subdirectories). Created with `os.makedirs(path, exist_ok=True)` on each tool call.
- **No cleanup, no rotation.** Files accumulate until the user deletes them manually. The server never reads or deletes previously written files.

### File Naming Convention

```
{YYYY-MM-DD}_{uuid4_short}.{format}
```

| Component | Type | Description |
|-----------|------|-------------|
| YYYY-MM-DD | str | ISO date of generation (local timezone) |
| uuid4_short | str | First 8 hex characters of uuid4 (collision probability negligible for single-user) |
| format | str | "mp3" or "wav", matches the output_format parameter |

**Generation logic:**

```python
from datetime import date
from uuid import uuid4
from pathlib import Path

def generate_output_path(output_dir: str, output_format: str) -> Path:
    today = date.today().isoformat()        # "2026-03-13"
    unique_id = uuid4().hex[:8]             # "a1b2c3d4"
    filename = f"{today}_{unique_id}.{output_format}"
    return Path(output_dir).expanduser().resolve() / filename
```

---

## API Contracts

### Supertone API: Synthesize Speech

```
POST /v1/text-to-speech/{voice_id}
Host: api.supertoneapi.com
x-sup-api-key: {api_key}
Content-Type: application/json

Request Body:
{
  "text": str,            // Required, 1-300 chars
  "language": str,        // "ko" | "en" | "ja"
  "output_format": str,   // "mp3" | "wav"
  "speed": float,         // 0.5-2.0
  "pitch_shift": int,     // -12 to +12
  "style": str | null     // Emotion style or omitted
}

Success Response:
  Status: 200
  Content-Type: audio/mpeg | audio/wav
  Body: binary audio stream

Error Responses:
  401/403: Authentication failure
  429: Rate limit exceeded
  4xx: Client error (invalid params)
  5xx: Server error
```

**Python request shape** (what `supertone_client.py` sends):

```python
from typing import TypedDict, NotRequired

class SynthesizeRequestBody(TypedDict):
    text: str
    language: str
    output_format: str
    speed: float
    pitch_shift: int
    style: NotRequired[str]  # Omitted from payload when None
```

**Python response shape** (what `supertone_client.synthesize()` returns):

```python
@dataclass
class SynthesizeResult:
    audio_data: bytes      # Raw audio bytes to write to file
    content_type: str      # "audio/mpeg" or "audio/wav"
    # Additional metadata from response headers if available
```

### Supertone API: List Voices

```
GET /v1/voices
Host: api.supertoneapi.com
x-sup-api-key: {api_key}

Success Response:
  Status: 200
  Content-Type: application/json
  Body: [
    {
      "voice_id": "sujin-01",
      "name": "Sujin",
      "supported_languages": ["ko", "en"],
      "supported_styles": ["neutral", "happy", "sad", "angry"]
    },
    ...
  ]
```

**Python response shape** (what `supertone_client.get_voices()` returns):

```python
from typing import TypedDict

class VoiceDict(TypedDict):
    voice_id: str
    name: str
    supported_languages: list[str]
    supported_styles: list[str]
```

**Note (Assumption A2, A5):** The exact field names in the Supertone API response are unverified. The client module must map whatever the API returns to the `VoiceInfo` / `VoiceDict` shape. If field names differ (e.g., `id` vs `voice_id`, `languages` vs `supported_languages`), add a mapping layer in `supertone_client.py`.

---

## Domain Exceptions

Custom exceptions for the three-module boundary. Raised in `supertone_client.py`, caught and formatted in `tools.py`.

```python
class SupertoneError(Exception):
    """Base exception for all Supertone API errors."""
    pass

class SupertoneAuthError(SupertoneError):
    """HTTP 401/403 from API."""
    pass

class SupertoneRateLimitError(SupertoneError):
    """HTTP 429 from API."""
    pass

class SupertoneServerError(SupertoneError):
    """HTTP 5xx from API."""
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"Server error: {status_code}")

class SupertoneAPIError(SupertoneError):
    """Other HTTP 4xx errors from API."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")

class SupertoneConnectionError(SupertoneError):
    """Network unreachable, DNS failure, timeout."""
    pass
```

**Error-to-message mapping** (implemented in `tools.py`):

| Exception | User-facing message (per UX spec) |
|-----------|-----------------------------------|
| `SupertoneAuthError` | Authentication failed. Please verify your SUPERTONE_API_KEY. |
| `SupertoneRateLimitError` | Rate limit exceeded. Please wait and try again. |
| `SupertoneServerError` | Supertone API server error ({status_code}). Please try again later. |
| `SupertoneAPIError` | API error ({status_code}): {message}. |
| `SupertoneConnectionError` | Failed to connect to Supertone API. Please check your network connection. |

---

## Constraints and Validation

### Input Validation Rules (tools.py, fail-fast before API call)

| Parameter | Rule | Error message template |
|-----------|------|----------------------|
| text | `len(text) == 0` | Text must not be empty. |
| text | `len(text) > 300` | Text exceeds the maximum length of 300 characters (received: {N}). Please shorten or split the text manually. |
| language | `value not in ["ko","en","ja"]` | Invalid language: "{value}". Supported languages: ko, en, ja. |
| output_format | `value not in ["mp3","wav"]` | Invalid output format: "{value}". Supported formats: mp3, wav. |
| speed | `value < 0.5 or value > 2.0` | Speed must be between 0.5 and 2.0 (received: {value}). |
| pitch_shift | `value < -12 or value > 12` | Pitch shift must be between -12 and +12 semitones (received: {value}). |
| style | Pass-through to API (validated per-voice when possible via list_voices data) | Style "{value}" is not supported by voice "{voice_id}". Available styles: {list}. |
| SUPERTONE_API_KEY | Not set or empty string | SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings. |

### File System Validation (tools.py, after API call)

| Condition | Error message |
|-----------|---------------|
| Output dir not writable (PermissionError) | Cannot write to output directory: {path}. Please check directory permissions or set SUPERTONE_OUTPUT_DIR to a writable location. |
| Disk full (OSError) | Cannot write audio file. Please check available disk space. |

### Application-level Rules (cannot be expressed as DB constraints)

- Text length is measured by Python `len()` (Unicode codepoints, not bytes).
- API key is never logged, printed in error messages, or included in tool responses (NFR-007).
- File paths returned to the user are always absolute, with `~` expanded (UX spec 6.2).
- `style` field is omitted from the API request body when `None` (not sent as `null`).
- Speed and pitch_shift validation uses inclusive bounds: `0.5 <= speed <= 2.0`, `-12 <= pitch_shift <= 12`.

---

## Configuration Model

```
Environment Variables:
+---------------------+----------+----------------------------------+-----------------------------+
| Variable            | Required | Default                          | Description                 |
+---------------------+----------+----------------------------------+-----------------------------+
| SUPERTONE_API_KEY   | Yes*     | (none)                           | Supertone API key.          |
|                     |          |                                  | *Server starts without it;  |
|                     |          |                                  | checked per tool call.      |
+---------------------+----------+----------------------------------+-----------------------------+
| SUPERTONE_OUTPUT_DIR| No       | ~/supertone-tts-output/          | Directory for audio files.  |
+---------------------+----------+----------------------------------+-----------------------------+

Hardcoded Constants:
+---------------------+----------------------------------+-----------------------------------+
| Constant            | Value                            | Rationale                         |
+---------------------+----------------------------------+-----------------------------------+
| SUPERTONE_BASE_URL  | https://api.supertoneapi.com     | SSRF prevention, single API      |
| HTTP_TIMEOUT        | 30 seconds                       | Architecture failure mode table   |
| DEFAULT_VOICE_ID    | TBD (Assumption A4)              | Stakeholder input needed          |
+---------------------+----------------------------------+-----------------------------------+
```

---

## Query Patterns

Since there is no database, "query patterns" here describe the data access sequences for each tool call.

### Pattern: text_to_speech (full flow)

- **Used by:** `text_to_speech` MCP tool
- **Sequence:**
  1. Read `SUPERTONE_API_KEY` from env -> fail if missing
  2. Validate all input parameters against constraints (in-memory)
  3. Resolve `voice_id` (apply default if not provided)
  4. Resolve `output_dir` from env var, expand `~`, `mkdir -p`
  5. Build `SynthesizeRequestBody` from validated `TTSRequest`
  6. HTTP POST to Supertone API -> receive `bytes` (audio data)
  7. Generate output filename (date + uuid4)
  8. Write bytes to file
  9. Calculate duration from saved file (mutagen)
  10. Construct `TTSResponse`, serialize to plain text
- **Expected data size:** Single audio file, typically 100KB-5MB
- **Performance:** Server overhead < 100ms (NFR-003). API call is 1-5 seconds.

### Pattern: list_voices (full flow)

- **Used by:** `list_voices` MCP tool
- **Sequence:**
  1. Read `SUPERTONE_API_KEY` from env -> fail if missing
  2. Validate `language` filter if provided (in-memory)
  3. HTTP GET to Supertone API -> receive JSON array
  4. Parse JSON into `list[VoiceDict]`
  5. Convert to `list[VoiceInfo]` (mapping layer for API field name differences)
  6. Filter by `language` if parameter was provided (in-memory list filter)
  7. Serialize to plain-text numbered list
- **Expected data size:** Small list (likely < 50 voices)
- **Performance:** Server overhead < 100ms (NFR-003). API call is < 1 second.

---

## Migrations

Not applicable. There is no database, no schema evolution, no versioned state.

The only "migration" concern is the file naming convention. If it changes in a future version, previously generated files are unaffected (they are standalone artifacts with no metadata index).

---

## Seed Data

Not applicable. There is no database to seed.

The only "default data" is the `DEFAULT_VOICE_ID` constant, which must be determined by inspecting the Supertone API (Assumption A4). This is a code constant, not seed data.

---

## Scaling Notes

- **Current design handles:** Single user, single process, sequential tool calls. Roughly 20-60 requests/minute (Supertone API rate limit is the bottleneck, not the server).
- **At 10x (multiple concurrent users):** Not applicable. Each MCP client spawns its own server process. Scale is inherently per-user. No shared state to contend over.
- **At 100x (batch/streaming v2):** Voice list caching (in-memory with TTL) would reduce redundant API calls. Batch TTS would require chunked file writes or progress reporting via MCP notifications. Neither requires a database.
- **What would require a storage change:** A usage-tracking or analytics feature would need persistent storage (SQLite or external service). This is not planned.

---

## Self-Review

### Access pattern coverage

Every tool call (`text_to_speech`, `list_voices`) and every sub-operation (validation, file write, config resolution) has a corresponding access pattern entry. No uncovered paths.

### Constraint audit

Every field on every dataclass has explicit nullability and range constraints documented. `style` is the only nullable field, and that is intentional (pass-through to API).

### N+1 / performance check

Traced both read paths:
1. `text_to_speech`: Single HTTP call, single file write, single duration parse. No N+1 possible.
2. `list_voices`: Single HTTP call, single in-memory filter. No N+1 possible.

There are no JOINs to optimize because there is no relational data.

### Confidence rating

**High.** This is a stateless CLI wrapper with two tools, two API endpoints, and no persistent storage. The type definitions directly mirror the requirements and architecture documents. The only uncertainty is the exact Supertone API response schema (Assumptions A1-A6), which affects field mapping in `supertone_client.py` but not the data model structure.
