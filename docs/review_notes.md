# Review Notes — ISSUE-025 (PR #40)

Expose SDK 0.2.3 `include_phonemes` (bool, default False) and `normalized_text`
(str | None, default None) on `text_to_speech`, threaded through
`client.synthesize` / `synthesize_stream` to the SDK calls. Pass-through only.

## Code Review

Verified against all five acceptance criteria:

- **AC #1 (include_phonemes=True forwarded):** `synthesize` /
  `synthesize_stream` forward `include_phonemes` to `create_speech_async` /
  `stream_speech_async`; `tools.text_to_speech` threads it on both the one-shot
  and streaming paths. Covered by
  `TestSynthesize::test_forwards_include_phonemes_true`,
  `TestSynthesizeStream::test_forwards_phoneme_and_normalized_params`,
  `TestTextToSpeechHandler::test_passes_phoneme_params_to_synthesize` and
  `test_passes_phoneme_params_to_stream`. PASS.
- **AC #2 (include_phonemes defaults False):** wrapper + handler defaults are
  `False`, matching the SDK default. Covered by
  `test_include_phonemes_defaults_false`,
  `test_stream_phoneme_params_default`,
  `test_phoneme_params_default_to_synthesize`. PASS.
- **AC #3 (normalized_text forwarded):** forwarded as-is (incl. non-ASCII
  "안녕하세요"). Covered by `test_forwards_normalized_text` and the tools/stream
  passthrough tests. PASS.
- **AC #4 (normalized_text defaults None):** wrapper + handler default `None`.
  Covered by `test_normalized_text_defaults_none`,
  `test_stream_phoneme_params_default`, `test_phoneme_params_default_to_synthesize`.
  PASS.
- **AC #5 (server schema + model-constraint doc):** server.py registers both
  params with schema-visible `Field` descriptions; `include_phonemes` is boolean
  with default false; `normalized_text` description states it applies only to
  `sona_speech_2` / `sona_speech_2_flash`. Covered by
  `test_text_to_speech_has_phoneme_params` and
  `test_normalized_text_documents_model_constraint`. PASS.

### Correctness
- SDK kwarg names verified against the installed SDK
  (`.venv/.../supertone/text_to_speech.py`): both methods accept
  `include_phonemes: Optional[bool] = False` and
  `normalized_text: Optional[str] = None`. Wrapper defaults match SDK defaults,
  so omitting the params reproduces prior behavior exactly.
- No client-side rejection for `normalized_text` on non-sona_speech_2 models,
  per spec (the SDK ignores it). Returned phoneme timing data is intentionally
  NOT surfaced (pass-through only) — documented in all three docstrings + schema.

### Edge cases / regressions
- No new validation surfaces and no new error branches; existing
  `_handle_sdk_errors` chain unaffected. `predict_duration` deliberately does
  NOT gain these audio-only params; the parity test was updated with a documented
  rationale (predict_duration produces no audio).

## Security Findings
None. No secrets, no injection surface (params passed as typed SDK kwargs, not
interpolated), no new filesystem/shell/network behavior.

## review_lessons.md cross-check
- RL-001 / RL-005 (TypedDict nullability): N/A — no new TypedDict.
- RL-002 / RL-003 (error-branch / pagination test symmetry): N/A — no new
  wrapped SDK methods; only new kwargs on existing `synthesize` /
  `synthesize_stream`, whose existing error-branch tests still apply.
- RL-004 (`NoReturn`) and RL-006 (404 mapping): pre-existing tracked tech-debt,
  not touched or worsened by this change.

## Test Quality
All 11 added tests contain real assertions; no hollow tests. Each AC maps to at
least one test. `uv run pytest` → 467 passed; `uv run ruff check` → clean.

## Severity Summary
No Critical/High/Medium findings. No follow-up issues required.
Confidence: High.
