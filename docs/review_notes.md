# Review Notes — ISSUE-024 (PR #38)

Relax the 300-character hard limit so long text is delegated to the SDK's
internal auto-chunking; retain the empty-text guard.

## Code Review

Verified against all six acceptance criteria:

- **AC #1 (text_to_speech 500-char):** `text_to_speech` never called
  `validate_text_max_length`; only `validate_text` (empty guard) runs. A
  500-char input reaches `client.synthesize(...)` with the full text. Covered by
  `TestTextToSpeechHandler::test_long_text_passes_through_to_sdk_without_length_error`
  (`synthesize.assert_awaited_once()` + `call_args.kwargs["text"] == long_text`,
  asserts no "exceeds the maximum length"). PASS.
- **AC #2 (predict_duration 500-char):** Removed the
  `validate_text_max_length(text)` call from `predict_duration`. A 500-char input
  now reaches `client.predict_duration(...)`. Covered by
  `TestPredictDurationHandler::test_long_text_passes_through_to_sdk_without_length_error`. PASS.
- **AC #3 (text_to_speech empty):** `validate_text("")` raises
  `Text must not be empty.`, returned before any client construction. Covered by
  the pre-existing `test_empty_text_returns_error`. PASS.
- **AC #4 (predict_duration empty):** Same guard; `MC.assert_not_called()`.
  Covered by the pre-existing
  `TestPredictDurationHandler::test_empty_text_returns_validation_error_without_api_call`. PASS.
- **AC #5 (predict_duration description/docstring):** Tool description no longer
  says "same 300-character limit"; now notes auto-chunking + credit/latency
  scaling. Docstring `text:` line updated. Covered by
  `test_predict_duration_description_matches_ux_spec` (`"300" not in desc`,
  `"chunk" in desc.lower()`). PASS.
- **AC #6 (text_to_speech description):** Description notes long text is
  auto-split and credit/latency scale with length. PASS.

### Cleanliness
- `validate_text_max_length` had a single caller (`predict_duration`); removed the
  helper entirely per the Implementation Notes preference. The now-unused
  `TEXT_MAX_LENGTH` import was dropped from `tools.py`. The `TEXT_MAX_LENGTH`
  constant remains in `constants.py` for reference (no longer enforced).
- Remaining "300" references in `src/` are appropriate and non-enforcing:
  `supertone_client.py:98` documents the SDK's own chunk behavior; `tools.py`
  mentions are historical-context docstrings; `constants.py` is the unused
  reference constant.

### Edge cases / regressions
- Empty-text behavior preserved for both handlers (no API call).
- No new input surfaces; no other handler depended on the removed helper.

## Security Findings
None. Removing a client-side length cap introduces no injection/secret/auth
concern — the SDK chunks server-side and credit is proportional to input the
user supplies, so cost remains bounded by the caller's own text.

## Test Quality
All 4 changed/added tests contain real assertions; no hollow tests. Each AC maps
to at least one test. `uv run pytest` → 456 passed; `uv run ruff check` → clean.

## Severity Summary
No Critical/High/Medium findings. No follow-up issues required.
Confidence: High.
