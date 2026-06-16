---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-296
category: Phase 3 / Research Atlas / live-derived population
---

# Pre-Ticket Audit: ticket-296 Evidence DB Cluster Summary Projection

## Verdict: **GO** (operator-private DB-only cluster summary; mock-only pytest)

Populates `clusters[]` for evidence DB atlas export so coherence `missing_fields_create_refactor_risk` clears the empty-clusters warn and overall verdict can reach **pass** on the mock evidence spine.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | DB-only `cluster_reports` insert; no `export-public` change |
| Public site | **No** | |
| Schema migrations | **No** | Uses existing `cluster_reports` table |
| Theory / inference | **No** | Informational cluster summary only; no theory_candidates |
| Live Ollama | **No** | Mock-only tests; reuse ticket-294 spine stubs |

## Hardened scope

### In scope

1. **`ensure_evidence_cluster_summary(conn, topic, domain_pack)`** in `evidence_db_atlas.py`:
   - Requires non-fixture manual claims + evidence run lineage (ticket-294)
   - Derives included concepts from claim–concept links on evidence claims
   - References active `relationships` rows when present (may be zero on extract+link-only spine)
   - Inserts minimal `cluster_reports` row via `ClusterReportRepository` with evidence `run_id`
   - **No** golden threshold padding; **no** `ensure_golden_cluster_thresholds`; **no** disk write under `data/reports/` during atlas export
   - Idempotent on re-run (skip when run-scoped cluster row exists)
2. **Hook** in `build_atlas_snapshot_from_db` after `ensure_evidence_run_report` (non-fixture only)
3. **`tests/unit/test_evidence_db_cluster_projection.py`**: mock evidence spine → atlas export → `clusters[]>=1`, overall coherence **pass** (or explicit blocker note in report)

### Out of scope

- Public atlas UI, live default pytest, schema migration
- Full LLM cluster report generation (`cluster_reporter.generate_cluster_report` golden path)
- Changing golden MVP cluster threshold behavior

## Safety

- Cluster summary uses claim/concept/relationship ids and labels only — no raw source text or prompts
- Evidence contract isolated from `GOLDEN_CLUSTER_LABEL` / golden padding
- Atlas export remains operator-private

## Recommendation

**GO** — implement minimal DB-only cluster summary hook for evidence atlas overall coherence pass.
