# Evidence Atom Clustering + Purpose-Gated Retrieval

- Template: `evidence-atom-clustering-purpose-gating`
- Date: 2026-06-19
- Verdict: **PARTIAL**

## Summary

Implemented backend-only evidence atom clustering and purpose-gated evidence acceptance. RGE can now cluster compatible quote-backed claims into shared atoms when scope and concept signatures align, track source diversity and stance profile, and expose purpose match/mismatch status through private Atlas traces and public-safe trace previews.

This is **PARTIAL**, not GO, because the committed fixture still shows a thin graph: 15 claims, 14 atoms, only 1 multi-claim/source-diverse atom, 13 weak atoms, 0 clustered atoms, and relationship density of 0.1333. The contract is stronger, but the default graph still needs broader relationship and atom consolidation work.

## Changed Files

- `rge/modules/evidence_atoms.py`
- `rge/modules/purpose_gating.py`
- `rge/modules/atlas_trace.py`
- `rge/modules/failure_recommender.py`
- `rge/modules/run_evaluator.py`
- `rge/modules/atlas_snapshot_builder.py`
- `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`
- `tests/unit/test_evidence_atom_clustering_purpose_gating.py`

## Metrics Before / After

Before this packet, Atlas connection metrics exposed atom and relationship counts but did not report multi-claim atom count, source-diverse atom count, purpose mismatch count, weak/clustered atom counts, synthesis readiness, or frontend-ready trace count.

After this packet, the regenerated fixture reports:

- `claims`: 15
- `atoms`: 14
- `relationships`: 2
- `multi_claim_atom_count`: 1
- `source_diverse_atom_count`: 1
- `purpose_mismatch_count`: 0
- `weak_atom_count`: 13
- `clustered_atom_count`: 0
- `synthesis_ready_cluster_count`: 1
- `frontend_ready_trace_count`: 15
- `relationship_density`: 0.1333

## Atom Clustering Findings

- Compatible same-scope claims can cluster into one shared atom.
- Incompatible scopes remain separate.
- Clustered atom payloads preserve merged claim IDs, quote IDs, concepts, source count, concept overlap, source diversity, stance counts, and `why_clustered`.
- Duplicate one-claim atoms are removed when superseded by a clustered atom.
- Maturity promotion works in targeted tests, including `clustered` when enough compatible claims and source diversity exist.
- Fixture-level clustering remains limited: most committed fixture atoms still represent weak one-claim objects.

## Purpose-Gating Findings

- Style/originality questions now require style, originality, aesthetic, design, novelty, visual, or visual-language evidence.
- Agency/co-creation questions now require agency, control, collaboration, autonomy, co-creation, authorship, ownership, or human-control evidence.
- Generic AI/diversity evidence is rejected for unrelated style or agency questions.
- Purpose-matched originality/design evidence passes.
- Purpose status and downgrade/rejection reasons are included in private traces and public-safe previews.

## Graph / Atlas Readiness

- Atlas trace previews now include atom cluster maturity, purpose match status, evidence decision, why clustered, and downgrade/rejection reason.
- Public-safe previews still strip `claim_id`, `source_id`, `quote_id`, raw text, prompts, local paths, and hidden notes.
- Graph readiness metrics now include `multi_claim_atom_count`, `source_diverse_atom_count`, `purpose_mismatch_count`, `weak_atom_count`, `clustered_atom_count`, `synthesis_ready_cluster_count`, and `frontend_ready_trace_count`.

## Frontend Readiness Notes

The UI can now consume richer non-private trace rows and readiness metrics, but the frontend should not yet treat the graph as mature. The data contract can explain weak/mismatched evidence and thin relationship density, which is useful for honest UI states.

## Model Readiness

- Local-model readiness: **PARTIAL**. The gate is deterministic and mock-safe; live Ollama is not required for tests. Purpose gates can constrain future model retrieval/extraction outputs.
- Paid-API readiness: **NO-GO**. No paid provider path was added, and the graph is still too sparse for escalation-based synthesis.

## Verification

- `python -m pytest tests/unit/test_evidence_atom_clustering_purpose_gating.py -q` -> pass, `11 passed`
- `python -m pytest tests/unit/test_evidence_atom_clustering_purpose_gating.py tests/unit/test_evidence_atoms.py tests/unit/test_connection_layer_atlas_trace.py tests/unit/test_failure_recommender.py tests/unit/test_research_purpose_classifier.py tests/unit/test_atlas_snapshot_builder.py -q` -> pass, `40 passed`
- `python -m pytest tests/unit/test_safety_auditor_atlas_preview.py tests/unit/test_atlas_snapshot_contract.py tests/unit/test_atlas_coherence_report.py -q` -> pass, `16 passed`
- `python -m pytest tests/golden/test_19_run_report.py tests/golden/test_35_acquisition_quality_tickets.py tests/golden/test_34_asset_export_candidates.py -q` -> pass, `8 passed`
- `python -m rge.modules.safety_auditor --audit full` -> pass
- `python -m py_compile ...` on edited Python files -> pass

Full verification was not run because this packet did not add migrations, alter quote validation, change source download behavior, or change public card export schema. Full safety audit was run because Atlas-safe previews changed.

## Top Blockers

1. Relationship density remains low (`0.1333`), so Atlas still has too many weakly connected claims.
2. Fixture graph has 13 weak atoms and 0 clustered atoms despite the clustering API working in targeted tests.
3. Purpose gates are deterministic but not yet wired into every retrieval path as a hard pipeline gate.

## Next 3 Recommended Packets

1. Relationship Density Expansion: create more typed support/qualification/contradiction edges per cluster and reduce orphan claims.
2. Pipeline-Wide Purpose Gate Enforcement: apply purpose-fit decisions during source ranking, abstract evidence generation, and full-text claim acceptance.
3. Clustered Atom Fixture Spine: add/adjust fixture evidence so committed Atlas previews contain at least one truly `clustered` atom, not only targeted-test proof.
