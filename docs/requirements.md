# Requirements: Supertone TTS MCP Server

> Generated: 2026-03-13 (v0.1) / 2026-05-26 (v0.2 extension)
> Source: PRD v0.2 (Draft, 2026-05-26)
> Analyst: requirements-analyst agent

> v0.2 adds: voice discovery (search/get/credit/preview), duration prediction, and voice cloning CRUD.
> Breaking change in v0.2: `list_voices` is replaced by `search_voice` (no deprecated alias).

---

## Goals (from PRD)

| ID | Goal | Measurement |
|----|------|-------------|
| G1 | Acquire MCP server development capability | A working server that conforms to the MCP standard |
| G2 | Bring Supertone TTS into the MCP ecosystem | Verified operation on Claude Desktop and Cursor |
| G3 | Publish as open-source to attract external users | Public GitHub repo + published on PyPI |

---

## Primary User

**MCP users (developers / creators)** who use MCP-compatible clients (Claude Desktop, Cursor, OpenClaw, etc.) and want to convert text to speech within their LLM workflow.

**Secondary:** Content creators who need high-quality Korean narration/dubbing and want to automate it inside an LLM pipeline.

---

## User Stories (prioritized)

### Must

#### US-001: Basic Text-to-Speech
**As an** MCP user, **I want** to input text and generate a speech audio file via Supertone TTS, **so that** I can listen to typed content as spoken audio.

**Acceptance Criteria:**
- [x] Given the MCP server is running and `SUPERTONE_API_KEY` is set, when the user calls `text_to_speech` with `text="Hello"`, then an audio file is saved to the output directory and the file path is returned.
- [x] Given valid input, when the tool completes, then the response includes the file path (absolute) and audio duration in seconds.
- [x] Given `text` is empty (zero-length string), when the tool is called, then an error message is returned indicating text must not be empty.
- [x] Given `text` exceeds 300 characters, when the tool is called, then an error is returned without automatic splitting, instructing the user to shorten the text.

#### US-002: List Available Voices
**As an** MCP user, **I want** to query the list of available voices, **so that** I can choose a voice for TTS.

**Acceptance Criteria:**
- [x] Given the server is running and API key is valid, when the user calls `list_voices` with no parameters, then a list of all voices is returned.
- [x] Each voice entry includes: `voice_id`, name, supported languages, and supported styles.
- [x] Given no voices match (e.g., API returns empty list), then an empty list is returned with no error.

#### US-003: Specify Language
**As an** MCP user, **I want** to specify the speech language (`ko`, `en`, `ja`), **so that** I can create multilingual content.

**Acceptance Criteria:**
- [x] Given `language="en"` is passed to `text_to_speech`, when the API is called, then the generated audio is in English.
- [x] Given no `language` parameter is provided, then `ko` is used as the default.
- [x] Given an unsupported language code (e.g., `language="zz"`), then an error is returned listing valid options (`ko`, `en`, `ja`).
- [x] Given `language="ja"` is passed to `list_voices`, then only Japanese-capable voices are returned.

### Should

#### US-004: Adjust Speed and Pitch
**As an** MCP user, **I want** to control speech speed and pitch, **so that** I can tailor the audio to my use case.

**Acceptance Criteria:**
- [x] Given `speed=1.5` is passed, then the generated audio plays at 1.5x speed.
- [x] Given `speed` is outside the range 0.5--2.0, then an error is returned stating the valid range.
- [x] Given `pitch_shift=3` is passed, then the audio pitch is shifted up by 3 semitones.
- [x] Given `pitch_shift` is outside the range -12 to +12, then an error is returned stating the valid range.
- [x] Given neither `speed` nor `pitch_shift` is provided, then defaults of `1.0` and `0` are used respectively.

#### US-005: Specify Emotion Style
**As an** MCP user, **I want** to set an emotion style (e.g., `neutral`, `happy`), **so that** I can create expressive speech.

**Acceptance Criteria:**
- [x] Given `style="happy"` is passed and the selected voice supports it, then the audio is generated with the happy style.
- [x] Given `style` is not provided, then the voice's default style is used.
- [x] Given an unsupported `style` value for the selected voice, then an error is returned indicating which styles are available for that voice.

#### US-006: Choose Output Format
**As an** MCP user, **I want** to select the output format (`wav` or `mp3`), **so that** I can get a file suitable for my purpose.

**Acceptance Criteria:**
- [x] Given `output_format="wav"` is passed, then the saved file has a `.wav` extension and contains valid WAV data.
- [x] Given `output_format` is not provided, then `mp3` is used as the default.
- [x] Given an invalid format (e.g., `output_format="ogg"`), then an error is returned listing valid options (`wav`, `mp3`).

### Could

#### US-007: Filter Voices by Language
**As an** MCP user, **I want** to filter the voice list by language, **so that** I only see voices relevant to my needs.

**Acceptance Criteria:**
- [x] Given `language="ko"` is passed to `list_voices`, then only voices supporting Korean are returned.
- [x] Given an unsupported language filter, then an error is returned listing valid language codes.

> Note: This is partially covered by US-003 AC for `list_voices` (v0.1) / `search_voice` (v0.2).

### Must (added in v0.2)

#### US-008: Search and Preview Voices
**As an** MCP user, **I want** to search voices by name, description, language, gender, age, use_case, style, or model and preview them via sample audio URLs, **so that** I can confidently pick a voice for TTS.

**Acceptance Criteria:**
- [ ] Given `search_voice` is called with no filters, when the tool completes, then the full voice list is returned (equivalent to former `list_voices`).
- [ ] Given `search_voice(language="ko", gender="female")` is called, when the tool completes, then only Korean female voices are returned and the response begins with a `Filters applied: ...` line.
- [ ] Given `search_voice` with filters returns zero results, then the tool returns `No voices found matching the filters.` (not an error).
- [ ] Given `get_voice(voice_id="...")` is called, then the response includes name, description, age, gender, use_cases, languages, styles, models, sample count, and thumbnail_image_url.
- [ ] Given `preview_voice(voice_id="...")` is called, then a numbered list of sample URLs (with language/style/model tags) is returned. v0.2 does NOT autoplay audio locally.
- [ ] Given `preview_voice` for a voice with zero samples, then `This voice has no preview samples.` is returned.

#### US-009: Check Credit Balance Before TTS
**As an** MCP user, **I want** to call `get_credit_balance`, **so that** I can confirm I have enough credits before running a long TTS synthesis.

**Acceptance Criteria:**
- [ ] Given `get_credit_balance()` is called with a valid API key, when the tool completes, then `Credit balance: {N} credits remaining.` is returned.
- [ ] Given the API returns plan name or expiry date, then these are appended on subsequent lines (`Plan: {name}`, `Expires: {date}`).
- [ ] Given the API key is invalid, then the standard auth error is returned (FR-007 mapping).

#### US-010: Predict Duration
**As an** MCP user, **I want** to call `predict_duration(text, ...)`, **so that** I know the expected output length without spending credits on full synthesis.

**Acceptance Criteria:**
- [ ] Given valid input, when `predict_duration` completes, then `Predicted duration: {N}.{NN}s (credit usage is proportional to duration).` is returned.
- [ ] Given text > 300 characters, then the same text-too-long error as `text_to_speech` is returned (FR-005).
- [ ] Given the same `text_to_speech` parameters (voice_id, language, model, output_format, speed, pitch_shift, style), then `predict_duration` accepts them with identical validation.
- [ ] Given the tool runs, then NO audio file is produced (it's a prediction-only call).

#### US-011: Clone and Manage Custom Voices
**As an** MCP user, **I want** to clone my voice from a single WAV/MP3 file (≤3MB), then search/edit/delete the resulting custom voices, **so that** I can produce TTS in my own voice.

**Acceptance Criteria:**
- [ ] Given `clone_voice(name="MyVoice", audio_path="~/sample.wav")` is called with a valid file, then `Custom voice created. voice_id: {id}. Use this voice_id in text_to_speech.` is returned.
- [ ] Given `audio_path` does not exist, then `Audio file not found: {path}.` is returned (no API call made).
- [ ] Given the file has an unsupported extension (e.g., `.flac`, `.ogg`), then `Unsupported audio format: "{ext}". Supported: wav, mp3.` is returned.
- [ ] Given the file is larger than 3MB, then `Audio file exceeds the 3MB limit (received: {N} bytes).` is returned (no API call made).
- [ ] Given `name` is empty, then `Voice name must not be empty.` is returned.
- [ ] Given `search_custom_voice()` is called, then a numbered list of custom voices is returned (or `No custom voices found.`).
- [ ] Given `edit_custom_voice(voice_id="x")` is called with neither `name` nor `description`, then `At least one of name or description must be provided.` is returned.
- [ ] Given `delete_custom_voice(voice_id="x")` is called, then `Custom voice deleted. voice_id: x.` is returned. No confirm gate is enforced (v0.2 product decision); the tool description warns the action is irreversible.

### Must (added in v0.4 — audio assembly)

#### US-018: Merge Multiple TTS Outputs
**As an** MCP user (LLM), **I want** to merge several audio files (produced by multiple `text_to_speech` calls) into a single audio file using ffmpeg, **so that** I can produce a single deliverable from multi-segment TTS workflows.

**Acceptance Criteria:**
- [ ] Given a list of two or more valid audio file paths, when `merge_audio_files` is called with no gap/crossfade args, then the files are concatenated head-to-tail and a merged file path is returned.
- [ ] Given `gap_ms > 0`, when called, then silence of that duration is inserted between each junction.
- [ ] Given `crossfade_ms > 0`, when called, then the audio clips are blended at each junction for the specified duration.
- [ ] Given both `gap_ms > 0` and `crossfade_ms > 0`, when called, then a validation error is returned and no file is produced.
- [ ] Given a single input path, when called, then the file is returned as-is (passthrough; no ffmpeg invocation needed).
- [ ] Given a file path that does not exist, when called, then a clear error is returned before invoking ffmpeg.
- [ ] Given an unsupported extension (not `.mp3` or `.wav`), when called, then a validation error is returned.
- [ ] Given all inputs have the same extension, when called, then the output uses that extension; if mixed, output defaults to `.mp3`.
- [ ] Given an explicit `output_format` override, when called, then the output uses that format.
- [ ] Given ffmpeg exits non-zero, when called, then an actionable error string is returned.
- [ ] Given an empty input list, when called, then an error is returned.

### Must (added in v0.3 — composable SDK toolkit pivot)

#### US-012: Per-Call Output Mode
**As an** MCP user (LLM), **I want** to choose how each TTS result is returned (file on disk / MCP resource / both) on a per-call basis, **so that** I can assemble tools to fit the situation without restarting or reconfiguring the server.

**Acceptance Criteria:**
- [ ] Given `text_to_speech(text="hi", output_mode="resources")`, then no file is written and the audio is returned as an MCP resource.
- [ ] Given `output_mode` is omitted, then `files` behavior is used regardless of any `SUPERTONE_MCP_OUTPUT_MODE` env var (which is no longer read).
- [ ] Given an invalid `output_mode`, then a validation error is returned with no API call.

#### US-013: Per-Call Autoplay
**As an** MCP user (LLM), **I want** to decide at call time whether the synthesized audio is played locally, **so that** the "playback" side-effect only happens when I intend it.

**Acceptance Criteria:**
- [ ] Given `autoplay` omitted, then audio is NOT played (default `false`), even if `SUPERTONE_MCP_AUTOPLAY=true` is set (no longer read).
- [ ] Given `autoplay=true` on macOS, then the audio is played via `afplay` after synthesis.

#### US-014: Per-Call Streaming vs One-Shot
**As an** MCP user (LLM), **I want** to use non-streaming (one-shot) TTS and choose streaming per call, **so that** I can pick the right mode (complete audio vs progressive processing) for the task.

**Acceptance Criteria:**
- [ ] Given `streaming` omitted, then one-shot `create_speech_async` is used (default `false`).
- [ ] Given `streaming=true` with `model=sona_speech_1`, then `stream_speech_async` is used.
- [ ] Given `streaming=true` with any other model, then the fail-fast validation error is returned before any SDK call.

#### US-015: Per-Call Model Selection
**As an** MCP user (LLM), **I want** to select the TTS model per call from the 7 SDK 0.2.3 models, **so that** I can trade off quality vs speed per situation.

**Acceptance Criteria:**
- [ ] Given any of the 7 models (`sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `sona_speech_3t`, `supertonic_api_1`, `supertonic_api_3`), then validation passes and synthesis proceeds.
- [ ] Given `model` omitted, then `sona_speech_2_flash` is used (default).

#### US-016: Single Custom Voice Detail
**As an** MCP user (LLM), **I want** to fetch the detail of a specific custom voice by id, **so that** I can check a known voice_id's state without running a search.

**Acceptance Criteria:**
- [ ] Given `get_custom_voice(voice_id="cv1")`, then voice_id, name, and description (and created_at when present) are returned.
- [ ] Given an empty voice_id, then `voice_id must not be empty.` is returned with no API call.

#### US-017: Usage History and Per-Voice Usage
**As an** MCP user (LLM), **I want** to query usage history and per-voice usage, **so that** I can analyze credit consumption and manage cost.

**Acceptance Criteria:**
- [ ] Given `get_usage_history()`, then a plain-text usage summary is returned (or a "no usage" message when empty).
- [ ] Given `get_voice_usage(voice_id="v1")`, then a usage summary for that voice is returned.
- [ ] Given an empty voice_id to `get_voice_usage`, then `voice_id must not be empty.` is returned with no API call.

---

## Functional Requirements

### Feature Area: TTS Core

#### FR-001: `text_to_speech` MCP Tool
- **Description:** Expose an MCP tool named `text_to_speech` that calls the Supertone API (`POST /v1/text-to-speech/{voice_id}`) and returns the resulting audio per the requested `output_mode`.
- **Priority:** Must
- **Parameters:** `text` (required), `voice_id`, `language`, `output_format`, `speed`, `pitch_shift`, `style`, `model`, and the v0.3 additions `output_mode`, `autoplay`, `streaming`, `include_phonemes`, `normalized_text` (all optional with defaults).
- **v0.3 changes (BREAKING):** Behavior is now driven by per-call parameters, not environment variables (see NFR-009). The removed env vars `SUPERTONE_MCP_OUTPUT_MODE` and `SUPERTONE_MCP_AUTOPLAY` are replaced by the `output_mode` and `autoplay` parameters. The 300-character hard rejection is removed (delegated to SDK auto-chunk; see FR-005 update). The streaming default flips to `false`.
- **v0.3 parameter additions:**
  - `output_mode` (str, default `files`): `files` (save to disk, return path), `resources` (return audio as MCP resource, no file), or `both`. Replaces `SUPERTONE_MCP_OUTPUT_MODE`. Invalid values return a validation error.
  - `autoplay` (bool, default `false`): when true, play the audio locally after synthesis (macOS `afplay`). Replaces `SUPERTONE_MCP_AUTOPLAY` (default changed `true`→`false`).
  - `streaming` (bool, default `false`): `false` uses one-shot `create_speech_async`; `true` uses `stream_speech_async`. **Streaming is only supported by `model=sona_speech_1`.**
  - `model` (str, default `sona_speech_2_flash`): one of the 7 SDK 0.2.3 models — `sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `sona_speech_3t`, `supertonic_api_1`, `supertonic_api_3`.
  - `include_phonemes` (bool, default `false`): return phoneme timing data with the audio (SDK 0.2.3 field).
  - `normalized_text` (str, optional): pre-normalized text; effective only for `sona_speech_2`/`sona_speech_2_flash` (ignored by other models).
- **Acceptance Criteria:**
  - The tool is registered in the MCP server and discoverable by MCP clients.
  - The tool calls the Supertone API (via the SDK) with correct authentication and parameters.
  - The audio from the API is returned per `output_mode` (file path for `files`, MCP audio resource for `resources`, both for `both`).
  - For `files`/`both`, the file is named with a timestamp and unique identifier (e.g., `2026-03-13_abc123.mp3`) and the returned text includes the absolute path and duration in seconds.
  - `streaming=true` with any model other than `sona_speech_1` returns the validation error `Streaming is only supported by model "sona_speech_1" (received: "{model}"). Set streaming=false or use sona_speech_1.` BEFORE any SDK call (fail-fast).
  - An invalid `output_mode` (not `files`/`resources`/`both`) returns a validation error and makes no API call.
- **Dependencies:** FR-003 (authentication).

#### FR-002: `list_voices` MCP Tool — **REMOVED in v0.2** (replaced by FR-012 `search_voice`)
- **Description (historical, v0.1):** Exposed an MCP tool named `list_voices` that queried the Supertone API and returned voice metadata.
- **Status:** Removed in v0.2 as a breaking change. Callers must migrate to `search_voice` (FR-012), which accepts a superset of filter parameters.

### Feature Area: Voice Discovery (v0.2)

#### FR-012: `search_voice` MCP Tool
- **Description:** Expose an MCP tool named `search_voice` that calls `voices.search_voices_async` (Supertone SDK) with optional filters. Replaces v0.1's `list_voices` (breaking change, no alias).
- **Priority:** Must
- **Parameters (all optional, server-side filtering):** `name`, `description`, `language`, `gender`, `age`, `use_case`, `style`, `model`.
- **Acceptance Criteria:**
  - The tool is registered and discoverable.
  - When called with no filters, returns the full voice list as a numbered plain-text list.
  - When called with any filter, prefixes output with a `Filters applied: key=value, ...` line.
  - When zero results, returns `No voices found matching the filters.` (success, not error).
  - Each entry includes: voice_id, name, languages, styles.
- **Dependencies:** FR-003.

#### FR-013: `get_voice` MCP Tool
- **Description:** Expose an MCP tool named `get_voice` that calls `voices.get_voice_async` and returns full voice detail.
- **Priority:** Must
- **Parameters:** `voice_id` (required).
- **Acceptance Criteria:**
  - Returns a plain-text block including voice_id, name, description, age, gender, use_cases, languages, styles, models, sample count, thumbnail_image_url.
  - Includes a closing line `Use preview_voice to fetch sample URLs.`.
  - Returns `voice_id must not be empty.` if input is empty.
- **Dependencies:** FR-003.

#### FR-014: `get_credit_balance` MCP Tool
- **Description:** Expose an MCP tool named `get_credit_balance` that calls `usage.get_credit_balance_async`.
- **Priority:** Must
- **Parameters:** None.
- **Acceptance Criteria:**
  - Returns `Credit balance: {N} credits remaining.`.
  - If the API response includes plan name or expiry, append `Plan: {name}` / `Expires: {date}` on additional lines.
  - Maps API errors per FR-007.
- **Dependencies:** FR-003.

#### FR-015: `preview_voice` MCP Tool
- **Description:** Expose an MCP tool named `preview_voice` that returns sample audio URLs filtered from `get_voice` data (no separate API call needed if SDK already includes samples).
- **Priority:** Must
- **Parameters:** `voice_id` (required), `language`, `style`, `model` (all optional filters).
- **Acceptance Criteria:**
  - Returns a numbered list. Each line format: `1. [language=ko, style=happy, model=sona_speech_1] https://.../sample.wav`.
  - If the voice has zero samples, returns `This voice has no preview samples.`.
  - If filters match no samples, returns `No matching samples for the given filters.`.
  - v0.2 does NOT play audio locally. Audio playback is deferred to v0.3 (`play_audio_url` tool).
- **Dependencies:** FR-003.

### Feature Area: Duration Prediction (v0.2)

#### FR-016: `predict_duration` MCP Tool
- **Description:** Expose an MCP tool that calls `text_to_speech.predict_duration_async` to compute expected audio length without performing synthesis.
- **Priority:** Must
- **Parameters:** Same as `text_to_speech` minus actual synthesis (text required; voice_id, language, model, output_format, speed, pitch_shift, style optional).
- **Acceptance Criteria:**
  - Returns `Predicted duration: {N}.{NN}s (credit usage is proportional to duration).`.
  - Reuses FR-005 and FR-006 input validation rules (text length, parameter ranges).
  - Does NOT produce any audio file.
- **Dependencies:** FR-001 (shares validation), FR-003.

### Feature Area: Voice Cloning CRUD (v0.2)

#### FR-017: `clone_voice` MCP Tool
- **Description:** Create a cloned custom voice from a single local audio file via `custom_voices.create_cloned_voice_async`.
- **Priority:** Must
- **Parameters:** `name` (required, non-empty), `audio_path` (required, local FS path with `~` expansion), `description` (optional).
- **Acceptance Criteria:**
  - File extension MUST be `.wav` or `.mp3`. Invalid → `Unsupported audio format: "{ext}". Supported: wav, mp3.`.
  - File size MUST be ≤ 3MB. Larger → `Audio file exceeds the 3MB limit (received: {N} bytes).`.
  - File MUST exist. Missing → `Audio file not found: {path}.`.
  - `name` MUST be non-empty. Empty → `Voice name must not be empty.`.
  - All validations happen BEFORE any API call (fail-fast).
  - On success returns `Custom voice created. voice_id: {id}. Use this voice_id in text_to_speech.`.
  - SDK payload: `Files` object with `file_name`, `content` (bytes), `content_type`.
- **Dependencies:** FR-003.

#### FR-018: `search_custom_voice` MCP Tool
- **Description:** Search the user's own custom (cloned) voices via `custom_voices.search_custom_voices_async`.
- **Priority:** Must
- **Parameters:** `name`, `description` (both optional partial matches).
- **Acceptance Criteria:**
  - Returns a numbered list with voice_id, name, description, and created_at if available.
  - When zero results, returns `No custom voices found.`.
  - Pagination is handled internally using SDK defaults; no `page`/`limit` parameters exposed in v0.2.
- **Dependencies:** FR-003.

#### FR-019: `edit_custom_voice` and `delete_custom_voice` MCP Tools
- **Description:** Partial update and deletion of cloned voices via `custom_voices.edit_custom_voice_async` and `custom_voices.delete_custom_voice_async`.
- **Priority:** Must
- **Parameters (edit):** `voice_id` (required), `name` (optional), `description` (optional). At least one of `name`/`description` MUST be provided.
- **Parameters (delete):** `voice_id` (required).
- **Acceptance Criteria (edit):**
  - With both `name` and `description` omitted → `At least one of name or description must be provided.` (no API call).
  - On success returns `Custom voice updated. voice_id: {id}.`.
- **Acceptance Criteria (delete):**
  - On success returns `Custom voice deleted. voice_id: {id}.`.
  - NO confirm gate is enforced in v0.2. The tool description text MUST warn the user this is irreversible (UX spec).
- **Dependencies:** FR-003.

### Feature Area: SDK 0.2.3 Surface Expansion (v0.3)

#### FR-023: `merge_audio_files` MCP Tool
- **Description:** Expose an MCP tool named `merge_audio_files` that uses ffmpeg (bundled via `imageio-ffmpeg`) to concatenate two or more audio files into a single output file. Supports three operations: plain head-to-tail concat, concat with silence gap, and concat with crossfade. `gap_ms` and `crossfade_ms` are mutually exclusive.
- **Priority:** Must (v0.4)
- **Parameters:** `input_paths` (list[str], required, min 2; absolute or `~`-expanded paths), `gap_ms` (int, default 0), `crossfade_ms` (int, default 0), `output_format` (str, optional; `mp3` or `wav`; auto-detected if omitted).
- **Acceptance Criteria:**
  - Two or more valid files → merged file saved to `SUPERTONE_OUTPUT_DIR`, absolute path and duration returned.
  - Single file → passthrough (no ffmpeg invocation; returns path and duration).
  - Empty input list → `Input file list must not be empty.`
  - Nonexistent path → `Audio file not found: {path}.` (fail-fast, before ffmpeg).
  - Unsupported extension → `Unsupported format: "{ext}". Supported: mp3, wav.`
  - Both `gap_ms` > 0 and `crossfade_ms` > 0 → `gap_ms and crossfade_ms are mutually exclusive. Set one to 0.`
  - Output format auto-detected: all inputs same ext → use that ext; mixed → `.mp3`; explicit `output_format` overrides.
  - ffmpeg nonzero exit → `Audio merge failed: {stderr_excerpt}.`
- **Implementation:** ffmpeg binary resolved via `imageio_ffmpeg.get_ffmpeg_exe()`; invoked via `asyncio.create_subprocess_exec`. No system ffmpeg dependency.
- **Dependencies:** FR-004 (output dir reuse), FR-001 (naming convention reuse).

#### FR-020: `get_custom_voice` MCP Tool
- **Description:** Expose an MCP tool named `get_custom_voice` that fetches the detail of a single custom (cloned) voice via `custom_voices.get_custom_voice_async`. (Deferred in v0.2; promoted in v0.3 because SDK 0.2.3 provides the method.)
- **Priority:** Should
- **Parameters:** `voice_id` (required).
- **Acceptance Criteria:**
  - Returns a plain-text block including voice_id, name, description, and created_at (when available).
  - Returns `voice_id must not be empty.` if input is empty/whitespace (no API call).
  - Maps API errors per FR-007.
- **Dependencies:** FR-003.

#### FR-021: `get_usage_history` MCP Tool
- **Description:** Expose an MCP tool named `get_usage_history` that retrieves usage history via `usage.get_usage_async`. Paging uses SDK defaults.
- **Priority:** Should
- **Parameters:** All optional (within the SDK 0.2.3 period/paging parameter range).
- **Acceptance Criteria:**
  - Returns a plain-text summary of usage by period (e.g., character/request counts).
  - Returns a clear "no usage" message (not an error) when the history is empty.
  - Maps API errors per FR-007.
- **Dependencies:** FR-003.

#### FR-022: `get_voice_usage` MCP Tool
- **Description:** Expose an MCP tool named `get_voice_usage` that retrieves usage for a specific voice via `usage.get_voice_usage_async`.
- **Priority:** Should
- **Parameters:** `voice_id` (required).
- **Acceptance Criteria:**
  - Returns a plain-text usage summary for the given voice.
  - Returns `voice_id must not be empty.` if input is empty/whitespace (no API call).
  - Maps API errors per FR-007.
- **Dependencies:** FR-003.

### Feature Area: Configuration and Authentication

#### FR-003: API Key Authentication
- **Description:** Authenticate with the Supertone API using an API key provided via the `SUPERTONE_API_KEY` environment variable.
- **Priority:** Must
- **Acceptance Criteria:**
  - On server startup, if `SUPERTONE_API_KEY` is not set or is empty, the server starts but each tool call returns a clear error: "SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings."
  - The API key is sent as the `x-sup-api-key` HTTP header on every API request.
  - The API key is never logged or included in error messages returned to the user.
- **Dependencies:** None.

#### FR-004: Output Directory Configuration
- **Description:** Allow users to configure the output directory for saved audio files via the `SUPERTONE_OUTPUT_DIR` environment variable.
- **Priority:** Must
- **Acceptance Criteria:**
  - If `SUPERTONE_OUTPUT_DIR` is set, files are saved to that directory.
  - If `SUPERTONE_OUTPUT_DIR` is not set, files are saved to `~/supertone-tts-output/`.
  - If the output directory does not exist, it is created automatically (including intermediate directories).
  - If the directory cannot be created (permissions), a clear error is returned.
- **Dependencies:** None.

### Feature Area: Input Validation

#### FR-005: Text Length Validation
- **Description:** Validate that input text is non-empty. (v0.1/v0.2 enforced a 300-character hard cap; v0.3 RELAXES this — see below.)
- **Priority:** Must
- **Acceptance Criteria:**
  - Given an empty string, the tool returns an error: "Text must not be empty."
  - **(v0.3 update)** The MCP layer no longer hard-rejects text over 300 characters for `text_to_speech` or `predict_duration`. Long text is delegated to the SDK's internal auto-chunking (`_auto_chunk_text_async`), which splits, synthesizes in parallel, and concatenates the audio.
  - Tool descriptions note that very long inputs increase credit consumption and latency proportionally.
- **v0.3 change:** The prior behavior ("must NOT automatically split text > 300 chars; return a too-long error") is reversed. The `TEXT_MAX_LENGTH` constant may remain for reference but is no longer enforced as a hard cap.
- **Dependencies:** FR-001.

#### FR-006: Parameter Validation
- **Description:** Validate all optional parameters against their allowed values/ranges before making API calls.
- **Priority:** Must
- **Acceptance Criteria:**
  - `language` must be one of `ko`, `en`, `ja`. Invalid values return an error listing valid options.
  - `output_format` must be one of `wav`, `mp3`. Invalid values return an error listing valid options.
  - `speed` must be a number in range [0.5, 2.0]. Out-of-range values return an error stating the valid range.
  - `pitch_shift` must be a number in range [-12, +12]. Out-of-range values return an error stating the valid range.
  - All validation happens before any API call is made (fail-fast).
- **Dependencies:** FR-001.

### Feature Area: Error Handling

#### FR-007: API Error Propagation
- **Description:** Propagate Supertone API errors to the user with actionable information.
- **Priority:** Must
- **Acceptance Criteria:**
  - On HTTP 401/403, return: "Authentication failed. Please verify your SUPERTONE_API_KEY."
  - On HTTP 429, return: "Rate limit exceeded. Please wait and try again."
  - On HTTP 4xx (other), return the HTTP status code and the error message from the API response body.
  - On HTTP 5xx, return: "Supertone API server error ({status_code}). Please try again later."
  - On network timeout or connection error, return: "Failed to connect to Supertone API. Please check your network connection."
- **Dependencies:** FR-001, FR-002.

### Feature Area: Default Voice

#### FR-008: Default Voice Fallback
- **Description:** When `voice_id` is not provided to `text_to_speech`, use a default voice.
- **Priority:** Must
- **Acceptance Criteria:**
  - When `voice_id` is omitted, a pre-configured default voice ID is used.
  - The default voice supports at least the Korean language.
- **Dependencies:** FR-001.
- **Assumption:** PRD does not specify which voice ID is the default. This must be determined by inspecting the Supertone API documentation or selecting the first available Korean voice. **Verify with stakeholder.**

### Feature Area: Server Infrastructure

#### FR-009: MCP Server Entry Point
- **Description:** Implement an MCP server using the official MCP Python SDK that registers `text_to_speech` and `list_voices` as tools.
- **Priority:** Must
- **Acceptance Criteria:**
  - The server can be started via `uvx supertone-tts-mcp` or `python -m supertone_tts_mcp`.
  - The server communicates over stdio transport (standard for MCP CLI-based servers).
  - Both tools are listed when the client sends a `tools/list` request.
  - Tool schemas (parameter names, types, descriptions) are correctly exposed.
- **Dependencies:** None.

#### FR-010: PyPI Package
- **Description:** Package the server as `supertone-tts-mcp` on PyPI with a console entry point.
- **Priority:** Must
- **Acceptance Criteria:**
  - `pip install supertone-tts-mcp` installs the package and makes the `supertone-tts-mcp` command available.
  - `uvx supertone-tts-mcp` runs the server without prior installation.
  - The package has correct metadata (name, version, description, author, license).
- **Dependencies:** FR-009.

#### FR-011: MCP Registry Registration
- **Description:** Register the server on the official MCP Registry and PulseMCP.
- **Priority:** Should
- **Acceptance Criteria:**
  - A valid `server.json` file exists with correct schema, name (`io.github.pillip/supertone-tts`), description, and package reference.
  - The server is searchable on the official MCP Registry.
  - The server is listed on PulseMCP.
- **Dependencies:** FR-010.

---

## Non-functional Requirements

#### NFR-001: Installation Simplicity
- **Description:** The server must be installable with a single command.
- **Measurable Target:** `uvx supertone-tts-mcp` or `pip install supertone-tts-mcp` completes successfully in under 60 seconds on a standard broadband connection.
- **Priority:** Must

#### NFR-002: MCP Protocol Compliance
- **Description:** The server must conform to the MCP specification and work with major MCP clients.
- **Measurable Target:** Passes integration tests with Claude Desktop and Cursor (both tools callable and returning valid results).
- **Priority:** Must

#### NFR-003: Server-side Latency
- **Description:** The MCP server must introduce minimal overhead beyond the Supertone API response time.
- **Measurable Target:** Server-side processing overhead (excluding Supertone API call and file I/O) < 100ms at p95.
- **Priority:** Must

#### NFR-004: Error Message Quality
- **Description:** All error messages must be understandable by non-technical users and actionable.
- **Measurable Target:** Every error path returns a message that (a) states what went wrong, (b) suggests a fix or next step. No raw stack traces or internal error codes exposed to users.
- **Priority:** Must

#### NFR-005: Test Coverage
- **Description:** Automated tests must cover core functionality.
- **Measurable Target:**
  - pytest-based unit tests exist for all tools and the Supertone client wrapper.
  - All external API calls are mocked in tests (no real network calls in CI).
  - Test files: `tests/test_tools.py`, `tests/test_supertone_client.py`.
  - Minimum test count: at least 1 test per tool, 1 test per error path for FR-007.
- **Priority:** Must

#### NFR-006: Python Version Compatibility
- **Description:** The server must run on Python 3.11 and above.
- **Measurable Target:** CI passes on Python 3.11 and 3.12+.
- **Priority:** Must

#### NFR-007: Security -- API Key Handling
- **Description:** API keys must not be leaked.
- **Measurable Target:**
  - API key is read from environment variable only, never from config files committed to the repo.
  - API key is never printed in logs, error messages, or MCP tool responses.
  - `.env.example` contains only a placeholder value.
- **Priority:** Must

#### NFR-008: Async HTTP
- **Description:** HTTP calls to the Supertone API must be asynchronous.
- **Measurable Target:** Uses `httpx.AsyncClient` for all API calls. No blocking I/O on the event loop.
- **Priority:** Should

#### NFR-010: ffmpeg Bundling and Availability (v0.4)
- **Description:** The ffmpeg binary used by `merge_audio_files` must be bundled with the Python package so that `uvx supertone-mcp` remains zero-config. No system ffmpeg installation must be required.
- **Measurable Target:**
  - `imageio-ffmpeg>=0.5` is listed as a project dependency in `pyproject.toml` (added via `uv add imageio-ffmpeg`).
  - `imageio_ffmpeg.get_ffmpeg_exe()` resolves a valid executable path at runtime.
  - CI tests mock the ffmpeg subprocess; no real ffmpeg binary is required in the CI environment.
- **Priority:** Must (v0.4)

#### NFR-009: Behavior Controlled by Parameters, Not Env Vars (v0.3)
- **Description:** All tool *behavior* must be controllable via per-call parameters; environment variables are reserved for authentication and stable defaults only. The SDK dependency must be version-pinned so SDK additions cannot silently desync validation.
- **Measurable Target:**
  - Zero behavior-control environment variables (auth/default-value env vars excepted). Specifically, `SUPERTONE_MCP_OUTPUT_MODE` and `SUPERTONE_MCP_AUTOPLAY` are removed and replaced by the `output_mode`/`autoplay` parameters.
  - Retained env vars are limited to `SUPERTONE_API_KEY` (auth), `SUPERTONE_MCP_VOICE_ID` (default voice), and `SUPERTONE_OUTPUT_DIR` (save directory).
  - `pyproject.toml` pins `supertone>=0.2.3,<0.3`; validated SDK version is 0.2.3.
- **Priority:** Should

---

## Out of Scope

The following are explicitly excluded from v0.2 per PRD Section 3:

1. **STT (Speech-to-Text)** -- incompatible with MCP's tool-calling architecture.
2. **Voice conversation interface** (STT -> LLM -> TTS pipeline) -- separate project.
3. **Batch conversion** (`batch_tts`) -- deferred to v0.3+.
3a. **Audio mix/overlay** (`mix_audio_files`) -- deferred to a future issue; v0.4 scope is concat only.
4. **Multi-file voice cloning** (multi-sample upload) -- v0.2 supports single file only; deferred to v0.3+.
5. **Local audio autoplay** for `preview_voice` -- v0.2 returns URLs only; autoplay is the responsibility of the future v0.3 `play_audio_url` tool.
6. **`list_models` tool** (TTS model catalog) -- deferred to v0.3+.
7. **Single-fetch `get_custom_voice` tool** -- deferred; `search_custom_voice` results are sufficient in v0.2.
8. **Delete confirmation gate** for `delete_custom_voice` -- v0.2 relies on the tool description's irreversibility warning; explicit confirm prompts deferred.
9. **Automatic text splitting** for 300+ characters -- deferred to v0.3+.
10. **Web UI or standalone client application**.
11. **Support for TTS engines other than Supertone**.
12. **Audio playback within the MCP response** -- MCP does not stream binary; file paths or URLs are returned.
13. **Rate limiting or request queuing on the MCP server side** -- users are subject to Supertone API rate limits directly.
14. **User authentication / multi-tenancy on the MCP server** -- single-user, single API key model.

> Note: v0.1 listed voice cloning, duration prediction, and credit balance check as out of scope. These have been promoted to v0.2 (FR-014, FR-016, FR-017–019).

---

## Assumptions

| ID | Assumption | Risk if Wrong |
|----|-----------|---------------|
| A1 | The Supertone API base URL is `https://api.supertoneapi.com`. PRD states "docs에서 확인 필요" (needs verification from docs). **Verify with stakeholder.** | API calls fail; requires code change to fix URL. |
| A2 | The voice listing endpoint is `GET /v1/voices`. PRD states this is an estimate ("추정"). **Verify with stakeholder.** | `list_voices` tool will not work. |
| A3 | The Supertone API returns audio duration in its response headers or metadata. PRD requires returning duration but does not specify how it is obtained. **Verify with stakeholder.** If the API does not return duration, it must be calculated from the audio file (e.g., parsing WAV headers or using a library). | Additional dependency required (e.g., `mutagen` or `pydub`) if duration must be computed locally. |
| A4 | A sensible default `voice_id` exists and can be hardcoded or fetched at startup. PRD says "미지정 시 기본 보이스 사용" but does not specify which voice. **Verify with stakeholder.** | If no default is provided, the tool may fail when `voice_id` is omitted. |
| A5 | The `style` parameter values (e.g., `neutral`, `happy`) are per-voice and can be discovered from the `list_voices` response. | If the API does not expose available styles per voice, validation of the `style` parameter is not possible and must be passed through as-is. |
| A6 | The Supertone API supports `speed` and `pitch_shift` parameters as described. PRD lists them but they may not map directly to API parameters. **Verify against actual API documentation.** | Parameters silently ignored or cause API errors. |
| A7 | MCP stdio transport is sufficient for Claude Desktop and Cursor integration. No SSE or HTTP transport is needed for v1. | Would need to implement additional transport layer. |
| A8 | The file naming pattern `{date}_{unique_id}.{format}` is acceptable. PRD shows `2026-03-13_abc123.mp3` as an example but does not formalize the pattern. | No user impact; cosmetic only. |

---

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Supertone API documentation is incomplete or inaccurate (base URL, endpoints, parameters). | High | High | Perform M1 (API spike) first. Validate all endpoints with real API calls before building the MCP wrapper. |
| R2 | Supertone API does not return audio duration, requiring local computation. | Medium | Low | Add `mutagen` or equivalent as optional dependency; compute duration from file if API does not provide it. |
| R3 | MCP SDK introduces breaking changes (ecosystem is young and fast-moving). | Medium | Medium | Pin `mcp` SDK version in `pyproject.toml`. Monitor SDK changelog. |
| R4 | Rate limits (20-60 req/min) may frustrate users generating multiple audio files. | Medium | Medium | Out of scope for v1 but document the limitation clearly in README. Consider queuing in v2. |
| R5 | The `style` parameter may not be supported by all voices, leading to confusing errors. | Medium | Low | Validate `style` against `list_voices` data when possible; return clear error otherwise. |
| R6 | PyPI package name `supertone-tts-mcp` may already be taken. | Low | High | Check name availability before development. Have fallback names ready. |
| R7 | File system permissions prevent writing to the output directory on some OS configurations. | Low | Medium | Catch permission errors explicitly and return actionable error message (FR-004). |

---

## Success Metrics (quantitative, measurable)

| ID | Metric | Target | Timeframe |
|----|--------|--------|-----------|
| SM-001 | GitHub stars | >= 50 | 3 months post-launch |
| SM-002 | PyPI downloads | >= 200 | 3 months post-launch |
| SM-003 | MCP Registry listing | Registered and searchable | At launch |
| SM-004 | Client compatibility | Verified on Claude Desktop AND Cursor | At launch |
| SM-005 | Unit test count | >= 10 tests covering tools, client, and error paths | At launch |
| SM-006 | Test pass rate | 100% in CI | Continuous |

---

## Traceability Matrix

| User Story | Functional Requirements | NFRs |
|-----------|------------------------|------|
| US-001 | FR-001, FR-003, FR-004, FR-005, FR-007, FR-008 | NFR-003, NFR-004, NFR-008 |
| US-002 (v0.1, superseded) | FR-002 (removed) → migrated to US-008/FR-012 | NFR-004 |
| US-003 | FR-001, FR-012, FR-006 | NFR-004 |
| US-004 | FR-001, FR-006 | NFR-004 |
| US-005 | FR-001, FR-006 | NFR-004 |
| US-006 | FR-001, FR-006 | NFR-004 |
| US-007 | FR-012 | NFR-004 |
| US-008 (v0.2) | FR-012, FR-013, FR-015, FR-003, FR-007 | NFR-004 |
| US-009 (v0.2) | FR-014, FR-003, FR-007 | NFR-004 |
| US-010 (v0.2) | FR-016, FR-005, FR-006, FR-003, FR-007 | NFR-004 |
| US-011 (v0.2) | FR-017, FR-018, FR-019, FR-003, FR-007 | NFR-004, NFR-007 |
| -- | FR-009, FR-010, FR-011 | NFR-001, NFR-002, NFR-005, NFR-006, NFR-007 |
| US-018 (v0.4) | FR-023, FR-004 | NFR-010, NFR-004, NFR-005 |
