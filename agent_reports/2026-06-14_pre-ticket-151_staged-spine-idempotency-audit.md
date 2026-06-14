---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-151
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-151 Staged Phase 3 Full Spine Idempotency

## Verdict: **GO**

Each staged spine command already exposes idempotent short-circuit statuses
(`already_queued`, `already_fetched`, `already_extracted`, `already_linked`,
`already_built`, `already_detected`, `already_reconciled`, `already_generated`).
ticket-151 may add **unit tests only** proving stable row counts when the full
discover→report spine or individual commands re-run on the same DB.

## 1. Idempotent command surfaces

| Step | Module | Re-run status |
|------|--------|---------------|
| discover + enqueue | `research_queue.enqueue_discovered_candidates` | `already_queued` |
| fetch-candidate | `fetcher.fetch_staged_candidate_artifact` | `already_fetched` |
| ingest-staged | `ingest_local_source` (checksum) | stable source row |
| extract-claims | `claim_extractor` | `already_extracted` |
| link-concepts | `concept_linker` | `already_linked` |
| build-relationships | `relationship_builder` | `already_built` |
| detect-contradictions | `contradiction_detector` | `already_detected` |
| reconcile-scores | `score_reconciler` | `already_reconciled` |
| generate-run-report | `run_evaluator` | `already_generated` |

## 2. Reference pattern

`tests/unit/test_manual_source_pipeline_idempotency.py` (tickets 093, 106):

- Full spine twice → identical `_PipelineCounts`
- Per-command reruns after baseline → counts unchanged

Mirror with staged helpers from `test_staged_ingest_run_report_spine.py`.

## 3. Expected stable counts (after first full spine)

| Metric | Expected |
|--------|----------|
| `sources` | 2 (domain base + staged) |
| `candidate_sources` | 2 (OpenAlex fixture) |
| `research_queue` | 2 queued items |
| staged accepted claims | 1 |
| staged rejected claims | 1 |
| staged concept links | 3 |
| staged relationships (distinct, staged claim evidence) | 2 |
| `score_events` | 1 |
| `run_reports` | 1 |
| qualifies evidence | 1 |

## 4. Minimal implementation

One new file: `tests/unit/test_staged_ingest_idempotency.py`

- `_run_full_spine()` — discover through `generate-run-report` (mock network)
- `_spine_counts(db, staged_source_id)` — dataclass for assertions
- `test_staged_phase3_full_spine_twice_is_idempotent`
- `test_staged_phase3_per_command_reruns_are_idempotent`

No production code changes unless a test exposes a genuine idempotency bug
(out of scope to fix in this ticket unless trivial).

## 5. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_ingest_idempotency.py -q
python -m pytest tests/unit/test_staged_ingest_*_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## 6. Out of scope

- Second candidate fetch (ticket-152)
- Live network / Ollama
- Schema migrations, public export/site

## Audit gate

Principal cadence satisfied by ticket-150 / post-ticket-149 principal audit.
Pre-ticket audit for ticket-151: **GO**.
