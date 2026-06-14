---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-149
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-149 Generate Run Report on Staged-Ingested Source

## Verdict: **GO**

`generate-run-report` is **deterministic** (no LLM). ticket-148 already leaves a DB state with
discovered candidates, ingested sources, claims, relationships, qualifications, and score events.
ticket-149 may add a **unit test only** extending the ticket-148 spine through
`generate-run-report` — no new mock LLM fixture required.

**Note:** ticket JSON cites `run_report_generator.py`; the implemented module is
`rge/modules/run_evaluator.py` (`generate_run_report`, `build_run_report`).

## 1. Tables / repositories

| Layer | Table | Repository |
|-------|-------|------------|
| Run metadata | `research_runs` | `ResearchRunRepository` |
| Run report | `run_reports` | `RunReportRepository` |
| Aggregated inputs | `candidate_sources`, `sources`, `claims`, `relationships`, `score_events` | read via SQL in `aggregate_run_metrics()` |

## 2. Existing command / module

- CLI: `python -m rge.cli generate-run-report --run-id <id> --topic <text> --domain creativity [--db] [--output-dir]`
- Module: `rge/modules/run_evaluator.py` — `generate_run_report()` → `build_run_report()` + persist

No `--fixture` flag; reporting aggregates current DB counters and rejection histograms.

## 3. Existing fixture / golden pattern

Golden Test 19 (`tests/golden/test_19_run_report.py`):

1. Build a multi-source spine (ingest → extract → link → build → reconcile → detect …)
2. `generate-run-report` with explicit `run_id`, `topic`, `--output-dir`
3. Assert `run_reports` row, `run_report_latest.json`, required counters, and `top_failure_modes`

Staged spine should mirror this pattern with Phase 3 discover/fetch/ingest steps upstream.

## 4. How ticket-148 leaves the DB

After `test_staged_ingest_reconcile_spine.py` spine (domain seed + staged discover → fetch →
ingest-staged → extract → link → build → detect → reconcile):

| Metric | Expected minimum |
|--------|------------------|
| `candidate_sources` | 2 (OpenAlex fixture discover) |
| `sources` ingested | 2 (domain base + staged) |
| `claims` accepted | 3 (2 base + 1 staged co-creativity) |
| `claims` rejected | 1 (staged missing_quote_span) |
| `relationships` active | 2 (base may_reduce + staged may_increase) |
| `score_events` | 1 (staged reconcile 0.5 → 0.62) |
| `relationship_evidence` qualifies | 1 (ticket-147) |

## 5. Minimal implementation for staged run report

**No LLM fixture.** Optional staged run constants in test only:

```text
STAGED_RUN_ID = "run_staged_phase3_spine"
STAGED_TOPIC = "Human-AI co-creativity and semantic diversity (staged Phase 3 spine)"
```

After ticket-148 helper completes:

```text
generate-run-report --run-id run_staged_phase3_spine --topic "..." --domain creativity --db <temp> --output-dir <temp/reports>
```

Assert report JSON counters meet staged minimums and `missing_quote_span` appears in
`top_failure_modes`.

## 6. Test proof

New `tests/unit/test_staged_ingest_run_report_spine.py`:

1. Reuse ticket-148 `_run_spine_through_detect_contradictions` + `reconcile-scores` (extract helper or shared module optional; copy acceptable for ticket isolation)
2. `generate-run-report` with staged run id/topic
3. Assert:
   - `report_type == "run_report"`
   - `sources_discovered >= 2`
   - `sources_ingested >= 2`
   - `claims_accepted >= 3`, `claims_rejected >= 1`
   - `relationships_updated >= 2`
   - `score_events_created >= 1`
   - `missing_quote_span` in `top_failure_modes`
   - `run_reports` row + `run_report_latest.json` on disk
4. Idempotency re-run (`already_generated`) optional second test

## 7. Mock / golden determinism

- `RGE_LLM_MODE=mock` autouse (same as prior staged spine tests)
- `generate-run-report` does not call the model client
- Golden GT19 unchanged; no new golden test required at ticket scope

## 8. Out of scope (ticket non_goals)

- Live Ollama, public export/site, schema migrations
- Full `research run --fixture-mode` automation
- Improvement ticket generation (`generate-improvement-tickets`)
- Broad `run_evaluator` refactor

## 9. Expected file changes

| File | Change |
|------|--------|
| `tests/unit/test_staged_ingest_run_report_spine.py` | new e2e spine through generate-run-report |
| `agent_reports/2026-06-14_ticket-149_staged-run-report-spine.md` | implementation report (post-impl) |

**Likely no production code changes** unless audit finds a counter gap during implementation
(e.g. `sources_discovered` not populated — verified: discover-sources writes `candidate_sources`).

Optional doc fix: ticket-149 JSON `affected_modules` should reference `run_evaluator.py` not
`run_report_generator.py` (cosmetic; do not broaden ticket scope to rename modules).

## 10. Rollback plan

Delete `test_staged_ingest_run_report_spine.py`. ticket-148 reconcile spine unchanged.

## Hardened scope

### In

1. Unit test extending ticket-148 spine through `generate-run-report`
2. Staged run id/topic constants in test
3. Counter + failure-mode assertions listed above

### Out

- New fixtures under `fixtures/llm_outputs/` (not needed)
- `run_evaluator.py` changes unless counter bug found
- Public export, site, schema, improvement tickets

## Risk assessment

| Risk | Mitigation |
|------|------------|
| Counter under-count staged discover | Assert `sources_discovered >= 2` from existing discover enqueue |
| Non-deterministic `created_at` | Do not assert timestamp equality; structure-only checks |
| Scope creep into full fixture-mode run | Test calls `generate-run-report` only after manual spine steps |

## Recommendation

**GO** — implement ticket-149 as a **test-forward** ticket (mirrors ticket-148 reconcile pattern).
After done, seed ticket-150 for staged spine completion checkpoint or operator documentation only if
product-risk requires; do **not** jump to public export or full `research run` automation.

Suggested next after ticket-149: principal audit checkpoint (cadence overdue since ticket-137) before
further Phase 3 tickets.
