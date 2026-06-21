# Graph Maturity / Evidence Atom Upgrade

**Date:** 2026-06-20  
**Packet:** Graph Maturity / Evidence Atom Upgrade  
**Cycle:** Operator loop cycle 3 — after local model extraction comparison  
**Verdict:** **PARTIAL** (expected on live abstracts)

## Live run summary (2026-06-20 — cycle 3)

| Signal | Result |
| --- | ---: |
| Questions ingested | 5 (3 sources each) |
| Accepted claims | **11** |
| Concept links seeded | 14 |
| Relationships | **8** |
| Orphan claims | 8 → **0** |
| Multi-claim atoms | **0** |
| Cluster | `synthesis_ready` (1 contradiction, 3 qualification edges) |

| Question | Accepted |
| --- | ---: |
| AI + human creativity | 3 |
| AI assistance + diversity | 3 |
| Co-creation + agency (strict) | 0 |
| Artist style + originality (strict) | 2 |
| AI creativity benchmark | 3 |

**PARTIAL** is expected: relationships and cluster explanations improved; multi-claim atom consolidation remains thin on unique live abstract quote scopes.

## Verification

| Command | Status |
| --- | --- |
| Live run `--sync-public --limit-per-question 3` | **PARTIAL** (exit 0) |
| `pytest tests/unit/test_graph_maturity_evidence_atom_upgrade.py -q` | **PASS** (6 passed) |
| Safety audit | **PASS** |
| `npm run build` | **PASS** |

## Next recommended packet

**Web Adapter / Scrapling Proof** (`web-adapter-scrapling-proof`)

```powershell
$env:RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF = "1"
$env:RGE_LLM_MODE = "mock"
python scripts/run_web_adapter_scrapling_proof.py --sync-public
```
