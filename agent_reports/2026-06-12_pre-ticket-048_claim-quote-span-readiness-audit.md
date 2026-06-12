---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-048 Claim Quote Span Validation Readiness Audit

- Audit type: focused pre-ticket audit — adversarial readiness review before implementing ticket-048
- Date: 2026-06-12
- Scope: read-only audit of ticket-048 claims vs existing claim validation, GT02, fixture spine, and improvement-ticket provenance. No implementation in this pass.

## Release / CI context (terminal review)

The operator push and CI watch session is **healthy and trustworthy**:

| Check | Result | Evidence |
|---|---|---|
| Push to `origin/main` | pass | `4e32d44..c98726b main -> main` |
| GitHub auth | pass | `gh` logged in as Hlax |
| Golden Gate run 27425020457 | **success** | All 12 steps green: UTF-8 validate → `pip install -e ".[dev]"` → golden → pytest → smoke collect check → safety audit → npm build |
| Prior failure run 27422772206 | explained | Failed at self-defeating `live_smoke` grep step before CI hotfix landed; not a regression |
| Local == remote | pass | `HEAD` and `origin/main` both at `c98726b` |

**Release status: PASS** — remote CI now matches local gates for the pushed tip.

## Summary

**Do not implement ticket-048 as written.** The promoted ticket describes behavior that is **already implemented and golden-tested**. The `missing_quote_span_count=1` evidence comes from the **intentional** fixture spine (`claim_extraction_valid_and_missing_quote.json`), not from a production gap.

**Verdict: REJECT ticket-048 (duplicate / false-positive improvement ticket).**

The real follow-up work is to **harden the improvement-ticket generator** so expected golden rejections are not promoted as builder queue items.

## Ticket-048 claim vs repo reality

| ticket-048 acceptance criterion | Already satisfied? | Evidence |
|---|---|---|
| Claims without quote spans rejected with machine-readable reasons | **Yes** | `claim_validator.py` returns `missing_quote_span`; GT02 `test_claims_without_quote_spans_are_rejected` passes |
| Accepted claims always include primary quote spans | **Yes** | `ClaimRepository.insert_accepted` writes `claim_quotes` with `is_primary=1`; GT02 asserts quotes on accepted claims |
| GT02 test plan | **Already green** | 4/4 pass in mock mode |

### Why the improvement ticket exists

1. Fixture-mode MVP uses `claim_extraction_valid_and_missing_quote.json` (by design).
2. One candidate has `"quote_span": null` → correctly rejected as `missing_quote_span`.
3. Run report aggregates this as `top_failure_modes: [{reason: missing_quote_span, count: 1}]`.
4. `write_improvement_tickets()` maps any qualifying failure mode to `GOLDEN_FAILURE_TEMPLATES["missing_quote_span"]` without checking whether golden tests already cover intentional rejection.
5. ticket-045 promoted that draft to `tickets/ticket-048.json`.

This is a **generator false positive**, not missing validation logic.

## Code paths reviewed (no gaps found for ticket scope)

| Module | Finding |
|---|---|
| `rge/modules/claim_validator.py` | Rejects empty/null `quote_span`; verifies quote in chunk text |
| `rge/modules/claim_extractor.py` | Validates before persist; never writes accepted claims without passing validator |
| `rge/db/repositories.py` | `insert_accepted` persists primary quote from `quote_span` |
| `fixtures/llm_outputs/claim_extraction_valid_and_missing_quote.json` | Deliberately includes null quote_span candidate for GT02/GT20 spine |
| `tests/golden/test_02_claim_extraction.py` | Explicit rejection + acceptance tests |

### Optional future work (out of ticket-048 scope)

- **`char_start` / `char_end` offsets** in `claim_quotes` are NULL today (`05_DATA_MODEL.md` allows nullable). Computing offsets would be a **separate** ticket if traceability requirements tighten.
- **Live Ollama extract-claims** quote-span quality is untested in CI (mock-only by design).

## Hardened recommendation

### Reject ticket-048

Mark `ticket-048` as `rejected` in queue JSON and notes. Do not open an implementation branch. Implementing the ticket as written would either be a no-op or risk weakening intentionally strict validation.

### Seed ticket-049 (recommended next repair ticket)

**Title:** Skip improvement tickets for golden-covered intentional rejection modes

**Problem:** `write_improvement_tickets()` promotes failure modes like `missing_quote_span` even when GT02/GT20 already prove correct reject-closed behavior on fixture spine.

**Acceptance criteria (draft):**

1. `missing_quote_span` (and similarly golden-covered reasons) do not produce improvement drafts when only fixture-intentional rejections occurred.
2. GT20/GT21 still pass; fixture MVP run still records failure modes in run report (reporting unchanged).
3. Operator loop no longer surfaces stale promotion for already-promoted drafts.

**Risk:** low–medium (ticket_writer only; no public export changes).

### Cadence note

Principal audit cadence is **overdue** (5 done tickets since post-ticket-042). This pre-ticket audit satisfies the **ticket-048 implementation gate** (by rejecting implementation). Before the *next* feature ticket after ticket-049, write `agent_reports/2026-06-12_principal-audit-post-ticket-047.md` or run `/rge-principal-audit`.

### Housekeeping

- Stale draft remains in `data/tickets/improvement_ticket_latest.json` — operator loop still recommends promotion even though ticket-048 was already promoted. Clear or supersede the draft artifact when ticket-049 lands.
- Node.js 20 deprecation annotation on Actions is informational only; not blocking.

## Verdict

| Gate | Result |
|---|---|
| Release / CI | **PASS** |
| ticket-048 implementation | **REJECT — duplicate / false positive** |
| Safe to start ticket-048 branch | **NO** |
| Recommended next move | Reject ticket-048; seed and implement ticket-049 (improvement generator filter) |

## Suggested next prompt for operator

```txt
Reject ticket-048 as duplicate per agent_reports/2026-06-12_pre-ticket-048_claim-quote-span-readiness-audit.md.
Seed ticket-049 to stop promoting golden-covered failure modes from improvement drafts.
Write post-ticket-047 principal audit checkpoint, then implement ticket-049 on its own branch.
```
