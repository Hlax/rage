# Self-Improvement Spine Audit

Date: 2026-06-22

## Current Verdict

NO-GO.

The self-improvement/build loop is more aligned after this audit, but it is not release-ready. The release governor must continue to block promotion because:

- `python -m rge.cli verify --skip-site` still exits 1.
- The autonomous synthesis governor ledger still contains two historical NO-GO rows.
- The working tree is dirty across this audit's files plus pre-existing operator/public artifacts.

## Self-Improvement Spine Map

1. Research/run report
   - Source of truth: `rge/modules/run_evaluator.py`, research DB/run report artifacts.
   - Inputs: research DB, run contract, graph/pipeline metrics.
   - Outputs: run report JSON and quality/failure signals.
   - Gates: run contract drift, missing graph evidence, unsafe export policy.
   - Blocked action: repair the research spine or rerun fixture/mock proof.
   - LLM boundary: mock/Ollama may be used upstream for structured extraction; report aggregation is deterministic Python.
   - Contracts touched: may read/write private DB/graph records; no public Atlas by default.
2. Evaluator
   - Source of truth: evaluator/report modules and quality artifacts.
   - Inputs: run report, graph metrics, failure modes.
   - Outputs: improvement evidence and recommended build focus.
   - Gates: insufficient evidence, cadence/drift gates.
   - Blocked action: run principal/operator proof or gather stronger evidence.
   - LLM boundary: local/mock structured proposals only unless explicitly cloud-gated.
   - Contracts touched: no DB/graph schema or public Atlas contract.
3. Improvement ticket/instruction packet
   - Source of truth: `rge/modules/autonomous_synthesis_governor.py`, governor ledger.
   - Inputs: grounded synthesis packet, budget/provider gates, circuit breaker state.
   - Outputs: GO/PARTIAL/NO-GO review row, optional governed instruction packet.
   - Gates: NO-GO/PARTIAL ledger rows, open circuit breaker, missing budget/provider allowance, grounding failures.
   - Blocked action: inspect and remediate ledger reasons; reset circuit breaker only through explicit audited operator command.
   - LLM boundary: OpenAI/OpenRouter/mock may draft synthesis only when gated; deterministic Python governs.
   - Contracts touched: public Atlas synthesis/review summaries only after private-field scan; no graph writes.
4. Draft ticket
   - Source of truth: `rge/modules/instruction_packet_ticket_draft.py`, `data/operator/draft_tickets/*.json`.
   - Inputs: GO instruction packet and cited refs.
   - Outputs: private draft ticket JSON.
   - Gates: stale/missing packet, missing refs, forbidden actions, private-field scan.
   - Blocked action: regenerate from latest GO packet or fix packet content.
   - LLM boundary: no new LLM call; parses governed packet.
   - Contracts touched: no DB/graph schema or public Atlas contract.
5. Expected files/backfill
   - Source of truth: `rge/modules/instruction_packet_ticket_draft.py`.
   - Inputs: draft ticket and source instruction packet.
   - Outputs: `expected_files`, `expected_files_inferred`, optional patch revalidation summary.
   - Gates: missing draft, private-field scan, patch revalidation failure.
   - Blocked action: repair draft/instruction packet, then rerun backfill.
   - LLM boundary: none.
   - Contracts touched: private operator draft only.
6. Patch staging
   - Source of truth: `rge/modules/tier2_patch_staging.py`.
   - Inputs: draft ticket, expected files, working-tree diff.
   - Outputs: patch bundle, validation JSON, Tier 2 preview summary.
   - Gates: forbidden paths, size limits, missing tests, public-surface safety flags.
   - Blocked action: revise patch and re-stage; do not apply NO-GO bundles.
   - LLM boundary: external builder may propose code; Python validates staged diff.
   - Contracts touched: may update public-safe Tier 2 Atlas preview; no graph writes.
7. Tier 2 implementation
   - Source of truth: `rge/modules/tier2_local_implementation.py`.
   - Inputs: GO draft, Tier 2 policy, optional GO patch bundle.
   - Outputs: local branch, local commit, test/safety result sidecars.
   - Gates: circuit breaker, dirty tree, tier policy, test/safety failure.
   - Blocked action: fix implementation/tests or lower autonomy to manual handoff.
   - LLM boundary: external builder/IDE only; no model output writes accepted graph records.
   - Contracts touched: implementation files only, depending on draft scope.
8. Tests/safety
   - Source of truth: `rge/modules/verify_runner.py`, `rge/modules/safety_auditor.py`.
   - Inputs: repo working tree, mock LLM mode.
   - Outputs: verification and safety reports.
   - Gates: pytest/golden failure, public/private leak, unsafe route/model-tool violations.
   - Blocked action: fix real health failures before release governor GO.
   - LLM boundary: mock only.
   - Contracts touched: no DB/graph schema or public Atlas contract.
9. Release batch
   - Source of truth: `rge/modules/release_batch_assembler.py`, `data/operator/release_batches/*.json`.
   - Inputs: draft ticket, branch/commit, tests, safety, agent reports.
   - Outputs: private candidate batch JSON.
   - Gates: unsafe dirty tree, missing test/safety/report metadata, missing rollback plan.
   - Blocked action: clean tree and attach passing result artifacts.
   - LLM boundary: none.
   - Contracts touched: private operator batch; public Atlas summary may reference it.
10. Release governor
   - Source of truth: `rge/modules/release_governor.py`, `data/operator/release_governor_report_latest.json`.
   - Inputs: candidate batch, verify, safety audit, synthesis ledger, circuit breaker, Tier 2 staging state.
   - Outputs: release governor report and public-safe Atlas release governor artifact.
   - Gates: verify failure, synthesis NO-GO/PARTIAL rows, open circuit breaker, unsafe batch/dirty tree.
   - Blocked action: fix repo health first; remediate ledger/circuit state only through explicit audited commands.
   - LLM boundary: none.
   - Contracts touched: public Atlas release governor summary; no graph writes.
11. Atlas preview
   - Source of truth: `apps/public-site/public/data/*atlas*_latest.json`.
   - Inputs: public-safe operator artifacts.
   - Outputs: `/atlas-preview` panels.
   - Gates: private-field scan, static render/build failure.
   - Blocked action: refresh safe artifact and rebuild public site.
   - LLM boundary: none.
   - Contracts touched: public Atlas artifacts only.

The same map is now machine-readable in `data/operator/self_improvement_status_latest.json`.

## Current NO-GO Diagnosis

Verification:

- `python -m rge.cli verify --skip-site`: failed.
- Golden tests: `RGE_LLM_MODE=mock python -m pytest tests/golden` passed, `165 passed`.
- Full pytest: `RGE_LLM_MODE=mock python -m pytest` failed with one test during the full run:
  `tests/unit/test_atlas_snapshot_builder.py::test_build_atlas_snapshot_matches_committed_creativity_fixture`.
- Safety audit inside verify passed.
- Direct reproduction:
  `python -m pytest tests/unit/test_atlas_snapshot_builder.py::test_build_atlas_snapshot_matches_committed_creativity_fixture -q` passed.
- Containing module:
  `python -m pytest tests/unit/test_atlas_snapshot_builder.py -q` passed, `7 passed`.

Interpretation: the remaining verify blocker is a real repo-health failure because the canonical full-suite command exits 1. The direct pass suggests order-dependent generated state or fixture drift, not a stable isolated unit failure.

Synthesis governor and circuit breaker:

- `data/operator/autonomous_synthesis_governor_ledger.json` contains `syn_gov_c8f498f9f233` as NO-GO because the circuit breaker was open, OpenAI was not explicitly allowlisted, and `RGE_CLOUD_MAX_USD_PER_RUN` / `RGE_CLOUD_MAX_TOKENS_PER_CALL` were missing.
- The ledger also contains `syn_gov_d2555e428c61` as NO-GO because the circuit breaker was open.
- `data/operator/autonomy_circuit_breaker.json` currently reports `status: closed`, `latest_stop_reason: operator_reset`, and zero consecutive synthesis failures.

Interpretation: the open-circuit reason inside the ledger is historical/stale relative to the current circuit breaker artifact, but the NO-GO rows are still real release-governor blockers by design. They were not reset, deleted, or mutated.

Release governor:

- `data/operator/release_governor_report_latest.json` reports NO-GO for `batch-draft-tier2-rehearsal`.
- Failure reasons are:
  - `synthesis governor NO-GO review present: syn_gov_c8f498f9f233`
  - `synthesis governor NO-GO review present: syn_gov_d2555e428c61`
  - `verify failed`
- `python scripts/run_release_governor.py --inspect` completed successfully.

Operator plan:

- `python -m rge.modules.operator_loop --mode plan` completed, but current recommendation is blocked:
  `resolve_documentation_git_drift`.
- Reason: working tree contains uncommitted changes spanning multiple tickets: `ticket-041`, `ticket-059`.

## Alignment Fixes Implemented

- Added `rge/modules/self_improvement_status.py`, a private operator summary writer for `data/operator/self_improvement_status_latest.json`.
- Added `tests/unit/test_self_improvement_status.py`.
- Updated operator-loop/autocycle test fixtures to seed a neutral synthesis human-review Atlas artifact when tests are not about synthesis gates.
- Updated release batch/Tier 2 tests to prove the current truthful priority order:
  expected-files backfill runs before patch staging when needed; after backfill succeeds, the next recommendation advances to patch staging.

No circuit breaker reset was performed. No ledger rows were deleted or mutated. `TICKET_QUEUE.md` was not edited. No push, merge, publish, or ticket promotion was performed.

## Test And Safety Results

- `python -m pytest tests/unit/test_self_improvement_status.py tests/unit/test_operator_loop.py tests/unit/test_operator_loop_release_batch_candidate.py tests/unit/test_tier2_patch_staging_followups4.py tests/unit/test_operator_loop_autonomous_scratch_inspection.py tests/unit/test_operator_loop_autonomous_improvement_inspection.py tests/unit/test_operator_loop_autonomous_hook.py tests/unit/test_operator_loop_autonomous_execute_safe_refresh.py tests/unit/test_operator_loop_autonomous_execute_safe_improvement_refresh.py tests/unit/test_operator_autocycle_autonomous_scratch.py tests/unit/test_operator_autocycle_autonomous_execute_safe_sync.py tests/unit/test_operator_autocycle_autonomous_execute_safe_reason_sync.py tests/unit/test_operator_autocycle_autonomous_execute_safe_improvement_sync.py -q`
  - Passed: `94 passed`.
- `python -m pytest --lf -q`
  - Passed: `23 passed, 187 deselected`.
- `python -m rge.modules.safety_auditor --audit full`
  - Passed.
- `python -m rge.modules.operator_loop --mode plan`
  - Completed; blocked on documentation/git drift.
- `python scripts/run_release_governor.py --inspect`
  - Completed.

## LLM And Builder Boundary

Current verification and tests used `RGE_LLM_MODE=mock`.

The self-improvement loop allows:

- Mock/Ollama for upstream structured extraction where already supported by the research pipeline.
- OpenAI/OpenRouter/mock cloud only for gated synthesis proposal text, with deterministic Python governor review.
- External builder/IDE agents for Tier 2 implementation proposals.

It does not allow model output to write accepted DB/graph records directly.

## Database, Graph, And Atlas Contracts

This audit did not change database schema, graph schema, accepted graph write paths, public write routes, public ingestion routes, or public agent-execution routes.

Code changes add a private operator artifact under `data/operator/`. Existing public Atlas release governor JSON was already dirty and remains part of the current local state; this audit did not add a new public Atlas contract.

## Next Safest Ticket

Create a narrow ticket to isolate and fix the full-suite-only Atlas snapshot fixture failure:

`ticket-next-atlas-snapshot-full-suite-order-dependence`

Scope: reproduce `tests/unit/test_atlas_snapshot_builder.py::test_build_atlas_snapshot_matches_committed_creativity_fixture` under the full-suite ordering, identify the generated state or fixture drift source, and make the snapshot test deterministic without weakening public/private export checks.
