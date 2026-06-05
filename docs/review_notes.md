# Review Notes — ISSUE-022 (PR #34)

Remove behavior env vars → per-call `output_mode`/`autoplay` (BREAKING).

## Code Review

**Verdict: APPROVE.** No Critical/High findings. Clean, well-scoped refactor.

Findings:
- Correctness — `validate_output_mode(mode)` validates the per-call argument
  against `VALID_OUTPUT_MODES`, case-normalizes, and raises with the AC error
  string `Invalid output mode: "{mode}". Valid modes: files, resources, both.`
  The quoted token preserves the original (un-normalized) input, matching the
  existing validator style in `tools.py`.
- No-API-call on invalid mode — validation runs inside the pre-client `try`
  block; `text_to_speech` returns the error string before constructing
  `SupertoneClient`. Covered by
  `test_invalid_output_mode_returns_error_no_api_call` (asserts
  `MC.assert_not_called()`).
- Env ignored for behavior — `validate_output_mode` reads no environment;
  autoplay is driven solely by the `autoplay` arg (default False). The removed
  `SUPERTONE_MCP_OUTPUT_MODE` / `SUPERTONE_MCP_AUTOPLAY` vars are referenced
  ONLY by the one-time migration warning and in docstrings — never to drive
  logic. Verified via grep.
- `resolve_output_mode()` and `resolve_autoplay()` fully removed from `src/`.
- predict_duration parity — the schema-parity test was updated (not weakened):
  `predict_duration` produces no audio, so it legitimately excludes the new
  synthesis-only output-handling params; the test now asserts synthesis-input
  parity AND that the output-handling params are absent from `predict_duration`.

Review lessons applied:
- RL-004 (NoReturn): N/A — `validate_output_mode` returns a value and raises
  only conditionally; `-> str` is correct, no always-raises helper added.
- RL-001 (TypedDict): N/A — no TypedDicts touched.

## Security Findings

- No Critical/High/Medium issues.
- The migration warning prints only env var **names** that are set, never their
  values — no risk of leaking secrets/config. Logging goes to stderr (stdout is
  reserved for the MCP stdio protocol). Informational only.
- No new injection/auth/input-validation surface; behavior moved from env to
  typed function parameters (reduces ambient/implicit config surface).

## Tests

- `uv run pytest` → 448 passed. `ruff check` + `ruff format --check` clean.
- AC coverage: all 8 ACs mapped to parameter-based tests in
  `tests/test_tools.py` (`TestValidateOutputMode`, `TestTextToSpeechHandler`)
  and `tests/test_server.py` (`TestToolRegistration`).
- Checkpoint runner caveat: bare `python3 -m pytest` hits the pre-existing
  pyenv-3.10 + pytest-asyncio collection INTERNALERROR (sprint_state.md Tooling
  Notes). `uv run pytest` + CI (3.12/3.13) are the authoritative gates.

## Follow-ups

None. No unresolved Critical/High findings; no new follow-up issues required.

---

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

---

# Review Notes: ISSUE-021 (PR #32)

SDK 0.2.3 sync: model enum + default + version pin. Reviewed by team-lead
(reviewer role) against PR #32 on branch `issue/ISSUE-021-sdk-023-sync`.

## Code Review

### Correctness
- `SUPPORTED_MODELS` and the `Model` Literal now list exactly the 7 SDK 0.2.3
  models in the same order as the installed `supertone==0.2.3`
  `APIConvertTextToSpeechUsingCharacterRequestModel` enum:
  sona_speech_1, sona_speech_2, sona_speech_2_flash, sona_speech_2t,
  sona_speech_3t, supertonic_api_1, supertonic_api_3. Matches AC exactly. PASS.
- `DEFAULT_MODEL = "sona_speech_2_flash"`. Matches AC. PASS.
- `validate_model` error-string format is unchanged
  (`Invalid model: "{model}". Supported models: {comma-joined}.`) and now
  emits the full 7-model list because it joins `SUPPORTED_MODELS`. Consistent
  with sibling validators. The AC's expected string is matched by the new
  exact-message test. PASS.
- `pyproject.toml` pins `supertone>=0.2.3,<0.3` (was bare `supertone`). PASS.
- `_MODEL_MAP` / `_PREDICT_MODEL_MAP` are built dynamically from the SDK enums,
  so both already resolve the 2 new models with no source change. Verified by
  new `TestModelMapResolution` tests + a synthesize-path enum-passing test. PASS.
- `server.py` `text_to_speech` docstring no longer states
  "sona_speech_1 (default, streaming)"; it lists all 7 models with
  sona_speech_2_flash as default and preserves the sona_speech_1 streaming
  caveat (routing deferred to ISSUE-023). PASS.

### Findings
- [Medium] `server.py` `predict_duration` docstring previously read
  `model: TTS model identifier (default: "sona_speech_1")`. Because
  `predict_duration` resolves its default from `DEFAULT_MODEL`, the actual
  default silently became `sona_speech_2_flash` with this change, leaving the
  docstring factually stale. **FIXED in review**: updated to
  `(default: "sona_speech_2_flash")`. Functional behavior was already correct
  (always used `DEFAULT_MODEL`); documentation-accuracy fix only.
- [Info] Remaining `sona_speech_1` references in `server.py` (search_voice /
  preview_voice arg examples) and `tools.py` (`format_voice_samples` docstring
  example) are illustrative `e.g.` examples for unrelated tools and remain
  valid. No change needed.

### Test Coverage (vs AC)
All 8 ACs covered by real-assertion tests; no hollow tests. See
`TestValidateModel`, `TestModelConstants`, `TestTextToSpeechHandler`
(test_tools.py), `TestModelMapResolution` (test_supertone_client.py), and the
updated `TestConstants` (test_models.py). pyproject pin and docstring ACs
verified manually in the diff. Full suite: 453 passed under `uv run pytest`.

### Review Lessons applicability
- RL-001/002/003/005/006: N/A — no TypedDict, no new client methods, no
  pagination loops, no new inspection handlers.
- RL-004 (`_handle_sdk_errors -> NoReturn`): pre-existing tech-debt, not touched
  by this PR; out of scope. Still tracked separately. No new occurrences (no
  new wrapped SDK methods).

## Security Findings
No new external input surfaces, secrets, auth changes, or new dependencies.
Tightening `supertone` to `>=0.2.3,<0.3` is security-positive (prevents an
unvetted future 0.3.x from being silently pulled in). No findings.

## Summary
No Critical or High severity findings. One Medium documentation-accuracy issue
found and fixed in-review. Confidence: High. **APPROVE.** Ship.
