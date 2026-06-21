# Local Model Extraction Comparison

**Date:** 2026-06-20  
**Packet:** Local Model Extraction Comparison  
**Cycle:** Operator loop cycle 3 — after live source expansion  
**Verdict:** **GO**

## Live run summary (2026-06-20 — cycle 3)

| Signal | Result |
| --- | ---: |
| Ollama model | `qwen3.5:9b-q4_K_M` |
| Abstracts compared | 5 |
| Mock accepted | 5 (100% quote validity) |
| Ollama accepted | 2 (100% quote validity on accepted) |
| Quality vs mock | **thinner** (4 thinner, 1 better) |
| Ollama rejections | `overgeneralized_scope` (6), `unsupported_claim` (2) |

Evaluation-only — no DB writes.

## Verification

| Command | Status |
| --- | --- |
| Live run `--sync-public --limit 5` | **PASS** (GO) |
| `pytest tests/unit/test_local_model_extraction_comparison.py -q` | **PASS** (9 passed) |
| Safety audit | **PASS** |
| `npm run build` | **PASS** |

## Next recommended packet

**Graph Maturity / Evidence Atom Upgrade** (`graph-maturity-evidence-atom-upgrade`) — expect **PARTIAL** on live abstracts.

```powershell
$env:RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE = "1"
$env:RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE = "1"
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python scripts/run_graph_maturity_evidence_atom_upgrade.py --sync-public --limit-per-question 3
```
