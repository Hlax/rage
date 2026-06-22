# Atlas Snapshot Full-Suite Order-Dependence

Date: 2026-06-22

## Verdict

PARTIAL/GO for this ticket's verify objective.

The previously observed full-suite-only Atlas snapshot failure did not reproduce during this pass. The strict Atlas fixture test now passes in isolation, as a module, in an Atlas/public neighboring group, under full pytest, and under the full `verify --skip-site` ordering.

No Atlas builder code was changed because a speculative change would risk weakening the exact public/private fixture contract without evidence of a persistent mutation source.

## Exact Reproduction Commands

Initial requested reproducer:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest -q tests/unit/test_atlas_snapshot_builder.py
```

Result: `7 passed`.

Full-suite reproducer:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest -q
```

Result: `1287 passed, 49 deselected`.

Verify-order reproducer:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
```

Result: `status: pass`.

Targeted neighboring Atlas/public group:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest -q tests/unit/test_atlas_snapshot_builder.py tests/unit/test_atlas_snapshot_export_cli.py tests/unit/test_atlas_snapshot_report_summary.py tests/unit/test_atlas_snapshot_cluster_members.py tests/unit/test_atlas_snapshot_coherence_summary.py tests/unit/test_atlas_coherence_preview_sync.py tests/unit/test_public_atlas_preview_fixture.py tests/unit/test_safety_auditor_atlas_preview.py tests/unit/test_atlas_evidence_cards_preview.py
```

Result: `56 passed`.

## Root Cause Assessment

No persistent mutation source was found.

What was checked:

- `tests/unit/test_atlas_snapshot_builder.py` builds its fixture DB under `tmp_path` and compares the generated snapshot strictly against `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`.
- `rge/modules/atlas_snapshot_builder.py` uses fixture-mode constants for snapshot ID, timestamp, and audit ID, and validates the public/private policy before returning/exporting snapshots.
- Neighboring Atlas tests that export snapshots write to `tmp_path`, not the committed fixture.
- Public preview tests read committed public data or write temp copies; they do not write the committed creativity Atlas fixture.
- Searches did not find tests writing `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` or mutating Atlas fixture constants.

The best current explanation is that the earlier failure was a transient full-run state from the prior dirty audit session, not a stable order-dependent Atlas writer. Because the requested reproducers are now green, no fixture isolation or ordering patch was applied.

## Files Changed

No Atlas/public-private implementation files were changed in this ticket.

This report was added:

- `agent_reports/2026-06-22_atlas-snapshot-full-suite-order-dependence.md`

The working tree still contains the useful prior audit/repair changes from the self-improvement spine pass.

## Public/Private Atlas Checks

The public/private checks were not weakened.

- The exact snapshot equality assertion in `tests/unit/test_atlas_snapshot_builder.py` was not changed.
- `assert_no_private_fields` behavior was not changed.
- Atlas snapshot validation was not loosened.
- Release governor gates were not changed.
- No committed Atlas fixture or public Atlas JSON was edited by this ticket.

## Verification Results

- `python -m pytest -q tests/unit/test_atlas_snapshot_builder.py`: passed, `7 passed`.
- Neighboring Atlas/public group: passed, `56 passed`.
- `python -m pytest -q`: passed, `1287 passed, 49 deselected`.
- `python -m rge.cli verify --skip-site`: passed.
  - Golden tests: `165 passed`.
  - Full pytest: `1287 passed, 49 deselected`.
  - Safety audit: passed.
- `python -m rge.modules.safety_auditor --audit full`: passed.
- `python -m rge.modules.operator_loop --mode plan`: completed; next action remains blocked on documentation/git drift.
- `python scripts/run_release_governor.py --inspect`: completed.

## Remaining Release-Governor Blockers

After verify is green, the remaining release-governor blockers are not Atlas snapshot test failures.

Known remaining blockers:

- Historical synthesis governor NO-GO ledger rows remain:
  - `syn_gov_c8f498f9f233`
  - `syn_gov_d2555e428c61`
- The working tree remains dirty from the prior audit/repair pass plus this report.
- Operator plan reports `resolve_documentation_git_drift` because uncommitted changes span multiple ticket markers: `ticket-041`, `ticket-059`.

Circuit breaker status from inspect remains `closed`; it was not reset or modified by this ticket.

No synthesis governor ledger rows were mutated, deleted, or reset.
