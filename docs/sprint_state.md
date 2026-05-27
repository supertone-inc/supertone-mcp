# Sprint State

## Meta
- Started: 2026-05-27
- Iteration: 2 / 20
- Parallel: 1 (serialized — ISSUE-015/016/018/019 all touch tools.py and server.py)
- Status: running
- Scope: v0.2 autonomous phase — ISSUE-015~020 (ISSUE-011 marked Manual, excluded)

## Issue Progress
| Issue | Status | Attempts | Last Error | Phase | PR |
|-------|--------|----------|------------|-------|----|
| ISSUE-013 | done | 1 | - | shipped | #10 (merged 9c01cc4) |
| ISSUE-014 | done | 1 | - | shipped | #12 (merged 22c5bd4) |
| ISSUE-015 | done | 1 | - | shipped | #14 (merged dcee0fd) |
| ISSUE-016 | backlog | 0 | - | backlog | - |
| ISSUE-017 | backlog | 0 | - | backlog | - |
| ISSUE-018 | backlog | 0 | - | backlog | - |
| ISSUE-019 | backlog | 0 | - | backlog | - |
| ISSUE-020 | backlog | 0 | - | backlog | - |

## Discovered Issues
- (none — no Critical/High findings during implement or review for this docs-only change)

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
