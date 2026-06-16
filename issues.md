# Issues: Supertone TTS MCP Server

> Generated: 2026-03-13
> Source: PRD, requirements.md, architecture.md, ux_spec.md, data_model.md

---

## Issue Index

| ID | Title | Priority | Estimate | Depends-On |
|----|-------|----------|----------|------------|
| ISSUE-001 | Scaffold project with uv, pyproject.toml, and src layout | P0 | 0.5d | none | done |
| ISSUE-002 | Define domain types, constants, and exception hierarchy | P0 | 0.5d | ISSUE-001 | done |
| ISSUE-003 | Implement SupertoneClient with synthesize and get_voices methods | P0 | 1d | ISSUE-002 | done |
| ISSUE-004 | Implement input validation and output formatting in tools module | P0 | 1d | ISSUE-002 | done |
| ISSUE-005 | Implement text_to_speech tool handler | P1 | 1d | ISSUE-003, ISSUE-004 | done |
| ISSUE-006 | Implement list_voices tool handler | P1 | 0.5d | ISSUE-003, ISSUE-004 | done |
| ISSUE-007 | Implement MCP server entry point and tool registration | P1 | 1d | ISSUE-005, ISSUE-006 | done |
| ISSUE-008 | Configure PyPI packaging and console entry point | P1 | 0.5d | ISSUE-007 | done |
| ISSUE-009 | Set up GitHub Actions CI pipeline | P1 | 0.5d | ISSUE-001 | done |
| ISSUE-010 | Write README and MCP client configuration docs | P2 | 0.5d | ISSUE-007 | done |
| ISSUE-011 | Create server.json and register on MCP Registry | P2 | 0.5d | ISSUE-008 | done |
| ISSUE-012 | ElevenLabs-style audio output modes (files/resources/both) | P1 | 0.5d | ISSUE-005 | done |
| ISSUE-013 | Update PRD/docs for v0.2 (voice discovery + cloning) | P0 | 0.5d | none | done |
| ISSUE-014 | Extend SupertoneClient with voice discovery methods | P0 | 0.5d | ISSUE-013 | done |
| ISSUE-015 | Replace `list_voices` with `search_voice` tool (breaking) | P1 | 0.5d | ISSUE-014 | done |
| ISSUE-016 | Add `get_voice` + `get_credit_balance` tools | P1 | 0.5d | ISSUE-014 | done |
| ISSUE-017 | Add `preview_voice` tool (returns sample URLs) | P1 | 0.5d | ISSUE-014, ISSUE-016 | done |
| ISSUE-018 | Add `predict_duration` tool (client + handler) | P1 | 0.5d | ISSUE-014 | done |
| ISSUE-019 | Add `clone_voice` tool (single file ≤3MB) | P1 | 1d | ISSUE-014 | done |
| ISSUE-020 | Custom voice CRUD tools (search/edit/delete) | P1 | 1d | ISSUE-019 | done |
| ISSUE-021 | SDK 0.2.3 sync: model enum + default + version pin | P0 | 0.5d | none | done |
| ISSUE-022 | Remove behavior env vars → per-call output_mode/autoplay (BREAKING) | P1 | 1d | ISSUE-021 | done |
| ISSUE-023 | Add streaming param + route synthesize vs stream + sona_speech_1-only validation | P1 | 1d | ISSUE-021, ISSUE-022 | done |
| ISSUE-024 | Relax 300-char hard limit → delegate to SDK auto-chunk | P2 | 0.5d | ISSUE-022 | done |
| ISSUE-025 | Expose include_phonemes + normalized_text TTS params | P2 | 0.5d | ISSUE-022 | done |
| ISSUE-026 | New tool get_custom_voice | P2 | 0.5d | ISSUE-021 | done |
| ISSUE-027 | New usage tools get_usage_history + get_voice_usage | P2 | 1d | ISSUE-021 | done |
| ISSUE-028 | Docs/README reframe + env→param migration + 0.2.0 release | P2 | 1d | ISSUE-021..ISSUE-027 | done |
| ISSUE-029 | Add merge_audio_files tool (ffmpeg-backed audio concatenation) | P2 | 1.5d | - | done |

---

### ISSUE-001: Scaffold project with uv, pyproject.toml, and src layout
- Track: platform
- PRD-Ref: FR-009, FR-010
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: none

#### Goal
The project has a working uv-managed Python project structure with all dependencies declared and the src layout created.

#### Scope (In/Out)
- In: `pyproject.toml` with metadata, dependencies (mcp, httpx, mutagen), dev dependencies (pytest, pytest-asyncio, pytest-cov), src/supertone_tts_mcp/ directory with `__init__.py`, tests/ directory with `__init__.py`, `.env.example`, `.gitignore`, console script entry point declaration
- Out: Implementation code, CI pipeline, README content

#### Acceptance Criteria (DoD)
- [ ] Given a fresh clone of the repo, when `uv sync` is run, then all dependencies install without error
- [ ] Given the project is initialized, when `uv run pytest -q` is run, then pytest executes successfully (0 tests collected, exit 0 or 5)
- [ ] Given `pyproject.toml` exists, when inspected, then it declares `name = "supertone-tts-mcp"`, `python >= 3.11`, dependencies `mcp`, `httpx`, `mutagen`, and dev dependencies `pytest`, `pytest-asyncio`, `pytest-cov`
- [ ] Given the src layout, when `src/supertone_tts_mcp/__init__.py` is inspected, then it contains `__version__ = "0.1.0"`
- [ ] Given `pyproject.toml`, when inspected, then a `[project.scripts]` entry maps `supertone-tts-mcp` to `supertone_tts_mcp.server:main`
- [ ] Given `.env.example` exists, when inspected, then it contains `SUPERTONE_API_KEY=your-api-key-here` and `SUPERTONE_OUTPUT_DIR=~/supertone-tts-output/` as placeholders only

#### Implementation Notes
- Use `uv init --python 3.11` then manually adjust pyproject.toml
- src layout: `src/supertone_tts_mcp/` per architecture.md
- Files to create: `pyproject.toml`, `src/supertone_tts_mcp/__init__.py`, `src/supertone_tts_mcp/server.py` (stub), `src/supertone_tts_mcp/tools.py` (stub), `src/supertone_tts_mcp/supertone_client.py` (stub), `tests/__init__.py`, `.env.example`, `.gitignore`
- Add `[tool.pytest.ini_options]` section per claude.md

#### Tests
- [ ] `uv sync` completes without error (manual verification)
- [ ] `uv run pytest -q` runs without import errors

#### Rollback
Delete generated files and revert pyproject.toml changes.

---

### ISSUE-002: Define domain types, constants, and exception hierarchy
- Track: platform
- PRD-Ref: FR-005, FR-006, FR-007, FR-008
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-001

#### Goal
All shared types (TTSRequest, TTSResponse, VoiceInfo, AppConfig), constants (validation ranges, defaults), and domain exceptions are defined and importable.

#### Scope (In/Out)
- In: Dataclasses (TTSRequest, TTSResponse, VoiceInfo, AppConfig), Literal types (Language, OutputFormat), constants (SPEED_MIN/MAX, PITCH_SHIFT_MIN/MAX, TEXT_MAX_LENGTH, SUPPORTED_LANGUAGES, SUPPORTED_FORMATS, DEFAULT_VOICE_ID, DEFAULT_LANGUAGE, DEFAULT_FORMAT, DEFAULT_SPEED, DEFAULT_PITCH_SHIFT, HTTP_TIMEOUT, SUPERTONE_BASE_URL), TypedDicts (SynthesizeRequestBody, VoiceDict), exception classes (SupertoneError hierarchy), `generate_output_path()` utility
- Out: Validation logic, HTTP calls, MCP integration

#### Acceptance Criteria (DoD)
- [ ] Given the module is imported, when `TTSRequest(text="hi", voice_id="v1", language="ko", output_format="mp3", speed=1.0, pitch_shift=0, style=None)` is constructed, then it creates a frozen dataclass instance with all fields accessible
- [ ] Given the constants module, when `TEXT_MAX_LENGTH` is accessed, then it equals 300
- [ ] Given the constants module, when `SPEED_MIN` and `SPEED_MAX` are accessed, then they equal 0.5 and 2.0 respectively
- [ ] Given `SupertoneServerError(502)` is raised, when caught, then `e.status_code` equals 502
- [ ] Given `generate_output_path("/tmp/out", "mp3")` is called, when the result is inspected, then the path matches pattern `/tmp/out/YYYY-MM-DD_XXXXXXXX.mp3` where X is hex chars

#### Implementation Notes
- Create `src/supertone_tts_mcp/models.py` for dataclasses and TypedDicts
- Create `src/supertone_tts_mcp/constants.py` for all constants and Literal types
- Create `src/supertone_tts_mcp/exceptions.py` for the exception hierarchy
- Add `generate_output_path()` to models.py or a separate utils.py
- Follow data_model.md exactly for field definitions
- DEFAULT_VOICE_ID is "TBD" pending API spike -- use a placeholder string

#### Tests
- [ ] Test TTSRequest construction with valid fields succeeds
- [ ] Test TTSRequest is frozen (assignment raises FrozenInstanceError)
- [ ] Test TTSResponse plain-text serialization matches UX spec format
- [ ] Test VoiceInfo plain-text serialization matches UX spec format
- [ ] Test generate_output_path returns correct pattern
- [ ] Test SupertoneServerError stores status_code
- [ ] Test SupertoneAPIError stores status_code and message
- [ ] Test all exception subclasses are instances of SupertoneError

#### Rollback
Remove models.py, constants.py, exceptions.py and their test files.

---

### ISSUE-003: Implement SupertoneClient with synthesize and get_voices methods
- Track: product
- PRD-Ref: FR-001, FR-002, FR-003, FR-007
- Priority: P0
- Estimate: 1d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-002

#### Goal
The SupertoneClient class wraps all Supertone API HTTP communication and translates HTTP errors into domain exceptions.

#### Scope (In/Out)
- In: `SupertoneClient.__init__(api_key, base_url)`, `async synthesize(voice_id, text, language, output_format, speed, pitch_shift, style) -> tuple[bytes, str]` (audio bytes + content_type), `async get_voices() -> list[VoiceDict]`, `async aclose()`, HTTP error-to-exception mapping (401/403 -> AuthError, 429 -> RateLimitError, 5xx -> ServerError, other 4xx -> APIError, connection/timeout -> ConnectionError)
- Out: Input validation (handled in tools.py), file saving, MCP registration

#### Acceptance Criteria (DoD)
- [ ] Given a valid API key and mocked 200 response with audio bytes, when `synthesize()` is called, then it returns the audio bytes and content type
- [ ] Given a valid API key and mocked 200 response with JSON voice list, when `get_voices()` is called, then it returns a list of VoiceDict objects
- [ ] Given a mocked 401 response, when `synthesize()` is called, then `SupertoneAuthError` is raised
- [ ] Given a mocked 429 response, when `get_voices()` is called, then `SupertoneRateLimitError` is raised
- [ ] Given a mocked 503 response, when `synthesize()` is called, then `SupertoneServerError` is raised with status_code 503
- [ ] Given a mocked connection timeout, when `synthesize()` is called, then `SupertoneConnectionError` is raised
- [ ] Given the client is constructed, when the request headers are inspected, then `x-sup-api-key` is set and the API key value is never in any log output

#### Implementation Notes
- File: `src/supertone_tts_mcp/supertone_client.py`
- Use `httpx.AsyncClient` with `timeout=30.0` (HTTP_TIMEOUT constant)
- POST body uses SynthesizeRequestBody TypedDict; omit `style` key when None
- Catch `httpx.ConnectError`, `httpx.TimeoutException` -> SupertoneConnectionError
- Map response status codes in a private `_handle_error_response()` method
- Base URL from constant: `https://api.supertoneapi.com`
- Test file: `tests/test_supertone_client.py`
- All tests use `pytest-asyncio` and mock httpx responses (no real network calls)

#### Tests
- [ ] Test synthesize() returns bytes on 200 with audio/mpeg content-type
- [ ] Test synthesize() sends correct POST path `/v1/text-to-speech/{voice_id}`
- [ ] Test synthesize() sends `x-sup-api-key` header
- [ ] Test synthesize() omits `style` from body when style is None
- [ ] Test synthesize() includes `style` in body when style is provided
- [ ] Test get_voices() returns parsed list on 200
- [ ] Test get_voices() sends GET to `/v1/voices`
- [ ] Test 401 raises SupertoneAuthError
- [ ] Test 403 raises SupertoneAuthError
- [ ] Test 429 raises SupertoneRateLimitError
- [ ] Test 500 raises SupertoneServerError with status_code=500
- [ ] Test connection error raises SupertoneConnectionError
- [ ] Test timeout raises SupertoneConnectionError
- [ ] Test aclose() closes the underlying httpx client

#### Rollback
Revert `supertone_client.py` and `tests/test_supertone_client.py`.

---

### ISSUE-004: Implement input validation and output formatting in tools module
- Track: product
- PRD-Ref: FR-003, FR-004, FR-005, FR-006, FR-008
- Priority: P0
- Estimate: 1d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-002

#### Goal
All input validation functions and output formatting functions exist in tools.py (or a helpers module) and produce the exact error messages and output text specified in the UX spec.

#### Scope (In/Out)
- In: `validate_text(text)`, `validate_language(language)`, `validate_output_format(fmt)`, `validate_speed(speed)`, `validate_pitch_shift(pitch)`, `resolve_api_key()`, `resolve_output_dir()`, `ensure_output_dir(path)`, `format_tts_response(TTSResponse) -> str`, `format_voice_list(voices, language_filter) -> str`, `calculate_duration(file_path) -> float`
- Out: MCP tool handler glue, HTTP calls, server registration

#### Acceptance Criteria (DoD)
- [ ] Given text is empty string, when `validate_text("")` is called, then it raises ValueError with message "Text must not be empty."
- [ ] Given text has 301 characters, when `validate_text(text)` is called, then it raises ValueError with message "Text exceeds the maximum length of 300 characters (received: 301). Please shorten or split the text manually."
- [ ] Given text has exactly 300 characters, when `validate_text(text)` is called, then no error is raised
- [ ] Given language is "zz", when `validate_language("zz")` is called, then it raises ValueError with message `Invalid language: "zz". Supported languages: ko, en, ja.`
- [ ] Given speed is 5.0, when `validate_speed(5.0)` is called, then it raises ValueError with message "Speed must be between 0.5 and 2.0 (received: 5.0)."
- [ ] Given pitch_shift is 15, when `validate_pitch_shift(15)` is called, then it raises ValueError with message "Pitch shift must be between -12 and +12 semitones (received: 15)."
- [ ] Given output_format is "ogg", when `validate_output_format("ogg")` is called, then it raises ValueError with message `Invalid output format: "ogg". Supported formats: mp3, wav.`
- [ ] Given SUPERTONE_API_KEY env var is not set, when `resolve_api_key()` is called, then it raises ValueError with message "SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings."
- [ ] Given SUPERTONE_OUTPUT_DIR is not set, when `resolve_output_dir()` is called, then it returns the expanded absolute path of `~/supertone-tts-output/`
- [ ] Given a TTSResponse object, when `format_tts_response()` is called, then it returns the exact plain-text format from UX spec section 4.1
- [ ] Given a list of VoiceInfo objects, when `format_voice_list()` is called, then it returns the numbered list format from UX spec section 4.2

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (validation and formatting functions)
- Error messages must match UX spec Section 4.1 error states exactly (copy-paste from spec)
- `resolve_output_dir()` uses `Path.expanduser().resolve()` to return absolute path
- `ensure_output_dir()` calls `os.makedirs(path, exist_ok=True)` and catches PermissionError
- `calculate_duration()` uses `mutagen` to parse audio file and return duration in seconds
- `format_tts_response()` produces multi-line plain text per UX spec
- `format_voice_list()` produces numbered list with blank-line separators per UX spec
- File paths in output must be absolute, no `~` (UX spec 6.2)
- Test file: `tests/test_tools.py`

#### Tests
- [ ] Test validate_text with empty string returns correct error message
- [ ] Test validate_text with 301 chars returns correct error message with count
- [ ] Test validate_text with 300 chars passes
- [ ] Test validate_text with 1 char passes
- [ ] Test validate_language with each valid value passes
- [ ] Test validate_language with invalid value returns correct error message
- [ ] Test validate_output_format with "mp3" and "wav" passes
- [ ] Test validate_output_format with "ogg" returns correct error message
- [ ] Test validate_speed at boundaries (0.5, 2.0) passes
- [ ] Test validate_speed out of range (0.4, 2.1) returns correct error messages
- [ ] Test validate_pitch_shift at boundaries (-12, 12) passes
- [ ] Test validate_pitch_shift out of range (-13, 13) returns correct error messages
- [ ] Test resolve_api_key returns key when env var is set
- [ ] Test resolve_api_key raises when env var is missing
- [ ] Test resolve_api_key raises when env var is empty string
- [ ] Test resolve_output_dir returns default when env var not set
- [ ] Test resolve_output_dir returns custom path when env var is set
- [ ] Test format_tts_response produces exact UX spec format
- [ ] Test format_voice_list with 2 voices produces numbered list
- [ ] Test format_voice_list with 0 voices and language filter produces "No voices found" message
- [ ] Test format_voice_list with 0 voices and no filter produces "No voices found" message
- [ ] Test calculate_duration returns float seconds for a valid audio file (use a tiny test fixture)

#### Rollback
Revert changes to `tools.py` and `tests/test_tools.py`.

---

### ISSUE-005: Implement text_to_speech tool handler
- Track: product
- PRD-Ref: FR-001, FR-005, FR-006, FR-007, FR-008, US-001, US-003, US-004, US-005, US-006
- Priority: P1
- Estimate: 1d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-003, ISSUE-004

#### Goal
The `text_to_speech` async function accepts parameters, validates them, calls SupertoneClient, saves the audio file, calculates duration, and returns a formatted plain-text response or error message.

#### Scope (In/Out)
- In: `async text_to_speech(text, voice_id?, language?, output_format?, speed?, pitch_shift?, style?) -> str` function that orchestrates validation, API call, file write, duration calculation, and response formatting. Error handling that catches all domain exceptions and returns UX-spec error messages.
- Out: MCP server registration (ISSUE-007), SupertoneClient implementation (ISSUE-003), validation functions (ISSUE-004)

#### Acceptance Criteria (DoD)
- [ ] Given valid parameters and a mocked API returning audio bytes, when `text_to_speech(text="Hello")` is called, then an audio file is written to the output directory and the response contains the absolute file path and duration in seconds
- [ ] Given voice_id is not provided, when `text_to_speech(text="Hello")` is called, then the default voice ID is used
- [ ] Given text exceeds 300 characters, when `text_to_speech(text=long_text)` is called, then the validation error message is returned without any API call being made
- [ ] Given the API returns 401, when `text_to_speech(text="Hello")` is called, then the response is "Authentication failed. Please verify your SUPERTONE_API_KEY."
- [ ] Given the API returns 429, when `text_to_speech(text="Hello")` is called, then the response is "Rate limit exceeded. Please wait and try again."
- [ ] Given a network error occurs, when `text_to_speech(text="Hello")` is called, then the response is "Failed to connect to Supertone API. Please check your network connection."
- [ ] Given the output directory cannot be created due to permissions, when `text_to_speech(text="Hello")` is called, then a clear permissions error is returned with the directory path
- [ ] Given the response, when the file path is inspected, then it is absolute (no `~`) and matches the naming pattern `{YYYY-MM-DD}_{uuid8hex}.{format}`

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (add the `text_to_speech` handler function)
- Orchestration flow per data_model.md "Pattern: text_to_speech"
- Catch ValueError from validation, SupertoneError subclasses from client, OSError from file writes
- All error paths return a string (not raise) -- MCP tools return text responses
- Use `generate_output_path()` from ISSUE-002
- Use `calculate_duration()` from ISSUE-004
- Use `format_tts_response()` from ISSUE-004
- Test file: `tests/test_tools.py` (extend)

#### Tests
- [ ] Test happy path: valid input -> file saved, response contains path and duration
- [ ] Test default voice_id is applied when omitted
- [ ] Test default language "ko" is applied when omitted
- [ ] Test default output_format "mp3" is applied when omitted
- [ ] Test default speed 1.0 and pitch_shift 0 are applied when omitted
- [ ] Test validation error for empty text returns error string (not exception)
- [ ] Test validation error for invalid language returns error string
- [ ] Test SupertoneAuthError is caught and formatted correctly
- [ ] Test SupertoneRateLimitError is caught and formatted correctly
- [ ] Test SupertoneServerError is caught and formatted with status code
- [ ] Test SupertoneConnectionError is caught and formatted correctly
- [ ] Test PermissionError on output dir is caught and formatted correctly
- [ ] Test file is written with correct bytes from API response

#### Rollback
Revert text_to_speech handler code and related tests.

---

### ISSUE-006: Implement list_voices tool handler
- Track: product
- PRD-Ref: FR-002, FR-007, US-002, US-003, US-007
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-003, ISSUE-004

#### Goal
The `list_voices` async function accepts an optional language filter, calls SupertoneClient, filters results, and returns a formatted plain-text voice list or error message.

#### Scope (In/Out)
- In: `async list_voices(language?) -> str` function that validates language filter, calls `get_voices()`, filters by language, and formats the result using `format_voice_list()`. Error handling for domain exceptions.
- Out: MCP server registration (ISSUE-007)

#### Acceptance Criteria (DoD)
- [ ] Given a mocked API returning 3 voices, when `list_voices()` is called with no filter, then the response contains all 3 voices in numbered list format
- [ ] Given a mocked API returning 3 voices (2 Korean, 1 Japanese), when `list_voices(language="ko")` is called, then only the 2 Korean voices are returned
- [ ] Given a mocked API returning 0 voices, when `list_voices()` is called, then the response is "No voices found." (not an error)
- [ ] Given language filter is "zz", when `list_voices(language="zz")` is called, then the validation error message is returned
- [ ] Given the API returns 401, when `list_voices()` is called, then the response is "Authentication failed. Please verify your SUPERTONE_API_KEY."

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (add the `list_voices` handler function)
- Filtering: iterate voices, check if `language` is in `voice.supported_languages`
- Use `format_voice_list()` from ISSUE-004
- Catch ValueError from validation, SupertoneError subclasses from client
- Test file: `tests/test_tools.py` (extend)

#### Tests
- [ ] Test happy path: no filter returns all voices formatted
- [ ] Test language filter returns only matching voices
- [ ] Test empty result returns "No voices found" message
- [ ] Test invalid language filter returns error string
- [ ] Test SupertoneAuthError is caught and formatted correctly
- [ ] Test SupertoneConnectionError is caught and formatted correctly

#### Rollback
Revert list_voices handler code and related tests.

---

### ISSUE-007: Implement MCP server entry point and tool registration
- Track: product
- PRD-Ref: FR-009, NFR-002
- Priority: P1
- Estimate: 1d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-005, ISSUE-006

#### Goal
The MCP server starts via `supertone-tts-mcp` command, registers both tools with correct schemas, and handles tool calls over stdio transport.

#### Scope (In/Out)
- In: `server.py` with `main()` function that creates MCP Server instance, registers `text_to_speech` and `list_voices` as tools with parameter schemas and descriptions matching UX spec, runs stdio transport. Tool descriptions and parameter descriptions must match UX spec Section 2.1 and 2.2 exactly.
- Out: PyPI publishing, CI pipeline

#### Acceptance Criteria (DoD)
- [ ] Given the package is installed, when `supertone-tts-mcp` command is run, then the MCP server starts and listens on stdio
- [ ] Given the server is running, when a `tools/list` request is sent, then both `text_to_speech` and `list_voices` are returned with correct schemas
- [ ] Given the server is running, when the `text_to_speech` tool schema is inspected, then the description matches UX spec: "Convert text to speech using Supertone TTS API. Saves the audio file locally and returns the file path and duration. Supports Korean, English, and Japanese. Maximum 300 characters per call."
- [ ] Given the server is running, when the `list_voices` tool schema is inspected, then the description matches UX spec: "List available Supertone TTS voices. Returns voice ID, name, supported languages, and supported emotion styles for each voice. Optionally filter by language."
- [ ] Given a `text_to_speech` tool call with `{"text": "Hello"}`, when processed, then the `text_to_speech` handler from tools.py is invoked and the result is returned
- [ ] Given the server, when `python -m supertone_tts_mcp` is run, then the server also starts (alternative entry point)

#### Implementation Notes
- File: `src/supertone_tts_mcp/server.py`
- Use MCP Python SDK: `from mcp.server import Server` and `server.run_stdio()`
- Register tools using `@server.tool()` decorator or `server.add_tool()` method
- Parameter schemas must include types, descriptions, required fields, enums, and ranges
- `text` parameter is required; all others are optional with defaults
- Add `__main__.py` for `python -m` support
- Logging to stderr (stdout reserved for MCP protocol)
- Test file: `tests/test_server.py`
- Integration test: can use MCP SDK test client or mock stdio

#### Tests
- [ ] Test server registers exactly 2 tools
- [ ] Test text_to_speech tool schema has correct parameter names and types
- [ ] Test text_to_speech tool has `text` marked as required
- [ ] Test list_voices tool schema has `language` as optional parameter
- [ ] Test tool descriptions match UX spec exactly
- [ ] Test main() function is callable without error (with mocked stdio)
- [ ] Test __main__.py module exists and calls main()

#### Rollback
Revert `server.py`, `__main__.py`, and `tests/test_server.py`.

---

### ISSUE-008: Configure PyPI packaging and console entry point
- Track: platform
- PRD-Ref: FR-010, NFR-001
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-007

#### Goal
The package builds successfully with `uv build` and the resulting distribution installs with `pip install` and makes the `supertone-tts-mcp` command available.

#### Scope (In/Out)
- In: Complete pyproject.toml metadata (name, version, description, author, license, URLs, classifiers, python-requires), verify `[project.scripts]` entry, `uv build` produces working sdist and wheel, verify `pip install dist/*.whl` makes `supertone-tts-mcp` command available
- Out: Actual PyPI publishing (manual step), CI publish workflow (ISSUE-009)

#### Acceptance Criteria (DoD)
- [ ] Given the project, when `uv build` is run, then a `.whl` and `.tar.gz` are created in `dist/`
- [ ] Given the built wheel, when installed with `pip install dist/*.whl` in a fresh venv, then `supertone-tts-mcp` command is available and starts the server
- [ ] Given pyproject.toml, when inspected, then it contains: description, author, license (MIT), python_requires >= 3.11, project URLs (repository, homepage)
- [ ] Given pyproject.toml, when inspected, then classifiers include Python 3.11, 3.12, 3.13

#### Implementation Notes
- Update pyproject.toml with full metadata
- Verify console_scripts entry works end-to-end
- Test with `uv build` then local install
- Add `long_description` pointing to README.md with content-type text/markdown

#### Tests
- [ ] `uv build` succeeds without error (manual verification)
- [ ] Local wheel install creates working `supertone-tts-mcp` command (manual verification)

#### Rollback
Revert pyproject.toml metadata changes.

---

### ISSUE-009: Set up GitHub Actions CI pipeline
- Track: platform
- PRD-Ref: NFR-005, NFR-006
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-001

#### Goal
A GitHub Actions workflow runs tests on push and PR across Python 3.11, 3.12, and 3.13, and a publish job triggers on version tags.

#### Scope (In/Out)
- In: `.github/workflows/ci.yml` with test matrix (3.11, 3.12, 3.13), `uv sync` + `uv run pytest -q --cov=src --cov-report=term-missing`, publish job on `v*` tags using `uv build` + `uv publish`
- Out: Actual PyPI token setup (manual), MCP registry steps

#### Acceptance Criteria (DoD)
- [ ] Given a push to any branch, when GitHub Actions runs, then the test job executes on Python 3.11, 3.12, and 3.13
- [ ] Given the CI workflow, when the test step is inspected, then it runs `uv sync` followed by `uv run pytest -q --cov=src --cov-report=term-missing`
- [ ] Given a tag matching `v*` is pushed, when GitHub Actions runs, then the publish job builds and publishes to PyPI using `UV_PUBLISH_TOKEN` secret
- [ ] Given the publish job, when inspected, then it depends on the test job passing (needs: test)

#### Implementation Notes
- File: `.github/workflows/ci.yml`
- Use `actions/checkout@v4` and `astral-sh/setup-uv@v4`
- Per architecture.md CI/CD Pipeline Outline
- Publish step uses `UV_PUBLISH_TOKEN` from repository secrets

#### Tests
- [ ] CI YAML is valid (use actionlint or manual review)
- [ ] Workflow triggers on push and pull_request events

#### Rollback
Delete `.github/workflows/ci.yml`.

---

### ISSUE-010: Write README and MCP client configuration docs
- Track: product
- PRD-Ref: FR-009, NFR-001, NFR-002
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-007

#### Goal
The README.md contains installation instructions, Claude Desktop and Cursor configuration examples, usage examples, and environment variable documentation.

#### Scope (In/Out)
- In: README.md with: project description, features list, installation (`uvx supertone-tts-mcp`, `pip install supertone-tts-mcp`), Claude Desktop config JSON example (from PRD 8.4), Cursor config example, environment variables table (SUPERTONE_API_KEY, SUPERTONE_OUTPUT_DIR), usage examples, license
- Out: MCP registry registration (ISSUE-011)

#### Acceptance Criteria (DoD)
- [ ] Given the README, when inspected, then it contains a working Claude Desktop configuration JSON with `"command": "uvx"` and `"args": ["supertone-tts-mcp"]`
- [ ] Given the README, when inspected, then it documents both environment variables with their defaults and descriptions
- [ ] Given the README, when inspected, then it includes at least one usage example showing a natural language prompt and expected output
- [ ] Given the README, when inspected, then it lists supported languages (ko, en, ja) and parameter ranges

#### Implementation Notes
- Include the `mcp-name: io.github.pillip/supertone-tts` metadata line for MCP Registry
- Reference PRD Section 8.4 for Claude Desktop config format
- Keep it concise -- developers are the audience

#### Tests
- [ ] README renders correctly on GitHub (manual verification)
- [ ] All code blocks in README use correct syntax highlighting tags

#### Rollback
Revert README.md changes.

---

### ISSUE-011: Create server.json and register on MCP Registry
- Track: product
- PRD-Ref: FR-011
- Priority: P2
- Estimate: 0.5d
- Status: done
- Manual: false
- Owner:
- Branch: feat/mcp-registry-publish
- GH-Issue:
- PR: #26
- Depends-On: ISSUE-008

#### Goal
The server is registered and searchable on the official MCP Registry. Aggregators (PulseMCP, GitHub MCP Registry) now ingest from the official registry, so a single publish propagates to community directories.

#### Scope (In/Out)
- In: `server.json` (schema `2025-12-11`) with name `io.github.supertone-inc/supertone-mcp`, description, version, and PyPI package reference (`registryType: pypi`, identifier `supertone-mcp`). `mcp-name` ownership marker in README. Automated `mcp-publisher publish` via GitHub Actions (OIDC) on release tags.
- Out: Ongoing maintenance of registry listings; manual PulseMCP self-registration (now covered by aggregation)

#### Acceptance Criteria (DoD)
- [x] Given `server.json`, when validated against the `2025-12-11` server schema, then it passes validation
- [x] Given `server.json`, when inspected, then the name is `io.github.supertone-inc/supertone-mcp` and the package identifier is `supertone-mcp` with `registryType: pypi`
- [x] Given the README, when inspected, then it contains the `mcp-name: io.github.supertone-inc/supertone-mcp` marker (carried into the PyPI description for ownership verification)
- [x] Given a `v*` tag is pushed, when the `publish-registry` CI job runs, then it authenticates via GitHub OIDC and publishes to the MCP Registry after PyPI indexing
- [x] Given `mcp-publisher publish` succeeds, when the MCP Registry is searched for "supertone", then the server appears in results

#### Implementation Notes
- File: `server.json` in project root (schema `2025-12-11`, camelCase fields: `registryType`, `environmentVariables`, `transport`)
- Namespace verified via GitHub OIDC (repo under `supertone-inc` org → `io.github.supertone-inc/*`); no secret required
- PyPI ownership verified by `mcp-name` marker in README → published package description
- Automated in `.github/workflows/ci.yml` `publish-registry` job (`needs: publish`, `id-token: write`)
- This issue was blocked until PyPI publishing (ISSUE-008) — now complete

#### Tests
- [x] server.json is valid JSON matching the schema (validated via check-jsonschema)
- [x] Server is searchable on MCP Registry (verified: `io.github.supertone-inc/supertone-mcp` v0.1.1 active, published 2026-05-27)

#### Rollback
Remove server.json + `publish-registry` job, contact MCP Registry to delist if needed.

---

### ISSUE-012: ElevenLabs-style audio output modes (files/resources/both)
- Track: product
- PRD-Ref: FR-001
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-005

#### Goal
LLM 클라이언트(Claude Desktop, Cursor 등)가 오디오를 직접 재생할 수 있도록, ElevenLabs MCP처럼 3가지 출력 모드를 지원한다. 환경변수 `SUPERTONE_MCP_OUTPUT_MODE`로 제어한다.

#### Scope (In/Out)
- In: `constants.py`에 출력 모드 상수 추가, `tools.py`에 `resolve_output_mode()` / `format_tts_metadata()` 추가, `text_to_speech()` 반환 타입을 `str | list`로 변경하여 `AudioContent` + `TextContent` 반환 지원, `server.py` tool description 업데이트, 테스트 추가
- Out: MCP 클라이언트 측 재생 구현

#### Output Modes

| Mode | Behavior | Return Type |
|------|----------|-------------|
| `files` (default) | 디스크 저장, 경로 반환 | `str` (TextContent) |
| `resources` | 디스크 저장 없음, 오디오 데이터 직접 반환 | `list` — AudioContent + TextContent(메타) |
| `both` | 디스크 저장 + 오디오 데이터 반환 | `list` — AudioContent + TextContent(경로+메타) |

#### Acceptance Criteria (DoD)
- [x] Given `SUPERTONE_MCP_OUTPUT_MODE` is unset or `"files"`, when `text_to_speech()` is called, then behavior is identical to before (disk save + text response)
- [x] Given `SUPERTONE_MCP_OUTPUT_MODE=resources`, when `text_to_speech()` is called, then no file is written to disk and `[AudioContent, TextContent]` is returned
- [x] Given `SUPERTONE_MCP_OUTPUT_MODE=both`, when `text_to_speech()` is called, then a file is saved to disk and `[AudioContent, TextContent]` is returned with file path in metadata
- [x] Given an invalid output mode, when `text_to_speech()` is called, then a validation error string is returned
- [x] Given `resources` mode with `output_format="wav"`, when the result is inspected, then `AudioContent.mimeType` is `"audio/wav"`
- [x] Given `resources` mode, when the AudioContent data is base64-decoded, then it matches the original audio bytes

#### Implementation Notes
- MCP SDK의 `AudioContent` 타입 사용 (`from mcp.types import AudioContent, TextContent`)
- `resolve_output_mode()`는 환경변수를 읽고 소문자로 변환 후 검증
- `format_tts_metadata()`는 `"Duration: 2.3s | Voice: v1 | Language: ko | Format: mp3"` 형태의 간결한 메타 텍스트 생성
- `files` 모드 외에는 `output_dir` resolve/create를 건너뜀

#### Tests
- [x] `TestResolveOutputMode`: default, valid modes, case-insensitive, invalid mode
- [x] `TestFormatTtsMetadata`: with/without file path
- [x] `TestTextToSpeechHandler`: resources mode returns AudioContent, no file written, both mode saves + returns AudioContent, WAV mime type, invalid mode error, base64 encoding correctness

#### Rollback
Revert changes to constants.py, tools.py, server.py, test_tools.py, test_server.py.

---

### ISSUE-013: Update PRD/docs for v0.2 (voice discovery + cloning)
- Track: platform
- PRD-Ref: PRD §3, §6, §11
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-013-v02-docs
- GH-Issue:
- PR: #10
- Depends-On: none

#### Goal
Project documents reflect the v0.2 scope: voice discovery (search_voice, get_voice, get_credit_balance, preview_voice), duration prediction (predict_duration), and voice cloning CRUD (clone_voice, search/edit/delete_custom_voice). The follow-up implementation issues (ISSUE-014~020) can reference concrete FR numbers.

#### Scope (In/Out)
- In: PRD.md updates (move clone_voice and predict_duration out of §3 Non-Goals into §6 FRs; assign FR-012~FR-019 to new tools; add user stories US-008~US-011; update §11 Future Considerations accordingly), `docs/requirements.md` regenerated/extended for new FRs, `docs/architecture.md` note on `custom_voices` and `usage` SDK modules, `docs/ux_spec.md` text/error message specs for each new tool, STATUS.md reset to "M4: v0.2 implementation"
- Out: Any code changes, test files

#### Acceptance Criteria (DoD)
- [ ] Given PRD.md, when §3 is inspected, then voice cloning and duration prediction are no longer listed as Non-Goals
- [ ] Given PRD.md, when §6 is inspected, then FR-012 (search_voice), FR-013 (get_voice), FR-014 (get_credit_balance), FR-015 (preview_voice), FR-016 (predict_duration), FR-017 (clone_voice), FR-018 (search_custom_voice), FR-019 (edit/delete_custom_voice) are documented with input/output specs
- [ ] Given PRD.md, when §5 is inspected, then user stories US-008 (search/preview voices to choose one), US-009 (check credits before TTS), US-010 (predict duration), US-011 (clone and manage custom voices) are listed
- [ ] Given `docs/ux_spec.md`, when inspected, then it contains exact tool descriptions and error message text for each new tool
- [ ] Given a `docs(claude)` commit, when inspected, then it follows the claude.md sync rule

#### Implementation Notes
- Use existing PRD style/structure; do not invent new sections
- Cross-reference SDK methods discovered during API verification (`voices.search_voices_async`, etc.)
- Keep clone_voice constraints explicit: WAV/MP3, ≤3MB, single file
- `preview_voice` returns sample URL(s); no autoplay in v0.2
- delete_custom_voice has no confirm gate at this stage (per product decision)

#### Tests
- [ ] PRD-Ref forward references in ISSUE-014~020 resolve to actual FR numbers after this issue is merged (manual verification)

#### Rollback
Revert PRD.md, docs/*.md, STATUS.md changes.

---

### ISSUE-014: Extend SupertoneClient with voice discovery methods
- Track: product
- PRD-Ref: FR-012, FR-013, FR-014
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-014-client-voice-discovery
- GH-Issue: #11
- PR: #12
- Depends-On: ISSUE-013

#### Goal
`SupertoneClient` exposes `search_voices()`, `get_voice()`, and `get_credit_balance()` async methods that wrap the corresponding SDK calls with consistent error handling.

#### Scope (In/Out)
- In: New methods on `SupertoneClient`: `async search_voices(name?, description?, language?, gender?, age?, use_case?, style?, model?) -> list[VoiceDict]` (auto-paginates), `async get_voice(voice_id) -> VoiceDetailDict` (new TypedDict with samples/models/styles/use_cases/thumbnail), `async get_credit_balance() -> CreditBalanceDict`. New TypedDicts in `models.py` (VoiceDetailDict, SampleDict, CreditBalanceDict). Error mapping reuses existing `_handle_sdk_errors`.
- Out: Tool handlers (ISSUE-015~016), formatting functions

#### Acceptance Criteria (DoD)
- [ ] Given a mocked SDK returning a paginated voice list, when `search_voices(gender="female")` is called, then all pages are concatenated and returned as `list[VoiceDict]`
- [ ] Given a mocked SDK 200 response for a single voice, when `get_voice("v1")` is called, then a `VoiceDetailDict` with `samples`, `models`, `styles`, `use_cases`, `thumbnail_image_url` is returned
- [ ] Given a mocked SDK 401 on any of the three methods, when called, then `SupertoneAuthError` is raised
- [ ] Given a mocked SDK 429 on any method, when called, then `SupertoneRateLimitError` is raised
- [ ] Given `models.py`, when `VoiceDetailDict` is imported, then it includes typed fields matching the SDK `GetCharacterByIDResponse` shape

#### Implementation Notes
- File: `src/supertone_tts_mcp/supertone_client.py` (extend)
- SDK methods: `voices.search_voices_async`, `voices.get_voice_async`, `usage.get_credit_balance_async`
- `search_voices` filter params are all `Optional[str]` per SDK signature — pass-through
- Pagination loop pattern same as existing `get_voices`
- Add new TypedDicts to `models.py` (do not modify existing `VoiceDict` to preserve `list_voices` until ISSUE-015 removes it)
- Test file: `tests/test_supertone_client.py` (extend)

#### Tests
- [ ] Test search_voices pagination concatenates pages
- [ ] Test search_voices passes all filter params through to SDK
- [ ] Test get_voice returns full detail dict
- [ ] Test get_credit_balance returns balance dict
- [ ] Test 401/403 raises SupertoneAuthError on each method
- [ ] Test 429 raises SupertoneRateLimitError on each method
- [ ] Test 5xx raises SupertoneServerError on each method
- [ ] Test connection error raises SupertoneConnectionError on each method

#### Rollback
Revert SupertoneClient additions and corresponding tests; revert new TypedDicts in models.py.

---

### ISSUE-015: Replace `list_voices` with `search_voice` tool (breaking)
- Track: product
- PRD-Ref: FR-012, US-008
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-015-search-voice
- GH-Issue: https://github.com/pillip/supertone-mcp/issues/13
- PR: https://github.com/pillip/supertone-mcp/pull/14
- Depends-On: ISSUE-014

#### Goal
The `list_voices` tool is removed and replaced by `search_voice`, which accepts server-side filters (language, gender, age, use_case, style, model, name, description) and returns a formatted voice list. Without filters, behavior is equivalent to the old `list_voices`.

#### Scope (In/Out)
- In: New `async search_voice(language?, gender?, age?, use_case?, style?, model?, name?, description?) -> str` tool handler in `tools.py`; removal of `list_voices` handler; updated/extended `format_voice_list()` to include filter summary line; server registration replaces `list_voices` with `search_voice` (with full parameter schema and description); README updated; tests for `list_voices` removed; new tests for `search_voice`
- Out: get_voice (ISSUE-016), preview_voice (ISSUE-017)

#### Acceptance Criteria (DoD)
- [ ] Given the package, when `tools/list` is queried, then `list_voices` is NOT registered and `search_voice` IS registered
- [ ] Given `search_voice()` with no parameters, when called against a mocked SDK returning 3 voices, then all 3 are returned in numbered list format
- [ ] Given `search_voice(gender="female", language="ko")`, when called, then the underlying SDK call receives both filters and the response shows the active filters in the header line
- [ ] Given the API returns 0 results, when `search_voice(gender="zzz")` is called, then the response is `"No voices found matching the filters."`
- [ ] Given the API returns 401, when `search_voice()` is called, then the auth error string is returned
- [ ] Given the server is running, when the `search_voice` tool description is inspected, then it matches the UX spec (per ISSUE-013)

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` — remove `list_voices`, add `search_voice`
- File: `src/supertone_tts_mcp/server.py` — replace tool registration
- Filter values are passed through; do not validate enum membership client-side (SDK/API authoritative). EXCEPT keep `validate_language` if language is provided
- `format_voice_list` extended: if any filter is non-None, prefix output with `Filters applied: {k=v, ...}` line
- Update README.md examples
- Test files: `tests/test_tools.py`, `tests/test_server.py` — delete list_voices tests, add search_voice tests

#### Tests
- [ ] Test search_voice with no filters returns all voices
- [ ] Test search_voice with single filter passes it to client
- [ ] Test search_voice with multiple filters passes all to client
- [ ] Test search_voice empty result returns "No voices found matching the filters."
- [ ] Test search_voice 401 returns auth error string
- [ ] Test server registers `search_voice` and NOT `list_voices`
- [ ] Test format_voice_list shows filter summary header when filters are active

#### Rollback
Restore `list_voices` handler/tests; revert server registration; revert README.

---

### ISSUE-016: Add `get_voice` + `get_credit_balance` tools
- Track: product
- PRD-Ref: FR-013, FR-014, US-008, US-009
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-016-get-voice-and-balance
- GH-Issue: https://github.com/pillip/supertone-mcp/issues/15
- PR: https://github.com/pillip/supertone-mcp/pull/16
- Depends-On: ISSUE-014

#### Goal
Two small inspection tools are added: `get_voice(voice_id)` returns full voice detail (description, age, gender, use_cases, languages, styles, models, sample URLs, thumbnail), and `get_credit_balance()` returns the current credit balance.

#### Scope (In/Out)
- In: `async get_voice(voice_id: str) -> str` and `async get_credit_balance() -> str` handlers in `tools.py`, new `format_voice_detail(VoiceDetailDict) -> str` and `format_credit_balance(CreditBalanceDict) -> str` formatters, server registration for both tools, tests
- Out: preview_voice (ISSUE-017)

#### Acceptance Criteria (DoD)
- [ ] Given a mocked client returning a voice detail, when `get_voice("v1")` is called, then the response includes voice_id, name, description, age, gender, use_cases (joined), languages (joined), styles (joined), models (joined), and sample count
- [ ] Given `get_voice("")` or whitespace, when called, then a validation error string is returned without an API call
- [ ] Given a mocked client raising `SupertoneAuthError`, when `get_voice("v1")` is called, then the auth error string is returned
- [ ] Given a mocked client returning a credit balance, when `get_credit_balance()` is called, then the response includes the numeric balance and (if present) plan/expiry info
- [ ] Given the server is running, when `tools/list` is queried, then both `get_voice` and `get_credit_balance` are registered

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (add 2 handlers + 2 formatters)
- File: `src/supertone_tts_mcp/server.py` (register both)
- `format_voice_detail` is multi-line plain text; do NOT include sample URLs in this formatter (URLs are surfaced via `preview_voice` in ISSUE-017)
- `format_credit_balance` is single-line: e.g. `Credit balance: 12,345 chars remaining.`
- Validate `voice_id` is non-empty string in `get_voice`
- Test file: `tests/test_tools.py`, `tests/test_server.py`

#### Tests
- [ ] Test get_voice happy path returns formatted detail
- [ ] Test get_voice with empty voice_id returns validation error string
- [ ] Test get_voice auth/connection errors return formatted error strings
- [ ] Test get_credit_balance happy path returns formatted balance
- [ ] Test get_credit_balance auth/connection errors return formatted error strings
- [ ] Test server registers both tools with correct schemas

#### Rollback
Revert tools.py additions, server.py registrations, and related tests.

---

### ISSUE-017: Add `preview_voice` tool (returns sample URLs)
- Track: product
- PRD-Ref: FR-015, US-008
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: feat/ISSUE-017-preview-voice
- GH-Issue: https://github.com/pillip/supertone-mcp/issues/17
- PR: https://github.com/pillip/supertone-mcp/pull/18
- Depends-On: ISSUE-014, ISSUE-016

#### Goal
`preview_voice(voice_id, language?, style?, model?)` returns matching sample audio URLs from the voice's `samples` array so users (or the client) can listen to a preview before choosing a voice.

#### Scope (In/Out)
- In: `async preview_voice(voice_id, language?, style?, model?) -> str` handler that calls `get_voice()` under the hood and filters the `samples` array; new `format_voice_samples(samples, filters) -> str` formatter; server registration; tests
- Out: Local autoplay (deferred to a future `play_audio_url` tool)

#### Acceptance Criteria (DoD)
- [ ] Given a voice with 4 samples and no filters, when `preview_voice("v1")` is called, then all 4 sample URLs are returned with their language/style/model metadata
- [ ] Given a voice and `language="ko"`, when called, then only Korean samples are returned
- [ ] Given a voice and `language="ko", style="happy"`, when called, then samples matching both are returned
- [ ] Given filters that match nothing, when called, then `"No matching samples for the given filters."` is returned
- [ ] Given a voice with no samples at all (samples is None or []), when called, then `"This voice has no preview samples."` is returned
- [ ] Given an empty voice_id, when called, then a validation error string is returned
- [ ] Given auth/connection errors, when called, then the appropriate formatted error string is returned

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (add handler + formatter)
- File: `src/supertone_tts_mcp/server.py` (register tool)
- `format_voice_samples` output (one per line):
  ```
  1. [language=ko, style=happy, model=sona_speech_1] https://.../sample.wav
  ```
- Reuse `get_voice` from ISSUE-016 (call the SDK once to fetch voice detail, then filter `samples`)
- Test file: `tests/test_tools.py`, `tests/test_server.py`

#### Tests
- [ ] Test preview_voice with no filter returns all samples
- [ ] Test preview_voice with each filter dimension narrows results correctly
- [ ] Test preview_voice with combined filters narrows correctly
- [ ] Test preview_voice empty samples returns "no preview samples" message
- [ ] Test preview_voice no-match filter returns "no matching samples" message
- [ ] Test preview_voice empty voice_id returns validation error
- [ ] Test preview_voice auth/connection errors are formatted

#### Rollback
Revert tools.py additions, server.py registration, and related tests.

---

### ISSUE-018: Add `predict_duration` tool (client + handler)
- Track: product
- PRD-Ref: FR-016, US-010
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-018-predict-duration
- GH-Issue: https://github.com/pillip/supertone-mcp/issues/19
- PR: https://github.com/pillip/supertone-mcp/pull/20
- Depends-On: ISSUE-014

#### Goal
`predict_duration(text, voice_id?, language?, model?, output_format?, speed?, pitch_shift?, style?)` calls the Supertone duration prediction API and returns the predicted audio length in seconds, which is proportional to credit consumption.

#### Scope (In/Out)
- In: New `async predict_duration(...)` method on `SupertoneClient` wrapping `text_to_speech.predict_duration_async`, new `async predict_duration(...)` tool handler in `tools.py`, validation reuse (text/language/speed/pitch_shift/output_format), server registration, tests
- Out: Cost-in-currency calculation (only seconds; the response wording notes proportionality to credits)

#### Acceptance Criteria (DoD)
- [ ] Given valid params and a mocked client returning duration=2.34, when `predict_duration(text="hi")` is called, then the response is `"Predicted duration: 2.34s (credit usage is proportional to duration)."`
- [ ] Given text >300 chars, when called, then the validation error string is returned without an API call
- [ ] Given invalid speed/pitch/language/format, when called, then the matching validation error is returned
- [ ] Given the API returns 401, when called, then the auth error string is returned
- [ ] Given the API returns 429, when called, then the rate limit error string is returned
- [ ] Given the server, when `tools/list` is queried, then `predict_duration` is registered with the same parameter schema as `text_to_speech` except no `output_format` defaulting differences

#### Implementation Notes
- File: `src/supertone_tts_mcp/supertone_client.py` (add method)
- File: `src/supertone_tts_mcp/tools.py` (add handler)
- File: `src/supertone_tts_mcp/server.py` (register)
- Default voice_id uses the same env-var resolution as `text_to_speech` (`SUPERTONE_VOICE_ID`)
- Default model: `sona_speech_1` (SDK default)
- Default output_format: `wav` (SDK default; duration is format-agnostic in practice but match SDK)
- Test files: `tests/test_supertone_client.py`, `tests/test_tools.py`, `tests/test_server.py`

#### Tests
- [ ] Test SDK method wrapper passes all params through
- [ ] Test handler happy path returns formatted duration
- [ ] Test handler text-length validation
- [ ] Test handler speed/pitch/language/format validation
- [ ] Test handler default voice_id resolution
- [ ] Test handler auth/rate/connection errors are formatted
- [ ] Test server registers predict_duration

#### Rollback
Revert client method, tool handler, server registration, and tests.

---

### ISSUE-019: Add `clone_voice` tool (single file ≤3MB)
- Track: product
- PRD-Ref: FR-017, US-011
- Priority: P1
- Estimate: 1d
- Status: done
- Owner:
- Branch: feat/ISSUE-019-clone-voice
- GH-Issue: #21
- PR: #22
- Depends-On: ISSUE-014

#### Goal
`clone_voice(name, audio_path, description?)` creates a custom (cloned) voice from a local audio file (WAV or MP3, ≤3MB) and returns the new custom voice ID.

#### Scope (In/Out)
- In: New `async create_cloned_voice(name, audio_bytes, file_name, content_type, description?) -> dict` method on `SupertoneClient` wrapping `custom_voices.create_cloned_voice_async`, new `async clone_voice(name, audio_path, description?) -> str` tool handler that reads the file, validates extension/size, builds the SDK `Files` payload, and calls the client. Validation functions (`validate_audio_path`, `validate_audio_file_size`) in tools.py. Server registration. Tests.
- Out: Multi-file clone (single only per product decision), custom voice browsing/editing (ISSUE-020)

#### Acceptance Criteria (DoD)
- [ ] Given a valid local WAV file ≤3MB and `clone_voice(name="MyVoice", audio_path=path)`, when called, then the file is read, sent to the SDK, and the new voice_id is returned in a formatted response
- [ ] Given `audio_path` pointing to a non-existent file, when called, then `"Audio file not found: {path}"` is returned without an API call
- [ ] Given `audio_path` with an unsupported extension (e.g. `.ogg`), when called, then `"Unsupported audio format. Supported: WAV, MP3."` is returned without an API call
- [ ] Given an audio file >3MB, when called, then `"Audio file too large: {size_mb:.2f}MB. Maximum: 3MB."` is returned without an API call
- [ ] Given `name=""` or whitespace, when called, then `"Voice name must not be empty."` is returned without an API call
- [ ] Given the API returns 401, when called, then the auth error string is returned
- [ ] Given the server, when `tools/list` is queried, then `clone_voice` is registered with required params `name` and `audio_path`, and optional `description`

#### Implementation Notes
- File: `src/supertone_tts_mcp/supertone_client.py` (add method)
- File: `src/supertone_tts_mcp/tools.py` (add handler + validators)
- File: `src/supertone_tts_mcp/server.py` (register)
- `audio_path` is a local filesystem path string; expand `~` with `Path.expanduser()`
- Read file with `Path.read_bytes()` after size check (use `stat().st_size` first to fail fast)
- Map extension → content_type: `.wav` → `audio/wav`, `.mp3` → `audio/mpeg`
- SDK `Files` object: `{file_name: basename, content: bytes, content_type: mime}`
- Response format: `Custom voice created. voice_id: {id}. Use this voice_id in text_to_speech.`
- Constants: `MAX_AUDIO_FILE_BYTES = 3 * 1024 * 1024`, `SUPPORTED_CLONE_FORMATS = {".wav": "audio/wav", ".mp3": "audio/mpeg"}`
- Test fixtures: tiny WAV (a few bytes) for happy path; oversize file simulated via mocked stat

#### Tests
- [ ] Test client method passes correct Files payload
- [ ] Test handler happy path with WAV
- [ ] Test handler happy path with MP3
- [ ] Test handler missing file returns error
- [ ] Test handler unsupported extension returns error
- [ ] Test handler oversize file returns error (mock stat)
- [ ] Test handler empty name returns error
- [ ] Test handler expands `~` in path
- [ ] Test handler auth/connection errors are formatted
- [ ] Test server registers clone_voice with correct schema

#### Rollback
Revert client method, tool handler, validators, constants, server registration, and tests.

---

### ISSUE-020: Custom voice CRUD tools (search/edit/delete)
- Track: product
- PRD-Ref: FR-018, FR-019, US-011
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: feat/ISSUE-020-custom-voice-crud
- GH-Issue: 24
- PR: 23
- Depends-On: ISSUE-019

#### Goal
Three tools for managing custom (cloned) voices: `search_custom_voice` (filtered listing), `edit_custom_voice` (name/description partial update), and `delete_custom_voice` (remove by ID). No destructive-confirm gate at this stage.

#### Scope (In/Out)
- In: Three new methods on `SupertoneClient` wrapping `custom_voices.search_custom_voices_async`, `custom_voices.edit_custom_voice_async`, `custom_voices.delete_custom_voice_async`. Three tool handlers in `tools.py`. Server registration of all three. Formatter for custom voice list (reuse `format_voice_list` if compatible, else a small variant). Tests.
- Out: get_custom_voice (deferred — list/search output is sufficient for now), delete confirmation flow

#### Acceptance Criteria (DoD)
- [ ] Given a mocked client returning 2 custom voices, when `search_custom_voice()` is called, then both are returned in a numbered list with name/description/voice_id
- [ ] Given filters (name/description), when `search_custom_voice(name="my")` is called, then only matching voices are returned
- [ ] Given `edit_custom_voice("cv1", name="NewName")`, when called against a mocked SDK 200, then the response is `"Custom voice updated. voice_id: cv1."`
- [ ] Given `edit_custom_voice("cv1")` with no name and no description, when called, then `"Provide at least one of: name, description."` is returned without an API call
- [ ] Given `delete_custom_voice("cv1")`, when called against a mocked SDK 204/200, then the response is `"Custom voice deleted. voice_id: cv1."`
- [ ] Given `delete_custom_voice("")` or whitespace, when called, then a validation error string is returned without an API call
- [ ] Given any of the three returns 401, when called, then the auth error string is returned
- [ ] Given the server, when `tools/list` is queried, then all three tools are registered

#### Implementation Notes
- File: `src/supertone_tts_mcp/supertone_client.py` (add 3 methods)
- File: `src/supertone_tts_mcp/tools.py` (add 3 handlers + formatter)
- File: `src/supertone_tts_mcp/server.py` (register all 3)
- `search_custom_voice` pagination same pattern as `search_voices`
- `edit_custom_voice` does partial update: only send fields that are non-None
- `delete_custom_voice` is irreversible; tool description warns about this even without a confirm gate
- Custom voice list format mirrors preset voice list but adds `description` field
- Test files: `tests/test_supertone_client.py`, `tests/test_tools.py`, `tests/test_server.py`

#### Tests
- [ ] Test search_custom_voice pagination and filters
- [ ] Test edit_custom_voice partial update (name only, description only, both)
- [ ] Test edit_custom_voice with no fields returns validation error
- [ ] Test delete_custom_voice happy path
- [ ] Test delete_custom_voice empty voice_id returns validation error
- [ ] Test all three handlers map auth/connection errors
- [ ] Test server registers all three tools

#### Rollback
Revert client methods, tool handlers, server registrations, and tests.

---

### ISSUE-021: SDK 0.2.3 sync: model enum + default + version pin
- Track: platform
- PRD-Ref: FR-001, US-015, NFR-009 (SDK 0.2.3)
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: team-lead
- Branch: issue/ISSUE-021-sdk-023-sync
- GH-Issue: 31
- PR: 32 (merged)
- Depends-On: none

#### Goal
`constants.SUPPORTED_MODELS` matches the SDK 0.2.3 model enum (all 7 models), the default model is `sona_speech_2_flash`, and the `supertone` dependency is pinned to `>=0.2.3,<0.3` so future SDK additions cannot silently desync the validator.

#### Scope (In/Out)
- In: Add `sona_speech_3t` and `supertonic_api_3` to `SUPPORTED_MODELS` and the `Model` Literal in `constants.py`; change `DEFAULT_MODEL` from `sona_speech_1` to `sona_speech_2_flash`; pin `supertone>=0.2.3,<0.3` in `pyproject.toml`; update `validate_model` tests; correct the stale `text_to_speech` docstring text in `server.py` (`"sona_speech_1 (default, streaming)"`) to reflect the new default and the full 7-model list.
- Out: streaming-vs-synthesize routing (ISSUE-023), env-var removal (ISSUE-022), new tools (ISSUE-026/027).

#### Acceptance Criteria (DoD)
- [ ] Given `constants.SUPPORTED_MODELS`, when inspected, then it contains exactly the 7 SDK 0.2.3 models: `sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `sona_speech_3t`, `supertonic_api_1`, `supertonic_api_3`
- [ ] Given each of the 7 supported models, when `validate_model(model)` is called, then no error is raised
- [ ] Given `validate_model("sona_speech_3t")` and `validate_model("supertonic_api_3")` (previously rejected), when called, then no error is raised
- [ ] Given an unsupported model `"sona_speech_99"`, when `validate_model("sona_speech_99")` is called, then it raises `ValueError` with message `Invalid model: "sona_speech_99". Supported models: sona_speech_1, sona_speech_2, sona_speech_2_flash, sona_speech_2t, sona_speech_3t, supertonic_api_1, supertonic_api_3.`
- [ ] Given `constants.DEFAULT_MODEL`, when inspected, then it equals `"sona_speech_2_flash"`
- [ ] Given a mocked SDK and `text_to_speech(text="hi", model="sona_speech_3t", streaming=False)` (or `supertonic_api_3`), when called, then the client `synthesize` path is invoked with the corresponding SDK enum member and no validation error is returned
- [ ] Given `pyproject.toml`, when inspected, then the `dependencies` list contains `"supertone>=0.2.3,<0.3"` (not the bare `"supertone"`)
- [ ] Given the `text_to_speech` tool docstring in `server.py`, when inspected, then it no longer states `sona_speech_1 (default, streaming)` and lists all 7 models with `sona_speech_2_flash` as the default

#### Implementation Notes
- File: `src/supertone_mcp/constants.py` — extend `Model` Literal and `SUPPORTED_MODELS`; set `DEFAULT_MODEL = "sona_speech_2_flash"`.
- File: `pyproject.toml` — change `"supertone"` to `"supertone>=0.2.3,<0.3"` in `[project] dependencies`.
- File: `src/supertone_mcp/server.py` — fix the `model:` line in the `text_to_speech` docstring (lines ~48-50). Keep the streaming caveat for ISSUE-023.
- `_MODEL_MAP` / `_PREDICT_MODEL_MAP` in `supertone_client.py` are already built dynamically from the SDK enum, so they already accept all 7 — no client change needed beyond confirming the maps resolve `sona_speech_3t` / `supertonic_api_3`.
- Test files: `tests/test_tools.py` (validate_model), `tests/test_supertone_client.py` (enum-map resolution for the 2 new models).
- Note: changing `DEFAULT_MODEL` to a non-streaming model is intentional and is the precondition for ISSUE-023's streaming default change — do NOT also change streaming routing here.

#### Tests
- [ ] Test `validate_model` passes for all 7 models (parametrized)
- [ ] Test `validate_model` passes for `sona_speech_3t` and `supertonic_api_3` specifically (regression for the stale-list bug)
- [ ] Test `validate_model` rejects an unknown model with the exact 7-model error string
- [ ] Test `DEFAULT_MODEL == "sona_speech_2_flash"`
- [ ] Test `_MODEL_MAP` and `_PREDICT_MODEL_MAP` contain `sona_speech_3t` and `supertonic_api_3` keys
- [ ] Test `text_to_speech` with `model="supertonic_api_3"` (mocked client) does not return a validation error

#### Rollback
Revert `constants.py`, `pyproject.toml`, the `server.py` docstring edit, and the related tests.

---

### ISSUE-022: Remove behavior env vars → per-call output_mode/autoplay (BREAKING)
- Track: platform
- PRD-Ref: FR-001, FR3 (config), US-012, US-013, NFR-009
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: -
- Branch: issue/ISSUE-022-output-mode-autoplay-params
- GH-Issue: #33
- PR: #34
- Depends-On: ISSUE-021

#### Goal
`text_to_speech` decides output mode and autoplay per call via the new `output_mode` and `autoplay` parameters; the behavior-control environment variables `SUPERTONE_MCP_OUTPUT_MODE` and `SUPERTONE_MCP_AUTOPLAY` are no longer read, and `autoplay` defaults to `false`.

#### Scope (In/Out)
- In: Add `output_mode` (str, default `files`) and `autoplay` (bool, default `false`) parameters to the `tools.text_to_speech` handler and to the `server.py` tool registration + docstrings; replace `resolve_output_mode()` (env read) with per-call validation of the `output_mode` argument; remove `resolve_autoplay()` and stop reading `SUPERTONE_MCP_AUTOPLAY`; remove `DEFAULT_AUTOPLAY` constant usage for env-driven behavior; keep the `files`/`resources`/`both` output logic but drive it from the parameter; update all tests that set those env vars.
- Out: streaming routing (ISSUE-023), relaxed length (ISSUE-024), new TTS params (ISSUE-025).

#### Acceptance Criteria (DoD)
- [ ] Given no `output_mode` argument, when `text_to_speech(text="hi")` is called against a mocked client, then it behaves as `files` mode (disk save + plain-text response) regardless of any `SUPERTONE_MCP_OUTPUT_MODE` env value
- [ ] Given `output_mode="resources"`, when `text_to_speech(text="hi", output_mode="resources")` is called, then no file is written and `[AudioContent, TextContent]` is returned
- [ ] Given `output_mode="both"`, when called, then a file is saved AND `[AudioContent, TextContent]` is returned with the file path in the metadata line
- [ ] Given `output_mode="invalid"`, when called, then a validation error string is returned (e.g., `Invalid output mode: "invalid". Valid modes: files, resources, both.`) and no API call is made
- [ ] Given `SUPERTONE_MCP_OUTPUT_MODE=resources` is set in the environment but `output_mode` is omitted, when `text_to_speech(text="hi")` is called, then the env var is ignored and `files` behavior is used
- [ ] Given no `autoplay` argument, when `text_to_speech(text="hi")` is called, then audio is NOT played (autoplay defaults to false), even if `SUPERTONE_MCP_AUTOPLAY=true` is set in the environment
- [ ] Given `autoplay=true` on macOS, when `text_to_speech(text="hi", autoplay=True)` is called, then `_autoplay(...)` is invoked
- [ ] Given the source, when `tools.py` is inspected, then `resolve_output_mode()` and `resolve_autoplay()` no longer read environment variables for behavior control (the functions are removed or refactored to validate the parameter)

#### Implementation Notes
- File: `src/supertone_mcp/tools.py` — `text_to_speech` signature gains `output_mode: str | None = None` (resolved to `DEFAULT_OUTPUT_MODE` when None) and `autoplay: bool = False`. Replace the `resolve_output_mode()` env read with a `validate_output_mode(mode)` helper that validates the passed value against `VALID_OUTPUT_MODES`. Remove `resolve_autoplay()` and call `_autoplay(...)` only when the `autoplay` argument is truthy.
- File: `src/supertone_mcp/constants.py` — keep `VALID_OUTPUT_MODES` / `DEFAULT_OUTPUT_MODE`; remove `DEFAULT_AUTOPLAY` (or leave only as a documented `False` default in the handler signature — do NOT use it to drive env behavior).
- File: `src/supertone_mcp/server.py` — add `output_mode` and `autoplay` params to the `text_to_speech` wrapper + docstring; document that these REPLACE the removed env vars and that `autoplay` now defaults to `false`.
- BREAKING: anyone relying on `SUPERTONE_MCP_OUTPUT_MODE` / `SUPERTONE_MCP_AUTOPLAY` must migrate to the params (covered in ISSUE-028 migration guide). Optionally emit a one-time stderr warning if either env var is set.
- Test files: `tests/test_tools.py`, `tests/test_server.py` — replace env-var-based output-mode/autoplay tests with parameter-based tests; assert env vars are ignored.

#### Tests
- [ ] Test default (no args) → files behavior, env `SUPERTONE_MCP_OUTPUT_MODE` ignored
- [ ] Test `output_mode="resources"` → no file, AudioContent returned
- [ ] Test `output_mode="both"` → file saved + AudioContent returned
- [ ] Test `output_mode="invalid"` → validation error, no API call
- [ ] Test `autoplay` defaults to false (no `_autoplay` call) even with `SUPERTONE_MCP_AUTOPLAY=true` set
- [ ] Test `autoplay=True` triggers `_autoplay` (patched/mock subprocess)
- [ ] Test server registers `text_to_speech` with `output_mode` and `autoplay` params in the schema

#### Rollback
Revert `tools.py`, `constants.py`, `server.py`, and the updated tests; restore `resolve_output_mode()`/`resolve_autoplay()` env reads.

---

### ISSUE-023: Add streaming param + route synthesize vs stream + sona_speech_1-only validation
- Track: product
- PRD-Ref: FR-001, US-014, US-015
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: -
- Branch: issue/ISSUE-023-streaming-routing
- GH-Issue: 35
- PR: 36
- Depends-On: ISSUE-021, ISSUE-022

#### Goal
`text_to_speech` accepts a per-call `streaming` parameter (default `false`) that routes to the one-shot `client.synthesize` path by default and to `client.synthesize_stream` when `true`, with fail-fast validation that rejects `streaming=true` for any model other than `sona_speech_1` before any SDK call.

#### Scope (In/Out)
- In: Add `streaming: bool = False` to the `tools.text_to_speech` handler + `server.py` registration/docstring; wire the currently-unused `client.synthesize()` (one-shot) path through the existing `output_mode` (files/resources/both) and autoplay logic; route to `client.synthesize_stream()` when `streaming=True`; add cross-field validation per locked decision #3.
- Out: model enum sync (ISSUE-021), env removal (ISSUE-022), length relax (ISSUE-024).

#### Acceptance Criteria (DoD)
- [ ] Given default arguments (`model` defaults to `sona_speech_2_flash`, `streaming` defaults to `False`), when `text_to_speech(text="hi")` is called against a mocked client, then `client.synthesize` is called (NOT `synthesize_stream`) and a `files`-mode response is returned
- [ ] Given `streaming=True` and `model="sona_speech_2_flash"` (or any non-`sona_speech_1` model), when `text_to_speech(text="hi", streaming=True)` is called, then the exact validation error `Streaming is only supported by model "sona_speech_1" (received: "sona_speech_2_flash"). Set streaming=false or use sona_speech_1.` is returned and NEITHER `synthesize` NOR `synthesize_stream` is called
- [ ] Given `streaming=True` and `model="sona_speech_1"`, when `text_to_speech(text="hi", model="sona_speech_1", streaming=True)` is called, then `client.synthesize_stream` is invoked and the file/resource output is produced from the streamed chunks
- [ ] Given `streaming=False` and `output_mode="resources"`, when called, then `client.synthesize` is used and `[AudioContent, TextContent]` is returned from the one-shot bytes (no file written)
- [ ] Given `streaming=False`, when the one-shot path returns a duration from the SDK (`synthesize` third tuple element), then that duration is preferred over the mutagen-derived value when present
- [ ] Given the server, when the `text_to_speech` schema is inspected, then `streaming` (boolean, default false) is present and its description states it requires `model=sona_speech_1`

#### Implementation Notes
- File: `src/supertone_mcp/tools.py` — `text_to_speech` gains `streaming: bool = False`. Add a validation step (after `validate_model`) of the form: `if streaming and model != "sona_speech_1": return 'Streaming is only supported by model "sona_speech_1" (received: "{model}"). Set streaming=false or use sona_speech_1.'`. When `streaming=False`, call `audio_bytes, content_type, sdk_duration = await client.synthesize(...)`, write to disk if `needs_file`, and collect bytes for resources/both. When `streaming=True`, keep the existing `synthesize_stream` chunk loop.
- `client.synthesize` already returns `(bytes, content_type, duration|None)`; reuse `format_tts_response` / `format_tts_metadata`. Prefer `sdk_duration` when not None, else `calculate_duration(file_path)`.
- File: `src/supertone_mcp/server.py` — add `streaming` to the wrapper + docstring (note default false, sona_speech_1-only).
- The streaming-model error must be raised BEFORE constructing/calling the client (fail-fast), alongside the other `validate_*` checks.
- Test files: `tests/test_tools.py`, `tests/test_server.py`.

#### Tests
- [ ] Test default path calls `synthesize` (mock), not `synthesize_stream`
- [ ] Test `streaming=True` + `sona_speech_2_flash` returns the exact error string and calls neither SDK method
- [ ] Test `streaming=True` + `sona_speech_1` calls `synthesize_stream`
- [ ] Test `streaming=False` + `output_mode="resources"` returns AudioContent from one-shot bytes, no file
- [ ] Test `streaming=False` prefers SDK-provided duration when present
- [ ] Test server schema includes `streaming` boolean with sona_speech_1 note

#### Rollback
Revert `tools.py` routing changes, `server.py` registration, and the tests; restore the streaming-only behavior.

---

### ISSUE-024: Relax 300-char hard limit → delegate to SDK auto-chunk
- Track: product
- PRD-Ref: FR-001, FR-016, FR-005 (relaxed)
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner: -
- Branch: issue/ISSUE-024-relax-text-length
- GH-Issue: #37
- PR: #38
- Depends-On: ISSUE-022

#### Goal
`text_to_speech` and `predict_duration` no longer hard-reject text over 300 characters; long text is delegated to the SDK's internal auto-chunking, while empty-text validation is retained.

#### Scope (In/Out)
- In: Remove the `validate_text_max_length` hard rejection from `predict_duration` (and confirm `text_to_speech` does not call it); keep `validate_text` (non-empty); update the `text_to_speech` and `predict_duration` tool descriptions/docstrings to note that long text is auto-chunked and that credit/latency scale with length; update/remove tests asserting the 300-char rejection.
- Out: Soft-warning UI, streaming routing, new params.

#### Acceptance Criteria (DoD)
- [ ] Given text of 500 characters, when `text_to_speech(text=long_text)` is called against a mocked client, then no length-validation error is returned and the SDK synthesize path is invoked
- [ ] Given text of 500 characters, when `predict_duration(text=long_text)` is called against a mocked client, then no length-validation error is returned and the SDK `predict_duration` path is invoked
- [ ] Given empty text `""`, when `text_to_speech(text="")` is called, then `Text must not be empty.` is returned without an API call
- [ ] Given empty text `""`, when `predict_duration(text="")` is called, then `Text must not be empty.` is returned without an API call
- [ ] Given the `predict_duration` tool docstring/description, when inspected, then it no longer claims a 300-character limit and instead notes auto-chunking with proportional credit/latency
- [ ] Given the `text_to_speech` tool description, when inspected, then it notes long text is automatically split (auto-chunked) and credit/latency scale with length

#### Implementation Notes
- File: `src/supertone_mcp/tools.py` — remove the `validate_text_max_length(text)` call from `predict_duration` (lines ~917-918); leave `validate_text(text)` in place. `text_to_speech` already does not call `validate_text_max_length`, so just confirm and update its description. Consider removing `validate_text_max_length` entirely if no other caller remains, or keep it as a dead helper documented as unused — prefer removal.
- File: `src/supertone_mcp/server.py` — update the `predict_duration` description (remove "applies the same 300-character limit") and the `predict_duration` docstring `text:` arg line ("Maximum 300 characters (no auto-chunking...)") to reflect auto-chunking; update `text_to_speech` description if needed.
- Note: `TEXT_MAX_LENGTH` constant may remain for reference but is no longer enforced as a hard cap.
- Test files: `tests/test_tools.py` — remove/adjust the 301-char rejection tests for both handlers; add long-text pass-through tests.

#### Tests
- [ ] Test `text_to_speech` with 500-char text passes validation and calls the SDK (mock)
- [ ] Test `predict_duration` with 500-char text passes validation and calls the SDK (mock)
- [ ] Test both handlers still reject empty text with `Text must not be empty.`
- [ ] Test removal/adjustment of the prior 301-char rejection assertions

#### Rollback
Re-add `validate_text_max_length` calls and restore the 300-char rejection tests and descriptions.

---

### ISSUE-025: Expose include_phonemes + normalized_text TTS params
- Track: product
- PRD-Ref: FR-001, US-014
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner: -
- Branch: issue/ISSUE-025-tts-phoneme-params
- GH-Issue: #39
- PR: #40
- Depends-On: ISSUE-022

#### Goal
`text_to_speech` exposes the SDK 0.2.3 `include_phonemes` (bool, default false) and `normalized_text` (str, optional) parameters, passing them through to the client/SDK, with `normalized_text` documented as effective only for `sona_speech_2`/`sona_speech_2_flash`.

#### Scope (In/Out)
- In: Add `include_phonemes: bool = False` and `normalized_text: str | None = None` to the `tools.text_to_speech` handler, the `client.synthesize` (and, where applicable, `synthesize_stream`) signatures, and the `server.py` registration/docstrings; pass both through to the SDK call.
- Out: Surfacing/parsing the returned phoneme timing data into the response (pass-through only for now), other params.

#### Acceptance Criteria (DoD)
- [ ] Given `include_phonemes=True`, when `text_to_speech(text="hi", include_phonemes=True)` is called against a mocked client, then the client/SDK synthesize call receives `include_phonemes=True`
- [ ] Given `include_phonemes` omitted, when `text_to_speech(text="hi")` is called, then the synthesize call receives `include_phonemes=False` (default)
- [ ] Given `normalized_text="안녕하세요"` with `model="sona_speech_2_flash"`, when called, then the synthesize call receives `normalized_text="안녕하세요"`
- [ ] Given `normalized_text` omitted, when called, then `normalized_text` is not sent / sent as None (SDK default)
- [ ] Given the server, when the `text_to_speech` schema is inspected, then `include_phonemes` (boolean, default false) and `normalized_text` (string, optional) are present, and `normalized_text` documentation states it applies only to `sona_speech_2`/`sona_speech_2_flash`

#### Implementation Notes
- File: `src/supertone_mcp/supertone_client.py` — add `include_phonemes: bool = False` and `normalized_text: str | None = None` to `synthesize` (and `synthesize_stream` if streaming supports them) and forward to the SDK `create_speech_async` / `stream_speech_async` calls (SDK 0.2.3 fields).
- File: `src/supertone_mcp/tools.py` — add both params to `text_to_speech`, pass through to `client.synthesize` / `synthesize_stream`.
- File: `src/supertone_mcp/server.py` — add both params + docstrings; document the model constraint for `normalized_text` (no client-side rejection — other models ignore it per SDK).
- Test files: `tests/test_supertone_client.py` (params forwarded to SDK), `tests/test_tools.py` (passthrough), `tests/test_server.py` (schema).

#### Tests
- [ ] Test `include_phonemes=True` forwarded to SDK synthesize call
- [ ] Test `include_phonemes` defaults to False when omitted
- [ ] Test `normalized_text` forwarded when provided
- [ ] Test `normalized_text` omitted/None when not provided
- [ ] Test server schema includes both params with correct defaults and the model note

#### Rollback
Revert the client signature, `tools.py`, `server.py`, and tests.

---

### ISSUE-026: New tool get_custom_voice
- Track: product
- PRD-Ref: FR-020, US-016
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner: -
- Branch: issue/ISSUE-026-get-custom-voice
- GH-Issue: #41
- PR: #42
- Depends-On: ISSUE-021

#### Goal
A new `get_custom_voice(voice_id)` tool returns the detail of a single custom (cloned) voice by wrapping `custom_voices.get_custom_voice_async`, with empty-`voice_id` validation.

#### Scope (In/Out)
- In: New `async get_custom_voice(voice_id) -> CustomVoiceDict` (or detail dict) method on `SupertoneClient` wrapping `custom_voices.get_custom_voice_async`; new `async get_custom_voice(voice_id) -> str` tool handler + `format_custom_voice_detail(...)` formatter in `tools.py`; `server.py` registration; empty `voice_id` validation; tests.
- Out: Listing/searching custom voices (already in ISSUE-020), usage tools (ISSUE-027).

#### Acceptance Criteria (DoD)
- [ ] Given a mocked client returning a custom voice detail, when `get_custom_voice("cv_abc123")` is called, then the response includes voice_id, name, description (and created_at when present)
- [ ] Given `get_custom_voice("")` or whitespace, when called, then `voice_id must not be empty.` is returned without an API call
- [ ] Given a mocked client raising `SupertoneAuthError`, when `get_custom_voice("cv1")` is called, then `Authentication failed. Please verify your SUPERTONE_API_KEY.` is returned
- [ ] Given a mocked client raising `SupertoneConnectionError`, when called, then the connection error string is returned
- [ ] Given the server, when `tools/list` is queried, then `get_custom_voice` is registered with required param `voice_id`

#### Implementation Notes
- File: `src/supertone_mcp/supertone_client.py` — add `get_custom_voice(voice_id)` wrapping `self._sdk.custom_voices.get_custom_voice_async(voice_id=voice_id)`; map the response into a `CustomVoiceDict` (voice_id, name, optional description, optional created_at) using the same `_handle_sdk_errors` try/except pattern as the other wrappers.
- File: `src/supertone_mcp/tools.py` — add the handler (validate non-empty `voice_id` first, mirror `get_voice` error handling) and a `format_custom_voice_detail(detail)` formatter (reuse `format_custom_voice_list` style fields).
- File: `src/supertone_mcp/server.py` — register `get_custom_voice` with a description (single custom voice detail by voice_id).
- Test files: `tests/test_supertone_client.py`, `tests/test_tools.py`, `tests/test_server.py`.

#### Tests
- [ ] Test client wrapper maps SDK response to dict and maps errors
- [ ] Test handler happy path returns formatted detail
- [ ] Test handler empty/whitespace voice_id returns validation error, no API call
- [ ] Test handler auth/rate/5xx/connection errors are formatted
- [ ] Test server registers `get_custom_voice` with `voice_id` required

#### Rollback
Revert the client method, tool handler, formatter, server registration, and tests.

---

### ISSUE-027: New usage tools get_usage_history + get_voice_usage
- Track: product
- PRD-Ref: FR-021, FR-022, US-017
- Priority: P2
- Estimate: 1d
- Status: done
- Owner: -
- Branch: issue/ISSUE-027-usage-tools
- GH-Issue: 43
- PR: https://github.com/supertone-inc/supertone-mcp/pull/44
- Depends-On: ISSUE-021

#### Goal
Two new tools expose usage data: `get_usage_history()` wraps `usage.get_usage_async` and `get_voice_usage(voice_id)` wraps `usage.get_voice_usage_async`, each returning a formatted plain-text usage summary.

#### Scope (In/Out)
- In: New `async get_usage_history(...) -> dict|list` and `async get_voice_usage(voice_id) -> dict` methods on `SupertoneClient`; two tool handlers (`get_usage_history`, `get_voice_usage`) + formatters in `tools.py`; `server.py` registration for both; empty-`voice_id` validation for `get_voice_usage`; tests.
- Out: Cost-in-currency conversion, charting, custom date-range UI beyond what the SDK exposes.

#### Acceptance Criteria (DoD)
- [ ] Given a mocked client returning a usage history payload, when `get_usage_history()` is called, then a formatted plain-text summary (e.g., per-period character/request counts) is returned
- [ ] Given a mocked client returning empty usage, when `get_usage_history()` is called, then a clear "no usage" style message is returned (not an error)
- [ ] Given a mocked client returning voice usage, when `get_voice_usage("v1")` is called, then a formatted summary for that voice is returned
- [ ] Given `get_voice_usage("")` or whitespace, when called, then `voice_id must not be empty.` is returned without an API call
- [ ] Given any of the two tools and a mocked `SupertoneAuthError`, when called, then `Authentication failed. Please verify your SUPERTONE_API_KEY.` is returned
- [ ] Given the server, when `tools/list` is queried, then both `get_usage_history` and `get_voice_usage` are registered (the latter with required `voice_id`)

#### Implementation Notes
- File: `src/supertone_mcp/supertone_client.py` — add `get_usage_history(...)` wrapping `self._sdk.usage.get_usage_async(...)` and `get_voice_usage(voice_id)` wrapping `self._sdk.usage.get_voice_usage_async(voice_id=voice_id)`; reuse the `_handle_sdk_errors` try/except pattern. Pass through whatever optional period/paging params the SDK 0.2.3 signature exposes (keep them all optional).
- File: `src/supertone_mcp/tools.py` — add `format_usage_history(...)` and `format_voice_usage(...)` formatters and the two handlers (mirror `get_credit_balance` for the no-arg one; validate non-empty `voice_id` for the voice one).
- File: `src/supertone_mcp/server.py` — register both tools with descriptions.
- Test files: `tests/test_supertone_client.py`, `tests/test_tools.py`, `tests/test_server.py`.

#### Tests
- [ ] Test `get_usage_history` client wrapper forwards optional params and maps errors
- [ ] Test `get_usage_history` handler happy path formats the summary
- [ ] Test `get_usage_history` handler empty-usage message
- [ ] Test `get_voice_usage` client wrapper maps response + errors
- [ ] Test `get_voice_usage` handler happy path formats the summary
- [ ] Test `get_voice_usage` empty/whitespace voice_id returns validation error, no API call
- [ ] Test both handlers map auth/rate/5xx/connection errors
- [ ] Test server registers both tools with correct schemas

#### Rollback
Revert the two client methods, two handlers, two formatters, server registrations, and tests.

---

### ISSUE-028: Docs/README reframe + env→param migration + 0.2.0 release
- Track: product
- PRD-Ref: PRD §1 (v0.3 pivot), FR-001, FR3 (config), FR-020, FR-021, FR-022, US-012..US-017
- Priority: P2
- Estimate: 1d
- Status: done
- Owner: -
- Branch: issue/ISSUE-028-docs-v03-release
- GH-Issue: 45
- PR: 46
- Depends-On: ISSUE-021, ISSUE-022, ISSUE-023, ISSUE-024, ISSUE-025, ISSUE-026, ISSUE-027
- Manual: true

#### Goal
The README and release metadata reflect the v0.3 "composable SDK toolkit" framing, document the env→param migration (output_mode/autoplay, autoplay & streaming default changes, DEFAULT_MODEL change), register the new tools, and ship version 0.3.0.

#### Scope (In/Out)
- In: Reframe README intro to "composable SDK toolkit"; update the environment variable table (remove `SUPERTONE_MCP_OUTPUT_MODE`/`SUPERTONE_MCP_AUTOPLAY`, keep `SUPERTONE_API_KEY`/`SUPERTONE_MCP_VOICE_ID`/`SUPERTONE_OUTPUT_DIR`); add a migration guide (old env → new param mapping; `autoplay` default `true`→`false`; `streaming` default now `false`; `DEFAULT_MODEL` `sona_speech_1`→`sona_speech_2_flash`); document the 3 new tools (`get_custom_voice`, `get_usage_history`, `get_voice_usage`) and new TTS params; update `server.json` description; bump version to `0.3.0` in `pyproject.toml` and `src/supertone_mcp/__init__.py`; update MCP registry metadata.
- Out: PRD edits (PRD is already reframed to v0.3 — this issue only references it), actual `mcp-publisher publish` run (handled by the release CI job / manual release step).

#### Acceptance Criteria (DoD)
- [ ] Given the README, when inspected, then the intro frames the server as a composable SDK toolkit (LLM assembles tools), not "TTS the LLM output"
- [ ] Given the README env var table, when inspected, then `SUPERTONE_MCP_OUTPUT_MODE` and `SUPERTONE_MCP_AUTOPLAY` are no longer listed as supported, and a migration note maps them to the `output_mode`/`autoplay` parameters
- [ ] Given the README migration section, when inspected, then it states `autoplay` now defaults to `false`, `streaming` now defaults to `false`, and the default model is `sona_speech_2_flash`
- [ ] Given the README tool list, when inspected, then `get_custom_voice`, `get_usage_history`, and `get_voice_usage` are documented along with the new `output_mode`/`autoplay`/`streaming`/`include_phonemes`/`normalized_text` parameters
- [ ] Given `pyproject.toml` and `src/supertone_mcp/__init__.py`, when inspected, then the version is `0.3.0`
- [ ] Given `server.json`, when inspected, then its `description` reflects the v0.3 composable-toolkit framing and references the expanded tool set
- [ ] Given the README, when inspected, then it retains the `mcp-name: io.github.supertone-inc/supertone-mcp` ownership marker

#### Implementation Notes
- Files: `README.md`, `server.json`, `pyproject.toml` (version), `src/supertone_mcp/__init__.py` (`__version__`).
- PRD/registry files: PRD.md is already at v0.3 — do NOT rewrite it; only cross-reference. `server.json` and the PyPI description carry the registry metadata (ownership marker + description).
- Keep the migration guide concise and developer-focused; show a before/after MCP client config plus before/after tool-call examples for output_mode/autoplay/streaming.
- Release: bump version, ensure CI test matrix passes, tag `v0.3.0` to trigger the existing `publish` + `publish-registry` jobs.
- This is a docs/release issue — no behavior code changes beyond version bumps.

#### Tests
- [ ] README renders correctly on GitHub and all code fences are tagged (manual verification)
- [ ] `server.json` is valid against its schema (validate via check-jsonschema)
- [ ] Version strings in `pyproject.toml` and `__init__.py` agree at `0.3.0`
- [ ] `uv build` succeeds and the built artifact reports version 0.3.0 (manual verification)

#### Rollback
Revert README/server.json/version changes; if a broken 0.3.0 is published, yank it on PyPI (`uv publish --yank 0.3.0`).

---


### ISSUE-029: Add merge_audio_files tool (ffmpeg-backed audio concatenation)
- Track: product
- PRD-Ref: US-018, FR-023, NFR-010
- Priority: P2
- Estimate: 1.5d
- Status: done
- Owner: -
- Branch: issue/ISSUE-029-merge-audio-files
- GH-Issue: https://github.com/supertone-inc/supertone-mcp/issues/48
- PR: https://github.com/supertone-inc/supertone-mcp/pull/49
- Depends-On: -
- Spec-Required: true
- Spec: docs/specs/SPEC-029.md

#### Goal
Add a `merge_audio_files` MCP tool backed by a bundled ffmpeg binary that concatenates two or more audio files produced by `text_to_speech` calls into a single deliverable, supporting head-to-tail concat, silence-gap insertion, and crossfade blending.

#### Scope (In/Out)
- In: New `src/supertone_mcp/audio_ops.py` module with async ffmpeg subprocess logic; new `merge_audio_files` tool handler in `tools.py`; server registration in `server.py`; `imageio-ffmpeg>=0.5` dependency in `pyproject.toml`; `MERGE_SUPPORTED_EXTENSIONS` constant in `constants.py`; tests in `tests/test_audio_ops.py` and extensions to `tests/test_tools.py` / `tests/test_server.py`.
- Out: Audio mix/overlay (deferred to a future issue), multi-track panning, any operation beyond concat/gap/crossfade, system ffmpeg reliance.

#### Acceptance Criteria (DoD)
- [ ] Given two or more valid audio file paths with the same extension, when `merge_audio_files` is called with no gap/crossfade args, then the files are concatenated head-to-tail and a merged file is saved to `SUPERTONE_OUTPUT_DIR` with the standard `{YYYY-MM-DD}_{uuid8}.{ext}` naming; the response contains the absolute path, duration, input count, and format.
- [ ] Given `gap_ms=500`, when called with two valid files, then 500ms of silence is inserted at each junction.
- [ ] Given `crossfade_ms=200`, when called with two valid files, then a 200ms crossfade blend is applied at each junction.
- [ ] Given both `gap_ms > 0` and `crossfade_ms > 0`, when called, then `gap_ms and crossfade_ms are mutually exclusive. Set one to 0.` is returned and no ffmpeg process is spawned.
- [ ] Given a single input path, when called, then the file is returned as-is (passthrough; no ffmpeg invoked).
- [ ] Given an empty input list, when called, then `Input file list must not be empty.` is returned.
- [ ] Given a file path that does not exist, when called, then `Audio file not found: {path}.` is returned before invoking ffmpeg.
- [ ] Given a file with an unsupported extension (e.g., `.ogg`), when called, then `Unsupported format: ".ogg". Supported: mp3, wav.` is returned.
- [ ] Given mixed-extension inputs (.mp3 + .wav) with no explicit `output_format`, when called, then the output defaults to `.mp3`.
- [ ] Given `output_format="wav"`, when called, then the output uses `.wav` regardless of input extensions.
- [ ] Given `output_format="ogg"`, when called, then `Invalid output format: "ogg". Supported formats: mp3, wav.` is returned.
- [ ] Given ffmpeg exits with a nonzero code (mocked), when called, then `Audio merge failed: {stderr_excerpt}.` is returned.
- [ ] Given the tool is registered in the server, when `tools/list` is queried, then `merge_audio_files` appears with correct schema.

#### Implementation Notes
- **Dependency:** Add `imageio-ffmpeg>=0.5` by running `uv add imageio-ffmpeg` (do NOT edit `pyproject.toml` by hand — let uv manage it).
- File: `src/supertone_mcp/audio_ops.py` (new) — `async merge_audio(input_paths: list[str], gap_ms: int, crossfade_ms: int, output_format: str) -> tuple[bytes, str]`; resolves ffmpeg via `imageio_ffmpeg.get_ffmpeg_exe()`; for plain concat uses the ffmpeg concat demuxer; for `gap_ms` inserts `aevalsrc=0:duration={gap_ms/1000}` silence; for `crossfade_ms` uses `acrossfade` filter; invokes via `asyncio.create_subprocess_exec` with `-y`; captures stdout bytes and stderr; raises `RuntimeError` with stderr excerpt on nonzero exit.
- File: `src/supertone_mcp/tools.py` — add `async merge_audio_files(input_paths: list[str], gap_ms: int = 0, crossfade_ms: int = 0, output_format: str | None = None) -> str`; perform all fail-fast validation (empty list, file existence, extension check, mutually-exclusive gap+crossfade, output_format enum); single-file passthrough path; output dir resolution and filename generation reuse existing helpers; call `audio_ops.merge_audio(...)`; write bytes; calculate duration; return formatted response.
- File: `src/supertone_mcp/server.py` — register `merge_audio_files` tool with full parameter schema and description matching UX spec §2.16.
- File: `src/supertone_mcp/constants.py` — add `MERGE_SUPPORTED_EXTENSIONS: list[str] = ["mp3", "wav"]` (or reuse `SUPPORTED_FORMATS` if already equivalent).
- Tests: `tests/test_audio_ops.py` (new) mocks `asyncio.create_subprocess_exec` and `imageio_ffmpeg.get_ffmpeg_exe`; `tests/test_tools.py` covers all validation paths and the happy-path handler; `tests/test_server.py` verifies tool registration. No real ffmpeg in CI — all subprocess calls are mocked.
- Error-mapping: `RuntimeError` from `audio_ops.merge_audio` → user-facing `Audio merge failed: ...` string; `OSError`/`PermissionError` on file write → existing output-dir error messages.
- Review lessons applied: fail-fast before subprocess, no system binary reliance, mock subprocess in all tests (never real network/process in CI).
- Spec-gate bypass rationale: decisions (ffmpeg bundling via imageio-ffmpeg, gap_ms/crossfade_ms mutual exclusion, output-format auto-detect→mp3, single-file passthrough) are already documented in this block + docs/architecture.md tradeoffs/failure-modes + docs/test_plan.md Flow 13; a separate SPEC would duplicate.

#### Tests
- [ ] TC-140: Happy path — 2 same-extension MP3 files → merged file saved, response has path + duration + "Inputs: 2" + "Format: mp3".
- [ ] TC-141: 3 same-extension WAV files → merged WAV, "Inputs: 3".
- [ ] TC-142: Single-file passthrough — no ffmpeg invoked; original path returned.
- [ ] TC-143: Empty input list → `Input file list must not be empty.`; no ffmpeg.
- [ ] TC-144: Missing file → `Audio file not found: {path}.`; no ffmpeg.
- [ ] TC-145: Unsupported extension `.ogg` → `Unsupported format: ".ogg". Supported: mp3, wav.`
- [ ] TC-146: Mixed .mp3 + .wav → output defaults to `.mp3`.
- [ ] TC-147: Mixed inputs + `output_format="wav"` → output uses `.wav`.
- [ ] TC-148: `gap_ms=500` → ffmpeg invoked with silence at junctions.
- [ ] TC-149: `crossfade_ms=200` → ffmpeg invoked with acrossfade filter.
- [ ] TC-150: Both `gap_ms > 0` and `crossfade_ms > 0` → mutual-exclusion error; no ffmpeg.
- [ ] TC-151: Mocked ffmpeg nonzero exit → `Audio merge failed: {stderr_excerpt}.`
- [ ] TC-152: `imageio_ffmpeg.get_ffmpeg_exe()` is called to resolve binary (no system ffmpeg).
- [ ] TC-153: `output_format="ogg"` → `Invalid output format: "ogg". Supported formats: mp3, wav.`

#### Rollback
Revert `audio_ops.py`, the `merge_audio_files` handler and registration in `tools.py` / `server.py`, the `MERGE_SUPPORTED_EXTENSIONS` constant addition, and all new tests. Remove `imageio-ffmpeg` dep with `uv remove imageio-ffmpeg`. No DB or migration concerns.

---
## Dependency Graph

```
ISSUE-001 (Scaffold)
  |
  +-- ISSUE-002 (Types/Constants/Exceptions)
  |     |
  |     +-- ISSUE-003 (SupertoneClient)  [can parallel with ISSUE-004]
  |     |     |
  |     +-- ISSUE-004 (Validation/Formatting)  [can parallel with ISSUE-003]
  |           |
  |           +-- ISSUE-005 (text_to_speech handler)  [needs 003 + 004]
  |           |     |
  |           |     +-- ISSUE-012 (Audio output modes)  [needs 005]
  |           |     |
  |           +-- ISSUE-006 (list_voices handler)  [needs 003 + 004, can parallel with 005]
  |                 |
  |                 +-- ISSUE-007 (MCP Server)  [needs 005 + 006]
  |                       |
  |                       +-- ISSUE-008 (PyPI Packaging)
  |                       |     |
  |                       |     +-- ISSUE-011 (Registry)
  |                       |
  |                       +-- ISSUE-010 (README)
  |
  +-- ISSUE-009 (CI)  [only needs 001, can parallel with everything]
```

**Critical path:** 001 -> 002 -> 003/004 (parallel) -> 005/006 (parallel) -> 007 -> 008 -> 011

**Maximum parallelism:**
- After ISSUE-001: ISSUE-002 and ISSUE-009 can run in parallel
- After ISSUE-002: ISSUE-003 and ISSUE-004 can run in parallel
- After ISSUE-003+004: ISSUE-005 and ISSUE-006 can run in parallel
- After ISSUE-007: ISSUE-008, ISSUE-010 can run in parallel

### v0.2 Sub-Graph (ISSUE-013 onwards)

```
ISSUE-013 (Docs sync — PRD/requirements/ux_spec)
  |
  +-- ISSUE-014 (Client: search/get/credit)
        |
        +-- ISSUE-015 (search_voice tool — replaces list_voices)
        +-- ISSUE-016 (get_voice + get_credit_balance tools)
        |     |
        |     +-- ISSUE-017 (preview_voice tool)  [needs 014 + 016]
        |
        +-- ISSUE-018 (predict_duration: client + tool)
        +-- ISSUE-019 (clone_voice: client + tool)
              |
              +-- ISSUE-020 (custom voice CRUD: search/edit/delete)
```

**v0.2 critical path:** 013 -> 014 -> (015, 016, 018, 019 in parallel) -> 017, 020

**v0.2 parallelism:**
- After ISSUE-014: ISSUE-015, ISSUE-016, ISSUE-018, ISSUE-019 can run in parallel
- After ISSUE-016: ISSUE-017 unlocks
- After ISSUE-019: ISSUE-020 unlocks

### v0.3 Sub-Graph (ISSUE-021 onwards — concept pivot)

```
ISSUE-021 (SDK 0.2.3 sync: model enum + DEFAULT_MODEL + version pin)
  |
  +-- ISSUE-022 (Remove behavior env vars → output_mode/autoplay params)  [BREAKING]
  |     |
  |     +-- ISSUE-023 (streaming param + synthesize/stream routing + sona_speech_1 validation)  [needs 021 + 022]
  |     +-- ISSUE-024 (relax 300-char hard limit → SDK auto-chunk)
  |     +-- ISSUE-025 (include_phonemes + normalized_text params)
  |
  +-- ISSUE-026 (new tool get_custom_voice)            [needs 021, parallel with 022 chain]
  +-- ISSUE-027 (new usage tools get_usage_history + get_voice_usage)  [needs 021]
        |
ISSUE-028 (docs/README reframe + env→param migration + 0.2.0 release)  [needs 021..027]
```

**v0.3 critical path:** 021 -> 022 -> 023 -> 028

**v0.3 parallelism:**
- After ISSUE-021: ISSUE-022, ISSUE-026, ISSUE-027 can run in parallel
- After ISSUE-022: ISSUE-023, ISSUE-024, ISSUE-025 can run in parallel
- ISSUE-028 is the release gate; it waits on all of ISSUE-021..ISSUE-027

---

## Requirement Coverage Check

| Requirement | Covered by |
|-------------|-----------|
| FR-001 | ISSUE-003, ISSUE-005 |
| FR-002 | ISSUE-003, ISSUE-006 |
| FR-003 | ISSUE-003, ISSUE-004 |
| FR-004 | ISSUE-004, ISSUE-005 |
| FR-005 | ISSUE-004, ISSUE-005 |
| FR-006 | ISSUE-004, ISSUE-005 |
| FR-007 | ISSUE-003, ISSUE-005, ISSUE-006 |
| FR-008 | ISSUE-002, ISSUE-005 |
| FR-009 | ISSUE-001, ISSUE-007 |
| FR-010 | ISSUE-008 |
| FR-011 | ISSUE-011 |
| US-001 | ISSUE-005 |
| US-002 | ISSUE-006 |
| US-003 | ISSUE-004, ISSUE-005, ISSUE-006 |
| US-004 | ISSUE-004, ISSUE-005 |
| US-005 | ISSUE-005 |
| US-006 | ISSUE-004, ISSUE-005 |
| US-007 | ISSUE-006 |
| NFR-001 | ISSUE-008 |
| NFR-002 | ISSUE-007 |
| NFR-003 | ISSUE-005, ISSUE-006 |
| NFR-004 | ISSUE-004, ISSUE-005, ISSUE-006 |
| NFR-005 | All issues include tests |
| NFR-006 | ISSUE-009 |
| NFR-007 | ISSUE-003, ISSUE-004 |
| NFR-008 | ISSUE-003 |
| FR-012 (search_voice) | ISSUE-013, ISSUE-014, ISSUE-015 |
| FR-013 (get_voice) | ISSUE-013, ISSUE-014, ISSUE-016 |
| FR-014 (get_credit_balance) | ISSUE-013, ISSUE-014, ISSUE-016 |
| FR-015 (preview_voice) | ISSUE-013, ISSUE-017 |
| FR-016 (predict_duration) | ISSUE-013, ISSUE-018 |
| FR-017 (clone_voice) | ISSUE-013, ISSUE-019 |
| FR-018 (search_custom_voice) | ISSUE-013, ISSUE-020 |
| FR-019 (edit/delete_custom_voice) | ISSUE-013, ISSUE-020 |
| US-008 (browse/preview voices) | ISSUE-015, ISSUE-016, ISSUE-017 |
| US-009 (check credits before TTS) | ISSUE-016 |
| US-010 (predict duration) | ISSUE-018 |
| US-011 (clone & manage custom voices) | ISSUE-019, ISSUE-020 |
| FR-001 (v0.3 params: output_mode/autoplay/streaming/model/include_phonemes/normalized_text + relaxed length) | ISSUE-021, ISSUE-022, ISSUE-023, ISSUE-024, ISSUE-025 |
| FR-020 (get_custom_voice) | ISSUE-026 |
| FR-021 (get_usage_history) | ISSUE-027 |
| FR-022 (get_voice_usage) | ISSUE-027 |
| NFR-009 (behavior via params not env; SDK version pin) | ISSUE-021, ISSUE-022 |
| US-012 (per-call output mode) | ISSUE-022 |
| US-013 (per-call autoplay) | ISSUE-022 |
| US-014 (per-call streaming + one-shot TTS) | ISSUE-023, ISSUE-024, ISSUE-025 |
| US-015 (per-call model selection, 7 models) | ISSUE-021, ISSUE-023 |
| US-016 (single custom voice detail) | ISSUE-026 |
| US-017 (usage history + voice usage) | ISSUE-027 |
| v0.3 docs/release (composable toolkit framing + migration) | ISSUE-028 |
| US-018 (merge multiple TTS outputs) | ISSUE-029 |
| FR-023 (merge_audio_files tool) | ISSUE-029 |
| NFR-010 (ffmpeg bundling & availability) | ISSUE-029 |

**Orphaned requirements:** None. All FRs, user stories, and NFRs are covered.

---

## Confidence Rating

**High.** The project scope is small and well-defined (2 tools, 3 modules, no database). Architecture and data model documents are detailed with exact type definitions and error messages. The only uncertainties are Supertone API specifics (Assumptions A1-A6), which affect implementation details within ISSUE-003 but not the issue decomposition or dependencies.
