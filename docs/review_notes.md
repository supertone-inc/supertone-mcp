# Review Notes — ISSUE-023 (PR #36)

Add per-call `streaming` param + route one-shot `synthesize` vs `synthesize_stream`
+ fail-fast `sona_speech_1`-only validation.

## Code Review

Verified the implementation against all six acceptance criteria:

- **AC #1 (default routing):** `streaming` defaults to `False`; the `else` branch
  awaits `client.synthesize(...)`. The default path no longer touches
  `synthesize_stream`. Covered by `test_default_routes_to_synthesize_not_stream`
  (`synthesize.assert_awaited_once()`). PASS.
- **AC #2 (fail-fast error):** The `if streaming and model != "sona_speech_1"`
  guard sits AFTER `validate_model` and BEFORE `SupertoneClient(...)` is
  constructed. The returned string matches the spec exactly:
  `Streaming is only supported by model "sona_speech_1" (received: "sona_speech_2_flash"). Set streaming=false or use sona_speech_1.`
  Covered by `test_streaming_true_non_sona1_fails_fast` which also asserts
  `MC.assert_not_called()` (neither SDK method reachable). PASS.
- **AC #3 (streaming sona_speech_1):** `streaming=True` + `sona_speech_1` enters
  the chunk loop; file/resource output produced from chunks. Covered by
  `test_streaming_true_sona1_invokes_stream` (asserts `synthesize` NOT awaited)
  and `test_streaming_writes_chunks_to_file`. PASS.
- **AC #4 (resources one-shot):** `streaming=False` + `output_mode=resources`
  uses `synthesize`, returns `[AudioContent, TextContent]`, writes no file.
  Covered by `test_resources_mode_returns_audio_content`
  (`synthesize.assert_awaited_once()`) + `test_resources_mode_no_file_written`. PASS.
- **AC #5 (SDK duration preference):** `if sdk_duration is not None:
  duration = round(sdk_duration, 1)` else mutagen. Rounding is consistent with
  `calculate_duration` (both `round(_, 1)`). Covered by
  `test_streaming_false_prefers_sdk_duration` (7.2 wins over mutagen 3.5) and the
  `test_streaming_false_falls_back_to_mutagen_duration` fallback. PASS.
- **AC #6 (server schema):** `streaming` registered as
  `Annotated[bool, Field(description=...)]`; schema shows `type: boolean`,
  `default: false`, and a description naming `sona_speech_1`. Docstring updated.
  Covered by `test_text_to_speech_has_streaming_param` +
  `test_text_to_speech_streaming_documents_sona1_requirement`. PASS.

Other observations:
- Error-handling parity: the one-shot `synthesize` path raises the same domain
  exceptions, caught by the same outer `except` chain; partial-file cleanup for
  `SupertoneServerError` / `SupertoneConnectionError` applies to both paths.
- `predict_duration` param-parity test correctly updated to treat `streaming`
  as a routing param (excluded), consistent with how `output_mode`/`autoplay`
  were treated in ISSUE-022.

## Security Findings

- No secrets, no injection vectors, input validation unchanged. API key resolved
  from env only. `_autoplay` uses a list-form `Popen` for the file path
  (no shell); the in-memory branch uses `shell=True` but that pre-dates this PR
  and the tempfile path is server-controlled, not user input. No new surface.
- Severity: none (no Critical/High/Medium security findings).

## Findings Summary

| # | Severity | Finding | Code change? |
|---|----------|---------|--------------|
| 1 | Low | One-shot `with open()` write failure surfaces as the generic OSError "Cannot write audio file" without an explicit `unlink` of a possible partial file — identical to the pre-existing streaming-path behavior. Not a regression. | No |

No Critical or High findings. Confidence: High. APPROVE — ship.
