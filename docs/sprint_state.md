# Sprint State

## Meta
- Started: 2026-06-05
- Iteration: 8 / 20
- Parallel: 1 (serialized — ISSUE-022~027 all touch tools.py + server.py; parallel worktrees would conflict on merge, per v0.2 lesson)
- Status: completed
- Scope: v0.3 concept pivot — ISSUE-021~027 (ISSUE-028 release deferred to human; Manual=true, excluded). User directive: auto implement→review→merge code, NO autonomous PyPI publish.

## Issue Progress
| Issue | Status | Attempts | Last Error | Phase |
|-------|--------|----------|------------|-------|
| ISSUE-021 | done | 0 | PR #32 merged | shipped |
| ISSUE-022 | done | 1 | PR #34 merged | shipped |
| ISSUE-023 | done | 0 | PR #36 merged | shipped |
| ISSUE-024 | done | 0 | PR #38 merged | shipped |
| ISSUE-025 | done | 0 | PR #40 merged | shipped |
| ISSUE-026 | done | 0 | PR #42 merged | shipped |
| ISSUE-027 | done | 0 | PR #44 merged | shipped |

## Discovered Issues
- [iteration 1] ISSUE-021 review: predict_duration docstring stale default
  ("sona_speech_1" -> "sona_speech_2_flash"). Severity Medium. FIXED in-review
  within PR #32 (one-line doc fix); no follow-up issue needed.
- [iteration 1] Observation (not a blocking issue): no `tests/test_constants.py`
  exists, but constants are covered by `tests/test_models.py::TestConstants` and
  `tests/test_tools.py::TestModelConstants`. No real coverage gap; testgen
  auto-fill skipped. Optional future cleanup: rename/relocate constant tests.

- [iteration 2] ISSUE-022 shipped (PR #34 merged → squash 05faea2). PIPELINE
  implement→review→ship clean. `uv run pytest` 448 passed on branch + on main
  post-merge; CI test (3.12)+(3.13) green. No test gaps (changed src files
  tools.py/server.py/constants.py all covered by test_tools.py/test_server.py).
  Reused the known checkpoint-runner caveat: the bare `python3 -m pytest`
  used by the implement `test`, review `test`, and ship `smoke` checkpoints
  hit the pre-existing pyenv-3.10 + pytest-asyncio collection INTERNALERROR
  (false-negative); treated `uv run pytest` + CI as authoritative per the
  documented Tooling Notes. No developer/reviewer Critical/High findings →
  no follow-up issues created.

- [iteration 3] ISSUE-023 shipped (PR #36 merged → squash 626ccc8). PIPELINE
  implement→review→ship clean. GH issue #35 created + closed via PR.
  `uv run pytest` 456 passed on branch + on main post-merge; CI test (3.12) +
  (3.13) green; publish/publish-registry correctly skipped (no release).
  Default routing flipped from synthesize_stream to one-shot synthesize;
  fail-fast sona_speech_1-only streaming validation added. Reused the known
  checkpoint-runner caveat: implement `test`, review `test`, and ship `smoke`
  bare `python3 -m pytest` hit the pre-existing pyenv-3.10 + pytest-asyncio
  collection INTERNALERROR (false-negative); treated `uv run pytest` + CI as
  authoritative per Tooling Notes. Review: no Critical/High findings (one Low
  parity observation, not a regression) → no follow-up issues. Test-gap
  auto-fill: changed src files tools.py/server.py both covered by
  test_tools.py/test_server.py → testgen skipped.

- [iteration 4] ISSUE-024 shipped (PR #38 merged → squash 7a3d2fe; GH issue #37
  created + closed via PR). PIPELINE implement→review→ship clean. Removed the
  300-char hard cap: deleted `validate_text_max_length` (its only caller was
  `predict_duration`) + its call site, dropped the now-unused `TEXT_MAX_LENGTH`
  import; `validate_text` (empty guard) retained; updated text_to_speech +
  predict_duration descriptions/docstrings to note auto-chunking + credit/latency
  scaling. `uv run pytest` 456 passed on branch + on main post-merge; CI test
  (3.12)+(3.13) green; publish/publish-registry correctly skipped (no release).
  Reused the known checkpoint-runner caveat: implement `test`, review `test`, and
  ship `smoke` bare `python3 -m pytest` hit the pre-existing pyenv-3.10 +
  pytest-asyncio collection INTERNALERROR (false-negative); treated uv+CI as
  authoritative per Tooling Notes. Review: no Critical/High/Medium findings, no
  security concerns → no follow-up issues. Test-gap auto-fill: changed src files
  tools.py/server.py both covered by test_tools.py/test_server.py → testgen skipped.

- [iteration 5] ISSUE-025 shipped (PR #40 merged → squash 2a826ba; GH issue #39
  created + closed via PR). PIPELINE implement→review→ship clean. Exposed SDK
  0.2.3 `include_phonemes` (bool, default False) + `normalized_text` (str | None,
  default None) on `text_to_speech`, threaded through `client.synthesize` AND
  `synthesize_stream` to `create_speech_async` / `stream_speech_async` (SDK kwarg
  names verified in the installed SDK before forwarding). server.py registers
  both with schema-visible Field descriptions; `normalized_text` doc states it
  applies only to sona_speech_2 / sona_speech_2_flash (no client-side rejection —
  other models ignore it per SDK). Updated the `predict_duration` parity test to
  classify the two new audio-only params as synthesis-output-only (predict_duration
  produces no audio). `uv run pytest` 467 passed on branch + on main post-merge
  (+11 new tests over 456); CI test (3.12)+(3.13) green; publish/publish-registry
  correctly skipped (no release). Reused the known checkpoint-runner caveat:
  implement `red`/`test`, review `test`, and ship `smoke` bare `python3 -m pytest`
  hit the pre-existing pyenv-3.10 + pytest-asyncio collection INTERNALERROR
  (false-negative for green phases); treated uv+CI as authoritative per Tooling
  Notes. Review: no Critical/High/Medium findings, no security concerns → no
  follow-up issues; review_lessons.md unchanged (no new preventable pattern).
  Test-gap auto-fill: changed src files server.py/supertone_client.py/tools.py all
  covered by test_server.py/test_supertone_client.py/test_tools.py → testgen skipped.

- [iteration 6] ISSUE-026 shipped (PR #42 merged -> squash 843859b; GH issue #41
  created + closed via PR). PIPELINE implement->review->ship clean. Added a new
  read-only tool get_custom_voice(voice_id): client wrapper
  SupertoneClient.get_custom_voice wrapping custom_voices.get_custom_voice_async
  (maps voice_id/name/optional description via the shared _handle_sdk_errors
  pattern); tools.get_custom_voice handler (fail-fast empty/whitespace voice_id
  reuses the EXACT existing "voice_id must not be empty." string, mirrors
  get_voice error handling) + format_custom_voice_detail formatter reusing the
  format_custom_voice_list field style; server.py registration with required
  voice_id. VERIFIED SDK GetCustomVoiceResponse shape against the installed SDK
  (models/getcustomvoiceresponse.py): only voice_id, name, nullable description
  exist -- there is NO created_at field, so the spec's "optional created_at" was
  deliberately NOT mapped (truthful to source data, RL-001-consistent; same
  decision already documented for format_custom_voice_list). Reused existing
  CustomVoiceDict (no new TypedDict). `uv run pytest` 495 passed on branch + on
  main post-merge (+28 new tests over 467); CI test (3.12)+(3.13) green;
  publish/publish-registry correctly skipped (no release). ruff check + format
  clean (applied 2 pre-existing import-group blank-line fixes that the
  uncommitted-on-main ruff.toml now enforces). Reused the known checkpoint-runner
  caveat: implement red/test, review test, and ship smoke bare `python3 -m pytest`
  hit the pre-existing pyenv-3.10 + pytest-asyncio collection INTERNALERROR
  (false-negative for green phases); treated uv+CI as authoritative per Tooling
  Notes. Review: no Critical/High/Medium findings, no security concerns -> no
  follow-up issues; review_lessons.md unchanged (no new preventable pattern).
  Test-gap auto-fill: changed src files server.py/supertone_client.py/tools.py all
  covered by test_server.py/test_supertone_client.py/test_tools.py -> testgen skipped.

- [iteration 7] ISSUE-027 shipped (PR #44 merged -> squash 2fd077f; GH issue #43
  created + closed via PR). FINAL v0.3 code issue. PIPELINE implement->review->ship
  clean. Added two read-only usage tools: get_usage_history() wrapping
  usage.get_usage_async (advanced analytics) and get_voice_usage(voice_id)
  wrapping usage.get_voice_usage_async. SDK 0.2.3 signatures + response shapes
  VERIFIED against the installed SDK before mapping (usage.py,
  usageanalyticsresponse/usagebucket/usageresult,
  getusagelistv1response/getusageresponsev1data): get_usage_async REQUIRES
  start_time/end_time (RFC3339) -> wrapper supplies a default 30-day UTC window;
  get_voice_usage_async REQUIRES start_date/end_date (YYYY-MM-DD) and has NO
  voice_id param, so the wrapper fetches the date-range list and filters records
  client-side by voice_id (the only truthful way to honor both AC + SDK, recall
  ISSUE-026 spec-vs-SDK drift lesson). Only fields that actually exist are mapped;
  SDK api_key (sensitive) + thumbnail_url (out of scope) deliberately NOT
  surfaced -- no invented fields. 5 new TypedDicts (UsageResultDict/UsageBucketDict/
  UsageHistoryDict/VoiceUsageRecordDict/VoiceUsageDict) follow RL-001 (required by
  default, NotRequired only for genuinely nullable). Both wrappers reuse the
  shared _handle_sdk_errors except-tuple; fail-fast empty/whitespace voice_id
  reuses the EXACT existing "voice_id must not be empty." string; empty usage
  returns a "no usage" message (NOT an error) per AC. server.py registers both
  (get_usage_history no params; get_voice_usage required voice_id). 53 new tests
  (RL-002 symmetric error branches on both client methods). `uv run pytest` 548
  passed on branch + on main post-merge (+53 over 495); CI test (3.12)+(3.13)
  green on PR #44 AND on the post-merge main push run; publish/publish-registry
  correctly skipped (no release). ruff check + format clean. Reused the known
  checkpoint-runner caveat: implement red/test, review test, and ship smoke bare
  `python3 -m pytest` hit the pre-existing pyenv-3.10 + pytest-asyncio collection
  INTERNALERROR (false-negative for green phases; re-confirmed identical on
  untouched main this iteration); treated uv+CI as authoritative per Tooling
  Notes; did NOT revert the merge. Review: APPROVE, no Critical/High findings ->
  no follow-up issues created. One non-blocking Medium follow-up logged in
  review_notes.md: the two usage endpoints raise SupertoneDefaultError in
  production which _handle_sdk_errors does not map (pre-existing RL-006-class gap,
  consistent across the whole codebase, AC satisfied as written since tests mock
  the typed UnauthorizedErrorResponse which the wrappers DO map). review_lessons.md
  unchanged (RL-006 already catalogued; no new preventable pattern). Test-gap
  auto-fill: changed src files models.py/server.py/supertone_client.py/tools.py all
  covered by their test_*.py -> testgen skipped. v0.3 CODE SCOPE COMPLETE
  (ISSUE-021..027 all shipped); ISSUE-028 (docs/release) remains Manual/excluded
  -- no autonomous publish/version-bump per the user directive.

## Escalations
- (none) — ISSUE-021..ISSUE-027 all shipped cleanly. v0.3 code scope complete.
  ISSUE-028 (release) deferred to human (Manual=true, excluded from this sprint).

## Tooling Notes
- The implement/review/ship `test` and `smoke` checkpoints (verify_checkpoint.py
  `_run_python_tests_with_coverage` / `verify_ship_smoke`) invoke a BARE
  `python3 -m pytest`, which on this machine resolves to pyenv 3.10.15 with
  pytest 9.0.3 + an incompatible pytest-asyncio. That combo raises a collection
  INTERNALERROR (`'Package' object has no attribute 'obj'`) and reports a false
  failure. This reproduces IDENTICALLY on untouched `main` (pre-existing, not
  caused by any sprint change). Authoritative test results used instead:
  `uv run pytest` => 453 passed (453 on branch, 453 on main post-merge), and
  GitHub Actions CI `test (3.12)` + `test (3.13)` => pass. Recommend a kit/CI
  fix to make the checkpoint runner use the project toolchain (`uv run pytest`)
  or pin a compatible pytest-asyncio in the checkpoint interpreter.
