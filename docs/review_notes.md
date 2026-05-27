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
