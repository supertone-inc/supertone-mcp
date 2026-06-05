# Review Notes — ISSUE-026 (PR #42, get_custom_voice)

Add a `get_custom_voice(voice_id)` MCP tool returning the detail of a single
custom (cloned) voice by wrapping `custom_voices.get_custom_voice_async`, with
empty-`voice_id` validation. Senior review + security audit.

## Code Review

No Critical / High / Medium findings. Clean, pattern-consistent addition of a
single read-only inspection tool.

Verified against all five acceptance criteria:

- **AC #1 (detail includes voice_id, name, description):** client
  `TestGetCustomVoice::test_returns_parsed_detail` + handler
  `TestGetCustomVoiceHandler::test_happy_path_returns_formatted_detail`. PASS.
- **AC #2 (empty/whitespace → `voice_id must not be empty.`, no API call):**
  `test_empty_voice_id_returns_validation_error_without_api_call` and
  `test_whitespace_voice_id_returns_validation_error_without_api_call`, both
  asserting `MC.assert_not_called()`. PASS.
- **AC #3 (auth error string):** `test_auth_error_returns_formatted_string`. PASS.
- **AC #4 (connection error string):**
  `test_connection_error_returns_formatted_string`. PASS.
- **AC #5 (server registers get_custom_voice with required voice_id):**
  `test_get_custom_voice_tool_exists` + `test_get_custom_voice_voice_id_is_required`.
  PASS.

### Correctness
- `SupertoneClient.get_custom_voice` mirrors the existing `edit_custom_voice` /
  `search_custom_voices` mapping exactly: `voice_id` + `name` always set,
  `description` added only when the SDK returns non-None (`getattr` + guard).
  The `except` tuple is identical to every other wrapper.
- **SDK shape verified** against the installed SDK
  `models/getcustomvoiceresponse.py`: `GetCustomVoiceResponse` exposes only
  `voice_id` (str), `name` (str), `description` (OptionalNullable[str]). There is
  **no `created_at`** field. The issue spec's "optional created_at" was therefore
  correctly NOT mapped — inventing it would violate "truthful to source data"
  (same decision already documented for `format_custom_voice_list`). This is the
  one place where implementation deliberately diverges from the literal AC wording,
  and the divergence is correct.
- Handler reuses the EXACT existing `voice_id must not be empty.` string and the
  `get_voice` error-handling shape (auth/rate/5xx/connection), with `aclose()` in
  `finally`.
- `format_custom_voice_detail` reuses the `format_custom_voice_list` field style
  (`Voice ID` / `Name` / `Description`), `description or "-"` placeholder.

### Edge cases / regressions
- Empty + whitespace voice_id both rejected before any client construction.
- No new validation surfaces beyond the empty guard; existing `_handle_sdk_errors`
  chain unaffected; no other handlers/tools touched.

## Security Findings
None. No hardcoded secrets (API key from `SUPERTONE_API_KEY` env); no injection
surface (`voice_id` passed as a typed SDK kwarg / path param, not interpolated);
input validated; no new dependencies.

## review_lessons.md cross-check
- **RL-001 (TypedDict nullability):** Reuses existing `CustomVoiceDict`
  (`description = NotRequired`); no new `total=False` TypedDict. PASS.
- **RL-002 (symmetric error branches):** Full matrix tested — 401, 403, 429, 5xx,
  NoResponseError, httpx.ConnectError, httpx.TimeoutException. PASS.
- **RL-003 (pagination):** N/A — single-object fetch, no pagination loop.
- **RL-004 (`NoReturn` on `_handle_sdk_errors`):** pre-existing repo-wide tech-debt,
  unchanged by this PR.
- **RL-006 (404 mapping gap):** `get_custom_voice` does not surface a "custom voice
  not found" string for a real 404, identical to existing `get_voice` /
  `edit_custom_voice` / `delete_custom_voice`. Deliberate consistency choice; the
  gap is an already-open repo-wide pattern in RL-006. NOT a new regression.

## Test Quality
All 28 added tests (client 11, handler 11, formatter 3, server 4 — including
import-fix) contain real assertions; no hollow tests. Each AC maps to at least
one test.

## Verification
- `uv run pytest` → 495 passed (28 new over prior 467).
- `uv run ruff check` → clean; `ruff format --check` → clean.
- Checkpoint `test` / `smoke` bare `python3 -m pytest` hits the known
  pre-existing pyenv-3.10 + pytest-asyncio collection INTERNALERROR
  (false-negative); `uv run pytest` + CI (3.12/3.13) are authoritative.

## Severity Summary
No Critical/High/Medium findings. No follow-up issues required.
`review_lessons.md` unchanged (no new preventable pattern). Confidence: High.
