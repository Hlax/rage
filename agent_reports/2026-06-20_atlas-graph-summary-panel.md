# Agent report — Atlas graph summary panel + live staged coherence

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Role:** Principal product engineer (RGE)

## Verdict

**GO (mock/proof layers)** — Graph summary panel wired on `/atlas-preview` with run-artifact and fixture fallback modes. Prior atlas preview bundle committed as `cc534c9`. Live staged spine source-health coherence **skipped** on this operator run with documented `unsuitable_live_artifact` (layer-3 catalog mismatch; not a regression).

## Prior bundle commit

```text
cc534c9 Wire atlas preview panels and staged source-health operator hooks.
```

Includes question header, readiness, purpose panels, operator loop refresh/combined-smoke hints, staged source-health sync, coherence tests, and agent reports.

## Live staged spine source-health coherence

**Command:**

```powershell
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_spine_source_health_coherence.py -m live_network -q
```

**Result:** `1 skipped` — preflight `unsuitable_live_artifact`

Live OpenAlex fetch succeeded for at least one candidate, but fetched HTML lacked mock-spine marker phrases (`human-ai co-creativity`, `songwriting`). Per ticket-285/layer-3 semantics this is an expected operator-catalog skip, **not** a source-health artifact regression.

**Mock layer (CI-safe):**

```powershell
python -m pytest tests/unit/test_live_staged_spine_source_health_coherence.py::test_mock_staged_spine_source_health_coherence -q
```

**Result:** PASS

**Test fix applied:** added `live_staged_spine_source_health_coherence_env` fixture so pytest `conftest.py` gate defaults (`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=0`) do not mask operator shell env.

## Packet — Atlas Graph Summary Panel from Run Artifact

### Panel fields added (`resolveGraphSummaryPanelPreview`)

| Field | Run artifact source | Fixture fallback |
| --- | --- | --- |
| relationship_density | `graph_summary.connection_metrics` clusters/totals | `cluster.relationship_density` |
| relationship_count | totals.relationships | `cluster.relationships_per_cluster` |
| edge_type_counts | supports / contradicts / qualifies from totals | relationship `type` labels |
| clustered_atom_count | totals.clustered_atom_count | atom maturity filter |
| weak_atom_count | totals.weak_atom_count | seed/weak/promising atoms |
| multi_claim_atom_count | totals.multi_claim_atom_count | `why_clustered` heuristic |
| source_diverse_atom_count | totals.source_diverse_atom_count | `source_count >= 2` |
| orphan_claim_count | totals.orphan_claim_count | `cluster.orphan_claim_count` |
| orphan_atom_count | totals.orphan_atom_count | `cluster.orphan_atom_count` |
| synthesis_ready_cluster_count | totals.synthesis_ready_cluster_count | cluster synthesis flag |
| frontend_ready_trace_count | totals.frontend_ready_trace_count | `trace_details.length` |
| graph_readiness_verdict | derived from density/orphans/relationships | fixture cluster posture |
| top_graph_blockers | graph-filtered readiness warnings + derived blockers | gaps/graph warnings |
| next_recommended_packet | artifact field | gaps panel |
| recommender_reason | artifact field | gaps panel |

### Public / private boundary

- Read-only static JSON only; no fetches, writes, or API routes.
- Run artifact uses aggregated counts and humanized labels only — no `source_id`, `claim_id`, quotes, local paths, prompts, or hidden notes.
- Fixture fallback reuses existing public-safe tiny connection preview sections.
- Safety audit pass after panel addition; no `dangerouslySetInnerHTML`.

## Verification

| Command | Status |
| --- | --- |
| `pytest tests/unit/test_atlas_source_health_run_preview.py tests/unit/test_tiny_atlas_connection_preview.py tests/unit/test_live_staged_spine_source_health_coherence.py::test_mock_staged_spine_source_health_coherence -q` | **13 passed** |
| `cd apps/public-site && npm run build` | **pass** |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| Live `live_network` coherence | **skipped** (`unsuitable_live_artifact`) |

## Top blockers

1. Live staged coherence cannot assert end-to-end on this catalog without mock-spine marker phrases in fetched HTML.
2. Weak atom count remains >0 in committed run artifact (`weak_atom_count: 1`) — graph verdict stays PARTIAL.
3. Clustered atom count is 0 in run artifact — next packet clustering work still indicated.
4. Publisher bot challenges / 403s dominate live fetch failures on current OpenAlex top-N set.

## Next recommended packets

1. **Public Site Graph Panel Golden Gate** — extend GT12 static render checks for graph summary panel copy.
2. **Operator Loop Full Atlas Refresh Checklist** — plan-mode bundle when all three preview JSON files are stale.
3. **Atlas Graph Summary ↔ Snapshot Coherence Badge** — inline coherence verdict cross-link between graph panel and coherence summary.
