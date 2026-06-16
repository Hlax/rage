---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-295
category: Phase 3 / Research Atlas / live-derived population
---

# Pre-Ticket Audit: ticket-295 Evidence DB Run Report Projection

## Verdict: **GO** (operator-private DB-only run report; mock-only pytest)

Populates `run_reports[]` for evidence DB atlas export so coherence `reports_and_hypotheses_frontend_ready` can pass without golden contract pollution.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | DB-only `run_reports` insert; no `export-public` change |
| Public site | **No** | |
| Schema migrations | **No** | |
| Theory / inference | **No** | Informational run report metrics only |
| Live Ollama | **No** | Mock-only tests |

## Hardened scope

### In scope

1. **`ensure_evidence_run_report(conn, topic, domain_pack)`** in `evidence_db_atlas.py`:
   - Requires non-fixture manual claims + evidence run lineage (ticket-294)
   - Uses `build_run_report` + `RunReportRepository.insert` with evidence contract/run ids
   - **No** `ensure_golden_contract`; **no** disk write under `data/reports/` during atlas export
   - Idempotent on re-run
2. **Hook** in `build_atlas_snapshot_from_db` after claim-backed card seeding (non-fixture only)
3. **`tests/unit/test_evidence_db_run_report_projection.py`**: mock evidence spine → atlas export → `reports[]>=1`, coherence reports verdict pass

### Out of scope

- Public atlas UI, live default pytest, schema migration
- Full follow-up question generation beyond existing queue row from ticket-294
- Changing `generate-run-report` CLI golden contract behavior

## Safety

- Run report JSON is aggregated metrics only — no raw source text or prompts
- Evidence contract isolated from `GOLDEN_CONTRACT_ID`
- Atlas export remains operator-private

## Recommendation

**GO** — implement minimal DB-only run report hook for evidence atlas coherence.
