# Phase 4 Packet 6: ingest-webpage CLI Pipeline

Date: 2026-06-19
Branch: `phase-4/packets-002-004-evidence-quality-extraction`
Decision: **GO**

## Delivered

- `ingest-webpage` CLI command wiring `web_source_adapter` → chunk ingest → quote-first `extract-claims`
- Pipeline helpers in `rge/modules/web_source_adapter.py`:
  - `ingest_webpage_artifact_to_db()` — blocks `dirty_text`, persists clean text as `source_type=webpage`
  - `extract_webpage_claims_to_db()` — quote-first extraction with `WEBPAGE_EVIDENCE_BASIS`
  - `run_ingest_webpage_pipeline()` — orchestrated ingest + optional extract
  - `load_webpage_artifact_from_path()` — staged JSON artifact loader
- Source `domain_metadata_json` stores `url`, `acquisition_status`, `quality_metrics`, `parser_backend`
- `--no-extract` flag for ingest-only runs; `--artifact` for pre-staged JSON
- Tests:
  - `tests/unit/test_ingest_webpage_cli.py`
  - `tests/unit/test_web_source_adapter.py` (pipeline coverage)
  - `tests/golden/test_32_ingest_webpage.py`
- Golden gate inventory updated (`test_00_scaffold`, `test_22_builder_golden_gate`)
- Ticket `ticket-373` done

## Safety boundary

- No live network in default tests or CLI path (local `--html` / `--artifact` only)
- Scrapling integration deferred; `html_to_text` normalization boundary unchanged
- No public export or allowlist changes

## Verification

**Result (2026-06-19):** `verify --skip-site` **PASS** — 159 golden, 960 pytest, safety audit full.

## Next slice

Packet 7: surface parser metrics on cluster reports; GROBID fixture proof.
