# MVP Research Spine Integration — Evidence Report

**Date:** 2026-06-19  
**Branch:** `phase/mvp-research-spine-integration`  
**Scope:** Live selective fetch gate, DB ingest + claims extraction, parser tiers, full-text evidence

## Summary

Integrated the P5–P7 research demo loop with the DB spine:

1. **Live network selective fetch (operator opt-in)** — `RGE_ALLOW_LIVE_SELECTIVE_FETCH=1` plus existing `RGE_ALLOW_SOURCE_NETWORK=1` and `OPENALEX_MAILTO`; gated via `research_network.live_selective_fetch_enabled()`.
2. **DB ingest / research-run wiring** — `research-run --db --persist-claims [--staging-dir]` ingests clean selective full-text acquisitions and runs mock `extract-claims` into the claims table.
3. **Parser tiers** — TEI/XML → optional GROBID (`RGE_GROBID_URL`) → PyMuPDF → pypdf; never raw PDF UTF-8 decode.
4. **Full-text quote extraction** — `fulltext_evidence.py` cards + `research_spine.extract_fulltext_claims_to_db()` using fixture `fulltext_quote_first_openalex.json`.

**Note:** Phase 3 staged orchestrator (`execute_staged_fixture_mode_run` discover→fetch-candidate→ingest-staged) remains a separate path. This integration wires the **MVP research-run** resolver/selective-fulltext path to the same `ingest_local_source` + `extract_claims_for_source` primitives. Bridging staged orchestrator to selective full-text is a follow-up ticket.

## Key files

| Area | Path |
|------|------|
| Network gate | `rge/modules/research_network.py` |
| Config | `rge/config.py` (`allow_live_selective_fetch`, `grobid_url`) |
| Parser tiers | `rge/modules/document_parser.py` |
| Selective fetch | `rge/modules/selective_fulltext.py` |
| DB wiring | `rge/modules/research_spine.py` |
| Demo loop | `rge/modules/research_run.py` |
| Full-text evidence | `rge/modules/fulltext_evidence.py` |
| CLI | `rge/cli.py` (`research-run --db --persist-claims --staging-dir`) |

## Bug fixes during integration

- `_cmd_research_run`: undefined `db_path` / `staging_dir` — resolved paths added.
- `wire_selective_fulltext_to_db`: ingest status `"ingested"` was skipped for extract; now accepted alongside `"completed"` / `"already_ingested"`.
- Claim count aggregation: uses `accepted_claim_ids` from `extract_claims_for_source`.
- Tests: staging dir must be sibling of sqlite file, not child of file path.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_research_spine.py tests/unit/test_fulltext_evidence.py tests/golden/test_30_research_spine_db.py -q
# 5 passed

python -m rge.cli verify --skip-site
# PASS: 157 golden, 925 pytest, safety audit
```

## Operator commands

**Fixture DB persist:**

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli research-run --fixture-mode --mode full-text-augmented `
  --full-text-top-n 2 --db data/db/research_spine_scratch.sqlite --persist-claims
```

**Live selective fetch (operator opt-in; not CI):**

```powershell
$env:RGE_ALLOW_LIVE_SELECTIVE_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_selective_fulltext_validation.py -m live_network -q
```

**Optional GROBID:**

```powershell
$env:RGE_GROBID_URL = "http://127.0.0.1:8070"
```

## Env vars (`.env.example` updated)

- `RGE_ALLOW_LIVE_SELECTIVE_FETCH` — default off; requires source network.
- `RGE_GROBID_URL` — optional local GROBID service.

## Verdict

**GO** — mock verification green; DB persist path proven; live selective fetch gated and test-covered (`live_network` marker).

## Recommended next ticket

Wire selective full-text acquisition into staged orchestrator post-ingest (or document as operator-only parallel path) and run one-time live selective fetch operator proof on temp DB.
