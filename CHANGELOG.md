# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semver.

## [0.3.1] — 2026-06-17

Bug-fix release for `merge_audio_files` (reported against 0.3.0).

### Fixed
- **WAV merge `Duration` mis-reported (ISSUE-032).** ffmpeg rendered to a non-seekable
  `pipe:1`, so it could not patch the WAV RIFF/`data` chunk size headers and wrote the
  `0xFFFFFFFF` placeholder — read back as ~24347s (and the on-disk `.wav` header was itself
  corrupt). The merge now renders to a seekable temp file and reads the bytes back, so the
  header is finalized and the reported duration is correct. MP3 output was unaffected.
- **`crossfade_ms` intermittently truncated short clips (ISSUE-033).** ffmpeg's `acrossfade`
  filter is non-deterministic on short / similar-length inputs, occasionally dropping a whole
  stream (e.g. `1.36s + 1.36s, cf=500` → 0.86s instead of 2.22s on some runs). Replaced it with
  a deterministic manual crossfade (`afade` in/out + `adelay` offset + `amix=normalize=0`),
  fed each input's duration. Concat and `gap_ms` modes were already correct.

### Tests
- Added env-gated real-ffmpeg regression tests (`SUPERTONE_RUN_FFMPEG_TESTS=1`, skipped in
  default CI) pinning true WAV duration and crossfade determinism (10× repeat + 3-input chain).

## [0.3.0] — 2026-06-16

Audio-assembly milestone (v0.4 in planning docs): the toolkit can now stitch its own
`text_to_speech` outputs into a single deliverable without leaving the agent.

### Added
- **`merge_audio_files` tool** — concatenate two or more local audio files (mp3/wav) into
  one via a **bundled ffmpeg** (`imageio-ffmpeg`; no system ffmpeg required, NFR-001).
  Supports plain concat, silence-gap insertion (`gap_ms`), and crossfade blending
  (`crossfade_ms`, mutually exclusive with `gap_ms`). Output format auto-detected
  (all-same-ext → that ext; mixed → mp3) or forced via `output_format`. A single input
  is returned as-is. Input streams are normalized (sample rate / channel layout / format)
  before merging so heterogeneous clips combine correctly. Design: `docs/specs/SPEC-029.md`.

### Dependencies
- Added `imageio-ffmpeg>=0.5,<1.0` (bundles the ffmpeg binary).

## [0.2.0] — released (tag `v0.2.0`, on PyPI)

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
