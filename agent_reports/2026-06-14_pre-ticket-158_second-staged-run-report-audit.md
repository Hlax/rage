---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-158
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-158 Generate Run Report on Second Staged Source

## Verdict: **GO**

`generate-run-report` is deterministic (no LLM). ticket-157 leaves rank #2 DB state with
discovered candidates, ingested sources, claims, relationships, qualifications, and score events.
ticket-158 may add a **unit test only** extending the ticket-157 spine through
`generate-run-report` — no new mock LLM fixture required.

**Note:** ticket JSON cites `run_report_generator.py`; the implemented module is
`rge/modules/run_evaluator.py`.

## 1. Upstream state (ticket-157)

After domain seed + rank #2 discover → fetch → ingest-staged → extract → link → build → detect → reconcile:

| Metric | Expected minimum |
|--------|------------------|
| `candidate_sources` | 2 (OpenAlex fixture discover) |
| `sources` ingested | 2 (domain base + rank #2 staged) |
| `claims` accepted | 3 (2 base + 1 rank #2 constraint claim) |
| `claims` rejected | 1 (rank #2 `missing_quote_span`) |
| `relationships` active | 2 (base may_reduce + constraint may_increase human control) |
| `score_events` | 1 (rank #2 reconcile 0.5 → 0.62) |
| `relationship_evidence` qualifies | 1 (ticket-156) |

## 2. Test design

File: `tests/unit/test_staged_second_candidate_run_report_spine.py`

Run constants:

```text
SECOND_STAGED_RUN_ID = "run_second_staged_phase3_spine"
SECOND_STAGED_TOPIC = "Constraint management in AI-assisted creative teams (rank #2 staged spine)"
```

1. Reuse ticket-157 spine through reconcile-scores (explicit fixtures)
2. `generate-run-report --run-id … --topic … --domain creativity --output-dir …`
3. Assert report counters + `missing_quote_span` in `top_failure_modes`
4. Idempotency + CLI JSON tests (mirror ticket-149)

## 3. Out of scope

Live LLM, public export/site, schema, full `research run` automation, improvement tickets.

## 4. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_run_report_spine.py -q
python -m pytest tests/unit/test_staged_second_candidate_reconcile_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-158 | **GO** (test-forward) |
| Next | ticket-159 — principal audit checkpoint post-ticket-158 (rank #2 spine completion) |
