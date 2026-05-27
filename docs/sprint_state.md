# Sprint State

## Meta
- Started: 2026-05-27
- Iteration: 4 / 20
- Parallel: 1 (serialized — ISSUE-015/016/018/019 all touch tools.py and server.py)
- Status: running
- Scope: v0.2 autonomous phase — ISSUE-015~020 (ISSUE-011 marked Manual, excluded)

## Issue Progress
| Issue | Status | Attempts | Last Error | Phase | PR |
|-------|--------|----------|------------|-------|----|
| ISSUE-013 | done | 1 | - | shipped | #10 (merged 9c01cc4) |
| ISSUE-014 | done | 1 | - | shipped | #12 (merged 22c5bd4) |
| ISSUE-015 | done | 1 | - | shipped | #14 (merged dcee0fd) |
| ISSUE-016 | done | 1 | - | shipped | #16 (merged 4875195) |
| ISSUE-017 | done | 1 | - | shipped | #18 (merged 61be53e) |
| ISSUE-018 | backlog | 0 | - | backlog | - |
| ISSUE-019 | backlog | 0 | - | backlog | - |
| ISSUE-020 | backlog | 0 | - | backlog | - |

## Discovered Issues
- (none — no Critical/High findings during implement or review for this docs-only change)
- [iteration 3] RL-006 (review_lessons): Map every documented error path in `_handle_sdk_errors` before promising it in a handler. Surfaced by PR #16 (`get_voice` has no 404→`Voice not found: "..."` mapping per ux_spec §4.4). Affects ISSUE-017 (`preview_voice`) and ISSUE-019 (`edit_custom_voice`/`delete_custom_voice`). Candidate tech-debt issue: wire 404 mapping into supertone_client.py._handle_sdk_errors.
- [iteration 3] RL-001 NOT applied to `VoiceDetailDict` (models.py:90) — still declared `TypedDict, total=False`, making `voice_id`/`name`/`use_case` etc. NotRequired. PR #16's `format_voice_detail` accesses these directly (tools.py:563/564/572). Pytest 235/235 passing because mocks include all keys, but pyright correctly flags as runtime-unsafe. ISSUE-017 will fold the fix into its worktree (apply RL-001: default-required + NotRequired only for `samples`/`thumbnail_image_url`).
- **Pre-existing pyright tech debt** (surfaced 2026-05-27 by IDE diagnostics on ISSUE-015 worktree; not introduced by PR #14): `tools.py` lines 12 (mutagen private import), 337 (output_dir possibly unbound), 401 (Optional.parent), 425 (str|None → file_path), 435 (bytes|None → b64encode); `tests/test_tools.py` lines 533/684/717/785/831/859 (audio mode helper types). All originate from commits b9928104/27c172b1/e37fe300 (ISSUE-012 era). Pytest 197/197 passing — runtime-safe. Candidate for a future tech-debt issue.

## Escalations
- (none)

## Notes
- ISSUE-013 PR #10 merged at commit 9c01cc4. PRD.md, docs/requirements.md, docs/architecture.md, docs/ux_spec.md, STATUS.md all updated for v0.2.
- `list_voices` is removed in v0.2 (breaking change, no deprecated alias). README/CHANGELOG must call this out before publishing 0.2.0.
- User chose progressive execution: ISSUE-013 alone, then review, then ISSUE-014, then 015~020.
- ISSUE-014 PR #12 merged at commit 22c5bd4. Smoke test on main: 184/184 passing.
- Sprint resumed 2026-05-27 per user instruction — proceed through ISSUE-015~020, parallel=1.
- ISSUE-011 is explicitly OUT OF SCOPE for the v0.2 sprint (requires manual PyPI publish + MCP Registry + PulseMCP web form).
- The uncommitted `issues.md` changes on main (which add ISSUE-012/013 specs) are intentionally left for the user; ISSUE-013's scope excluded touching issues.md.
- ISSUE-015 PR #14 merged at commit dcee0fd. Smoke test on main: 197/197 passing. `list_voices` removed; `search_voice` registered with full 8-filter schema.
- ISSUE-016 PR #16 merged at commit 4875195. Smoke test on main: 235/235 passing. `get_voice` + `get_credit_balance` registered; UX spec §4.4/§4.5 compliant; RL-006 (404-mapping gap) logged as a follow-up tech-debt candidate.
- ISSUE-017 PR #18 merged at commit 61be53e. Smoke test on main: 267/267 passing. `preview_voice` tool registered with `voice_id` required + `language/style/model` optional filters; output matches UX spec §4.6 exact format. RL-001 fix-along applied to `VoiceDetailDict` (default-required + `NotRequired` on `samples`/`thumbnail_image_url`); pyright now shows 0 errors on `models.py` and PR #16's `format_voice_detail` type errors at `tools.py:563/564/572` are resolved. Remaining 5 pyright errors on `tools.py` are unchanged ISSUE-012-era tech debt. RL-006 (404 mapping) still applies to `preview_voice` — explicitly out of scope per task instruction.
