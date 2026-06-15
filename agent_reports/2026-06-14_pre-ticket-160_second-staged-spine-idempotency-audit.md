---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-160
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-160 Second Staged Candidate Full Spine Idempotency

## Verdict: **GO**

Rank #2 spine commands expose the same idempotent short-circuit statuses as rank #1
(`already_queued`, `already_fetched`, `already_extracted`, `already_linked`,
`already_built`, `already_detected`, `already_reconciled`, `already_generated`).
ticket-160 may add **unit tests only** mirroring ticket-151 with explicit rank #2
`--fixture` bindings.

## 1. Reference pattern

- `tests/unit/test_staged_ingest_idempotency.py` (ticket-151, rank #1)
- `tests/unit/test_staged_second_candidate_run_report_spine.py` (ticket-158 helpers)

## 2. Expected stable counts (rank #2 after first full spine)

| Metric | Expected |
|--------|----------|
| `sources` | 2 (domain base + rank #2 staged) |
| `candidate_sources` | 2 |
| `research_queue` | 2 |
| staged accepted claims | 1 |
| staged rejected claims | 1 |
| staged concept links | 3 |
| staged relationships (distinct, staged claim evidence) | 2 (build supports + detect qualifies on base edge) |
| `score_events` | 1 |
| `run_reports` | 1 |
| qualifies evidence | 1 |

## 3. Fixture constants

Explicit `--fixture` on extract, link, build, detect (no auto-routing for rank #2 title).

## 4. Out of scope

Dual-candidate combined DB, live network, schema, public export/site.

## 5. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_idempotency.py -q
python -m pytest tests/unit/test_staged_second_candidate_run_report_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-160 | **GO** |
| Next | ticket-161 — dual-candidate staged idempotency (optional) or live fetch opt-in hardening |
