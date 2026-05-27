# Review Notes — ISSUE-016 (PR #16)

> Reviewer: team-lead (Opus 4.7, 1M context)
> PR: https://github.com/pillip/supertone-mcp/pull/16
> Branch: `issue/ISSUE-016-get-voice-and-balance`
> Date: 2026-05-27
> Scope: `tools.py`, `server.py`, `tests/test_tools.py`, `tests/test_server.py` (4 files, +841/-5)
> Verdict: **Approve** (after F2 review fix below)
> Confidence: **High**

---

## Code Review

### Strengths

1. **AC coverage is complete and explicit.**
   - AC #1 (formatted detail render including sample COUNT, no URLs) → `TestFormatVoiceDetail::test_renders_all_fields` + `test_does_not_leak_sample_urls`.
   - AC #2 (empty/whitespace voice_id rejected without API call) → `TestGetVoiceHandler::test_empty_voice_id_returns_validation_error_without_api_call` + `test_whitespace_voice_id_returns_validation_error_without_api_call`, both assert `MC.assert_not_called()` and `inst.get_voice.assert_not_called()`.
   - AC #3 (SupertoneAuthError → auth error string) → `test_auth_error_returns_formatted_string`.
   - AC #4 (credit balance happy path including plan/expiry) → `TestGetCreditBalanceHandler::test_happy_path_returns_formatted_balance` + `test_happy_path_with_plan_and_expiry`.
   - AC #5 (both tools registered) → `TestToolRegistration::test_get_voice_tool_exists` + `test_get_credit_balance_tool_exists` + description-wording tests.

2. **RL-002 (symmetric error-branch testing) satisfied.** Each new handler exercises all four upstream branches: auth, rate-limit, server (with status code echo), and connection. Both also test missing-API-key short-circuit and `aclose()` on success + failure.

3. **RL-005 (nullable test-helper annotations) satisfied.** `_make_voice_detail` declares every optional field as `T | None = default` so null-handling paths can be exercised without type-checker fights.

4. **UX-spec fidelity (§4.4 / §4.5).** Output format matches exactly:
   - `Voice ID: ...` → `Name: ...` → ... → `Samples: N` → optional `Thumbnail: ...` → `Use preview_voice to fetch sample URLs.`
   - `Credit balance: 12,345 chars remaining.` as the canonical first line with thousands separators; optional `Plan:` / `Expires:` on subsequent lines.

5. **Sample-URL leak guard.** `test_does_not_leak_sample_urls` directly enforces the AC requirement that URLs only appear in `preview_voice` output, even when the SDK payload contains them.

6. **The "registers exactly two tools" assertion that would have failed every v0.2 PR was replaced with a forward-looking superset check.** This avoids unnecessary churn for ISSUE-017/018/019/020.

### Findings

| # | Severity | Category | Finding | Action |
|---|----------|----------|---------|--------|
| F1 | **Medium** | Functional gap | UX spec §4.4 specifies `Voice not found: "{voice_id}".` for 404 responses, but `_handle_sdk_errors` in `supertone_client.py` does not map any 404 type. A 404 from `voices.get_voice_async` will currently bubble as an unmapped exception (violates the "never raise to caller" contract). | Out of this PR's scope (ISSUE-014 client-layer limitation). Logged as discovered issue for a follow-up. |
| F2 | **Low** | Style | The forward-compat `plan`/`expires_at` access path used an `isinstance(extras, dict)` ladder with a `# type: ignore[assignment]` alias. | Fixed in this review pass. TypedDicts ARE dicts at runtime, so direct `.get(...)` with per-call `# type: ignore[typeddict-item]` is cleaner. |
| F3 | **Info** | Style | `format_credit_balance` returns a multi-line string when plan/expires are present, but the docstring leads with the single-line case. | Acceptable — the docstring already says "without breaking the single-line guarantee for the minimal case." No action. |
| F4 | **Info** | Test wording | `TestToolRegistration::test_registers_v02_tools` replaced the prior fixed `len == 2` assertion. | OK — superset check documented in code. |

### Architecture conformance

- Layering preserved: validation/formatting/handler boundary matches `text_to_speech` and `search_voice` patterns.
- No new module dependencies introduced. The two new imports (`CreditBalanceDict`, `VoiceDetailDict`) were already defined in `models.py` per ISSUE-014.
- `aclose()` is called in `finally` for both handlers — consistent with `search_voice`.

### Test quality

- 38 new assertions across 7 test classes (5 in `test_tools.py` covering formatters + handlers, 2 in `test_server.py` covering registration + schema).
- No hollow tests, no `pass`-only bodies — verified by the review checkpoint.
- 235/235 pass; ruff clean (post-auto-fix import sorting).

### Confidence

**High.** The implementation matches the UX spec precisely, all ACs have explicit test coverage, and the RL-001/002/005 patterns from PR #12 are honored. The single Medium finding (F1, voice-not-found mapping) is a pre-existing client-layer gap that does not block this PR. Recommend merging once CI is green.

---

## Security Findings

None new. The implementation reuses the audited PR #12 client surface.

- No new external inputs are unvalidated. `voice_id` is type-checked (`isinstance(str)`) before any API call.
- No new secrets or credentials are added; reuses the existing `resolve_api_key()` env-var path.
- No new file-system writes, subprocess calls, or network endpoints — both new tools only call existing SDK methods that were security-reviewed in PR #12.
- Error messages do NOT echo the API key in any branch.
- The mocked-client tests cannot accidentally hit a live API (verified: `SupertoneClient` is patched in every handler test).

---

## Follow-ups

- **F1 (Medium)** — Map a "voice not found" path through `_handle_sdk_errors` so `get_voice("nonexistent")` and `preview_voice("nonexistent")` (ISSUE-017) can both return `Voice not found: "{voice_id}".` per UX spec §4.4. A dedicated tech-debt issue would be appropriate; recorded as a Discovered Issue in `docs/sprint_state.md`.

---

# Review Notes — ISSUE-017 (PR #18)

> Reviewer: team-lead (Opus 4.7, 1M context)
> PR: https://github.com/pillip/supertone-mcp/pull/18
> Branch: `feat/ISSUE-017-preview-voice`
> Date: 2026-05-27
> Scope: `tools.py`, `server.py`, `models.py`, `tests/test_tools.py`, `tests/test_server.py` (5 files, +759/-6)
> Verdict: **Approve**
> Confidence: **High**

## Summary

ISSUE-017 adds the `preview_voice` MCP tool plus the pure `format_voice_samples` formatter, registers the tool in the server, and applies the mandatory RL-001 fix-along to `VoiceDetailDict`. All 267 tests pass in the worktree (`uv run pytest -q`), the unit gate passes, and the previously-broken pyright errors at `tools.py:563/564/572` (introduced by PR #16's `format_voice_detail`) are resolved.

## Code Review

### Correctness

- **Fail-fast voice_id validation** — `if not isinstance(voice_id, str) or not voice_id.strip(): return "voice_id must not be empty."` mirrors `get_voice` exactly. No API call when empty/whitespace; tests `test_empty_voice_id_returns_validation_error_without_api_call` and `test_whitespace_voice_id_returns_validation_error_without_api_call` assert `MC.assert_not_called()`.
- **Filter semantics** — AND-combined exact match across language/style/model. The `None` sentinel means "do not filter on this dimension." Each dimension is exercised by a dedicated test plus a combined-filter test (`test_combined_filters_narrow_correctly`).
- **Numbering** — restarts at 1 across the *filtered* subset (per UX spec §4.6). Verified by `test_numbering_resets_at_one_for_filtered_subset`.
- **Edge messages** — exact-string equality assertions guarantee spec compliance:
  - `"This voice has no preview samples."` for both `samples == []` and `samples is None`.
  - `"No matching samples for the given filters."` when filters mismatch.
- **Sample dict access pattern** — filter step uses `s.get("language")` (defensive against malformed SDK payloads), output uses `sample['language']` (type-safe since `SampleDict` is total-True). This asymmetry is intentional and acceptable.
- **Client lifecycle** — `aclose()` called in `finally` on both success and error paths; covered by `test_client_aclose_called_on_success` and `test_client_aclose_called_on_error`.

### Patterns / Conventions

- Follows the same handler shape as `get_voice` (validate → resolve api_key → instantiate client → try/except SDK errors → finally aclose → format result). Easy to spot-check.
- Error mapping is identical to `get_voice` (4 SDK error classes → 4 plain-text strings). Per **RL-002**, the connection-error branch is explicitly tested (`test_connection_error_returns_formatted_string`).
- Tool registration in `server.py` matches the `get_voice` pattern: `@mcp.tool(...)` decorator with a UX-spec-derived description, thin pass-through to the `tools.preview_voice` handler.

### Security

- No secrets or API keys echoed in any output path.
- No stack traces propagate to the caller.
- Input validation happens before any network I/O.
- No new dependencies introduced.

### Test Coverage

- **AC #1** (no filter → all samples): `test_renders_all_samples_with_no_filters`, `test_happy_path_no_filters_returns_all_samples`.
- **AC #2** (language filter): `test_filter_by_language_only`, `test_filter_by_language_narrows_results`; plus `test_filter_by_style_narrows`, `test_filter_by_model_narrows` for the other dimensions.
- **AC #3** (combined filters): `test_combined_filters_narrow_correctly`.
- **AC #4** (no-match message): `test_no_match_returns_no_matching_samples_message`, `test_no_match_filters_returns_no_matching_message`.
- **AC #5** (no samples message): `test_empty_samples_list_returns_no_preview_samples_message`, `test_none_samples_returns_no_preview_samples_message`, `test_empty_samples_returns_no_preview_message`, `test_samples_field_absent_returns_no_preview_message`.
- **AC #6** (empty voice_id): `test_empty_voice_id_returns_validation_error_without_api_call`, `test_whitespace_voice_id_returns_validation_error_without_api_call`.
- **AC #7** (error paths): `test_auth_error_returns_formatted_string`, `test_rate_limit_error_returns_formatted_string`, `test_server_error_returns_formatted_string`, `test_connection_error_returns_formatted_string`, `test_missing_api_key_returns_error_without_api_call`.
- **Server registration**: tool exists, description mentions "sample audio URLs" + "NOT play", `voice_id` required, `language/style/model` optional (6 assertions).

## RL-001 Fix-Along Verification

Per task instructions, applied RL-001 to `VoiceDetailDict` in `src/supertone_tts_mcp/models.py`:

```diff
-class VoiceDetailDict(TypedDict, total=False):
+class VoiceDetailDict(TypedDict):
     ...
-    samples: list[SampleDict]
-    thumbnail_image_url: str
+    samples: NotRequired[list[SampleDict]]
+    thumbnail_image_url: NotRequired[str]
```

Pyright verification (run inside the worktree's venv):

```
$ uv run pyright src/supertone_tts_mcp/tools.py src/supertone_tts_mcp/models.py
...
5 errors, 0 warnings, 0 informations
```

Breakdown of remaining 5 errors (all pre-existing ISSUE-012-era tech debt, explicitly out-of-scope per `docs/sprint_state.md`):

| File / Line | Error | Origin |
|---|---|---|
| tools.py:12 | `"File" is not exported from module "mutagen"` | ISSUE-012 (mutagen private import) |
| tools.py:352 | `"output_dir" is possibly unbound` | ISSUE-012 |
| tools.py:416 | `"parent" is not a known attribute of "None"` | ISSUE-012 |
| tools.py:440 | `Argument of type "str \| None" cannot be assigned to parameter "file_path" of type "str"` | ISSUE-012 |
| tools.py:450 | `Argument of type "bytes \| None" cannot be assigned to parameter "s" of type "ReadableBuffer"` | ISSUE-012 |

**Critically, the three errors PR #16 introduced are GONE:**

| File / Line (before this PR) | Was | Now |
|---|---|---|
| tools.py:563 (`detail["voice_id"]`) | `"voice_id" is not a required key... could be missing from "VoiceDetailDict"` | Clean |
| tools.py:564 (`detail["name"]`) | same | Clean |
| tools.py:572 (`detail["use_case"]`) | same | Clean |

`pyright src/supertone_tts_mcp/models.py` alone: **0 errors**.

## Test Quality

All test files contain real `assert ...` statements (no `pass`-only or empty-body tests). Each test mocks `SupertoneClient` rather than touching the network. No flaky behavior introduced.

## Documented Gaps (not blocking)

- **RL-006 (404 mapping)** — `preview_voice("nonexistent_voice_id")` will currently bubble the raw SDK exception through `_handle_sdk_errors` (which has no 404 branch) and therefore will NOT return the UX-spec-mandated `Voice not found: "{voice_id}".` string for that scenario. This is a known gap also affecting `get_voice` (PR #16). Per the explicit task instruction, I did NOT attempt the fix in this PR — it is a separate tech-debt candidate already logged in `docs/sprint_state.md` and `docs/review_lessons.md` (RL-006).

## Security Findings

None. The handler does not write to disk, does not echo credentials, validates input before network I/O, and uses pre-existing typed SDK error mapping.

## Verdict

**Approve.** All 7 ACs covered, RL-001 fix-along verified clean, no Critical/High findings. The single documented gap (404 mapping) is explicitly out of scope.

