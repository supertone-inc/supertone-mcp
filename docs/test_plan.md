# Test Plan: Supertone TTS MCP Server

> Generated: 2026-03-13
> Source: Requirements v0.1, UX Spec v0.1, Architecture v0.1

---

## Strategy

### Testing Pyramid

| Layer | Ratio | Scope | Rationale |
|-------|-------|-------|-----------|
| Unit | 50% | `tools.py` validation logic, `supertone_client.py` error mapping, file naming, output formatting | Business logic is concentrated in validation and formatting. These are pure functions or near-pure -- fast, deterministic, high value. |
| Integration | 40% | Tool handlers end-to-end with mocked HTTP, `SupertoneClient` with mocked `httpx` | The critical path is: validate -> HTTP call -> save file -> format response. Integration tests exercise this full chain with mocked externals. |
| E2E (manual) | 10% | Real MCP client (Claude Desktop / Cursor) with real API key | Cannot automate MCP client interaction in CI. Reserved for release verification. |

### Test Framework

- **Runner:** `pytest` with `pytest-asyncio` (all tool handlers and client methods are async).
- **Mocking:** `pytest-mock` / `unittest.mock` for `httpx.AsyncClient`, filesystem operations, and environment variables.
- **Coverage:** `pytest-cov` targeting `src/` with `--cov-report=term-missing`.

### CI Integration

- **Every PR:** All unit and integration tests (`uv run pytest -q --cov=src`). Matrix: Python 3.11, 3.12, 3.13. Must pass before merge.
- **Nightly:** N/A for v1 (no long-running performance benchmarks warranted for a CLI tool).
- **Release gate:** All tests pass + manual smoke checklist completed.

---

## Risk Matrix

| Flow | Likelihood of Failure | Impact if Fails | Risk | Coverage Level |
|------|-----------------------|-----------------|------|----------------|
| text_to_speech happy path | Medium (API assumptions A1, A3, A6 unverified) | Critical -- primary feature unusable | **High** | Unit + Integration |
| Input validation (text, params) | Low (pure logic) | High -- invalid data hits API, wastes quota or returns confusing errors | **High** | Unit (exhaustive) |
| API error propagation (401, 429, 5xx, network) | High (external dependency) | High -- user gets raw errors or hangs | **High** | Unit + Integration |
| API key handling / security | Low (simple env var read) | Critical -- key leak is a security incident | **High** | Unit + Integration |
| Output directory creation / write | Low | Medium -- TTS fails but list_voices still works | **Medium** | Unit + Integration |
| list_voices happy path | Medium (API assumption A2) | Medium -- discovery broken but TTS may still work with known voice_id | **Medium** | Unit + Integration |
| list_voices language filter | Low | Low -- convenience feature | **Low** | Unit |
| MCP server registration / tool discovery | Low (SDK handles it) | Critical -- nothing works if tools are not registered | **Medium** | Integration (manual verify) |
| Default voice fallback | Medium (Assumption A4) | Medium -- omitting voice_id fails | **Medium** | Unit |
| Output formatting (plain text, absolute paths) | Low | Low -- cosmetic but affects LLM parsing | **Low** | Unit |
| Voice discovery client (`search_voices`, `get_voice`, `get_credit_balance`) — v0.2 | Medium (SDK pagination + nullable fields) | Medium -- discovery features (FR-012/013/014) unusable | **Medium** | Unit (pagination + error mapping + null-field handling), covered by ISSUE-014 |
| Model enum sync / DEFAULT_MODEL (v0.3) | Medium (stale SUPPORTED_MODELS rejected 2 SDK models) | Medium -- valid models rejected; wrong default | **Medium** | Unit (all 7 models pass; regression for 3t/api_3), ISSUE-021 |
| Streaming routing + sona_speech_1-only validation (v0.3) | Medium (cross-field rule + dual code paths) | High -- wrong SDK method or unsupported-model 500s | **High** | Unit (routing + fail-fast error string), ISSUE-023 |
| Per-call output_mode/autoplay (env→param, v0.3) | Medium (BREAKING; env vars ignored) | Medium -- behavior surprises / leftover env reads | **Medium** | Unit (param-driven, env ignored), ISSUE-022 |
| Relaxed 300-char limit (v0.3) | Low (removal of a check) | Low -- long text now delegated to SDK | **Low** | Unit (long text passes; empty still rejected), ISSUE-024 |
| New TTS params include_phonemes/normalized_text (v0.3) | Low (pass-through) | Low | **Low** | Unit (forwarded to SDK), ISSUE-025 |
| New tools get_custom_voice / usage (v0.3) | Medium (new SDK wrappers + formatters) | Medium -- FR-020/021/022 unusable | **Medium** | Unit (wrapper + handler + error mapping), ISSUE-026/027 |
| merge_audio_files ffmpeg subprocess (v0.4) | Medium (subprocess + binary packaging) | Medium -- FR-023 unusable; other tools unaffected | **Medium** | Unit (mocked subprocess + imageio-ffmpeg); integration with real ffmpeg binary (manual), ISSUE-029 |

---

## Critical Flows (ordered by risk)

### Flow 1: text_to_speech -- Happy Path

- **Risk level:** High
- **Related requirements:** FR-001, FR-003, FR-004, FR-008, NFR-003, NFR-008

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-001 | `SUPERTONE_API_KEY` set, output dir writable, API returns 200 with audio bytes | Call `text_to_speech(text="Hello")` with defaults | File saved to output dir, response contains absolute path, duration in seconds, voice_id, language "ko", format "mp3" | Integration | CI |
| TC-002 | Same as TC-001 | Call `text_to_speech(text="Test", language="en", output_format="wav", speed=1.5, pitch_shift=3, style="happy", voice_id="yuki-01")` | All parameters forwarded to API correctly. Response shows voice "yuki-01", language "en", format "wav". File has `.wav` extension. | Integration | CI |
| TC-003 | Same as TC-001 | Call `text_to_speech(text="Test")` without `voice_id` | Default voice ID used in API call. Response includes the default voice_id for transparency. | Unit | CI |
| TC-004 | Output dir does not exist | Call `text_to_speech(text="Test")` | Directory created automatically (including intermediates). File saved successfully. | Integration | CI |
| TC-005 | Same as TC-001 | Verify file naming pattern | File named `{YYYY-MM-DD}_{8-char-uuid}.{format}`, e.g., `2026-03-13_a1b2c3d4.mp3` | Unit | CI |
| TC-006 | Same as TC-001 | Verify returned file path | Path is absolute (starts with `/`), `~` is expanded, uses forward slashes | Unit | CI |
| TC-007 | Same as TC-001 | Verify duration calculation | `mutagen` called on saved file, duration returned as float with "seconds" label | Unit | CI |

### Flow 2: Input Validation

- **Risk level:** High
- **Related requirements:** FR-005, FR-006, NFR-004

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-010 | None | `text_to_speech(text="")` | Error: "Text must not be empty." No API call made. | Unit | CI |
| TC-011 | None | `text_to_speech(text="a" * 301)` | Error: "Text exceeds the maximum length of 300 characters (received: 301). Please shorten or split the text manually." No API call made. | Unit | CI |
| TC-012 | None | `text_to_speech(text="a" * 300)` | Accepted. Proceeds to API call. | Unit | CI |
| TC-013 | None | `text_to_speech(text="a")` -- single character | Accepted. Proceeds to API call. | Unit | CI |
| TC-014 | None | `text_to_speech(text="..." , language="zz")` | Error: `Invalid language: "zz". Supported languages: ko, en, ja.` No API call made. | Unit | CI |
| TC-015 | None | `text_to_speech(text="...", output_format="ogg")` | Error: `Invalid output format: "ogg". Supported formats: mp3, wav.` No API call made. | Unit | CI |
| TC-016 | None | `text_to_speech(text="...", speed=0.4)` | Error: "Speed must be between 0.5 and 2.0 (received: 0.4)." No API call made. | Unit | CI |
| TC-017 | None | `text_to_speech(text="...", speed=2.1)` | Error: "Speed must be between 0.5 and 2.0 (received: 2.1)." No API call made. | Unit | CI |
| TC-018 | None | `text_to_speech(text="...", speed=0.5)` | Accepted (boundary -- inclusive lower). | Unit | CI |
| TC-019 | None | `text_to_speech(text="...", speed=2.0)` | Accepted (boundary -- inclusive upper). | Unit | CI |
| TC-020 | None | `text_to_speech(text="...", pitch_shift=-13)` | Error: "Pitch shift must be between -12 and +12 semitones (received: -13)." No API call made. | Unit | CI |
| TC-021 | None | `text_to_speech(text="...", pitch_shift=13)` | Error: "Pitch shift must be between -12 and +12 semitones (received: 13)." No API call made. | Unit | CI |
| TC-022 | None | `text_to_speech(text="...", pitch_shift=-12)` | Accepted (boundary -- inclusive lower). | Unit | CI |
| TC-023 | None | `text_to_speech(text="...", pitch_shift=12)` | Accepted (boundary -- inclusive upper). | Unit | CI |
| TC-024 | None | `text_to_speech(text="...", language="ko")` | Accepted. Each valid enum value tested: "ko", "en", "ja". | Unit | CI |
| TC-025 | None | `text_to_speech(text="...", output_format="mp3")` | Accepted. Each valid enum value tested: "mp3", "wav". | Unit | CI |
| TC-026 | None | `text_to_speech(text="..." )` with Korean/Unicode text, 300 codepoints | Accepted. Character count uses Python `len()` (codepoints, not bytes). | Unit | CI |
| TC-027 | None | `list_voices(language="zz")` | Error: `Invalid language filter: "zz". Supported languages: ko, en, ja.` No API call made. | Unit | CI |

### Flow 3: API Error Propagation

- **Risk level:** High
- **Related requirements:** FR-007, NFR-004

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-030 | `SUPERTONE_API_KEY` not set / empty | Call any tool | Error: "SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings." No HTTP request made. | Integration | CI |
| TC-031 | API returns HTTP 401 | Call `text_to_speech(text="Test")` | Error: "Authentication failed. Please verify your SUPERTONE_API_KEY." | Integration | CI |
| TC-032 | API returns HTTP 403 | Call `text_to_speech(text="Test")` | Error: "Authentication failed. Please verify your SUPERTONE_API_KEY." | Integration | CI |
| TC-033 | API returns HTTP 429 | Call `text_to_speech(text="Test")` | Error: "Rate limit exceeded. Please wait and try again." | Integration | CI |
| TC-034 | API returns HTTP 500 | Call `text_to_speech(text="Test")` | Error: "Supertone API server error (500). Please try again later." | Integration | CI |
| TC-035 | API returns HTTP 502 | Call `text_to_speech(text="Test")` | Error: "Supertone API server error (502). Please try again later." | Integration | CI |
| TC-036 | API returns HTTP 503 | Call `text_to_speech(text="Test")` | Error: "Supertone API server error (503). Please try again later." | Integration | CI |
| TC-037 | `httpx.ConnectError` raised | Call `text_to_speech(text="Test")` | Error: "Failed to connect to Supertone API. Please check your network connection." | Integration | CI |
| TC-038 | `httpx.TimeoutException` raised | Call `text_to_speech(text="Test")` | Error: "Failed to connect to Supertone API. Please check your network connection." | Integration | CI |
| TC-039 | API returns HTTP 400 with body `{"error": "bad request detail"}` | Call `text_to_speech(text="Test")` | Error includes the HTTP status code and API error message from response body. | Integration | CI |
| TC-040 | API returns HTTP 401 | Call `list_voices()` | Error: "Authentication failed. Please verify your SUPERTONE_API_KEY." (same behavior for both tools) | Integration | CI |
| TC-041 | API returns HTTP 429 | Call `list_voices()` | Error: "Rate limit exceeded. Please wait and try again." | Integration | CI |
| TC-042 | Network error | Call `list_voices()` | Error: "Failed to connect to Supertone API. Please check your network connection." | Integration | CI |

### Flow 4: API Key Security

- **Risk level:** High
- **Related requirements:** FR-003, NFR-007

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-050 | `SUPERTONE_API_KEY=test-secret-key-123` | Call `text_to_speech` that triggers any error | Error message does NOT contain "test-secret-key-123" or any substring of the key. | Unit | CI |
| TC-051 | `SUPERTONE_API_KEY=test-secret-key-123` | Call `text_to_speech` successfully | Success response does NOT contain "test-secret-key-123". | Unit | CI |
| TC-052 | `SUPERTONE_API_KEY=test-secret-key-123` | Inspect HTTP request headers in mock | `x-sup-api-key` header set to "test-secret-key-123". | Integration | CI |
| TC-053 | `SUPERTONE_API_KEY` not in env | Server starts | Server starts without error (does not crash at startup). Error occurs at tool-call time. | Integration | CI |

### Flow 5: Output Directory Handling

- **Risk level:** Medium
- **Related requirements:** FR-004

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-060 | `SUPERTONE_OUTPUT_DIR` set to `/tmp/test-tts-output` | Call `text_to_speech` | File saved under `/tmp/test-tts-output/`. | Integration | CI |
| TC-061 | `SUPERTONE_OUTPUT_DIR` not set | Call `text_to_speech` | File saved under `~/supertone-tts-output/` (expanded to absolute). | Integration | CI |
| TC-062 | `SUPERTONE_OUTPUT_DIR` set to non-existent nested path `/tmp/a/b/c/tts` | Call `text_to_speech` | All intermediate directories created. File saved successfully. | Integration | CI |
| TC-063 | `SUPERTONE_OUTPUT_DIR` set to read-only directory | Call `text_to_speech` | Error: `Cannot write to output directory: {path}. Please check directory permissions or set SUPERTONE_OUTPUT_DIR to a writable location.` | Integration | CI |

### Flow 6: list_voices -- Happy Path

- **Risk level:** Medium
- **Related requirements:** FR-002

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-070 | API returns 3 voices | Call `list_voices()` | Response: "Found 3 voices:" followed by numbered list. Each entry has Name, Voice ID, Languages, Styles fields. | Integration | CI |
| TC-071 | API returns 3 voices, 2 support "ko" | Call `list_voices(language="ko")` | Response: "Found 2 voices matching language: ko" with only Korean-capable voices listed. | Integration | CI |
| TC-072 | API returns voices, none support "ja" | Call `list_voices(language="ja")` | Response: "No voices found matching language: ja." (success, not error) | Integration | CI |
| TC-073 | API returns empty list | Call `list_voices()` | Empty list returned, no error. | Integration | CI |

### Flow 7: MCP Server Registration

- **Risk level:** Medium
- **Related requirements:** FR-009, NFR-002

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-080 | Server module importable | Inspect registered tools | Both `text_to_speech` and `list_voices` are registered in the MCP server. | Integration | CI |
| TC-081 | Server module importable | Inspect tool schemas | `text_to_speech` schema has `text` (required), `voice_id`, `language`, `output_format`, `speed`, `pitch_shift`, `style` (all optional). `list_voices` schema has `language` (optional). | Integration | CI |
| TC-082 | Server started | Send MCP `tools/list` request | Response includes both tools with correct names and descriptions. | E2E | Manual |

### Flow 8: Model Enum Sync (v0.3)

- **Risk level:** Medium
- **Related requirements:** FR-001, US-015, NFR-009; ISSUE-021

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-090 | None | `validate_model(m)` for each of the 7 models | No error for all 7 (`sona_speech_1/2/2_flash/2t/3t`, `supertonic_api_1/3`). | Unit | CI |
| TC-091 | None | `validate_model("sona_speech_3t")`, `validate_model("supertonic_api_3")` | No error (regression for the stale SUPPORTED_MODELS bug). | Unit | CI |
| TC-092 | None | `validate_model("sona_speech_99")` | Error: `Invalid model: "sona_speech_99". Supported models: sona_speech_1, sona_speech_2, sona_speech_2_flash, sona_speech_2t, sona_speech_3t, supertonic_api_1, supertonic_api_3.` | Unit | CI |
| TC-093 | None | Inspect `DEFAULT_MODEL` | Equals `sona_speech_2_flash`. | Unit | CI |
| TC-094 | Mocked client | `text_to_speech(text="hi", model="supertonic_api_3")` | No validation error; synthesize path invoked. | Unit | CI |

### Flow 9: Streaming Routing + sona_speech_1-Only Validation (v0.3)

- **Risk level:** High
- **Related requirements:** FR-001, US-014, US-015; ISSUE-023

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-100 | Mocked client | `text_to_speech(text="hi")` (defaults) | `client.synthesize` called, NOT `synthesize_stream`. Files-mode response. | Unit | CI |
| TC-101 | Mocked client | `text_to_speech(text="hi", streaming=True)` (model defaults to sona_speech_2_flash) | Returns exact error `Streaming is only supported by model "sona_speech_1" (received: "sona_speech_2_flash"). Set streaming=false or use sona_speech_1.`; neither SDK method called. | Unit | CI |
| TC-102 | Mocked client | `text_to_speech(text="hi", model="sona_speech_1", streaming=True)` | `client.synthesize_stream` invoked; output produced from chunks. | Unit | CI |
| TC-103 | Mocked client | `text_to_speech(text="hi", streaming=False, output_mode="resources")` | `client.synthesize` used; `[AudioContent, TextContent]` returned, no file. | Unit | CI |
| TC-104 | Mocked client returns SDK duration | `text_to_speech(text="hi", streaming=False)` | SDK-provided duration preferred over mutagen value. | Unit | CI |

### Flow 10: Per-Call output_mode / autoplay (env→param, v0.3)

- **Risk level:** Medium
- **Related requirements:** FR-001, US-012, US-013, NFR-009; ISSUE-022

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-110 | `SUPERTONE_MCP_OUTPUT_MODE=resources` set | `text_to_speech(text="hi")` (no output_mode arg) | Env ignored; files behavior used. | Unit | CI |
| TC-111 | Mocked client | `text_to_speech(text="hi", output_mode="resources")` | No file written; AudioContent returned. | Unit | CI |
| TC-112 | Mocked client | `text_to_speech(text="hi", output_mode="both")` | File saved + AudioContent returned with path in metadata. | Unit | CI |
| TC-113 | Mocked client | `text_to_speech(text="hi", output_mode="invalid")` | Validation error `Invalid output mode: "invalid". Valid modes: files, resources, both.`; no API call. | Unit | CI |
| TC-114 | `SUPERTONE_MCP_AUTOPLAY=true` set, macOS | `text_to_speech(text="hi")` (no autoplay arg) | `_autoplay` NOT called (default false; env ignored). | Unit | CI |
| TC-115 | macOS, patched subprocess | `text_to_speech(text="hi", autoplay=True)` | `_autoplay` invoked. | Unit | CI |

### Flow 11: Relaxed Length + New TTS Params (v0.3)

- **Risk level:** Low
- **Related requirements:** FR-001, FR-005 (relaxed), FR-016; ISSUE-024, ISSUE-025

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-120 | Mocked client | `text_to_speech(text="a"*500)` | No length error; synthesize called. | Unit | CI |
| TC-121 | Mocked client | `predict_duration(text="a"*500)` | No length error; predict_duration called. | Unit | CI |
| TC-122 | None | `text_to_speech(text="")` / `predict_duration(text="")` | `Text must not be empty.`; no API call. | Unit | CI |
| TC-123 | Mocked client | `text_to_speech(text="hi", include_phonemes=True)` | SDK synthesize call receives `include_phonemes=True`. | Unit | CI |
| TC-124 | Mocked client | `text_to_speech(text="hi", normalized_text="x", model="sona_speech_2_flash")` | SDK synthesize call receives `normalized_text="x"`. | Unit | CI |

### Flow 12: New Tools — get_custom_voice / usage (v0.3)

- **Risk level:** Medium
- **Related requirements:** FR-020, FR-021, FR-022, US-016, US-017; ISSUE-026, ISSUE-027

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-130 | Mocked client | `get_custom_voice("cv1")` | Formatted detail (voice_id, name, description). | Unit | CI |
| TC-131 | None | `get_custom_voice("")` | `voice_id must not be empty.`; no API call. | Unit | CI |
| TC-132 | Mocked client | `get_usage_history()` | Formatted usage summary. | Unit | CI |
| TC-133 | Mocked client returns empty | `get_usage_history()` | "no usage" message (not an error). | Unit | CI |
| TC-134 | Mocked client | `get_voice_usage("v1")` | Formatted per-voice usage summary. | Unit | CI |
| TC-135 | None | `get_voice_usage("")` | `voice_id must not be empty.`; no API call. | Unit | CI |
| TC-136 | Mocked auth error | Any of the 3 new tools | `Authentication failed. Please verify your SUPERTONE_API_KEY.` | Unit | CI |
| TC-137 | Server importable | Inspect registered tools | `get_custom_voice`, `get_usage_history`, `get_voice_usage` are registered. | Integration | CI |

### Flow 13: merge_audio_files (v0.4 / ISSUE-029)

- **Risk level:** Medium
- **Related requirements:** FR-023, US-018, NFR-010, NFR-004

#### Test Cases

| ID | Precondition | Action | Expected Result | Type | Auto |
|----|-------------|--------|-----------------|------|------|
| TC-140 | 2 valid MP3 files exist | `merge_audio_files(input_paths=[p1, p2])` | Merged file saved to output dir; response contains absolute path, duration, "Inputs: 2", "Format: mp3". | Integration | CI |
| TC-141 | 3 valid WAV files exist | `merge_audio_files(input_paths=[p1, p2, p3])` | Merged file saved; format is wav; "Inputs: 3" in response. | Integration | CI |
| TC-142 | 1 valid MP3 file exists | `merge_audio_files(input_paths=[p1])` | Single-file passthrough; no ffmpeg invoked; original path returned. | Unit | CI |
| TC-143 | None | `merge_audio_files(input_paths=[])` | Error: `Input file list must not be empty.`; no ffmpeg invoked. | Unit | CI |
| TC-144 | One path does not exist | `merge_audio_files(input_paths=["missing.mp3", p2])` | Error: `Audio file not found: missing.mp3.`; no ffmpeg invoked. | Unit | CI |
| TC-145 | File has `.ogg` extension | `merge_audio_files(input_paths=[ogg_file, p2])` | Error: `Unsupported format: ".ogg". Supported: mp3, wav.`; no ffmpeg invoked. | Unit | CI |
| TC-146 | Mixed .mp3 + .wav inputs | `merge_audio_files(input_paths=[mp3, wav])` | Auto-format resolves to mp3; merged file has `.mp3` extension. | Integration | CI |
| TC-147 | Mixed .mp3 + .wav, explicit override | `merge_audio_files(input_paths=[mp3, wav], output_format="wav")` | Output uses `.wav`. | Integration | CI |
| TC-148 | None | `merge_audio_files(input_paths=[p1, p2], gap_ms=500)` | ffmpeg invoked with silence gap of 500ms between clips. | Unit | CI |
| TC-149 | None | `merge_audio_files(input_paths=[p1, p2], crossfade_ms=200)` | ffmpeg invoked with a deterministic 200ms crossfade (`afade`+`adelay`+`amix`, not `acrossfade` — ISSUE-033). | Unit | CI |
| TC-156 | Two short ~1.36s clips, real ffmpeg | `merge_audio_files(..., crossfade_ms=500)` repeated ≥10× | Every result is the correct length (~2.22s), no intermittent truncation; merged WAV reports its true duration (ISSUE-032/033). | Integration | gated (`SUPERTONE_RUN_FFMPEG_TESTS=1`) |
| TC-150 | None | `merge_audio_files(input_paths=[p1, p2], gap_ms=500, crossfade_ms=200)` | Error: `gap_ms and crossfade_ms are mutually exclusive. Set one to 0.`; no ffmpeg invoked. | Unit | CI |
| TC-151 | ffmpeg exits nonzero (mocked) | `merge_audio_files(input_paths=[p1, p2])` | Error: `Audio merge failed: {stderr_excerpt}.` | Unit | CI |
| TC-152 | `imageio_ffmpeg` mocked | `merge_audio_files(...)` | `imageio_ffmpeg.get_ffmpeg_exe()` is called to resolve the ffmpeg binary (no system ffmpeg relied upon). | Unit | CI |
| TC-153 | None | `merge_audio_files(input_paths=[p1, p2], output_format="ogg")` | Error: `Invalid output format: "ogg". Supported formats: mp3, wav.`; no ffmpeg invoked. | Unit | CI |
| TC-154 | None | `merge_audio_files(input_paths=[p1, p2], gap_ms=-1)` | Error: `gap_ms and crossfade_ms must be non-negative.`; no ffmpeg invoked. (PR #49 review H2) | Unit | CI |
| TC-155 | None | `merge_audio_files(input_paths=[p1, p2], crossfade_ms=-5)` | Error: `gap_ms and crossfade_ms must be non-negative.`; no ffmpeg. | Unit | CI |
| TC-156 | Heterogeneous inputs (44100/stereo mp3 + 24000/mono wav) | `merge_audio([a, b], ...)` for concat/gap/crossfade | ffmpeg command normalizes every stream (`aresample`/`aformat`) and matches silence params; merge succeeds (validated against real ffmpeg, not just mock). (PR #49 review C1/C2, RL-007) | Integration (manual/opt-in) | local |
| TC-157 | ffmpeg hangs (mocked TimeoutError) | `merge_audio(...)` | Process is killed and `RuntimeError("ffmpeg timed out ...")` raised. (PR #49 review H1) | Unit | CI |
| TC-158 | ffmpeg nonzero exit, empty stderr (mocked) | `merge_audio(...)` | `RuntimeError("ffmpeg exited with code N")` (no bare empty message). (PR #49 review M1) | Unit | CI |

---

## Edge Cases and Boundary Tests

### Text Input

| Case | Input | Expected |
|------|-------|----------|
| Empty string | `""` | Error: "Text must not be empty." |
| Whitespace only | `"   "` | Accepted (whitespace is valid text for TTS). If API rejects it, API error propagated. |
| Exactly 300 chars | `"a" * 300` | Accepted. |
| 301 chars | `"a" * 301` | Error with count 301. |
| Unicode (Korean) | 300 Korean characters | Accepted. `len()` counts codepoints. |
| Emoji characters | `"Hello" + emoji * 295` | Accepted if total codepoints <= 300. |
| Newlines in text | `"Line1\nLine2"` | Accepted. Forwarded to API as-is. |
| Special characters | `"<script>alert(1)</script>"` | Accepted (no HTML/injection risk -- passed as JSON body to API). |

### Numeric Parameters

| Case | Input | Expected |
|------|-------|----------|
| Speed = 0.5 | Lower boundary inclusive | Accepted |
| Speed = 2.0 | Upper boundary inclusive | Accepted |
| Speed = 0.0 | Below range | Error |
| Speed = -1.0 | Negative | Error |
| Speed = 0.49 | Just below boundary | Error |
| Speed = 2.01 | Just above boundary | Error |
| Pitch = -12 | Lower boundary inclusive | Accepted |
| Pitch = +12 | Upper boundary inclusive | Accepted |
| Pitch = 0 | Default / zero | Accepted |

### Concurrent / Timing

| Case | Expected |
|------|----------|
| Two rapid `text_to_speech` calls | Each generates a unique filename (UUID component). No file collision. |
| API times out after 30s | `httpx.TimeoutException` caught, network error message returned. |

---

## Test Data and Fixtures

### API Response Fixtures

```python
# fixtures/api_responses.py

VOICES_RESPONSE = [
    {
        "voice_id": "sujin-01",
        "name": "Sujin",
        "supported_languages": ["ko", "en"],
        "supported_styles": ["neutral", "happy", "sad", "angry"],
    },
    {
        "voice_id": "minho-01",
        "name": "Minho",
        "supported_languages": ["ko"],
        "supported_styles": ["neutral", "serious"],
    },
    {
        "voice_id": "yuki-01",
        "name": "Yuki",
        "supported_languages": ["ja", "en"],
        "supported_styles": ["neutral", "happy"],
    },
]

# Minimal valid MP3 binary (use a real tiny MP3 file as bytes fixture)
MOCK_AUDIO_MP3 = b"\xff\xfb\x90\x00" + b"\x00" * 256  # placeholder
MOCK_AUDIO_WAV = b"RIFF" + b"\x00" * 40  # placeholder

# Use actual tiny audio files in tests/fixtures/ for mutagen duration tests
```

### pytest Fixtures (conftest.py)

```python
# tests/conftest.py

import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def api_key_env(monkeypatch):
    """Set a fake API key in the environment."""
    monkeypatch.setenv("SUPERTONE_API_KEY", "test-api-key-do-not-use")

@pytest.fixture
def no_api_key_env(monkeypatch):
    """Ensure no API key is set."""
    monkeypatch.delenv("SUPERTONE_API_KEY", raising=False)

@pytest.fixture
def output_dir(tmp_path, monkeypatch):
    """Set output directory to a temporary path."""
    out = tmp_path / "tts-output"
    monkeypatch.setenv("SUPERTONE_OUTPUT_DIR", str(out))
    return out

@pytest.fixture
def readonly_dir(tmp_path, monkeypatch):
    """Create a read-only output directory."""
    out = tmp_path / "readonly"
    out.mkdir()
    out.chmod(0o444)
    monkeypatch.setenv("SUPERTONE_OUTPUT_DIR", str(out))
    yield out
    out.chmod(0o755)  # cleanup

@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for API call interception."""
    with patch("supertone_tts_mcp.supertone_client.httpx.AsyncClient") as mock_cls:
        client_instance = AsyncMock()
        mock_cls.return_value = client_instance
        yield client_instance

@pytest.fixture
def mock_successful_synthesis(mock_httpx_client):
    """Configure mock to return successful TTS response."""
    response = AsyncMock()
    response.status_code = 200
    response.content = b"\xff\xfb\x90\x00" + b"\x00" * 256
    response.headers = {"content-type": "audio/mpeg"}
    response.raise_for_status = lambda: None
    mock_httpx_client.post.return_value = response
    return mock_httpx_client

@pytest.fixture
def mock_successful_voices(mock_httpx_client):
    """Configure mock to return successful voices response."""
    response = AsyncMock()
    response.status_code = 200
    response.json.return_value = VOICES_RESPONSE  # from fixtures
    response.raise_for_status = lambda: None
    mock_httpx_client.get.return_value = response
    return mock_httpx_client
```

### Sensitive Data

- No real API keys in test code. Use obvious fake values: `"test-api-key-do-not-use"`.
- No `.env` files committed. Tests use `monkeypatch.setenv`.
- Audio fixture files are synthetic (generated, not recorded from real voices).

---

## Automation Candidates

### CI (every PR)

- All unit tests (`tests/test_tools.py`) -- validation logic, formatting, error messages.
- All integration tests (`tests/test_supertone_client.py`) -- mocked HTTP, error mapping.
- Integration tests for tool handlers end-to-end with mocked client.
- Linting: `ruff check .`
- Formatting: `black --check .`
- Coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Python version matrix: 3.11, 3.12, 3.13.

### Manual Verification (release only)

- MCP tool discovery from Claude Desktop (TC-082).
- Real API call with valid key -- generate audio and verify file plays correctly.
- Real API call from Cursor -- confirm both tools work.
- Verify `uvx supertone-tts-mcp` installs and starts without errors.
- Verify `pip install supertone-tts-mcp` installs correctly.

### Not Automated

- Accessibility audit: N/A (CLI tool, no UI).
- Performance benchmarks: Not justified for v1 (server overhead is negligible -- validation + file write).

---

## Test File Structure

```
tests/
  conftest.py                    # Shared fixtures
  fixtures/
    sample.mp3                   # Tiny valid MP3 for duration tests
    sample.wav                   # Tiny valid WAV for duration tests
  test_tools.py                  # Unit: validation, formatting, defaults
  test_supertone_client.py       # Integration: HTTP mocking, error mapping
  test_server.py                 # Integration: MCP tool registration, schemas
```

---

## Release Checklist (Smoke)

Execute in under 5 minutes with a real API key.

- [ ] `uvx supertone-tts-mcp` starts without error (server does not crash).
- [ ] In Claude Desktop, `text_to_speech(text="Hello world")` returns a file path and the file exists and plays audio.
- [ ] In Claude Desktop, `list_voices()` returns a numbered list of voices with IDs, languages, and styles.
- [ ] `text_to_speech` with no API key set returns the "SUPERTONE_API_KEY environment variable is not set" error (not a stack trace).
- [ ] `text_to_speech(text="")` returns "Text must not be empty." (not a stack trace).
- [ ] Generated audio file is saved in the configured output directory with the expected naming pattern.
