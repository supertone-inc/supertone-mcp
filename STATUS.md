# Project Status: Supertone TTS MCP Server

> Last updated: 2026-05-27

## Current Milestone

**M4: v0.2 implementation** — Documentation for v0.2 (voice discovery, duration prediction, voice cloning CRUD) is complete. Implementation issues ISSUE-014 through ISSUE-020 are queued.

## Issue Summary (v0.2 sprint)

| Metric | Count |
|--------|-------|
| Total v0.2 docs/impl issues | 8 (ISSUE-013–020) |
| Done | 6 (ISSUE-013, ISSUE-014, ISSUE-015, ISSUE-016, ISSUE-017, ISSUE-018) |
| In progress | 0 |
| Remaining | 2 (ISSUE-019–020) |

> v0.1 (ISSUE-001–010, 012) shipped. ISSUE-011 (MCP Registry + PulseMCP) is parked pending manual PyPI publish + registry form submission.

### v0.1 Merged PRs (history)

| PR | Title | Issues |
|----|-------|--------|
| #1 | feat(scaffold): initialize project structure | ISSUE-001 |
| #2 | feat(types): define domain types, constants, and exceptions | ISSUE-002 |
| #3 | ci: add GitHub Actions CI pipeline | ISSUE-009 |
| #4 | feat(client): implement SupertoneClient | ISSUE-003 |
| #5 | feat(tools): implement input validation and output formatting | ISSUE-004 |
| #6 | feat(tools): implement text_to_speech and list_voices handlers | ISSUE-005, ISSUE-006 |
| #7 | feat(server): implement MCP server entry point | ISSUE-007 |
| #8 | feat(packaging): complete PyPI metadata and README | ISSUE-008, ISSUE-010 |
| #9 | feat(stream): implement streaming TTS with Supertone SDK | ISSUE-012 |

### v0.2 Merged PRs

| PR | Title | Issues |
|----|-------|--------|
| #10 | docs(claude): sync PRD and ux_spec for v0.2 voice tools | ISSUE-013 |
| #12 | feat(client): add search_voices, get_voice, get_credit_balance | ISSUE-014 |
| #14 | feat(tools): replace list_voices with search_voice (breaking) | ISSUE-015 |
| #16 | feat(tools): add get_voice and get_credit_balance handlers | ISSUE-016 |
| #18 | feat(tools): add preview_voice tool (returns sample URLs) | ISSUE-017 |
| #20 | feat(tools): add predict_duration tool (client + handler) | ISSUE-018 |

## Next Steps (v0.2)

1. **ISSUE-014–020**: Implement the v0.2 tool surface — `search_voice`, `get_voice`, `get_credit_balance`, `preview_voice`, `predict_duration`, `clone_voice`, `search/edit/delete_custom_voice`. Note `list_voices` is removed (breaking change).
2. **PyPI 0.2.0**: After ISSUE-014–020 ship, bump version and publish.
3. **ISSUE-011** (parked): Create server.json, register on MCP Registry + PulseMCP.

## Key Risks

| Risk | Impact | Status |
|------|--------|--------|
| R1: Supertone API docs incomplete | High | Mitigated — using official Supertone SDK in v0.2 |
| R4: Default voice_id unknown | Medium | Mitigated — `SUPERTONE_DEFAULT_VOICE_ID` env var added in v0.1.x |
| R6: PyPI name availability | High | Open — confirm before 0.2.0 publish |
| R8 (v0.2): Breaking removal of `list_voices` | Medium | README + CHANGELOG must document migration to `search_voice` before publishing 0.2.0 |

## Documents

| Document | Status |
|----------|--------|
| `PRD.md` | v0.2 (updated for new tools, FR-012–019, US-008–011, non-goals revised) |
| `docs/requirements.md` | v0.2 (US-008–011, FR-012–019 added; out-of-scope list updated) |
| `docs/ux_spec.md` | v0.2 (tool schemas and error messages for all new tools) |
| `docs/architecture.md` | v0.2 (SDK-backed client; expanded tool surface in `tools.py`) |
| `docs/data_model.md` | v0.1 — to be revisited if cloning needs new types |
| `docs/test_plan.md` | v0.1 — to extend as ISSUE-014–020 land |
| `issues.md` | ISSUE-018 shipped (PR #20 → 86d7f49); ISSUE-019–020 queued |
