# Agent Report: ticket-294 — Evidence DB run lineage + live-derived atlas card projection v0

**Date:** 2026-06-16  
**Ticket:** ticket-294  
**Branch:** `phase-3/ticket-294-evidence-db-atlas-projection-v0`  
**Main tip before branch:** `bb42bad`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-294_evidence-db-atlas-projection-audit.md` (GO)

## Summary

Added `evidence_db_atlas` helpers to populate `research_runs[]` with question lineage and
project claim-backed `public_cards` (replacing golden placeholders) on non-fixture evidence
DB atlas export. Network-free unit tests prove the path; ticket-293 operator DB re-export
improved coherence from **fail → partial** with `runs>=1` and live-derived claim card.

## Scope

**In:** `evidence_db_atlas.py`, atlas builder hook, unit tests, operator re-export validation.

**Out:** Public atlas UI, default pytest live tests, schema migrations, review_batch,
staged network, public-site changes.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/evidence_db_atlas.py` | Run lineage + claim-backed card seeding |
| `rge/modules/atlas_snapshot_builder.py` | Non-fixture export hook |
| `tests/unit/test_evidence_db_atlas_projection.py` | Network-free projection tests |
| `tickets/ticket-294.json` | Status `done` |
| `tickets/ticket-295.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Evidence DB populates `research_runs` with question lineage | **PASS** |
| Atlas export uses claim-backed cards (not golden when live claims) | **PASS** |
| Network-free unit test for runs + claim cards | **PASS** — 3 tests |
| Optional ticket-293 re-run improved coherence | **PASS** — fail→partial, runs 0→1, claim card |
| Mock golden/full pytest green | **PASS** — 142 golden, 748 full |

## Operator re-run (ticket-293 DB)

After implementation, re-export on existing ticket-293 evidence DB:

- `overall_coherence_verdict`: **partial** (was fail)
- `population.runs`: **1** (was 0)
- `cards[0].id`: **`card_claim_bc569a46eae827ec`** (was `card_golden_diversity_001`)
- Golden placeholders replaced on re-export when only `card_golden_*` existed

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_evidence_db_atlas_projection.py -q  # 3 passed
python -m pytest tests/golden -q                                      # 142 passed
python -m pytest -q                                                   # 748 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                     # pass
```

## Spec deviations

Golden card replacement on re-export when **only** `card_golden_*` rows exist — minimal
migration for existing evidence DBs without schema change.

## Recommended next ticket

**ticket-295** — Evidence DB run report + follow-up projection for atlas coherence GO

Wire `generate-run-report` on evidence DB spine so `reports[]` populate and coherence
`reports_and_hypotheses_frontend_ready` can reach pass.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `0324d41`
