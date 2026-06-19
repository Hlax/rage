# MVP-P2/P4/P3 Research Loop — Evidence Report

**Date:** 2026-06-19  
**Branch:** `phase/mvp-p2-p4-p3-research-loop`  
**Packets:** MVP-P2 abstract evidence, MVP-P4 failure recommender, MVP-P3 field map  
**Status:** implemented (mock/fixture proven)

## Summary

Extended the P1 source resolver into a working mock research loop:

```text
resolve sources (P1)
-> abstract quote-first evidence cards (P2)
-> field-map synthesis (P3)
-> failure-classified improvement packet recommendation (P4)
```

## MVP-P2 — Abstract-first evidence cards

| Deliverable | Location |
|-------------|----------|
| Abstract chunk builder + quote-first extraction | `rge/modules/abstract_evidence.py` |
| Mock fixtures | `fixtures/llm_outputs/abstract_quote_first_*.json` |
| CLI | `generate-abstract-evidence --fixture-mode` |

Behavior:
- Uses existing `extract_and_validate_for_chunk` + claim validator (no validator rule changes)
- Labels all accepted claims `evidence_basis: abstract_only`
- Skips `metadata_only` sources without calling LLM
- Recommends full-text fetch when abstract extraction yields zero accepts but OA PDF exists

## MVP-P4 — Self-improvement recommender

| Deliverable | Location |
|-------------|----------|
| Dominant bottleneck classifier | `rge/modules/failure_recommender.py` |
| CLI | `recommend-improvement-packet --fixture-mode` |

Maps signals to MVP packets (e.g. `unsupported_claim_wall` → P6 PDF parser, `metadata_only` → P1 resolver, `weak_synthesis` → P3 field map).

## MVP-P3 — Field map report

| Deliverable | Location |
|-------------|----------|
| Metadata clustering + ranking + synthesis | `rge/modules/field_map.py` |
| CLI | `generate-field-map --fixture-mode --query "..."` |

Behavior:
- Pulls resolver fixture records
- Token-heuristic clusters (deterministic)
- Ranks top sources via existing `compute_discovered_relevance_score`
- Extracts abstract evidence for top-N
- Emits field report with metadata vs quote-grounded distinction + improvement recommendation

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_abstract_evidence.py tests/unit/test_failure_recommender.py tests/unit/test_field_map.py tests/golden/test_28_mvp_research_loop.py -q
# 20 passed

python -m pytest tests/unit/test_source_resolver.py tests/golden/test_27_source_resolver.py tests/golden/test_22_builder_golden_gate.py -q
# 45 passed combined MVP suite
```

## Example fixture chain

```powershell
python -m rge.cli generate-field-map --fixture-mode --query "AI creativity diversity"
python -m rge.cli generate-abstract-evidence --fixture-mode
python -m rge.cli recommend-improvement-packet --fixture-mode
```

## Remaining gaps

- No DB persistence for evidence cards or field-map reports (JSON CLI/output files only)
- Not wired into staged ingest / orchestrator spine
- Clustering is token-heuristic, not embedding-based
- Live network field-map runs not operator-proven in this session
- Concept linking not invoked on abstract claims (deferred to spine integration)

## Next recommended packet

**MVP-P5 — Selective full-text acquisition** for top-ranked sources when abstract evidence is thin.
