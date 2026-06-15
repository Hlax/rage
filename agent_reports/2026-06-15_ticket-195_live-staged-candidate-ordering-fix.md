---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-195
---

# ticket-195: Live Staged Candidate Ordering Fix

## Summary

Replaced invalid `ORDER BY rank ASC` with `ORDER BY priority_score DESC` in all nine
per-step `live_network` staged tests, aligning with `candidate_sources` schema and
ticket-193 orchestrator behavior.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-195 |
| Branch | `phase-2/ticket-195-live-staged-candidate-ordering-fix` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-194.md` |
| Main tip before branch | `2dbe892` (includes post-ticket-194 audit commit) |

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_live_staged_fetch_validation.py` | `priority_score DESC` |
| `tests/unit/test_live_staged_ingest_validation.py` | same |
| `tests/unit/test_live_staged_extract_mock_spine.py` | same |
| `tests/unit/test_live_staged_link_mock_spine.py` | same |
| `tests/unit/test_live_staged_build_mock_spine.py` | same |
| `tests/unit/test_live_staged_detect_mock_spine.py` | same |
| `tests/unit/test_live_staged_reconcile_mock_spine.py` | same |
| `tests/unit/test_live_staged_report_mock_spine.py` | same |
| `tests/unit/test_live_staged_rank2_report_mock_spine.py` | same (rank-2 uses `OFFSET 1` after DESC) |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | All live staged tests use `priority_score DESC` | **PASS** |
| 2 | Default pytest collection unchanged | **PASS** (16 deselected) |
| 3 | Golden pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 599 passed, 16 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

No live network pytest run (SQL-only hygiene fix).

## Merge to main

Merged @ `d5003f0`. Pushed to `origin/main`.

## Recommended next ticket

**ticket-196** — Shared live staged candidate query test helper (DRY).

## Suggested next prompt

`/rge-run-next-ticket`
