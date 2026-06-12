---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-021 Audit: Research Run Report Readiness

- Audit type: pre-implementation readiness audit (no ticket-021 code changes)
- Date: 2026-06-12
- Agent/model: Cursor builder agent (Auto)
- Scope: Git/main state after ticket-020, spine through domain proposal, schema/repository/module support for Golden Test 19, ticket-021 scope hardening, safety boundaries

## 1. Summary

The repo is **ready for ticket-021 (research run report / Golden Test 19)** with hardening folded into the ticket. Main is aligned with `origin/main` at `442def2b0b6964a7f0309387c86218332ef0173f`. All **85** golden tests pass without Ollama. Ticket **020** is merged, pushed, and consistently marked `done`. The intelligence spine through `generate-domain-proposal` is implemented and verified by Golden Tests 15–18. **`run_evaluator.py` is a Phase 0 stub**; **`RunReportRepository` / `ResearchRunRepository` and Golden Test 19 are absent** — expected pre-implementation state.

**Important naming correction:** ticket-021 JSON lists `run_reporter.py`, but the repo's canonical stub module is **`run_evaluator.py`** (`evaluate_run`). Ticket-021 should implement in `run_evaluator.py`, not introduce a duplicate module.

**Contract decisions for ticket-021:**

1. **No new migration** — `research_runs` and `run_reports` already exist in `0001_initial.sql` per `05_DATA_MODEL.md` §4.16–4.17.
2. Add `RunReportRepository` and `ResearchRunRepository` (or equivalent helpers) in `repositories.py`.
3. Implement deterministic run report aggregation in **`run_evaluator.py`** (not a new `run_reporter.py`).
4. CLI: `generate-run-report` with `--run-id`, `--topic`, `--domain`, `--db`, optional `--output-dir`, optional `--contract`.
5. Golden Test 19 runs a fixture spine (ingest → extract with rejections → link → relationships → score events → export-public optional count only), then generates a machine-readable run report with required counters and `top_failure_modes`.
6. Persist to `run_reports`; write `run_report_latest.json` under report dir.
7. Do **not** implement full `research run` LangGraph orchestration or live Ollama in this ticket.
8. No public export/site changes; run reports remain internal.

**Recommendation: proceed with ticket-021 as the next smallest safe ticket** — after this audit report is committed to `main`.

## 2. Git / Main Status

| Check | Result |
|---|---|
| Current branch | `main` |
| Working tree | **dirty (local artifacts only)** — modified `apps/public-site/public/data/build_info.json`, `public_cards.json`; untracked `data/` from prior audit spine/export runs. **Not ticket-021 blockers.** |
| `main` vs `origin/main` | **aligned** — both at `442def2b0b6964a7f0309387c86218332ef0173f` |
| ticket-020 merged & pushed | **yes** — merge `68da510`, docs hash `442def2` |
| ticket-019 merged & pushed | **yes** (prior) |
| Unmerged ticket work on main | **none** |
| Dangling local branch | `phase-1/ticket-020-domain-proposal` merged — no drift |

## 3. Ticket / Report Consistency

| Ticket | Queue | JSON | Report | Pre-ticket audit | Consistent |
|---|---|---|---|---|---|
| ticket-020 | `done` | `done` | `agent_reports/2026-06-12_phase-1_ticket-020_domain-proposal.md` | `2026-06-12_pre-ticket-020_domain-proposal-readiness-audit.md` | **yes** |
| ticket-021 | `proposed` | `proposed` | — (not yet) | **this report** | **correct next ticket** |

**Next ticket:** ticket-021 is the lowest-order `proposed` ticket in `TICKET_QUEUE.md`.

**Risk / audit gate:** ticket-021 JSON `risk_level: medium`. Runner protocol requires pre-ticket audit for medium/high risk. Self-improvement / run observability milestones benefit from audit. **Gate unmet until this report is committed; satisfied once committed.**

## 4. Report Claims vs Repo Reality (ticket-020)

| Claimed | Exists |
|---|---|
| `rge/db/migrations/0007_domain_proposals.sql` | **yes** |
| `rge/modules/domain_proposer.py` (full impl) | **yes** |
| `rge/cli.py` → `generate-domain-proposal` | **yes** |
| `tests/golden/test_18_domain_proposal.py` | **yes** (4 tests) |
| `domain_proposals` in `schema.sql` | **yes** |
| Migration in `test_01_ingestion.py` | **yes** (`0007_domain_proposals`) |
| Merge hash `68da510` | **yes** on main |

### Mismatches (expected for ticket-021)

| Item | Notes |
|---|---|
| `run_reporter.py` in ticket JSON | **Does not exist** — use `run_evaluator.py` |
| `tests/golden/test_19_run_report.py` | **Absent** — ticket-021 scope |
| `RunReportRepository` | **Absent** — ticket-021 scope |
| `generate-run-report` CLI | **Absent** — ticket-021 scope |
| `research run` CLI | **Still Phase 0 stub** — out of scope for ticket-021 |

## 5. Tests / Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | **PASS** | **85 passed** |
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_18_domain_proposal.py` | **PASS** | **4 passed** |
| Ollama required | **NO** | Mock mode only |
| Public site build | **NOT RUN** | No site changes since ticket-015 |

## 6. Spine Verification

Golden Tests 13–18 exercise the deterministic intelligence spine through domain proposals:

```txt
ingest → extract-claims → link-concepts → build-relationships
→ detect-contradictions → reconcile-scores → generate-cluster-report
→ generate-theory-candidates → generate-followup-questions
→ generate-ontology-pressure → generate-domain-proposal
```

| Command | Registered | Golden coverage |
|---|---|---|
| Through `generate-domain-proposal` | yes | GT18 |
| `generate-run-report` | **no** | **GT19 not yet** |
| `research run` (orchestrator) | stub only | not implemented |

**Counter sources ticket-021 should aggregate:**

| Field | DB / module source |
|---|---|
| `sources_discovered` | `candidate_sources` count (or fixture-mode constant) |
| `sources_ingested` | `sources` where `status` ingested/parsed |
| `claims_extracted` | accepted + rejected claim counts |
| `claims_accepted` / `claims_rejected` | `claims.status` |
| `relationships_updated` | `relationships` updates or active count |
| `score_events_created` | `score_events` count |
| `cards_exported` | `public_cards` count or export-public result |
| `top_failure_modes` | `GROUP BY rejection_reason` on rejected claims |
| `tickets_generated` | `improvement_tickets` count (0 until GT20) |

Golden Test 19 minimum fields per `00_GOLDEN_TESTS.md` Test 19 and `05_DATA_MODEL.md` §4.17:

```json
{
  "run_id": "...",
  "topic": "...",
  "domain_pack": "...",
  "sources_discovered": 0,
  "sources_ingested": 0,
  "claims_extracted": 0,
  "claims_accepted": 0,
  "claims_rejected": 0,
  "relationships_updated": 0,
  "score_events_created": 0,
  "cards_exported": 0,
  "top_failure_modes": [],
  "tickets_generated": 0
}
```

Extended fields from `08_REPORTING_SPEC.md` §6 (optional but useful): `report_type`, `contract_id`, `cluster_reports_created`, `theory_candidates_created`, `safety_audit_status`.

**GT19 failure conditions to guard against:**

- No report created
- Report only exists as prose (must be JSON in `run_reports.report_json`)
- Failure modes not machine-readable (must be `[{"reason": "...", "count": N}]`)
- Report not queryable (must persist with stable `run_id`)

## 7. Run-Evaluator Readiness

### Current state

| Component | Status |
|---|---|
| `rge/modules/run_evaluator.py` | **Phase 0 stub** — `evaluate_run()` raises `NotImplementedError` |
| `rge/modules/run_reporter.py` | **does not exist** |
| `research_runs` table | **present** in `0001_initial.sql` |
| `run_reports` table | **present** in `0001_initial.sql` |
| `RunReportRepository` | **absent** |
| `ResearchRunRepository` | **absent** |
| `generate-run-report` CLI | **absent** |
| `tests/golden/test_19_run_report.py` | **absent** |
| `run_reports` in `test_00_scaffold.py` EXPECTED_SCHEMA_TABLES | **yes** (table listed) |
| `ticket_writer.py` | **stub** — GT20 scope, not ticket-021 |

### What ticket-021 must add

1. **`RunReportRepository`** — insert/get/count/idempotent re-run by `run_id`.
2. **`ResearchRunRepository`** (minimal) — seed or fetch `research_runs` row for report linkage.
3. **`run_evaluator.py`** — aggregate counters from DB, build report JSON, persist, export file.
4. **CLI `generate-run-report`** — machine-readable JSON output.
5. **Golden Test 19** — `tests/golden/test_19_run_report.py` (~4 tests, consistent with GT15–18):
   - creates run report with required fields after fixture spine
   - `top_failure_modes` populated when rejections exist (use GT2 rejection fixtures)
   - idempotent re-run
   - CLI emits machine-readable JSON
6. **Scaffold updates** — `test_00_scaffold.py` CLI help scan for `generate-run-report`.

### What must remain internal

- Run reports in `run_reports` — not public export.
- Raw prompts, local paths, secrets excluded from `report_json`.
- `research run` orchestrator remains unimplemented (separate future ticket).

### What must not be exported publicly

- Run reports, node reports, failure mode details with private source text.
- Domain/theory/ontology draft artifacts (unchanged from prior tickets).

## 8. Safety Findings

| Boundary | Status |
|---|---|
| Public export exposes run reports | **NO** — `export-public` uses `public_cards` only |
| Public export exposes domain/theory/ontology drafts | **NO** |
| Domain proposals auto-activate | **NO** — GT18 guards |
| Theory candidates as facts | **NO** — GT15 guards |
| Public write routes | **NONE** |
| Run report JSON leaks paths/prompts | **N/A yet** — enforce in ticket-021 (no `local_path`, no prompt templates in report) |

## 9. Runner / Audit Gate

| Rule | Status |
|---|---|
| One ticket per invocation | **intact** |
| Medium/high risk → pre-ticket audit | **ticket-021 medium** — this audit satisfies |
| Schema migration milestone | **NO new migration expected** |
| Theory/inference/proposal milestone | **NO** — run reporting is observability, not synthesis |
| ticket-021 blocked until audit committed | **YES — commit this report before `/rge-run-next-ticket`** |

## 10. Blocking Issues

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| B1 | **gate** | No pre-ticket-021 audit on main | **Commit this report**, then run `/rge-run-next-ticket` |
| B2 | **info** | Local dirty public-site JSON + `data/` artifacts | Discard or gitignore; do not merge into ticket-021 |
| — | **naming** | Ticket JSON says `run_reporter.py` | Implement in **`run_evaluator.py`** per repo convention |

No failing tests, no main/origin drift, no ticket queue inconsistency for ticket-020.

## 11. Recommended Next Action

1. **Commit** `agent_reports/2026-06-12_pre-ticket-021_run-report-readiness-audit.md` to `main`.
2. Run **`/rge-run-next-ticket`** to implement ticket-021 on branch `phase-1/ticket-021-run-report`.

## 12. Hardened Ticket-021 Scope

Implement exactly:

- [ ] Full `run_evaluator.py` (aggregate counters, failure modes, persist, idempotent re-run)
- [ ] `RunReportRepository` + `ResearchRunRepository` (or minimal run seed helper) in `repositories.py`
- [ ] CLI `generate-run-report`
- [ ] `tests/golden/test_19_run_report.py` (4 tests)
- [ ] Update `test_00_scaffold.py` CLI help scan
- [ ] Fixture spine in GT19 including rejected claims for `top_failure_modes`
- [ ] Persist `run_reports` row; write `run_report_latest.json`
- [ ] `report_type: run_report` in JSON envelope
- [ ] No new migration (tables exist)
- [ ] No Ollama, LangGraph, live web discovery, public export/site, or full `research run` orchestrator

**Non-goals (reconfirm):** Ollama, LangGraph, live web discovery, public write routes, public export changes, ticket generation (GT20), LangGraph node reports.

---

**Recommendation: proceed with ticket-021 as the next smallest safe ticket** (after committing this audit report).
