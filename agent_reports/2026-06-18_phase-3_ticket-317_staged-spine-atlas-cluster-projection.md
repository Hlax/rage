# Agent Report: ticket-317 — Staged spine atlas cluster projection hook

**Date:** 2026-06-18  
**Ticket:** ticket-317  
**Branch:** `phase-3/ticket-317-staged-spine-atlas-cluster-projection`  
**Main tip before branch:** `ae7d17b`  
**Audit gate:** `agent_reports/2026-06-18_pre-ticket-317_staged-spine-atlas-cluster-projection-audit.md` (GO)

## Summary

Added staged-spine cluster projection hooks mirroring ticket-296 evidence DB pattern.
`export-atlas-snapshot` on staged orchestrator DBs now populates `clusters[]` from
rank-scoped claims and active relationships. Ticket-316 operator re-export upgrades
**partial → pass** on gitignored `ticket316_staged_spine_refresh.sqlite`.

## Scope

**In:** `ensure_staged_cluster_summaries`, atlas builder hook, unit tests, pre-ticket audit.

**Out:** Public export/site, README-only docs, schema migrations, live_network CI.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/evidence_db_atlas.py` | Staged cluster summary helpers |
| `rge/modules/atlas_snapshot_builder.py` | Hook when staged runs present |
| `tests/unit/test_staged_spine_cluster_projection.py` | 3 network-free tests |
| `agent_reports/2026-06-18_pre-ticket-317_staged-spine-atlas-cluster-projection-audit.md` | Pre-ticket GO |
| `agent_reports/2026-06-18_phase-3_ticket-317_staged-spine-atlas-cluster-projection.md` | This report |
| `tickets/ticket-317.json` | Status `done` |
| `tickets/ticket-318.json` | Seeded principal audit |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Staged export populates clusters[] from active relationships | **PASS** |
| Ticket-316 DB re-export coherence pass | **PASS** — `overall_coherence_verdict: pass` |
| Mock unit test; no live_network CI | **PASS** — 3 new tests |
| Golden + full pytest | **PASS** — 792 pytest (789+3), verify pass |

## Before / after (ticket-316 operator DB)

| Metric | ticket-316 (pre-317) | ticket-317 re-export |
|--------|---------------------:|---------------------:|
| `overall_coherence_verdict` | partial | **pass** |
| clusters | 0 | **2** |
| runs | 3 | 3 |
| cards | 2 | 2 |
| edges | 3 | 3 |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_spine_cluster_projection.py -q   # 3 passed
python -m pytest tests/unit/test_evidence_db_cluster_projection.py -q    # 3 passed
python -m rge.cli verify --skip-site                                     # pass

# Operator re-export on ticket-316 DB:
python -m rge.cli export-atlas-snapshot --db data/db/ticket316_staged_spine_refresh.sqlite ...
python -m rge.cli atlas-coherence-report --snapshot data/atlas/ticket316/atlas_snapshot_v317.json ...
# overall_coherence_verdict: pass
```

Safety audit not required — DB-only operator projection; no public surface changes.

## Recommended next ticket

**ticket-318** — Principal audit post-ticket-317 (cadence checkpoint after 315–317 batch).

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

Merge commit: _(pending)_
