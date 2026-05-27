# Review Notes: ISSUE-020 (PR #23)

## Reviewer Summary

PR #23 implements `search_custom_voice`, `edit_custom_voice`, and `delete_custom_voice` per the v0.2 spec. The implementation mirrors the established patterns of `search_voices` / `clone_voice` / `get_voice`. All eight ACs are exercised by 83 new tests; the full suite is 434/434 passing.

## AC Verification

| AC | Status | Test |
|----|--------|------|
| #1 search returns numbered list w/ name/desc/id | PASS | `TestSearchCustomVoiceHandler::test_happy_path_returns_numbered_list` |
| #2 filters work | PASS | `test_filters_forwarded_to_client` + multi-page test |
| #3 edit happy path message | PASS | `TestEditCustomVoiceHandler::test_happy_path_returns_success_message` |
| #4 edit no-fields validation | PASS | `test_no_fields_returns_validation_error_without_api_call` |
| #5 delete happy path message | PASS | `TestDeleteCustomVoiceHandler::test_happy_path_returns_success_message` |
| #6 delete empty/whitespace validation | PASS | `test_empty_voice_id_*` + `test_whitespace_voice_id_*` |
| #7 401 auth string on all three | PASS | `test_auth_error_returns_formatted_string` × 3 |
| #8 tools registered | PASS | `test_search_custom_voice_tool_exists` + edit + delete |

## RL-Compliance Audit

- **RL-001 (NotRequired vs total=False)**: `CustomVoiceDict` declared with default-required + `NotRequired[str | None]` only on `description` (the sole nullable SDK field). Type-checker-safe consumers (`format_custom_voice_list`) can access required fields without `.get()` guards.
- **RL-002 (symmetric error coverage)**: each of the three new SDK wrappers exercises the full error matrix (Unauthorized, Forbidden, TooManyRequests, InternalServerError, NoResponseError, httpx.ConnectError, httpx.TimeoutException). Tests counted: search 7 / edit 7 / delete 7.
- **RL-003 (multi-page pagination)**: `TestSearchCustomVoices::test_handles_pagination` uses `side_effect=[page1_with_token, page2_with_token, page3_terminal]` and asserts both concatenated voice_ids and the next_page_token threading in subsequent calls.
- **RL-004 (NoReturn on `_handle_sdk_errors`)**: NOT fixed (out of scope per task brief). New pyright errors introduced: **+5**, all the established "response possibly unbound" pattern on the three new methods (search wrapper has 2 occurrences because it reads `response.items` and `response.next_page_token` in a loop). Frequency now bumps from 3 to 4 across all PRs.
- **RL-005 (typed nullable test-helper defaults)**: `_make_custom_voice_item(..., description: str | None = "warm narrator")` declares the nullable param up front; same for `_make_update_custom_voice_response`.
- **RL-006 (404 mapping gap)**: still open and applies to BOTH new handlers (`edit_custom_voice` and `delete_custom_voice` would 404 for nonexistent voice_ids). UX spec §4.10/§4.11 promise `Custom voice not found: "{voice_id}".` Handler docstrings in both functions explicitly document the gap and reference RL-006. Per task brief: do NOT fix `_handle_sdk_errors` in this PR — separate tech-debt issue.

## Pyright Delta

| File | Baseline | After PR | Delta |
|------|----------|----------|-------|
| `supertone_client.py` | 24 | 29 | +5 (RL-004) |
| `tools.py` | 5 | 5 | 0 |
| `models.py` | 0 | 0 | 0 |
| `server.py` | 0 | 0 | 0 |
| **Total** | **29** | **34** | **+5** |

All five new errors are RL-004 occurrences on the three new wrappers; no NEW pyright-error categories introduced. Pre-existing 5 errors on `tools.py` (ISSUE-012 era) are untouched.

## Docs/SDK Drift Observed (Logged, NOT Fixed in This PR)

1. **UX spec §4.9 "Created" line**: the example output shows `Created: 2026-05-26` but the SDK schema (`GetCustomVoiceResponse`) exposes only `voice_id`, `name`, `description` — no created-at field. `format_custom_voice_list` intentionally omits the line to keep output truthful. Recommend a docs-only follow-up to either (a) drop the line from the UX spec or (b) request the field in the SDK.
2. **AC #4 wording vs UX spec §4.10**: AC says `"Provide at least one of: name, description."` while UX spec says `"At least one of name or description must be provided."` — handler follows the AC verbatim per the established convention (issue wording priority).
3. **architecture.md §pagination note** states `search_custom_voice` "relies on the SDK's default page size" but the issue's Implementation Notes + RL-003 demand the same auto-pagination pattern as `search_voices`. Implementation follows the issue (multi-page loop with token threading). Recommend updating `architecture.md` to reflect the implemented behavior.

## Risk Assessment

- **Behavioral risk**: Low. Three new tools, each behind input validation guards, no impact on existing tools.
- **Security risk**: None new. `delete_custom_voice` has no in-tool confirmation gate but per UX spec §4.11 this is intentional (LLM is the gate via tool-description text). Tool description carries the "IRREVERSIBLE — confirm with the user" warning per `test_delete_custom_voice_description_warns_irreversible`.
- **Performance risk**: `search_custom_voices` paginates server-side at `page_size=100`. For typical custom-voice catalogs (small, since these are user-created clones), this is sub-second.

## Findings (severity)

| # | Severity | Finding | Action |
|---|----------|---------|--------|
| 1 | Low | RL-004 frequency bumped 3 to 4 | Already-tracked tech-debt issue, no action in this PR |
| 2 | Low | RL-006 (404 mapping) widens scope to edit+delete | Already-tracked tech-debt issue, no action in this PR |
| 3 | Low | UX spec §4.9 "Created" line is unimplementable from SDK schema | Recommend docs follow-up |
| 4 | Low | architecture.md pagination note diverges from implementation | Recommend docs follow-up |

No Critical / High severity findings.

## Recommendation

**APPROVE.** Ship.
