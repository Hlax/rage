---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-144
---

# ticket-144: Extract Claims from Staged-Ingested Source (Mock Spine Step)

## Summary

Added **`staged_fetch_extract_claims.json`** mock fixture and auto-selection in
`claim_extractor` for staged fetch spine chunk text. Unit test proves full Phase 3 path:
**discover → enqueue → fetch → ingest-staged → extract-claims** with mock LLM only.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-144 |
| Branch | `phase-2/ticket-144-staged-ingest-extract-spine` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-144_staged-ingest-extract-spine-audit.md` (GO) |
| Main tip before branch | `494dc6c` |

## Scope

### In

- `fixtures/llm_outputs/staged_fetch_extract_claims.json`
- `claim_extractor._is_staged_fetch_spine_chunk()` + fixture routing
- `tests/unit/test_staged_ingest_extract_spine.py` (4 tests)

### Out

- Live LLM, link-concepts/relationship steps, schema, public site, full research run

## Changed files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_extract_claims.json` | mock extract fixture |
| `rge/modules/claim_extractor.py` | staged spine fixture selection |
| `tests/unit/test_staged_ingest_extract_spine.py` | e2e spine tests |
| `tickets/ticket-144.json` | status done |
| `tickets/ticket-145.json` | seeded link-concepts follow-on |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | extract-claims persists validated claims (fixture-backed) | **PASS** |
| 2 | E2E discover→fetch→ingest→extract unit test | **PASS** |
| 3 | No live LLM in default collection | **PASS** |
| 4 | Golden mock-only pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_ingest_extract_spine.py -q   # 4 passed
python -m pytest tests/golden -q                                      # 142 passed
python -m pytest -q                                                   # 540 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                       # pass
```

## Spec deviations

- No `cli.py` changes; existing `extract-claims --fixture` sufficient for explicit fixture path.

## Merge to main

Merged to `main` as `08eddff8e6e20eb3a756c3aaa70b265d242a4082` (2026-06-14).
Post-merge pytest: 540 passed, 6 deselected.

## Recommended next ticket

**ticket-145** — Link concepts on staged-ingested source (pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-145 audit, then `/rge-run-next-ticket` for ticket-145.
