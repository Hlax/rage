---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-026 / prompt-injection

## 1. Summary

Implemented deterministic prompt-injection fixture handling for Golden Test 24. Added a malicious-source fixture, a mock LLM output fixture with one legitimate research claim and four injected instruction candidates, deterministic prompt-injection helpers, validator rejection with `unsafe_or_injected_content`, automatic fixture selection for prompt-injection source text, and Golden Test 24 (4 tests). All 110 golden tests pass without Ollama; full safety audit returns `pass`.

## 2. Ticket

- Ticket ID: ticket-026
- Ticket title: Add prompt-injection golden fixture handling (Golden Test 24)
- Branch: `phase-1/ticket-026-prompt-injection`
- Phase: 1
- Agent/model: Cursor builder agent (GPT-5.5)
- Date: 2026-06-12
- Main tip before branch: `f109dbf` (includes pre-ticket-026 audit)

## 3. Scope

### In Scope

- Prompt-injection source fixture and mock claim-extraction fixture.
- Deterministic prompt-injection pattern helpers in `rge/safety/prompt_injection.py`.
- Candidate-claim validation boundary rejection with `unsafe_or_injected_content`.
- Prompt-injection fixture auto-selection in `claim_extractor.py`.
- Safety audit prompt-injection evidence check.
- Golden Test 24 (`tests/golden/test_24_prompt_injection.py`).

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, public export of injected text, broad pipeline rewrites, or any ticket beyond ticket-026 implementation.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `fixtures/sources/prompt_injection_creativity_short.txt` | New GT24 malicious-source fixture with one real research claim. |
| `fixtures/llm_outputs/claim_extraction_prompt_injection.json` | New deterministic mock output with one accepted candidate and four injected instruction candidates. |
| `rge/safety/prompt_injection.py` | Added deterministic injection patterns and candidate/source helper functions. |
| `rge/modules/claim_validator.py` | Rejects instruction-like candidates with `unsafe_or_injected_content` before accepted graph writes. |
| `rge/modules/claim_extractor.py` | Selects prompt-injection mock fixture when source text contains GT24 fixture markers. |
| `rge/modules/safety_auditor.py` | Verifies prompt-injection protection evidence files in full safety audit. |
| `tests/golden/test_24_prompt_injection.py` | New: Golden Test 24 (4 tests). |
| `tickets/TICKET_QUEUE.md` | ticket-026 done; ticket-027 proposed. |
| `tickets/ticket-026.json` | Status `done`. |
| `tickets/ticket-027.json` | Proposed public-site debug details ticket (GT25). |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-026_prompt-injection-readiness-audit.md` (commit `f109dbf`).
- Generated export artifacts were cleaned before the ticket branch was created.
- Prompt-injection checks run at the candidate-claim validation boundary, after source/chunk/quote provenance checks and before scope/field acceptance checks.
- The malicious fixture text is treated only as data. It is not used as an instruction and is not public-exported.
- Source credibility remains unchanged because ingestion does not assign a credibility boost from source text and extraction does not write `quality_score` or `credibility_notes`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Malicious instructions do not change extraction behavior or source credibility | PASS | GT24 checks accepted/rejected split and source credibility fields. |
| Only actual research claim is extracted; injected commands rejected or ignored | PASS | One accepted claim; four rejected claims with `unsafe_or_injected_content`. |
| `pytest tests/golden/test_24_prompt_injection.py` | PASS | 4/4. |
| Existing golden tests still pass (106+) | PASS | 110/110. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_24_prompt_injection.py` | PASS | 4 passed. |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS | 110 passed. |
| `RGE_LLM_MODE=mock python -m pytest` | PASS | 110 passed. |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS | status `pass`, exit 0, no blocked reasons. |

## 8. Manual CLI Verification

Golden Test 24 exercises `ingest`, `extract-claims`, `export-public`, run-report aggregation, and ticket-writing filtering on temp SQLite databases. No live model, live web discovery, or public write route was used.

## 9. Safety Audit

Full safety audit passes and now includes prompt-injection evidence files in `checked_files`:

- `fixtures/sources/prompt_injection_creativity_short.txt`
- `fixtures/llm_outputs/claim_extraction_prompt_injection.json`
- `rge/safety/prompt_injection.py`
- `tests/golden/test_24_prompt_injection.py`

## 10. Spec Deviations

- Added full-audit prompt-injection evidence checks beyond the ticket minimum so GT24 protection is visible to the safety gate.
- Added `ticket-027` as the next proposed ticket for Golden Test 25; no ticket-027 implementation was performed.

## 11. Merge to Main

- Merge commit: pending
- Branch: `phase-1/ticket-026-prompt-injection`
- Post-merge pytest on `main`: pending

## 12. Recommended Next Ticket

**ticket-027**: Add public-site debug details without private data exposure (Golden Test 25).

## 13. Suggested Next Prompt

Pre-ticket audit recommended before ticket-027 (medium risk; public site/export safety surface). Then:

```txt
/rge-run-next-ticket
```
