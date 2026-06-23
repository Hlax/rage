# Tier 2 Patch Staging + Diff Quality Gate

**Date:** 2026-06-22  
**Verdict:** GO  
**Phase:** Autonomy / Tier 2 pre-commit airlock

## Summary

Added a gitignored patch staging airlock under `data/operator/tier2_patch_staging/` so Tier 2 implementation changes are bundled, diff-validated, and operator-reviewed before apply/commit. The Tier 2 runner, operator loop, release batch assembler, and release governor all integrate staged validation metadata and gates.

## Staging schema

`tier2_patch_bundle_v0.1.0` (`rge/modules/tier2_patch_staging.py`):

| Field | Purpose |
|-------|---------|
| `draft_ticket_path` | Source draft ticket JSON |
| `instruction_packet_path` | Linked instruction packet ref |
| `branch_name` | Intended Tier 2 feature branch |
| `intended_files` | Draft `expected_files` |
| `proposed_changed_files` | Working-tree paths staged |
| `diff_summary` | File/line add/remove stats |
| `risk_class` | `low` / `medium` / `high` |
| `test_plan` | Draft test commands |
| `safety_audit_required` | True when public surfaces touched |
| `rollback_notes` | Operator rollback guidance |
| `generated_at` | UTC timestamp |
| `validation_verdict` | `pending` / `GO` / `PARTIAL` / `NO-GO` |
| `validation_reasons` | Gate failure messages (max 10) |

Each bundle directory contains `bundle.json`, `validation.json`, and `files/` with proposed file snapshots. No raw prompts, secrets, or private notes are written.

## Diff quality gates

Reject or flag when:

- Paths outside allowed implementation prefixes or draft scope
- Forbidden paths touched (`.env.local`, `TICKET_QUEUE.md`, raw sources, operator ledgers)
- Diff exceeds `RGE_TIER2_PATCH_MAX_FILES` (default 20) or `RGE_TIER2_PATCH_MAX_LINES` (default 2000)
- Too many deleted files (>5)
- Public artifacts changed without `safety_audit_required`
- Tests-only changes on non-test-only tickets
- Source changes without expected test updates
- Draft non-goals violated
- Forbidden push/merge/publish/promote language in bundle metadata
- Private-field scan violations on bundle payload

Verdict: 0 reasons → GO; 1–2 → PARTIAL; 3+ → NO-GO.

## CLI commands

```powershell
# Stage latest draft working-tree changes
python scripts/run_tier2_patch_staging.py --latest

# Validate an existing bundle
python scripts/run_tier2_patch_staging.py --bundle PATH --validate

# Apply a GO-validated bundle to working tree
python scripts/run_tier2_patch_staging.py --bundle PATH --apply

# Tier 2 runner staging modes
python scripts/run_tier2_local_implementation.py --latest --stage-only
python scripts/run_tier2_local_implementation.py --latest --apply-staged PATH --require-staged-validation
```

## Tier 2 runner changes

`rge/modules/tier2_local_implementation.py`:

- `--stage-only` — create bundle + validate; no apply/commit
- `--apply-staged PATH` — copy GO bundle files to working tree before tests/commit
- `--require-staged-validation` — block commit unless latest bundle for draft is GO
- Honors `RGE_REQUIRE_TIER2_PATCH_STAGING=1` as implicit require-staged

## Operator loop behavior

Priority (after circuit breaker / dirty-tree / verify blockers):

1. **fix_tier2_patch_staging** — PARTIAL/NO-GO bundle → blocked or review_gated
2. **run_tier2_patch_validation** — bundle exists, validation pending
3. **run_tier2_local_implementation** — GO bundle → apply-staged + commit flow
4. **run_tier2_patch_staging** — draft exists, no bundle yet
5. Existing Tier 2 continue / start / batch candidate recommendations

## Release batch / governor integration

- `release_batch_assembler.py` adds `candidate_metadata.patch_staging` via `patch_staging_metadata_for_batch()`
- `release_governor.py` check `tier2_patch_staging` blocks Tier 2 branches when `RGE_REQUIRE_TIER2_PATCH_STAGING=1` and validation is not GO
- `inspect_release_governor_plan_status()` surfaces patch staging recommendation flags

## Tests run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_tier2_patch_staging.py -q
python -m pytest tests/unit/test_tier2_local_implementation.py -q
python -m pytest tests/unit/test_operator_loop_release_batch_candidate.py -q
python -m pytest tests/unit/test_release_governor.py -q
```

**Result:** 74 related unit tests passed (23 new patch staging tests).

## Safety audit

```powershell
python -m rge.modules.safety_auditor --audit full
```

**Result:** pass (2026-06-22T18:40:22Z). Public-site build skipped — no public-site frontend behavior changed.

## What remains blocked

- Push, merge, publish, canonical ticket promotion (unchanged)
- Paid / live network API calls (unchanged)
- Commit without GO staged validation when `RGE_REQUIRE_TIER2_PATCH_STAGING=1`
- Apply/commit on PARTIAL or NO-GO bundles
- Circuit breaker open, unsafe dirty tree, failed verify/safety (unchanged)

## Next recommended packets

1. **Tier 2 staged patch → Atlas operator preview** — surface latest bundle verdict/risk in atlas release governor panel
2. **Autocycle execute-safe patch staging hook** — optional one-shot stage+validate in execute-safe when controlled dirty paths include implementation files
3. **Instruction packet → auto expected_files inference** — reduce PARTIAL verdicts from path-scope mismatches

## Files touched

- `rge/modules/tier2_patch_staging.py` (new)
- `rge/modules/tier2_local_implementation.py`
- `rge/modules/operator_loop.py`
- `rge/modules/operator_autocycle.py`
- `rge/modules/release_batch_assembler.py`
- `rge/modules/release_governor.py`
- `scripts/run_tier2_patch_staging.py` (new)
- `tests/unit/test_tier2_patch_staging.py` (new)
- `tests/unit/test_tier2_local_implementation.py`
- `tests/unit/test_operator_loop_release_batch_candidate.py`
- `.env.example`
