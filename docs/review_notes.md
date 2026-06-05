# Review Notes — ISSUE-028 (PR #46): Docs/README reframe + 31-language sync + 0.2.0 release prep

Reviewer verdict: **APPROVE-WITH-NITS** (senior code review + security audit). Every load-bearing
documented claim was verified against the actual shipped code (ISSUE-021..027), the installed
SDK 0.2.3 enums, and a passing `uv run pytest` (552 passed). No behavior regressions.

## Code Review

**Findings & fixes applied (this review):**
- **Medium — doc/code mismatch (README.md):** the `get_usage_history` row listed an Optional
  "time-window params" column, but the registered tool (`server.py: async def get_usage_history()`)
  takes **no parameters** (it computes a recent default window internally). Misleading at release.
  → Fixed: Optional cell changed to `— (reports a recent default window)`.
- **Low — stale language counts (server.py), folded in for release accuracy:** the LLM-facing
  server instructions string said "Supports 23 languages" and the `text_to_speech` docstring said
  "and 20+ more", both contradicting the new 31-language claim after the SUPPORTED_LANGUAGES sync.
  → Fixed: "23 languages" → "31 languages"; "20+ more" → "28 more (31 total)".
  → `tests/test_server.py` assertion updated `"23 languages"` → `"31 languages"` accordingly.

**Verified accurate (no action needed):** default model `sona_speech_2_flash`; all `text_to_speech`
params (output_mode/autoplay/streaming/include_phonemes/normalized_text + defaults, sona_speech_1-only
streaming); 7-model list; env vars (only API_KEY/VOICE_ID/OUTPUT_DIR read; removed vars only trigger a
one-time stderr notice); 3 new tools registered; no 300-char cap in predict_duration;
SUPPORTED_LANGUAGES == 31, set-equal to the SDK Language enum (no dupes/typos); version 0.2.0 consistent
across pyproject/__init__/server.json; `mcp-name:` marker retained; README anchors resolve; server.json
valid + schema-shaped.

**Test review:** `tests/test_version.py` (new) has real assertions (version triple-consistency +
removed-env-var guard). The lang test asserts each of the 8 new codes AND `len == 31` (catches
missing/extra/dupe). All green under `uv run pytest`.

## Security Findings

- **None introduced by this PR.** The diff references only the `SUPERTONE_API_KEY` variable name, no values.
- **Pre-existing (NOT this PR — do not block):** a plaintext API key lives in `.mcp.json` on `main`.
  Recommended follow-up: rotate the key, move it out of the tracked file (local/ignored config or env),
  and confirm `.mcp.json` is gitignored.

## Follow-ups (non-blocking)
1. Rotate + remove the plaintext API key in `.mcp.json`; verify gitignore.
2. (Done in this review) language-count strings aligned to 31 across README, server.json, and server.py.

## Release reminder
Publishing is NOT triggered by merging this PR — it fires on the `v0.2.0` tag push
(CI `publish` + `publish-registry`). Confirm PyPI does not already hold `0.2.0` before tagging.
