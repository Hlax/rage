---
template_id: pre_ticket_audit
status: GO
date: 2026-06-18
risk_level: medium
ticket: ticket-317
category: Phase 3 / Research Atlas / projection
---

# Pre-Ticket Audit: ticket-317 Staged Spine Atlas Cluster Projection Hook

## Verdict: **GO** (DB-only cluster projection hook; mock-only pytest)

Mirrors ticket-296 evidence DB cluster hook for staged orchestrator DBs so
`export-atlas-snapshot` populates `clusters[]` and ticket-316 partial coherence
(empty clusters warn) upgrades to **pass**.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | `cluster_reports` insert only; no `export-public` |
| Public site | **No** | |
| Schema migrations | **No** | Uses existing `cluster_reports` table |
| Theory / inference | **No** | Informational cluster summary only |
| Live Ollama | **No** | Mock staged spine tests only |

## Hardened scope

### In scope

1. **`db_has_staged_spine_runs(conn)`** — detect `research_runs.id` prefixed `run_staged_fixture_mode_spine`
2. **`ensure_staged_cluster_summaries(conn, topic, domain_pack)`** in `evidence_db_atlas.py`:
   - Per rank run (`_rank1`, `_rank2`): map to staged source via title fragment (orchestrator contract)
   - Derive included concepts from claim–concept links on run-scoped claims
   - Reference active relationships linked via `relationship_evidence` for those claims
   - Insert idempotent `cluster_reports` rows via `ClusterReportRepository`
3. **Hook** in `build_atlas_snapshot_from_db` when staged runs present (non-fixture export); runs **in addition to** evidence DB hooks when both coexist
4. **`tests/unit/test_staged_spine_cluster_projection.py`**: mock staged orchestrator → export → `clusters[]>=1`, overall coherence **pass**
5. **Regression:** `test_evidence_db_cluster_projection.py` unchanged behavior

### Out of scope

- Public site/export, README-only docs, schema migration, live_network CI
- Golden cluster threshold padding
- Full LLM `cluster_reporter.generate_cluster_report` path

## Safety

- Cluster summaries use claim/concept/relationship ids and labels only
- Staged hook isolated from golden MVP cluster padding
- Atlas export remains operator-private

## Recommendation

**GO** — minimal staged cluster projection hook to close ticket-316 coherence gap.
