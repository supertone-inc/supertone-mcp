# Review Notes: ISSUE-014 — Client Voice Discovery

> Reviewed: 2026-05-26
> PR: #12
> Branch: issue/ISSUE-014-client-voice-discovery
> Reviewer: Claude (Opus 4.7)
> Verdict: **Approve**
> Confidence: **High**

## Scope Recap

PR #12 extends `SupertoneClient` with three new async methods — `search_voices()`,
`get_voice()`, `get_credit_balance()` — and three new TypedDicts in `models.py`
(`SampleDict`, `VoiceDetailDict`, `CreditBalanceDict`). No MCP tool handlers,
no formatter changes, no removal of `list_voices`. Pure additive change.

## Code Review

### Findings

1. **OK: `search_voices` pagination loop mirrors `get_voices` pattern**
   - Same `page_size=100`, same `next_page_token` threading, same break-on-empty.
   - Filter kwargs are pass-through; the SDK is treated as the source of truth
     for enum validation (matches the architecture decision to delegate
     server-side filtering to the API).

2. **OK: `_handle_sdk_errors` reused for all three new methods**
   - Identical exception tuple as the existing `synthesize`/`get_voices`.
   - Consistent mapping: 401/403 -> `SupertoneAuthError`, 429 -> `SupertoneRateLimitError`,
     5xx -> `SupertoneServerError`, `NoResponseError`/`ConnectError`/`TimeoutException`
     -> `SupertoneConnectionError`.

3. **OK: `get_voice` correctly renames `language` -> `supported_languages`**
   - Maintains the project-wide convention from `VoiceDict`. Documented in the
     docstring. Avoids leaking SDK field naming into the MCP layer.

4. **OK: Optional field handling in `get_voice`**
   - `samples` and `thumbnail_image_url` are only added to the returned dict
     when non-None. Combined with `VoiceDetailDict(total=False)` this is type-safe.
   - Defensive `getattr(..., None)` is correct here — the SDK schema marks both
     as optional, so an older/sparse response would otherwise raise
     `AttributeError`.

5. **Low (Note, not blocking): `VoiceDetailDict` uses `total=False` for ALL fields**
   - Spec says only `samples` and `thumbnail_image_url` are nullable per SDK.
     Other fields (`voice_id`, `name`, `description`, `age`, `gender`, `language`,
     `styles`, `models`, `use_cases`) are required by the SDK.
   - Impact: type checker cannot catch a caller that omits required fields.
     A more precise model is to mark only the two optionals as `NotRequired`
     and keep the rest as required:
     ```python
     class VoiceDetailDict(TypedDict):
         voice_id: str
         # ... required fields ...
         samples: NotRequired[list[SampleDict]]
         thumbnail_image_url: NotRequired[str]
     ```
   - Why: tighter contract for consumers (ISSUE-016 formatter). Not blocking
     because the implementation produces correct dicts at runtime and tests
     verify the shape directly.

6. **Low (Note): `search_voices` exposes `use_cases` parameter not listed in the issue spec**
   - The issue's "In scope" enumerates `name?, description?, language?, gender?,
     age?, use_case?, style?, model?` (no `use_cases` plural).
   - Implementation added `use_cases: str | None` as a 9th parameter to mirror
     the SDK signature. This is forward-compatible and the SDK signature did
     include it, so it's a reasonable proactive addition.
   - Type concern: the SDK's `use_cases` parameter typically takes a list (the
     plural suggests array semantics). The local annotation `str | None` may
     be too narrow. Verify by inspecting the SDK signature in a follow-up; if
     it accepts `list[str]`, update the type. Pass-through still works at
     runtime regardless. Not blocking.

7. **Low (Note): Test asymmetry on connection error coverage**
   - `test_no_response_raises_connection_error` exists only on `TestGetCreditBalance`.
   - `test_timeout_raises_connection_error` exists only on `TestGetVoice`.
   - Each of the three methods should ideally test all three connection-error
     branches (`NoResponseError`, `httpx.ConnectError`, `httpx.TimeoutException`)
     for symmetry. Coverage is functionally adequate because `_handle_sdk_errors`
     is shared, but the absent tests would catch a future regression that
     re-orders the `except` tuple.

8. **Low (Note): `test_handles_missing_samples_and_thumbnail` uses a loose
   assertion**
   ```python
   assert "samples" not in result or result.get("samples") in (None, [])
   ```
   The implementation guarantees `samples` is omitted when the SDK returned
   `None`, so the disjunction is needlessly permissive. Tightening to
   `assert "samples" not in result and "thumbnail_image_url" not in result`
   would lock in the documented behavior. Not blocking.

### Verdict

**Approve.** All AC met, 184/184 tests passing, no critical or high findings.
The four `Low` items above are minor type-strictness/test-tightness improvements
and do not block merge.

## Security Findings

| Severity | Finding | Status |
|----------|---------|--------|
| None | No security issues found in this PR | Pass |

Detail:

- **Injection (SQL/command/template):** No SQL, no shell. All filter params
  are forwarded as kwargs to the SDK, which constructs the HTTP request
  internally with proper encoding. No string interpolation into URLs.
- **Auth / authz:** API key handling unchanged (same `Supertone(api_key=...)`
  constructor used by existing code). Never logged, never echoed.
- **Sensitive data:** No new logging surface. The three new methods return
  domain TypedDicts only.
- **Input validation:** New methods accept `Optional[str]` filter params and
  pass them to the SDK. The SDK is authoritative for enum validation per the
  architecture decision (delegation to server-side filtering). No new untrusted
  input enters the process here — these are internal API methods, not MCP tool
  handlers; user input arrives via `tools.py` (ISSUE-015/016 will validate).
- **Dependencies:** No dependency changes. No new transitive CVE surface.
- **XSS:** Not applicable (no HTML output, plain-text responses are produced
  in `tools.py`, not here).
- **Misconfiguration:** No new debug switches, no CORS, no new env vars.

**Conclusion:** Zero security findings at any severity level. The PR is a
clean, additive client-layer extension that introduces no new attack surface.

## Test Quality

### AC-to-Test Mapping

| AC | Test(s) | Result |
|----|---------|--------|
| AC1: `search_voices(gender="female")` paginates and concatenates | `TestSearchVoices::test_handles_pagination` (3-page side_effect, asserts ordered concatenation + threaded `next_page_token`) | Pass |
| AC2: `get_voice("v1")` returns `VoiceDetailDict` with samples/models/styles/use_cases/thumbnail | `TestGetVoice::test_returns_full_voice_detail` (asserts each field individually + sample shape) | Pass |
| AC3: 401 on any of the three methods -> `SupertoneAuthError` | `test_unauthorized_raises_auth_error` on each of the three classes | Pass |
| AC4: 429 on any method -> `SupertoneRateLimitError` | `test_429_raises_rate_limit_error` on each of the three classes | Pass |
| AC5: `VoiceDetailDict` importable, includes typed fields matching SDK | `TestVoiceDetailDictShape::test_voice_detail_dict_importable` (plus `test_sample_dict_importable`, `test_credit_balance_dict_importable`) | Pass |

### Coverage Summary

- 30 new tests, all passing.
- 184/184 total tests pass (`uv run pytest -q`, 0.82s).
- Happy path + 5 error branches per method (401, 403, 429, 5xx, connect/timeout/no-response).
- Edge cases tested: empty filter set, multi-page pagination, null balance,
  missing samples + thumbnail.

### Minor Test Quality Notes

See finding #7 (connection-error coverage asymmetry) and finding #8 (loose
assertion) under Code Review. Both are non-blocking suggestions for a follow-up.

## Pre-existing Tech Debt Observed (NOT this PR's scope)

Surfaced for follow-up issue creation. Do not fix here.

| Item | Location | Severity | Notes |
|------|----------|----------|-------|
| Pyright "response possibly unbound" warnings | `supertone_client.py:122, 185, 216, 225, 279, 316, 349` (now also lines for new methods) | Low | `_handle_sdk_errors` always raises, but Pyright lacks the type narrowing. Same pattern in pre-existing `synthesize`/`get_voices`. Could be fixed by typing the helper as `-> NoReturn` and re-raising the residual path. |
| Stream return type inconsistency | `supertone_client.py:187, 192` | Low | Pre-existing, untouched. |
| `checkpoint.sh` wrapper path bug | `.claude-kit/scripts/checkpoint.sh` references `$ROOT/scripts/verify_checkpoint.py` but the script lives at `.claude-kit/scripts/verify_checkpoint.py` | Low | Infra; outside PR scope. |
| `verify_checkpoint.py` test phase ignores `.venv` | `.claude-kit/scripts/verify_checkpoint.py` invokes `python3 -m pytest` without `uv run`, causing `ModuleNotFoundError` in matrix CI | Low | Infra; outside PR scope. |
| `autotest.py` hook runs from main repo when editing worktree files | `.claude/hooks/autotest.py` | Low | Tooling false positives; outside PR scope. |
| Cross-tree Pyright false positives | `test_supertone_client.py:893, 912, 924` / `supertone_client.py:21-23` flagged as unknown imports | None (expected) | Resolves automatically on merge; editable install on main does not yet have the new TypedDicts. |

**Suggested follow-up issue:**

- **ISSUE-021 — "Tech debt: tighten Pyright type narrowing in `supertone_client.py`"**
  - Type `_handle_sdk_errors` as `-> NoReturn` so Pyright understands the
    function never returns. This eliminates all "possibly unbound" warnings
    across `synthesize`, `synthesize_stream`, `get_voices`, `search_voices`,
    `get_voice`, `get_credit_balance` in one change. Stretch: tighten
    `VoiceDetailDict` to use `NotRequired` rather than `total=False`
    (finding #5) and verify `use_cases` parameter type against the SDK
    signature (finding #6).
  - Priority: P2
  - Estimate: 0.25d

## Self-Review Trace

1. **Severity re-assessment:** Re-read every finding. Nothing reaches Medium
   or above. The four Low items are type-strictness / test-tightness, not
   correctness bugs. Confirmed.
2. **False-positive check:** I considered flagging the `use_cases: str | None`
   annotation as "wrong type" — but the SDK signature was not directly
   inspected (cross-tree Pyright false positives prevent reliable inspection
   inside the worktree). Demoted to a "verify in follow-up" Low.
3. **Blind spot scan:** Checked specifically for:
   - **Race conditions / concurrency:** none — methods are independent async
     wrappers, no shared mutable state.
   - **Resource leaks:** none — SDK manages its own httpx client; `aclose()`
     pattern unchanged.
   - **Logging gaps:** none — but also no new logging added. Acceptable for
     a client-layer change; tool handlers will add logging.
   - **Backward compat:** confirmed — `VoiceDict` and `get_voices` untouched,
     `search_voices` does not shadow `get_voices`.
4. **AC verification:** All 5 AC have at least one matching test, all 5 pass.
5. **Confidence:** **High.** The change is small (160 LoC of source, 420 LoC
   of test), additive only, well-tested, well-documented.

## Skipped

- **UI Review** — not applicable, backend client extension only.
- **Design Audit** — not applicable, no UI surface.
- **Accessibility Audit** — not applicable, CLI/MCP server with no UI.
- **Figma structural / visual diff** — confirmed `figma-export/` does not
  exist; UI checkpoints auto-skip.

## Files Reviewed

- `src/supertone_tts_mcp/models.py` (+40 lines: `SampleDict`,
  `VoiceDetailDict`, `CreditBalanceDict`; -1 unused `NotRequired` import)
- `src/supertone_tts_mcp/supertone_client.py` (+138 lines: three new methods +
  TypedDict imports)
- `tests/test_supertone_client.py` (+419 lines: 3 test helpers, 4 test classes,
  30 new tests, `usage` mock on fixture)

## Code Fixes Applied

None. The Low-severity findings are notes for a follow-up issue; the PR is
mergeable as-is.
