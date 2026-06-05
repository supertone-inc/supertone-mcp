# Review Notes — ISSUE-027 (PR #44, get_usage_history + get_voice_usage)

Two new read-only MCP tools exposing Supertone usage analytics. Senior review +
security audit. Branch: issue/ISSUE-027-usage-tools.

## Code Review

### Scope verified against AC
- AC1 (usage-history payload -> formatted per-period summary): covered by
  `TestFormatUsageHistory::test_renders_per_period_summary` and
  `TestGetUsageHistoryHandler::test_happy_path_returns_formatted_summary`. PASS.
- AC2 (empty usage -> clear "no usage" message, NOT an error): formatter returns
  `"No usage recorded for the selected period."`; test asserts `"error"` absent.
  PASS.
- AC3 (voice usage -> formatted summary for that voice): covered by
  `TestFormatVoiceUsage::test_renders_voice_summary` and the handler happy path.
  PASS.
- AC4 (empty/whitespace voice_id -> exact `voice_id must not be empty.`, no API
  call): `test_empty_voice_id_*` / `test_whitespace_voice_id_*` assert
  `SupertoneClient` is never constructed (`MC.assert_not_called()`). Reuses the
  EXACT existing string from `get_voice`/`get_custom_voice`. PASS.
- AC5 (either tool + mocked auth error -> standard auth string via
  `_handle_sdk_errors`): client wrappers map `UnauthorizedErrorResponse` /
  `ForbiddenErrorResponse` -> `SupertoneAuthError`; handlers return
  `"Authentication failed. Please verify your SUPERTONE_API_KEY."` Covered for
  BOTH methods (client layer) and BOTH handlers. PASS.
- AC6 (tools/list includes both; get_voice_usage requires voice_id):
  `TestUsageToolsRegistration` (existence, required/optional params,
  descriptions). PASS.

### SDK fidelity (truthful-to-source — recall ISSUE-026)
Installed supertone 0.2.3 inspected before mapping:
- `usage.get_usage_async(*, start_time, end_time, bucket_width=DAY,
  breakdown_type=None, page_size=10, next_page_token=None)` ->
  `UsageAnalyticsResponse(data: list[UsageBucket], total: float,
  next_page_token)`. start/end REQUIRED (RFC3339). The wrapper supplies a
  computed default 30-day UTC window and forwards only the optional params the
  caller sets.
- `usage.get_voice_usage_async(*, start_date, end_date)` ->
  `GetUsageListV1Response(usages: list[GetUsageResponseV1Data])`. start/end
  REQUIRED (YYYY-MM-DD). **No voice_id parameter exists** — it is a date-range
  list, so the wrapper filters records client-side by `voice_id`. The only
  truthful way to honor both the AC and the SDK. Documented in the docstring and
  PR body.
- Only fields that actually exist on the SDK models are mapped. `UsageResult.
  api_key` (sensitive) and `GetUsageResponseV1Data.thumbnail_url` (out of scope)
  are intentionally NOT surfaced. No invented fields — avoids the ISSUE-026
  spec-vs-SDK drift class.

### Lessons compliance
- RL-001: five new TypedDicts default total=True; only genuinely nullable SDK
  fields are `NotRequired`, verified against SDK `Optional[...]` declarations.
  PASS.
- RL-002: both new client methods exercise the full error-branch matrix
  (Unauthorized, Forbidden, 429, 5xx, NoResponseError, ConnectError,
  TimeoutException). PASS.
- RL-004: `_handle_sdk_errors` remains `-> None` (pre-existing tech-debt, not
  introduced here; both wrappers reuse the shared helper). No change.

### Quality
- Handlers mirror the established `get_credit_balance` / `get_voice` patterns
  exactly (api-key resolution, client lifecycle in try/finally with `aclose()`,
  identical error-string mapping). Consistent, maintainable.
- ruff check + ruff format: clean on src and tests.
- `uv run pytest`: 548 passed (495 baseline + 53 new). CI `test (3.12)` +
  `test (3.13)`: PASS. publish/publish-registry correctly skipped (no release).

## Security Findings
- No secrets, no injection surface (read-only GET endpoints; date strings are
  server-generated, not user-controlled). The SDK `api_key` field returned by the
  usage endpoint is deliberately NOT echoed into any user-facing output. No
  Critical/High security findings.

## Follow-ups (non-blocking)
- [Medium] RL-006 (error-mapping completeness): in production the two usage
  endpoints raise `errors.SupertoneDefaultError` for 401/4XX/5XX (see SDK
  `usage.py`). `_handle_sdk_errors` does NOT map `SupertoneDefaultError`, so a
  real auth/server error from these endpoints would bubble raw instead of the
  friendly UX string. NOT a regression: it mirrors the exact documented gap
  already tracked for `get_voice` / `preview_voice` / `edit_custom_voice`
  (RL-006, no 404 mapping) and is consistent with the whole codebase's posture.
  The AC is satisfied as written (it says "verify via `_handle_sdk_errors`", and
  tests mock the typed `UnauthorizedErrorResponse`, which the wrappers DO map).
  The real fix — mapping `SupertoneDefaultError` by `raw_response.status_code`
  in `_handle_sdk_errors` — is a cross-cutting tech-debt item to be handled once
  for ALL wrappers, not bolted onto this PR. Logged in docs/sprint_state.md; no
  blocking change applied. Severity Medium -> does not spawn a P0/P1 follow-up
  per the review-triage rules.

## Verdict
APPROVE. All ACs met, tests green (uv + CI), lessons honored, SDK-truthful. No
Critical/High findings requiring in-review fixes. Confidence: High.
