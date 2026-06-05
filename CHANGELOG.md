# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semver.

## [0.2.0] — unreleased (merged to main; pending `v0.2.0` tag)

This release reframes the server as a **composable SDK toolkit** — the LLM assembles
discrete tools rather than issuing a single "speak this" command — and moves behavior
control from environment variables to per-call tool parameters.

### Added
- **`text_to_speech` per-call controls:** `output_mode` (files/resources/both), `autoplay`,
  `streaming` (sona_speech_1-only, validated fail-fast), `include_phonemes`, `normalized_text`,
  and explicit `model` selection.
- **New tools:** `get_custom_voice`, `get_usage_history`, `get_voice_usage`.
- **Voice discovery & cloning** (search/get/preview voices, credit balance, duration prediction,
  clone + custom-voice CRUD).
- Model set synced to SDK 0.2.3 (7 models incl. `sona_speech_3t`, `supertonic_api_3`).
- Language support synced to **31 languages**.

### Changed
- **BREAKING:** `SUPERTONE_MCP_OUTPUT_MODE` and `SUPERTONE_MCP_AUTOPLAY` env vars removed —
  use the `output_mode` / `autoplay` parameters instead.
- **BREAKING:** `autoplay` default changed `true` → `false`; `streaming` default is `false`.
- Default model changed `sona_speech_1` → `sona_speech_2_flash`.
- `list_voices` removed; use `search_voice` (call with no args for the full catalog).
- The hard 300-character limit is removed — long text is auto-chunked by the SDK.
- `supertone` SDK dependency pinned to `>=0.2.3,<0.3`.

### Migration
See the "Breaking changes & migration (0.2.0)" section in the README for the env→param mapping.

## [0.1.x]
- Initial MCP server: `text_to_speech` + voice listing, PyPI packaging, MCP Registry metadata.
