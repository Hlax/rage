# Phase 4 Packet 8: Asset Export Candidates + Human Review Gate

Date: 2026-06-19
Branch: `phase-4/packets-002-004-evidence-quality-extraction`
Decision: **GO**

## Delivered

- Tightened `qa_eval_candidate` promotion: **only** when `evidence_maturity == "clustered"` (`promising` no longer exports)
- Human-review gate fields on derived candidates:
  - `human_review_required` (true for `qa_eval_candidate` at clustered maturity)
  - `review_status` (`pending` | `not_applicable`)
- Category writers in export bundle:
  - `candidates_by_category`
  - `qa_eval_candidates`
  - `human_review_required_count` / `qa_eval_candidate_count`
- `rubric_candidate` when `rubric_candidate` tag + clustered maturity
- Tests expanded in `tests/unit/test_asset_export_candidates.py`
- Golden `tests/golden/test_34_asset_export_candidates.py`
- Ticket `ticket-375` done

## Safety boundary

- Operator-private `export-asset-candidates` only; no `export-public` allowlist changes
- Summaries truncated; no raw quotes in candidate records

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_asset_export_candidates.py tests/golden/test_34_asset_export_candidates.py -q
python -m rge.cli verify --skip-site
```

**Result (2026-06-19):** `verify --skip-site` **PASS** — 161 golden, 970 pytest, safety audit full.

## Next slice

Packet 9: seed improvement tickets from `acquisition_quality_summary` + quality gate blocks.
