# Phase 4 Packet 7: Parser Metrics + GROBID Fixture Proof

Date: 2026-06-19
Branch: `phase-4/packets-002-004-evidence-quality-extraction`
Decision: **GO**

## Delivered

- `rge/modules/acquisition_quality.py` — shared acquisition/parser summary helpers
  - `acquisition_quality_summary()` — run-report scope (all sources)
  - `cluster_acquisition_quality_summary()` — cluster-scoped source ids + metrics
  - Counts `parser_backend` from both `parse.parser_backend` and top-level metadata (webpage ingest)
- `build_cluster_report()` embeds `acquisition_quality_summary` with `cluster_source_ids`
- `run_evaluator._acquisition_quality_summary()` refactored to shared module (adds `source_type_counts`)
- GROBID fixture proof:
  - `fixtures/source_documents/grobid_response_tei.xml`
  - Mocked `urllib.request.urlopen` tests proving `grobid_tei` backend path
- Tests:
  - `tests/unit/test_acquisition_quality.py`
  - `tests/unit/test_document_parser.py` (GROBID mock)
  - `tests/golden/test_33_grobid_fixture_parse.py`
  - `tests/golden/test_13_cluster_report.py` (cluster summary assertion)
- Golden gate inventory updated
- Ticket `ticket-374` done

## Deferred

- Live GROBID operator proof (network; opt-in only)
- Unified PDF evidence card export path

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_acquisition_quality.py tests/unit/test_document_parser.py tests/golden/test_13_cluster_report.py tests/golden/test_33_grobid_fixture_parse.py -q
python -m rge.cli verify --skip-site
```

**Result (2026-06-19):** `verify --skip-site` **PASS** — 160 golden, 965 pytest, safety audit full.

## Next slice

Packet 8: promote `qa_eval_candidate` only when `evidence_maturity=clustered` + human review flag.
