# Agent Report: ticket-295 — Evidence DB run report projection for atlas coherence GO

**Date:** 2026-06-16  
**Ticket:** ticket-295  
**Branch:** `phase-3/ticket-295-evidence-db-run-report-projection`  
**Main tip before branch:** `2ac5433`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-295_evidence-db-run-report-projection-audit.md` (GO)

## Summary

Added `ensure_evidence_run_report` to persist DB-only run reports for evidence DB atlas
export (no golden contract, no disk write). Atlas `reports[]` now includes `run_id`;
coherence **meaningful** and **reports** sub-verdicts pass on mock evidence spine.
Ticket-293 operator re-export: reports 0→1; reports verdict pass (overall remains partial
due to empty clusters warn).

## Scope

**In:** `ensure_evidence_run_report`, atlas builder hook, unit tests.

**Out:** Public atlas UI, live default pytest, schema migration, CLI `generate-run-report` changes.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/evidence_db_atlas.py` | `ensure_evidence_run_report` |
| `rge/modules/atlas_snapshot_builder.py` | Hook after card seeding |
| `tests/unit/test_evidence_db_run_report_projection.py` | 3 network-free tests |
| `tickets/ticket-295.json` | Status `done` |
| `tickets/ticket-296.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Evidence DB atlas path ensures run_reports row | **PASS** |
| Atlas snapshot reports[] with run_id | **PASS** |
| Coherence meaningful + reports verdicts pass | **PASS** (mock spine) |
| Network-free unit test + golden/full pytest | **PASS** — 142 golden, 751 full |
| No public/site/schema/live default pytest | **PASS** |

## Operator re-run (ticket-293 DB)

| Metric | ticket-294 | ticket-295 |
|--------|------------|------------|
| `reports[]` | 0 | **1** |
| reports coherence verdict | partial | **pass** |
| overall_coherence_verdict | partial | partial (clusters warn) |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_evidence_db_run_report_projection.py -q  # 3 passed
python -m pytest tests/golden -q                                      # 142 passed
python -m pytest -q                                                  # 751 passed, 33 deselected
```

Safety audit not required — DB-only operator projection; no public surface changes.

## Recommended next ticket

**ticket-296** — Evidence DB cluster summary projection for atlas overall GO

Address `clusters[]` empty warn so overall coherence can reach pass on evidence DB export.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `a46929e`
