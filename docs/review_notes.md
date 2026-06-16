# Review Notes — ISSUE-029 (PR #49): merge_audio_files tool (ffmpeg-backed audio concat)

Reviewer: reviewer subagent + senior pass. Scope: `audio_ops.py`, `tools.merge_audio_files`,
`server.py` registration, tests, `pyproject.toml`, `SPEC-029.md`. Subprocess is mocked in CI,
so a real-ffmpeg integration check was run manually to validate the filter graph.

## Code Review

### Findings & resolutions

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| C1 | Critical | `concat`/`acrossfade` fed raw `[i:a]` streams with no normalization; ffmpeg requires matching sample rate / channel layout / format, so merging heterogeneous mp3+wav inputs (the headline use case) would fail at runtime. Invisible to mocked tests (RL-006/RL-007 class). | **Fixed** — every input stream is normalized via `aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo` (`[a{i}]`) before concat/crossfade. |
| C2 | Critical | `aevalsrc=0:d=…` silence used default 44100/mono/dbl, mismatching normalized inputs → gap mode broken at runtime. | **Fixed** — silence now `aevalsrc=0:d=…:s=44100:c=stereo` + `aformat=…fltp`, matched to the canonical params. |
| H1 | High | `proc.communicate()` had no timeout → a hung ffmpeg wedges the single-process stdio server forever. | **Fixed** — wrapped in `asyncio.wait_for(timeout=120s)`; on timeout the process is killed and a `RuntimeError("ffmpeg timed out …")` is raised. |
| H2 | High | Negative `gap_ms`/`crossfade_ms` passed validation then silently fell through to plain concat (the `> 0` guards), dropping the requested effect with a success message. | **Fixed** — fail-fast `gap_ms and crossfade_ms must be non-negative.` + tests. |
| M1 | Medium | Nonzero ffmpeg exit with empty stderr surfaced bare `Audio merge failed: .` | **Fixed** — `RuntimeError(excerpt or f"ffmpeg exited with code {rc}")`. |
| M2 | Medium | Success message `Audio merged:` diverged from UX spec §4.16 `Merged audio saved:`. | **Fixed** — aligned wording + test pinning the phrase. |
| L1 | Low | `_pipe_format` maps any non-`wav` to `mp3`; a future third format in `MERGE_SUPPORTED_EXTENSIONS` would silently transcode to mp3. | **Deferred** — defensive only; `output_format` is enum-validated upstream so no current bug. Tracked as follow-up. |
| L2 | Low | `imageio-ffmpeg>=0.5` had no upper bound (spec lists "binary unavailable" as a rollback trigger). | **Fixed** — pinned `>=0.5,<1.0` (consistent with `mcp`/`supertone` pins). |
| M3 | Medium | Single-file passthrough message shape differs from the merge block. | **Deferred** — matches AC ("returned as-is"); extension/existence validation DOES run before the passthrough branch, so a lone `.ogg` is still rejected. Cosmetic only. |

### Real-ffmpeg validation (beyond mocks)
Generated heterogeneous inputs (44100/stereo mp3 + 24000/mono wav) and ran the actual
`merge_audio` for all three modes against the bundled binary:
- concat → 32,644 bytes OK · gap(500ms) → 40,586 bytes OK (silence adds length) · crossfade(200ms) → 29,301 bytes OK (overlap shortens).
This confirms C1/C2 fixes work on the exact case the mocked suite cannot exercise.

## Security Findings
- **Subprocess injection:** Safe. `asyncio.create_subprocess_exec(*cmd)` (no shell); filenames pass as argv after `-i`. No exploit path.
- **Secrets:** none in this module.
- **Path handling:** `Path(raw).expanduser()` + `is_file()`; output path is server-controlled via `generate_output_path`. Acceptable for a local user-driven MCP tool.
- **Resource exhaustion:** addressed by the H1 timeout. No per-call input-count cap (acceptable for typical TTS clip counts).
- **Dependency surface:** bundled ffmpeg (LGPL/GPL build via imageio-ffmpeg) — no exploit path; upper-bound pin added (L2).

## Test coverage
- 588 tests pass (`uv run pytest`); `ruff check` clean.
- Added: normalization assertions (aresample/aformat present, matched aevalsrc), timeout-kills-process, empty-stderr fallback, negative-value validation, success-message phrase.
- Real-ffmpeg integration was done manually (not in CI, per the no-real-binary-in-CI convention).

## Follow-ups (non-blocking)
- Add an opt-in (CI-skipped) real-ffmpeg integration test tier for the merge path (RL-007).
- L1: make `_pipe_format` an explicit map that raises on unknown formats when `MERGE_SUPPORTED_EXTENSIONS` grows.
- M3: reconsider single-file passthrough message shape with the spec author.
