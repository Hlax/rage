# Operator Proof Bundle Drift Clearance

## Summary

Ran the mock arbitrary-source proof bundle requested for the product-risk/live-research drift packet. The proof bundle now completes successfully on the documented scratch paths with `usable_output: true`.

The operator loop did **not** fully clear the drift warning in plan/autocycle output. Current operator-loop logic still derives `proof_bundle_recommended` from the principal-audit `drift_warning` field rather than inspecting the newly written `operator_proof_bundle.json`. Tier 2 execute-safe autocycle also stopped on a dirty working tree, so ticket-059 is not yet a clean execute-safe target in the current repo state.

## Changed Files

- `rge/modules/operator_proof_bundle.py`
  - Forces the proof bundle onto the mock fixture staged path by temporarily disabling `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR`.
  - Uses the committed OpenAlex fixture and deterministic staged HTML bodies inside the proof-bundle command, avoiding live network drift for this mock-only proof.
  - Converts incomplete orchestrator payloads into structured error bundles instead of raw `KeyError`.
- `tests/unit/test_operator_proof_bundle.py`
  - Adds regression coverage that ambient live-orchestrator env state does not move the proof bundle off the fixture staged path.

Pre-existing/externally generated dirty path still present:

- `apps/public-site/public/data/atlas_release_governor_latest.json`

## Proof Bundle Command

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli prove-arbitrary-source-bundle `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/operator_proof_bundle_scratch.sqlite `
  --output-dir data/reports/operator_proof_bundle `
  --staging-dir data/sources/staged/operator_proof_bundle `
  --export-dir data/exports/operator_proof_bundle `
  --bundle-out data/reports/operator_proof_bundle/operator_proof_bundle.json
```

Result: pass after clearing the stale scratch DB from failed attempts.

## Output Paths

- Bundle: `data/reports/operator_proof_bundle/operator_proof_bundle.json`
- Run report: `data/reports/operator_proof_bundle/run_report_latest.json`
- Public-card export: `data/exports/operator_proof_bundle/public_cards.json`
- Scratch DB: `data/db/operator_proof_bundle_scratch.sqlite`
- Staging dir: `data/sources/staged/operator_proof_bundle`

## Proof Result

- `status`: `completed`
- `usable_output`: `true`
- `pipeline_mode`: `fixture_staged_rank1`
- `source_id`: `src_4c96a06b384f4b36`
- `rank1_candidate_id`: `disc_openalex_W2741809807`
- `claim_count`: 2
- `concept_link_count`: 3
- `relationship_count`: 2
- `qualification_count`: 1
- `reconcile.status`: `completed`
- `reconcile.score_events_created`: 1
- `card_count`: 2

Product-risk/live-research proof advanced: the packet proves the safe arbitrary-source mock spine can discover/enqueue staged OpenAlex fixture candidates, fetch/ingest rank-1 and rank-2 staged sources, run mock extraction/link/build/detect, reconcile scores, generate run reports, and export public cards from the rank-1 proof path.

Private-field scan: no matches for local paths, raw text, prompts, secrets, private fields, unsafe script content, or public export leakage in `operator_proof_bundle.json` or `public_cards.json`.

## Verification

- `git status --short`: dirty after packet changes:
  - `apps/public-site/public/data/atlas_release_governor_latest.json`
  - `rge/modules/operator_proof_bundle.py`
  - `tests/unit/test_operator_proof_bundle.py`
- `python scripts/run_release_governor.py --inspect`: pass, `status: completed`, effective tier 1.
- Initial `python -m rge.modules.operator_loop --mode plan`: working tree clean before edits; ticket-059 selected; drift warning present; proof bundle recommended.
- `python -m pytest tests/unit/test_operator_proof_bundle.py -q`: pass, 13 passed.
- `python -m pytest -q`: pass, 1289 passed, 49 deselected.
- First `python -m rge.cli verify --skip-site`: failed transiently in embedded full pytest on `test_atlas_coherence_cli_pipeline_fixture.py`; direct rerun of that test passed.
- Second `python -m rge.cli verify --skip-site`: pass; golden tests 165 passed, full pytest 1289 passed / 49 deselected, safety audit passed.
- `python -m rge.modules.safety_auditor --audit full`: pass.
- Post-proof `python -m rge.modules.operator_loop --mode plan`: still reports the principal-audit drift warning and blocks release recommendations on dirty working tree.
- Post-proof `python scripts/run_release_governor.py --inspect`: pass, `status: completed`, effective tier 1.

## Tier 2 Autocycle

Command:

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_AUTONOMY_TIER = "2"
$env:RGE_ALLOW_BRANCH_AUTONOMY = "1"
$env:RGE_EXECUTE_SAFE_DRAFT_BACKFILL = "1"
$env:RGE_EXECUTE_SAFE_PATCH_STAGING = "1"
$env:RGE_REVALIDATE_PATCH_AFTER_BACKFILL = "1"
$env:RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW = "1"
python -m rge.modules.operator_autocycle --mode execute-safe --max-cycles 3
```

Result: stopped after 1 cycle.

- `status`: `stopped`
- `stop_reason`: `working_tree_dirty`
- `recommended_action`: `resolve_unsafe_working_tree`
- `execute_safe_eligible`: `false`
- Dirty paths blocking release/Tier 2:
  - `apps/public-site/public/data/atlas_release_governor_latest.json`
  - `rge/modules/operator_proof_bundle.py`
  - `tests/unit/test_operator_proof_bundle.py`

The autocycle payload still includes the historical drift warning in the cycle block. It also reports `proof_bundle_recommended: false` in the top-level post-cycle fields, but the recommended action remains dirty-tree cleanup.

## Ticket-059 Readiness

Ticket-059 is still the intended next cloud-adapter implementation target from the operator plan/audit gate context, but it is **not yet a clean execute-safe target** in this working tree because:

1. This packet introduced required proof-bundle code/test changes that are currently uncommitted.
2. `apps/public-site/public/data/atlas_release_governor_latest.json` remains dirty.
3. Operator-loop plan mode still surfaces the principal-audit drift warning until queue/report/audit state is updated beyond simply writing the proof artifact.

No ticket-059 implementation was performed. No live OpenAI calls, push, merge, publish, ticket promotion, or `TICKET_QUEUE.md` edits were performed.

## Recommended Next Step

Review and commit or otherwise checkpoint this proof-bundle clearance packet, then rerun:

```powershell
python -m rge.modules.operator_loop --mode plan
$env:RGE_LLM_MODE = "mock"
$env:RGE_AUTONOMY_TIER = "2"
$env:RGE_ALLOW_BRANCH_AUTONOMY = "1"
$env:RGE_EXECUTE_SAFE_DRAFT_BACKFILL = "1"
$env:RGE_EXECUTE_SAFE_PATCH_STAGING = "1"
$env:RGE_REVALIDATE_PATCH_AFTER_BACKFILL = "1"
$env:RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW = "1"
python -m rge.modules.operator_autocycle --mode execute-safe --max-cycles 3
```

If the loop still routes to ticket-361 or keeps the drift warning after checkpointing, the next narrow fix should update operator-loop proof-bundle status inspection to recognize the completed `operator_proof_bundle.json` artifact, or complete the README documentation ticket-361 as the loop currently surfaces.
