# Agent Report: ticket-297 — Evidence DB relationship edge projection for atlas overall GO

**Date:** 2026-06-16  
**Ticket:** ticket-297  
**Branch:** `phase-3/ticket-297-evidence-db-relationship-projection`  
**Main tip before branch:** `d81b141`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-297_evidence-db-relationship-projection-audit.md` (GO)

## Summary

Added `ensure_evidence_relationship_edges` to seed deterministic active `relationships` and
`relationship_evidence` rows from claim–concept links on evidence DBs. Atlas `edges[]` now
populates on mock evidence spine and **overall_coherence_verdict** reaches **pass**.

## Scope

**In:** `ensure_evidence_relationship_edges`, atlas builder hook (before cluster summary), unit tests, pre-ticket audit.

**Out:** Public atlas UI, live default pytest, full build-relationships LLM spine, schema migration.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/evidence_db_atlas.py` | `ensure_evidence_relationship_edges` + helpers |
| `rge/modules/atlas_snapshot_builder.py` | Hook before cluster summary |
| `tests/unit/test_evidence_db_relationship_projection.py` | 3 network-free tests |
| `agent_reports/2026-06-16_pre-ticket-297_evidence-db-relationship-projection-audit.md` | Pre-ticket GO |
| `tickets/ticket-297.json` | Status `done` |
| `tickets/ticket-298.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Evidence DB atlas populates edges[] from active relationships | **PASS** |
| Mock spine overall_coherence_verdict pass | **PASS** |
| Network-free unit test + golden/full pytest | **PASS** — 142 golden, 757 full |
| No public/site/schema/live default pytest | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_evidence_db_relationship_projection.py -q  # 3 passed
python -m pytest tests/golden -q                                      # 142 passed
python -m pytest -q                                                  # 757 passed, 33 deselected
```

Safety audit not required — DB-only operator projection; no public surface changes.

## Recommended next ticket

**ticket-298** — Operator evidence DB atlas coherence re-export proof (ticket-293 DB path)

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `2d6b12b`
