# Review Notes: ISSUE-015 — Replace list_voices with search_voice (breaking)

> Reviewed: 2026-05-27
> PR: #14
> Branch: issue/ISSUE-015-search-voice
> Reviewer: Claude (Opus 4.7) via team-lead sprint pipeline
> Verdict: **Approve**
> Confidence: **High**

## Scope Recap
Removes the v0.1 `list_voices` tool and replaces it with `search_voice`,
which accepts eight optional server-side filters
(`language`, `gender`, `age`, `use_case`, `style`, `model`, `name`,
`description`). With no filters the behavior matches the legacy
`list_voices`. With any filter set, the response prefixes the numbered
voice list with a single `Filters applied: k=v, ...` line per UX spec
`docs/ux_spec.md` §2.3.

## Code Review

### Findings
| # | Severity | Area | Note |
|---|----------|------|------|
| 1 | Info | API surface | `SupertoneClient.search_voices()` exposes both `use_case` and `use_cases` (singular + plural). The handler only forwards `use_case`. Intentional — UX spec §2.3 lists only `use_case`. The plural shape is left in the client for direct SDK callers (e.g. future custom-voice search). |
| 2 | Low | Dead code | `format_voice_list(language_filter=...)` has no production callers after this PR; only the existing legacy tests exercise it. Kept for safety / test-surface continuity. Recommend a follow-up cleanup once the rest of the v0.2 tools land — but NOT in this PR (would force a churn round on legacy unit tests). |
| 3 | Info | Filter ordering | `Filters applied:` line lists filters in dict insertion order (`name, description, language, gender, age, use_case, style, model`). Deterministic. Captured in `test_all_filters_pass_through`. |
| 4 | Info | Validation policy | Only `validate_language` runs client-side (per ISSUE-015 Implementation Notes). All other enum-style filters are pass-through; the SDK / API is authoritative. Confirmed by `test_invalid_language_filter_short_circuits`. |

No Critical or High findings.

### Acceptance Criteria mapping
- **AC1** (registration) → `test_search_voice_tool_exists` + `test_list_voices_tool_removed` (PASS)
- **AC2** (no-filter → all voices) → `test_no_filter_returns_all` (PASS)
- **AC3** (multi-filter → SDK + header) → `test_multiple_filters_pass_through_and_show_in_header` (PASS)
- **AC4** (empty filtered result message) → `test_empty_result_with_filter` (PASS)
- **AC5** (401 → auth error string) → `test_auth_error_caught` (PASS)
- **AC6** (description matches UX spec) → `test_search_voice_description_matches_ux_spec` (PASS)

### Review-lessons compliance
- **RL-001** (NotRequired vs total=False) — N/A, no new TypedDicts in this PR.
- **RL-002** (symmetric connection-error testing) — PASS. `TestSearchVoiceHandler` tests 401, 429, 5xx, and connection. The shared SDK error mapping lives in `SupertoneClient.search_voices()` already covered in PR #12. No regression.
- **RL-003** (pagination tests) — N/A here; pagination is in the client layer (`SupertoneClient.search_voices`) already covered by `TestSearchVoices::test_handles_pagination` in PR #12. The `search_voice` tool just consumes the concatenated list.
- **RL-004** (NoReturn on raising helpers) — pre-existing tech-debt outside this PR's scope.
- **RL-005** (nullable test helper annotations) — `_mock_search_voices(voices=None)` follows the pattern (explicit None default, list payload always concrete). PASS.

## Security Findings
| Severity | Finding | Mitigation |
|---|---|---|
| None | No new attack surface. All filter strings are passed straight to the SDK, which forwards them as URL-encoded query params over HTTPS. No SQL/shell construction. No new env-var handling. |  — |

## Test Quality
- 13 new `TestSearchVoiceHandler` cases (real assertions, no hollow tests).
- 3 new `TestFormatVoiceList` cases for the `filters` kwarg.
- Updated `TestToolRegistration` with positive (`search_voice` exists, params optional, schema complete, description matches spec) and negative (`list_voices` removed) assertions.
- Full suite: **197/197 passing** under `uv run pytest -q`.

## Documentation
- README.md updated with breaking-change callout, new feature line, usage example, and the full 8-row `search_voice` parameter table.
- Tool description and docstrings on both `server.py` (`@mcp.tool`) and `tools.py` reference the new tool name. `text_to_speech` description and docstring no longer mention `list_voices`.
- `docs/ux_spec.md` was already updated in ISSUE-013 — no edits needed here.

## Follow-ups
1. (Low) Remove the legacy `format_voice_list(language_filter=...)` branch + its 2 tests after ISSUE-016/017/018 land — no callers will remain in the codebase by then.
2. (Info) Add a CHANGELOG entry documenting the breaking `list_voices` → `search_voice` swap before publishing 0.2.0 (tracked separately — sprint-state notes already call this out).

## Verdict
**Approve.** All six AC are satisfied with mapped tests. Implementation follows existing handler patterns (validation → client → error mapping → format), preserves backward-compat where reasonable, and matches the UX spec verbatim. No Critical or High findings.
