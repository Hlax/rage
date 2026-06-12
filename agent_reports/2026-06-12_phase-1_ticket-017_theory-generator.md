---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-017 / theory-generator

## 1. Summary

Implemented deterministic mock theory generation for Golden Test 15. Added migration `0005_theory_candidates`, `TheoryCandidateRepository`, `generate-theory-candidates` CLI command, mock theory fixture with fragment-based claim resolution, validation layer, and Golden Test 15 (4 tests). All 73 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-017
- Ticket title: Add mock theory generator (Golden Test 15)
- Branch: `phase-1/ticket-017-theory-generator`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-12

## 3. Scope

### In Scope

- `theory_generator.py`: fixture propose, claim-ID validation, candidate report build, persistence, file export.
- `TheoryCandidateRepository` and `0005_theory_candidates` migration.
- CLI `generate-theory-candidates` with `--domain`, `--cluster-report`, `--fixture`, `--output-dir`.
- Mock fixture `fixtures/llm_outputs/theory_generation_creativity_diversity.json`.
- Golden Test 15 (`tests/golden/test_15_theory_generator.py`).
- Pre-ticket-017 audit report (committed on main before branch).
- Schema reference and scaffold/ingestion test updates.

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, public theory cards/export.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/db/migrations/0005_theory_candidates.sql` | New: `theory_candidates` table. |
| `rge/db/schema.sql` | Reference DDL for `theory_candidates`. |
| `rge/db/repositories.py` | `TheoryCandidateRepository`, `make_theory_candidate_id`. |
| `rge/modules/theory_generator.py` | Full theory candidate pipeline (was Phase 0 stub). |
| `rge/cli.py` | `generate-theory-candidates` command. |
| `fixtures/llm_outputs/theory_generation_creativity_diversity.json` | Mock theory fixture. |
| `tests/golden/test_15_theory_generator.py` | New: Golden Test 15 (4 tests). |
| `tests/golden/test_00_scaffold.py` | `theory_candidates` table + CLI command. |
| `tests/golden/test_01_ingestion.py` | Migration list includes `0005_theory_candidates`. |
| `tickets/TICKET_QUEUE.md` | ticket-017 done; ticket-018 proposed. |
| `tickets/ticket-017.json` | Status `done`. |
| `tickets/ticket-018.json` | Proposed contract-respecting question generation ticket. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-017_theory-generator-readiness-audit.md`.
- Fixture resolves supporting/qualifying claim IDs by text fragments against cluster evidence packet claim IDs.
- Weakening evidence may be claim IDs or open-gap strings from the evidence packet.
- Theories persist with `status: candidate` only; idempotent re-runs return `already_generated`.
- Graph pattern `contradiction_by_metric` grounded in existing AI assistance ↔ diversity fixture edges.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Deterministic candidate theory from golden cluster evidence without Ollama | PASS | GT15 spine. |
| Theory JSON includes support, caveats, boundaries, weakening, next questions | PASS | GT15 assertions. |
| Theories stored as candidates, never facts | PASS | DB status + no accepted-theory claims. |
| `pytest tests/golden/test_15_theory_generator.py` | PASS | 4/4. |
| Existing golden tests still pass (69+) | PASS | 73/73. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_15_theory_generator.py` | PASS | 4 passed. |
| `python -m pytest tests/golden` | PASS | 73 passed. |
| `python -m pytest` | PASS | 73 passed. |

## 8. Manual CLI Verification

Not run separately; Golden Test 15 exercises `generate-theory-candidates` after cluster report on temp DB.

## 9. Safety Audit

Not required: no public export, public site, or write routes changed. Theory artifacts are internal candidates only.

## 10. Spec Deviations

- Added `0005_theory_candidates.sql` and `schema.sql` update (required by `05_DATA_MODEL.md` §4.22; not listed in ticket JSON `expected_files`).
- Weakening evidence may include open-gap strings when claim IDs are unavailable (per audit hardened scope).

## 11. Merge to Main

- Merge commit: `4aa2296f2bf86b1d39e64cf12fee78c8a2498550`
- Branch: `phase-1/ticket-017-theory-generator` merged to `main` and pushed to `origin/main`.
- Post-merge pytest on `main`: 73 passed.
- Pre-ticket audit commit included: `0154e87` (theory generator audit + runner gate).

## 12. Recommended Next Ticket

**ticket-018**: Add contract-respecting question generation (Golden Test 16).

## 13. Suggested Next Prompt

```txt
/rge-run-next-ticket
```
