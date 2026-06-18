# Agent Report: ticket-319 — Staged spine cluster projection test isolation hardening

**Date:** 2026-06-18  
**Ticket:** ticket-319  
**Branch:** `phase-3/ticket-319-staged-spine-cluster-test-isolation`  
**Main tip before branch:** `8e18bce`  
**Audit gate:** Not required (`risk_level: low`; principal audit post-ticket-317 at `agent_reports/2026-06-18_principal-audit-post-ticket-317.md`).

## Summary

Eliminated intermittent full-suite failure in `test_staged_spine_cluster_projection` when
`test_evidence_db_cluster_projection` ran first. Root cause was not patch leakage alone: staged
atlas exports called `ensure_evidence_research_run_lineage` on every non-fixture DB (including
staged-only), and `_primary_contract_id` tie-broke on `started_at`/id so follow-up projection
sometimes targeted `contract_golden_test_10` with no question rows → `overall_coherence_verdict:
partial`. Fix: guard evidence lineage to manual-evidence DBs, seed staged follow-up on the golden
contract, and stop leaked mock patches in evidence live-spine tests.

## Scope

**In:** `ensure_staged_atlas_follow_up_question`, atlas builder hooks, evidence test patch cleanup,
staged cluster unit test, queue/report.

**Out:** Public site, README-only docs, schema migrations, live_network CI.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/evidence_db_atlas.py` | `ensure_staged_atlas_follow_up_question` |
| `rge/modules/atlas_snapshot_builder.py` | Guard evidence lineage; staged follow-up hook |
| `tests/unit/test_staged_spine_cluster_projection.py` | Follow-up seed unit test |
| `tests/unit/test_evidence_db_atlas_projection.py` | `patch.stopall()` after mock live spine |
| `tickets/ticket-319.json` | Status `done` |
| `tickets/ticket-320.json` | Seeded public atlas preview refresh |
| `tickets/TICKET_QUEUE.md` | Queue update |
| `agent_reports/2026-06-18_phase-3_ticket-319_staged-spine-cluster-test-isolation.md` | This report |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Staged cluster tests pass after evidence cluster tests in same session | **PASS** — 10/10 combo runs |
| Minimal production hook only where required | **PASS** |
| Golden + full pytest | **PASS** — 148 golden, 793 pytest |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_evidence_db_cluster_projection.py tests/unit/test_staged_spine_cluster_projection.py -q
# 7 passed (10 consecutive combo runs: 7/7 each)

python -m pytest tests/golden -q   # 148 passed
python -m pytest -q                # 793 passed, 33 deselected
```

Safety audit not required — test hygiene and private atlas projection hooks only; no public export.

## Spec deviations

- Ticket JSON listed tests-only `affected_modules`; added minimal `evidence_db_atlas.py` and
  `atlas_snapshot_builder.py` hooks after root-cause analysis (documented in principal audit
  advisory).

## Recommended next ticket

**ticket-320** — Public atlas preview fixture refresh from staged spine export (product-facing proof).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

_Placeholder — updated after merge._
