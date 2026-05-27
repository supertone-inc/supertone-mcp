# Review Lessons

> Catalog of preventable patterns observed during code review. Each entry
> documents a pattern, why it matters, the fix, and where it has been observed.
>
> Update protocol: when a review surfaces a finding that could have been
> prevented earlier (at kickoff, design, or implementation time), add or
> update an entry here.

---

## [RL-001] Use `NotRequired` rather than `total=False` when only some TypedDict fields are optional

- **Category:** Code Quality
- **Pattern:** A `TypedDict` declared with `total=False` makes *every* field
  optional. When only one or two fields are actually nullable in the underlying
  schema, this overrelaxes the type contract and prevents the type checker
  from catching callers that omit required fields.
- **Why it matters:** Downstream consumers (formatters, handlers) lose a layer
  of safety. A missing `voice_id` would compile but blow up at runtime when
  the consumer reads it.
- **Fix:** Use a default-total TypedDict and mark only the nullable fields
  with `typing.NotRequired`:
  ```python
  class VoiceDetailDict(TypedDict):
      voice_id: str            # required (default)
      name: str
      # ...
      samples: NotRequired[list[SampleDict]]
      thumbnail_image_url: NotRequired[str]
  ```
- **Prevention point:** Implementation phase — when designing a new TypedDict,
  inspect the source schema to identify exactly which fields are nullable
  before defaulting to `total=False`.
- **Frequency:** 1
- **Observed-In:** PR #12 (ISSUE-014), `src/supertone_tts_mcp/models.py:90` —
  `VoiceDetailDict(TypedDict, total=False)` made all 12 fields optional when
  only 2 (`samples`, `thumbnail_image_url`) are nullable per the SDK.

---

## [RL-002] Test connection-error branches symmetrically across all methods that share an error helper

- **Category:** Testing
- **Pattern:** When multiple methods share a common error-mapping helper
  (e.g., `_handle_sdk_errors`), it is tempting to test each connection-error
  branch only once across the suite. This works for current behavior but
  leaves the test suite weak against regressions in the `except (...)` tuple
  of any single method — a re-ordering or omission would only fail one
  method's tests.
- **Why it matters:** A future refactor that removes `httpx.TimeoutException`
  from one of the three method's `except` tuples would slip through if only
  one of the three methods tests timeout handling.
- **Fix:** For each method that wraps an SDK call with shared error mapping,
  exercise all three connection-error branches (`NoResponseError`,
  `httpx.ConnectError`, `httpx.TimeoutException`) plus 401, 403, 429, 5xx.
  Use a parametrize fixture or shared test mixin to keep this DRY.
- **Prevention point:** Implementation phase — define the error-branch test
  matrix once (per method type) and apply uniformly.
- **Frequency:** 1
- **Observed-In:** PR #12 (ISSUE-014), `tests/test_supertone_client.py`
  `TestSearchVoices` (no `NoResponseError` or `TimeoutException` test),
  `TestGetVoice` (no `NoResponseError` test),
  `TestGetCreditBalance` (no `TimeoutException` test).

---

## [RL-003] When pagination is involved, test the multi-page concatenation explicitly

- **Category:** Testing
- **Pattern:** Methods that auto-paginate (loop on `next_page_token`) need a
  test where the mock returns multiple pages with non-None tokens followed
  by a terminal page with no token. A single-page happy-path test will not
  exercise the loop's break condition or the token threading.
- **Why it matters:** A bug like "use next_page_token but never update the
  local variable" produces an infinite loop with a single-page test but
  passes — only a multi-page test catches it.
- **Fix:** Always include a test with `side_effect=[page1_with_token,
  page2_with_token, page3_terminal]` that asserts:
  1. The concatenated result has items from all pages, in order.
  2. The `next_page_token` kwarg on subsequent calls equals the token from
     the previous response.
- **Prevention point:** Implementation phase — write the pagination test
  alongside the implementation, not as an afterthought.
- **Frequency:** 1
- **Observed-In:** PR #12 (ISSUE-014), `TestSearchVoices::test_handles_pagination` —
  good example. Captured here as a pattern to repeat for future paginated
  methods (e.g., ISSUE-019's `search_custom_voices`).

---

## [RL-004] Annotate "always raises" helpers with `-> NoReturn` to enable type narrowing

- **Category:** Code Quality
- **Pattern:** A helper function that always raises (like
  `_handle_sdk_errors`) but is typed as `-> None` will cause type checkers
  to flag every variable assigned inside a preceding `try` block as
  "possibly unbound" in the code after the try/except.
- **Why it matters:** Generates spurious type-checker warnings that hide
  real issues; pollutes the IDE/CI signal-to-noise ratio.
- **Fix:** Annotate the helper as `from typing import NoReturn; def
  _handle_sdk_errors(...) -> NoReturn:`. The type checker then knows the
  except branch never falls through, and the variable assigned in the try
  block is considered bound on the next line.
- **Prevention point:** Implementation phase — when writing a function whose
  only successful exit is via `raise`, annotate it `NoReturn` from the start.
- **Frequency:** 2
- **Observed-In:** Carried forward from earlier issues; surfaced again by
  ISSUE-014's new methods (`search_voices`, `get_voice`,
  `get_credit_balance`). **Re-observed in PR #20 (ISSUE-018)** where
  `predict_duration` adds one more occurrence at
  `supertone_client.py:425` (total 23 errors in `supertone_client.py`).
  Now affects 8 wrapped methods; the single-line `NoReturn` fix on
  `_handle_sdk_errors` would close all of them. Justified as a dedicated
  tech-debt issue per the lessons-escalation protocol (frequency ≥ 2 across
  multiple PRs).

---

## [RL-005] Test helper default values must use explicit nullable annotations when nullable callers exist

- **Category:** Testing
- **Pattern:** Test helper functions like `_make_voice_detail(...,
  thumbnail_image_url="https://cdn.test/v1.png")` infer `str` from the
  default — but callers may pass `None` to test null-handling paths, leading
  to type-checker errors.
- **Why it matters:** Forces post-implementation Pyright-fix commits (as
  happened in this PR — commit `eb1baaa` had to fix
  `_make_voice_detail.thumbnail_image_url` and `_make_credit_balance.balance`
  type annotations to `str | None` / `float | None`).
- **Fix:** When designing a test helper for a field that the implementation
  treats as nullable, explicitly type the parameter as `T | None` from the
  outset:
  ```python
  def _make_voice_detail(
      *,
      thumbnail_image_url: str | None = "https://cdn.test/v1.png",
      samples: list | None = None,
      ...
  ):
  ```
- **Prevention point:** Implementation phase — when writing the test helper,
  match the nullability of the production field.
- **Frequency:** 1
- **Observed-In:** PR #12 (ISSUE-014), `tests/test_supertone_client.py` —
  required fix commit `eb1baaa`.

---

## [RL-006] Map every documented error path in the client wrapper before promising it in the handler

- **Category:** Error Handling
- **Pattern:** When a UX spec describes a specific error string for a
  specific HTTP status (e.g., "Voice not found: \"{voice_id}\"." for 404),
  the handler can only deliver that string if the SDK wrapper maps the
  underlying status to a domain exception. If the wrapper's
  `_handle_sdk_errors` does not cover the status, the exception bubbles
  raw and the handler silently violates the "never raise to caller"
  contract.
- **Why it matters:** Tests against mocked clients pass because the mock
  returns whatever you tell it to; the gap only surfaces with a real 404
  from the API. The user sees a stack trace or an unhandled error rather
  than the friendly UX message the spec promised.
- **Fix:** When adding a new handler for an inspection endpoint
  (`get_voice`, `preview_voice`, `edit_custom_voice`, etc.), audit
  `_handle_sdk_errors` first. Every status documented in the UX spec
  ("voice not found", "custom voice not found", "file too large") needs
  a matching mapping. If the SDK exposes the status but not a typed
  exception, branch on `exc.raw_response.status_code` in the wrapper.
- **Prevention point:** Implementation phase — at the moment a new
  handler is written, cross-reference its UX spec error table against
  `_handle_sdk_errors` and the SDK's error module before coding the
  except chain.
- **Frequency:** 1
- **Observed-In:** PR #16 (ISSUE-016), `src/supertone_tts_mcp/tools.py`
  `get_voice` — UX spec §4.4 promises `Voice not found: "{voice_id}".`
  but `_handle_sdk_errors` does not map any 404. Will resurface for
  ISSUE-017 (`preview_voice`), ISSUE-019 (`edit_custom_voice`,
  `delete_custom_voice`). Logged as Discovered Issue in
  `docs/sprint_state.md`.
