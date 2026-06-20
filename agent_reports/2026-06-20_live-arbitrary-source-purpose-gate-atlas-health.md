# Live/Arbitrary Source Purpose Gate + Atlas Source Health

Date: 2026-06-20

Verdict: GO for mock/local-safe arbitrary-source proof.

Live OpenAlex/arXiv network and live Ollama were not used. Paid API readiness remains NO-GO by design.

## What Changed

- Added `rge/modules/live_arbitrary_source_health.py`, a local-safe proof path for the arbitrary question: "How does AI affect human creativity?"
- Persisted source-health metadata for resolver records into durable `sources.domain_metadata_json`.
- Added purpose-fit source metadata and summary counts: `purpose_fit_status`, `purpose_fit_reason`, and `purpose_gate_decision`.
- Added Atlas-safe `source_health_preview` projection to Atlas snapshots with public-safe source refs instead of private row IDs.
- Updated recommender signals for:
  - missing source health -> source-health persistence
  - dominant purpose mismatch -> purpose-gate/retrieval fixes
  - too-thin extractable sources -> acquisition/source expansion
  - acquisition/parser blockers still take precedence

## Arbitrary / Local-Safe Run Summary

The local-safe proof resolves the arbitrary question through manual fixture resolver mode, persists four source-health rows, skips metadata-only/unextractable records before extraction, purpose-gates abstract evidence, persists accepted/rejected DB claim rows, generates a DB-backed run report, and writes an Atlas-safe run artifact when an output directory is provided.

Expected artifact shape: `atlas_source_health_run_latest.json`.

## Findings

Source health persistence: GO. Run reports include acquisition/source health counts, parser backend counts, extractability counts, resolver source counts, availability counts, and purpose-fit counts.

Purpose gating: GO. Gates now affect source-level abstract evidence generation, persisted claim acceptance/rejection, atom promotion, relationship-density proof, graph metrics, and Atlas-safe projection.

Atlas preview/export: GO. `build_atlas_snapshot_from_db()` now includes `source_health_preview`, scrubbed of `source_id`, `claim_id`, `quote_id`, `chunk_id`, `local_path`, raw text, prompts, and private notes.

Graph/relationship readiness: PARTIAL. The local-safe proof can produce claims, atoms, and deterministic relationship-density edges, but arbitrary live network source diversity is still opt-in and unverified in this packet.

Local model readiness: GO for mock/local-safe mode. Live Ollama remains opt-in and was not exercised.

Paid API readiness: NO-GO. No paid provider calls were added or run.

Automation readiness: PARTIAL. The proof is callable from Python tests/modules; no broad automation or autonomous loop was added.

## Top Blockers

- Live resolver/source fetch remains behind explicit network gates and was not run here.
- Atlas public UI still reads the fixture-backed Tiny Atlas preview; DB-backed source-health preview is available in Atlas snapshot/artifact projection, not wired into a larger frontend.
- Relationship maturity remains dependent on enough accepted, purpose-matching claims and concept links.

## Next 3 Recommended Packets

1. Atlas Source Health Preview Wiring: optionally let `/atlas-preview` choose a generated Atlas-safe source-health artifact when present.
2. Live Network Source Health Smoke: operator-gated OpenAlex/arXiv resolver proof that persists the same source-health metadata on a temp DB.
3. Purpose-Gated Source Expansion: improve retrieval/ranking when purpose mismatch or extractable-source scarcity dominates.

## Verification

- `python -m py_compile rge/modules/live_arbitrary_source_health.py rge/modules/acquisition_quality.py rge/modules/atlas_snapshot_builder.py rge/modules/failure_recommender.py` PASS
- `python -m pytest tests/unit/test_live_arbitrary_source_health.py tests/unit/test_failure_recommender.py tests/unit/test_web_source_adapter.py tests/unit/test_purpose_gated_relationship_density_proof.py tests/unit/test_tiny_atlas_connection_preview.py -q` PASS, 32 passed
- `python -m pytest tests/golden/test_12_public_site_static_render.py tests/unit/test_safety_auditor_atlas_preview.py -q` PASS, 16 passed
- `npm run build` in `apps/public-site` PASS
- `python -m rge.modules.safety_auditor --audit full` PASS
