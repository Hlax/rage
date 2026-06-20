# Purpose-Gated Relationship Density Proof

- Date: 2026-06-20
- Verdict: **GO**
- Scope: backend/data-contract proof only; no frontend UI and no broad automation.

## Summary

Implemented a deterministic, purpose-gated relationship-density proof for the core fixture question: “Does AI assistance improve idea quality or reduce diversity?”

The fixture graph now forms a meaningful connected research cluster with quote-backed claims, typed relationship evidence, clustered atoms, public-safe Atlas trace previews, and readiness metrics that meet the requested acceptance targets.

## Changed Files

- `rge/modules/purpose_gating.py`
- `rge/modules/relationship_density_proof.py`
- `rge/modules/evidence_atoms.py`
- `rge/modules/cluster_reporter.py`
- `rge/modules/atlas_trace.py`
- `rge/modules/research_queue.py`
- `rge/modules/abstract_evidence.py`
- `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`
- `tests/unit/test_purpose_gated_relationship_density_proof.py`

## Before / After Metrics

Before:

- Claims: 15
- Atoms: 14
- Relationships: 2
- Orphan claims: 12
- Orphan atoms: 11
- Weak atoms: 13
- Clustered atoms: 0
- Relationship density: 0.1333
- Synthesis-ready clusters: 1

After:

- Claims: 15
- Atoms: 7
- Relationships: 10
- Orphan claims: 0
- Orphan atoms: 0
- Weak atoms: 0
- Clustered atoms: 4
- Multi-claim atoms: 6
- Source-diverse atoms: 6
- Contradiction edges: 2
- Qualification edges: 6
- Relationship density: 0.6667
- Synthesis-ready clusters: 1
- Frontend-ready traces: 15

## Purpose-Gate Findings

- Source ranking now annotates `purpose_match_status`, `purpose_gate_decision`, and `purpose_gate_reason`, and rejects hard purpose mismatches for purpose-specific queries.
- Abstract evidence generation now skips source records that fail hard purpose gates and moves claim-level mismatches into rejected abstract evidence with `purpose_mismatch`.
- Atom promotion and compatible atom clustering can enforce purpose gates, so mismatched claims are rejected or downgraded before graph promotion.
- Targeted tests prove generic AI/diversity evidence is rejected before atom promotion for a style/design purpose.

## Atom Clustering Findings

- Cluster promotion now runs after purpose-gated relationship proofing.
- Multi-claim clusters are preserved during repeated atom merges; previously clustered maturity is not downgraded by later idempotent promotion.
- The regenerated fixture contains 6 multi-claim/source-diverse atoms and 4 clustered atoms.

## Relationship-Density Findings

- Added deterministic typed relationship proof edges for support, contradiction, qualification, definition, and scope-difference.
- The core fixture cluster now has 10 relationships for 15 claims.
- Relationship density is 0.6667, above the 0.5 target.
- Orphan claims and orphan atoms are both 0.
- Contradiction and qualification evidence are both present.

## Atlas / Frontend Readiness

- Atlas trace previews now include relationship type data, connection reasons, cluster maturity, purpose-match status, and evidence decisions.
- Public-safe previews continue stripping private IDs, raw quote text, prompts, local paths, and hidden notes.
- The frontend can now render honest connected-cluster states from the data contract, but no UI was built in this packet.

## Model Readiness

- Local-model readiness: **PARTIAL**. The proof is deterministic and mock-safe. Purpose gates are now available around local-model outputs, but arbitrary live Ollama source runs remain outside this packet.
- Paid-API readiness: **NO-GO**. No paid provider or escalation path was added.

## Verification

- `python -m pytest tests/unit/test_purpose_gated_relationship_density_proof.py -q` -> pass, `6 passed`
- `python -m pytest tests/unit/test_purpose_gated_relationship_density_proof.py tests/unit/test_evidence_atom_clustering_purpose_gating.py tests/unit/test_connection_layer_atlas_trace.py tests/unit/test_failure_recommender.py tests/unit/test_manual_relationship_building.py tests/unit/test_atlas_snapshot_builder.py -q` -> pass, `44 passed`
- `python -m pytest tests/unit/test_safety_auditor_atlas_preview.py tests/unit/test_atlas_snapshot_contract.py tests/unit/test_atlas_coherence_report.py -q` -> pass, `16 passed`
- `python -m pytest tests/golden/test_19_run_report.py tests/golden/test_35_acquisition_quality_tickets.py tests/golden/test_34_asset_export_candidates.py -q` -> pass, `8 passed`
- `python -m rge.modules.safety_auditor --audit full` -> pass
- `python -m py_compile ...` on edited Python files and the new test -> pass

Full verification was not run because this packet did not add migrations, change quote validation, change source download behavior, or change public card export schema. Full safety audit was run because Atlas-safe previews changed.

## Top Blockers

1. Purpose gates are now wired into key deterministic paths, but not every future arbitrary-source/live path has a hard gate yet.
2. The density proof is deterministic fixture-backed; live arbitrary-source relationship density remains unproven.
3. Relationship types are represented in metadata/previews, but not yet normalized into a dedicated schema enum.

## Next 3 Recommended Packets

1. Live/Arbitrary Source Purpose Gate Enforcement: apply purpose gates to staged live discover/fetch/ingest/extract/link/build/detect paths.
2. Relationship Type Contract Formalization: promote relationship type metadata into a validated contract/enum and update tests around typed graph semantics.
3. Atlas Cluster UI Readiness Pass: consume the now-ready trace/metric fields in a minimal Atlas preview state, still read-only and public-safe.
