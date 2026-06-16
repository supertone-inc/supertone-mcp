# SPEC-029: Assemble multiple TTS clips into one deliverable via ffmpeg

> Linked Issue: ISSUE-029
> Status: `accepted`
> Date: 2026-06-16
> Author: pillip

## Problem

A user who generates a multi-line script with `text_to_speech` ends up with N separate audio files and no in-toolchain way to stitch them into a single deliverable (e.g., a narrated paragraph, a dialogue, an ad read). They must drop to an external editor to concatenate, insert pauses, or blend transitions. We want a `merge_audio_files` MCP tool that does this without the user leaving the agent. The consequential decision is **how to obtain the audio-processing engine** — getting this wrong either breaks `uvx supertone-mcp` zero-config installs (NFR-001) or quietly degrades audio quality for gap/crossfade operations.

## Context

- The server ships as a PyPI package run via `uvx supertone-mcp` inside LLM hosts (Claude Desktop, Cursor) and CI; these environments **do not** reliably have a system `ffmpeg` on `PATH`. (NFR-001: zero-config install.)
- Existing tools save audio to `SUPERTONE_OUTPUT_DIR` with the `{YYYY-MM-DD}_{uuid8}.{ext}` naming convention; the merge tool must reuse `generate_output_path()`, `resolve_output_dir()`, and `calculate_duration()` from `tools.py`/`models.py`.
- Supported audio formats today are `mp3` and `wav` only (`SUPPORTED_FORMATS` in `constants.py`); the merge tool must not silently introduce new formats.
- `docs/architecture.md` already records the target shape: a new `audio_ops.py` module with `async merge_audio(input_paths, gap_ms, crossfade_ms, output_format) -> tuple[bytes, str]`, ffmpeg discovered via `imageio_ffmpeg.get_ffmpeg_exe()`, invoked through `asyncio.create_subprocess_exec`.
- `docs/test_plan.md` Flow 13 (TC-140..TC-153) fixes the user-facing contract: fail-fast validation before any subprocess, single-file passthrough, mutually-exclusive gap/crossfade, output-format auto-detect→mp3 for mixed inputs.
- CI cannot run a real ffmpeg binary deterministically across the 3.11/3.12/3.13 matrix; all subprocess calls in tests are mocked.

## Options

> Decision axis: **how `merge_audio_files` obtains and drives the audio engine.**

### Option A: Bundle ffmpeg via `imageio-ffmpeg`, drive with concat demuxer + filters
- **Approach**: Add `imageio-ffmpeg>=0.5` as a runtime dependency. Resolve the binary at call time with `imageio_ffmpeg.get_ffmpeg_exe()`. For plain concat use the ffmpeg concat demuxer; for `gap_ms` inject `aevalsrc=0:duration=` silence between clips; for `crossfade_ms` use the `acrossfade` filter. Invoke via `asyncio.create_subprocess_exec` with `-y`, capture stdout bytes + stderr, raise on nonzero exit.
- **Pros**:
  - Zero-config: `uvx supertone-mcp` keeps working with no host setup, preserving NFR-001.
  - Full-fidelity gap and crossfade via battle-tested ffmpeg filters.
  - Binary discovery isolated to one library call; no `PATH` scanning logic.
- **Cons**:
  - `imageio-ffmpeg` bundles a platform ffmpeg (~20–30 MB), enlarging the install footprint.
  - Adds one runtime dependency to maintain.
- **Trade-off**: +1 runtime dependency, +25 MB install size, but -0 host-setup steps (preserves zero-config install) and full gap/crossfade fidelity.

### Option B: Rely on system `ffmpeg` from `PATH`
- **Approach**: Skip the bundled binary; call `shutil.which("ffmpeg")` and use whatever the host provides. Same filter graph as Option A.
- **Pros**:
  - +0 MB added to the wheel; no new Python dependency.
  - Uses the host's possibly-newer ffmpeg.
- **Cons**:
  - Breaks on hosts without ffmpeg (most LLM desktop apps and the CI runners), violating NFR-001.
  - Version/path variance across hosts makes filter behavior non-reproducible.
- **Trade-off**: +0 MB install size, but +1 mandatory host-setup step and an estimated >50% of target hosts fail at runtime (no ffmpeg on PATH).

### Option C: Pure-Python concatenation (`pydub`/manual WAV splicing), no ffmpeg
- **Approach**: Concatenate decoded PCM frames in Python. WAV via the stdlib `wave` module; MP3 via `pydub` — which itself shells out to ffmpeg, or requires a pure-Python MP3 decoder.
- **Pros**:
  - No subprocess management for the WAV-only path.
- **Cons**:
  - MP3 decode/encode in pure Python is either unavailable or transitively needs ffmpeg anyway, so it does not remove the dependency.
  - Crossfade requires hand-rolled sample-level mixing and resampling — fragile and easy to get wrong.
- **Trade-off**: -1 subprocess invocation for WAV only, but +5 days implementation for correct MP3 + crossfade handling and still a transitive ffmpeg dependency for MP3.

## Decision

**Chosen: Option A**

Option A is the only choice that preserves zero-config `uvx` installs (NFR-001) while giving full-fidelity gap and crossfade. Its trade-off line — "+25 MB install size, -0 host-setup steps" — is acceptable because the server's whole value proposition is frictionless install inside LLM hosts, and 25 MB is negligible next to that. Option B's ">50% of target hosts fail at runtime" is disqualifying, and Option C's "+5 days impl with a still-transitive ffmpeg dependency" buys nothing.

## Trade-offs Accepted

- We accept a ~25 MB larger install and one extra runtime dependency (`imageio-ffmpeg`) in exchange for zero-config audio merging on every supported host.
- We accept supporting only `mp3` and `wav` (matching `SUPPORTED_FORMATS`); `.ogg` and others are rejected with a clear error rather than silently transcoded.
- We accept that `gap_ms` and `crossfade_ms` are mutually exclusive — combining them is rejected fail-fast rather than defining ambiguous junction semantics.
- We accept that mixed-extension inputs with no explicit `output_format` default to `mp3` (lossy) rather than guessing the user's intent.
- We accept that real-ffmpeg behavior is verified only by manual integration testing; CI mocks the subprocess for determinism across the Python matrix.

## Migration

No data/schema migration. Additive feature only:

1. `uv add imageio-ffmpeg` (lets uv pin `imageio-ffmpeg>=0.5` and lockfile-manage it; do not hand-edit `pyproject.toml`).
2. Add `MERGE_SUPPORTED_EXTENSIONS = ["mp3", "wav"]` to `constants.py` (or reuse `SUPPORTED_FORMATS` if equivalent).
3. Create `src/supertone_mcp/audio_ops.py` with `async merge_audio(...)`.
4. Add the `merge_audio_files` handler to `tools.py` (fail-fast validation, single-file passthrough, output-dir resolution, response formatting).
5. Register `merge_audio_files` in `server.py` with the schema/description from UX spec §2.16.
6. Add tests: `tests/test_audio_ops.py` (mocked subprocess + `get_ffmpeg_exe`), plus `tests/test_tools.py` and `tests/test_server.py` extensions (TC-140..TC-153).

## Rollback

Fully additive, so rollback is clean. **Trigger signals**: `imageio-ffmpeg` fails to provide a working binary on a supported platform, or the bundled binary introduces a security/licensing concern. **Steps**: revert `audio_ops.py`, the handler + registration in `tools.py`/`server.py`, the `MERGE_SUPPORTED_EXTENSIONS` constant, and the new tests; run `uv remove imageio-ffmpeg`. No DB/migration concerns. Rollback effort: ~1 hour (single revert of the feature branch).

## Open Questions

- [ ] Should audio mix/overlay (multi-track, not head-to-tail) be a future tool? — owner: pillip, by: post-0.4 backlog grooming
- [ ] Should we expose per-junction gap/crossfade (a list) rather than one global value? — owner: pillip, by: after first user feedback on v0.4
