# Review Notes — ISSUE-019 (PR #22)

> Reviewer: team-lead (Opus 4.7, 1M context)
> PR: https://github.com/pillip/supertone-mcp/pull/22
> Branch: `feat/ISSUE-019-clone-voice`
> Date: 2026-05-27
> Scope: `constants.py`, `supertone_client.py`, `tools.py`, `server.py`, `tests/test_supertone_client.py`, `tests/test_tools.py`, `tests/test_server.py` (7 files, +956/-1)
> Verdict: **Approve**
> Confidence: **High**

---

## Code Review

### Strengths

1. **AC coverage is complete and explicit.**
   - AC #1 (happy path WAV ≤3MB → formatted voice_id response) → `TestCloneVoiceHandler::test_happy_path_with_wav`.
   - AC #2 (missing file returns `Audio file not found: {path}` without API call) → `test_missing_file_returns_error_without_api_call` with `MC.assert_not_called()`.
   - AC #3 (`.ogg` unsupported → `Unsupported audio format. Supported: WAV, MP3.` without API call) → `test_unsupported_extension_returns_error_without_api_call`.
   - AC #4 (>3MB → `Audio file too large: {N:.2f}MB. Maximum: 3MB.` without API call) → `test_oversize_file_returns_error_without_api_call` (validators patched, not `Path.stat` globally — avoids breaking `Path.is_file()`).
   - AC #5 (empty / whitespace name → `Voice name must not be empty.`) → `test_empty_name_returns_error_without_api_call` + `test_whitespace_only_name_returns_error_without_api_call`.
   - AC #6 (401 → auth error string) → `test_auth_error_returns_formatted_string`.
   - AC #7 (server registration: `name` + `audio_path` required, `description` optional) → 7 tests in `TestToolRegistration`.

2. **RL-002 (symmetric error-branch testing) satisfied.** `TestCreateClonedVoice` exercises all three connection branches (`NoResponseError` + `httpx.ConnectError` + `httpx.TimeoutException`) plus 401, 403, 429, 5xx — matching the pattern established by `TestPredictDuration` and `TestGetCreditBalance`. Handler-level `TestCloneVoiceHandler` mirrors with `SupertoneConnectionError` + `aclose` on both success and error paths.

3. **RL-001 / RL-005 N/A here:** no new TypedDict was introduced; the SDK's `FilesTypedDict` is reused directly. Test helpers do not have nullable defaults that would trip RL-005.

4. **Fail-fast ordering matches UX spec §4.8 ordering note** ("existence → extension → size → name non-empty"). My implementation actually validates `name` FIRST (before any I/O), then API key, then existence + extension, then size, then read. This is even stricter than the spec (rejects empty name without touching disk) and is faithful to the AC wording.

5. **Resource hygiene.** `Path.read_bytes()` closes the file automatically. `client.aclose()` runs in `finally`. The audio_bytes buffer is held only as long as needed for the SDK call — no module-level retention.

6. **Architecture conformance.**
   - The SDK wrapper signature matches `architecture.md` §SDK: `create_cloned_voice(name, file_name, content_bytes, content_type, description?)` — issue text says `audio_bytes` for the parameter name, which we used (slight naming diff from architecture.md but the issue is the authoritative spec for ISSUE-019).
   - Validation/formatting/handler layering preserved. No new module dependencies.
   - Server registration mirrors the established pattern (`@mcp.tool` decorator + thin pass-through to `tools.*`).

7. **Security.**
   - No secrets logged. The API key flows through `resolve_api_key()` only.
   - The `audio_bytes` buffer is never logged or echoed.
   - File path appears in error messages, which is acceptable because the caller provided it (matches `get_voice`/`preview_voice` style for `voice_id`).
   - No path-traversal vector: the path is owned by the user's local LLM session; we only `expanduser()` and never join with project-controlled prefixes.
   - The file extension is matched case-insensitively but the lookup is constrained to a closed dict, so no surprise content-type injection.

### Findings

| # | Severity | Category | Finding | Action |
|---|----------|----------|---------|--------|
| F1 | **Low** | Spec drift | UX spec §4.8 error wording differs from the AC wording in `issues.md` line 935–938 (e.g., spec says `Audio file not found: {path}.` with trailing period and `Audio file exceeds the 3MB limit (received: {N} bytes).`, but the AC says `Audio file not found: {path}` and `Audio file too large: {size_mb:.2f}MB. Maximum: 3MB.`). Implementation follows the AC strings exactly. | **No action in this PR.** The issue (AC) takes priority over the spec for implementation. Recommend a docs-only follow-up to reconcile `ux_spec.md` §4.8 with the issue wording. Logged in sprint state Discovered Issues. |
| F2 | **Low** | Tech debt | RL-004 still in play: the new `create_cloned_voice` wrapper triggers a 10th occurrence of the "response is possibly unbound" pyright error (line 468 of `supertone_client.py`). | **No action in this PR** — explicitly out of scope per the task instruction (the single-line `_handle_sdk_errors -> NoReturn` fix is tracked as a dedicated tech-debt issue; bumping RL-004 frequency does not reset that decision). |
| F3 | **Info** | Test ergonomics | The original `test_oversize_file_returns_error_without_api_call` patched `Path.stat` globally, which broke `Path.is_file()` (which internally calls `stat()`). Switched to patching `validate_audio_file_size` directly. | **Already fixed.** Documented in the test docstring so future maintainers see the rationale. |
| F4 | **Info** | UX | Extra `Cannot read audio file: {path}. Please check file permissions.` / `Cannot read audio file: {path}. {os_error}` fallbacks were added even though the AC doesn't require them — covers the "file exists at validation time but is unreadable" edge case (e.g., race condition, permission change after stat). | **OK.** Matches the defensive style of `text_to_speech` which has analogous `Cannot write to output directory` fallbacks. No test added because the AC doesn't require it; trivial branch coverage. |

### Architecture conformance

- Layering preserved: validation (`validate_audio_path` + `validate_audio_file_size`) → handler (`clone_voice`) → SDK wrapper (`SupertoneClient.create_cloned_voice`) → SDK call.
- Caller owns disk I/O (per `architecture.md` §SDK note); wrapper takes already-read `audio_bytes`. This keeps the wrapper testable without touching the filesystem.
- The wrapper builds a `FilesTypedDict` rather than constructing the pydantic `Files` model — the SDK accepts both (`Union[Files, FilesTypedDict]`), and the TypedDict avoids importing the pydantic class into our wrapper.
- `server.py` registration mirrors prior tools: thin `@mcp.tool` decorator with the UX-spec description, delegating to `tools.clone_voice`.

### Test plan

- `cd .worktrees/feat-ISSUE-019-clone-voice && .venv/bin/pytest -q` → **351 passed** (+44 vs 307 baseline on main).
- `uv run ruff check src/ tests/` → 0 errors.
- `uv run pyright src/supertone_tts_mcp/supertone_client.py src/supertone_tts_mcp/tools.py src/supertone_tts_mcp/server.py`:
  - `supertone_client.py`: 23 → 24 errors (+1 RL-004, pre-existing pattern)
  - `tools.py`: 5 → 5 errors (unchanged ISSUE-012-era tech debt)
  - `server.py`: 0 → 0 errors
- Post-merge smoke test (to run from main): `uv run pytest -q`.

---

## Security Findings

| # | Severity | Finding | Remediation |
|---|----------|---------|-------------|
| S1 | None | API key handled via env var (`resolve_api_key`). No new key paths introduced. | N/A |
| S2 | None | Audio bytes never logged, echoed, or persisted outside the SDK call. | N/A |
| S3 | None | Path traversal not possible — user-provided path is only expanded and stat-checked. The file extension and MIME mapping are closed sets. | N/A |
| S4 | None | No new dependencies; reuses the already-vendored `supertone` SDK and `httpx` (already in tree). | N/A |

---

## RL-004 lessons-escalation update (frequency now 3)

PR #22 adds a 10th wrapped method (`create_cloned_voice`) and a 1 new line of pyright "response possibly unbound" noise. RL-004 frequency increments from **2 → 3** with this PR — still tracked as a dedicated tech-debt issue (the single-line fix on `_handle_sdk_errors -> NoReturn` would clear all 10 occurrences plus the 24 errors in `supertone_client.py`). No new lesson is created.

## RL-006 (404 mapping) — not applicable to this PR

`clone_voice` is POST (resource create), so there is no "voice not found by id" 404 in the request shape. The SDK does declare a 404 in the response model (e.g., for an unknown sub-resource), but the UX spec for §4.8 does not promise a 404-specific user message, so no gap exists in this PR. `_handle_sdk_errors` continues to need 404 mapping for the GET-by-id handlers (`get_voice`, `preview_voice`, future `edit_custom_voice`, `delete_custom_voice`) per the existing Discovered Issue.
