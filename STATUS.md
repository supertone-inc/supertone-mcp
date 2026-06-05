# Project Status: Supertone MCP Server

> Last updated: 2026-06-05

## Current Milestone

**0.2.0 — Composable SDK toolkit (shipped to `main`, releasing via `v0.2.0` tag).**
The server is reframed from "TTS the LLM's output" to a composable toolkit the LLM
assembles: synthesis with per-call control (`output_mode`/`autoplay`/`streaming`/`model`),
voice discovery & preview, duration/credit prediction, usage tracking, and full
custom-voice CRUD — across 31 languages and 7 models.

> Versioning note: the discovery/cloning work historically called "v0.2" in the planning
> docs and the composable-toolkit pivot called "v0.3" in `issues.md` are released **together
> as package version 0.2.0** (the version field never shipped a standalone 0.2.0 before).

## Issue Summary

| Metric | Count |
|--------|-------|
| v0.3 batch (ISSUE-021–028) | 8 |
| Done | 8 (all shipped) |
| In progress | 0 |
| Remaining | 0 |

> v0.1 (ISSUE-001–010, 012) and the v0.2 discovery/cloning issues (ISSUE-013–020) previously shipped.
> ISSUE-011 (MCP Registry registration) is handled by the `publish-registry` CI job on the `v0.2.0` tag.

### v0.3 Merged PRs (composable-toolkit pivot → 0.2.0)

| PR | Title | Issue |
|----|-------|-------|
| #32 | sync 7-model enum + DEFAULT_MODEL=sona_speech_2_flash + SDK pin | ISSUE-021 |
| #34 | per-call output_mode/autoplay params, drop behavior env vars (BREAKING) | ISSUE-022 |
| #36 | per-call streaming param + synthesize/stream routing + sona_speech_1 validation | ISSUE-023 |
| #38 | relax 300-char hard limit, delegate long text to SDK auto-chunk | ISSUE-024 |
| #40 | expose include_phonemes + normalized_text pass-through params | ISSUE-025 |
| #42 | add get_custom_voice tool | ISSUE-026 |
| #44 | add get_usage_history + get_voice_usage tools | ISSUE-027 |
| #46 | README reframe + 31-language sync + 0.2.0 release prep | ISSUE-028 |

## Next Steps

1. **Release 0.2.0**: push the `v0.2.0` tag → CI `publish` (PyPI, trusted publishing) + `publish-registry` (MCP Registry).
2. **Post-release**: verify the PyPI page + MCP Registry listing; smoke-test `uvx supertone-mcp` from a clean client.
3. **Follow-ups** (non-blocking): rotate the plaintext API key in `.mcp.json` and remove it from version control; add a `SUPPORTED_*`-vs-SDK-enum guard test to catch future SDK drift loudly.

## Key Risks

| Risk | Impact | Status |
|------|--------|--------|
| R6: PyPI 0.2.0 availability | High | **Cleared** — PyPI holds only 0.1.0/0.1.1; 0.2.0 is free |
| R8: Breaking changes (env→param, autoplay/streaming defaults, list_voices removal) | Medium | Mitigated — README "Breaking changes & migration (0.2.0)" + CHANGELOG document the migration |
| R9: Plaintext API key committed in `.mcp.json` | Medium | Open — rotate + remove from tracked file (follow-up) |
| R10: Constant lists drift from SDK enums | Low | Observed twice (models, languages); guard-test follow-up proposed |

## Documents

| Document | Status |
|----------|--------|
| `PRD.md` | v0.3 (composable SDK toolkit pivot) |
| `docs/requirements.md` | v0.3 (FR-001 revised; FR-020–022; US-012–017; NFR-009) |
| `docs/ux_spec.md` | v0.3 (new params + error strings; new tools) |
| `docs/architecture.md` | v0.3 (env→param, synthesize/stream routing, SDK pin, new tools) |
| `docs/data_model.md` | v0.3 (new request-shape fields; usage response shapes) |
| `docs/test_plan.md` | v0.3 (streaming routing, output_mode, new tools, relaxed length) |
| `CHANGELOG.md` | 0.2.0 entry (pending `v0.2.0` tag) |
| `issues.md` | ISSUE-021–028 all shipped (PRs #32–#46) |
