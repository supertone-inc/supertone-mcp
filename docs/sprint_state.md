# Sprint State

## Meta
- Started: 2026-05-27
- Iteration: 1 / 20
- Parallel: 1
- Status: paused (ISSUE-014 shipped; awaiting user decision before continuing to ISSUE-015)
- Scope: ISSUE-013, ISSUE-014 shipped via progressive sprint per user decision

## Issue Progress
| Issue | Status | Attempts | Last Error | Phase | PR |
|-------|--------|----------|------------|-------|----|
| ISSUE-013 | done | 1 | - | shipped | #10 (merged 9c01cc4) |
| ISSUE-014 | done | 1 | - | shipped | #12 (merged 22c5bd4) |

## Discovered Issues
- (none — no Critical/High findings during implement or review for this docs-only change)

## Escalations
- (none)

## Notes
- ISSUE-013 PR #10 merged at commit 9c01cc4. PRD.md, docs/requirements.md, docs/architecture.md, docs/ux_spec.md, STATUS.md all updated for v0.2.
- `list_voices` is removed in v0.2 (breaking change, no deprecated alias). README/CHANGELOG must call this out before publishing 0.2.0.
- User chose progressive execution: ISSUE-013 alone, then review, then ISSUE-014, then 015~020.
- ISSUE-014 PR #12 merged at commit 22c5bd4. Smoke test on main: 184/184 passing.
- **Sprint paused after ISSUE-014 per user instruction. Do NOT auto-pickup ISSUE-015.**
- ISSUE-011 is explicitly OUT OF SCOPE for the v0.2 sprint (requires manual PyPI publish + MCP Registry + PulseMCP web form).
- The uncommitted `issues.md` changes on main (which add ISSUE-012/013 specs) are intentionally left for the user; ISSUE-013's scope excluded touching issues.md.
