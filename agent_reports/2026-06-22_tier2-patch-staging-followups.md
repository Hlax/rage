# Tier 2 Patch Staging Follow-ups (Execute-Safe Hook, Auto Preview Sync, Expected Files Inference)

**Date:** 2026-06-22  
**Verdict:** GO  
**Phase:** Autonomy / Tier 2 operator loop hardening

## Summary

Implemented three follow-up packets from the Tier 2 patch staging + Atlas preview work:

1. **Execute-safe patch staging hook** — opt-in stage/validate/preview refresh after mock verification pass
2. **Auto-sync Atlas preview** — refresh `atlas_tier2_patch_staging_latest.json` when bundles complete with GO/PARTIAL/NO-GO
3. **Instruction packet expected_files inference** — expand draft `expected_files` with companion tests and backtick paths to reduce path-scope PARTIAL verdicts

## 1. Execute-safe patch staging hook

**Env:** `RGE_EXECUTE_SAFE_PATCH_STAGING=0` (default off)

When enabled and Tier 2 branch autonomy is available:

- `execute-safe` may run on a **clean** tree or **Tier-2-controlled-dirty** tree (`rge/`, `tests/`, `scripts/`, etc.)
- After verification pass, `run_execute_safe_patch_staging_hook()` runs:
  - **stage** (if draft + working-tree changes exist)
  - **validate** latest bundle
  - **preview_refresh** → `atlas_tier2_patch_staging_latest.json`
- Results surface on plan/autocycle as `tier2_patch_staging_execute_safe_hook`

## 2. Auto-sync preview after bundle write

**Env:** `RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW=1` (default on)

`create_patch_bundle_from_working_tree()` calls `_maybe_sync_patch_staging_preview()` when validation verdict is GO, PARTIAL, or NO-GO — keeping Atlas preview aligned with the latest bundle without a separate refresh step.

## 3. Expected files inference

`infer_expected_files()` in `instruction_packet_ticket_draft.py`:

- Starts from packet **Files likely affected** bullets
- Extracts backtick paths from summary/build title
- Parses test commands for `tests/*.py` / `rge/*.py` paths
- Adds companion `tests/unit/test_<module>.py` when a matching test file exists (or a default companion path otherwise)

Draft tickets now include `expected_files_inferred: true`.

## Operator loop changes

- `_execute_safe_working_tree_eligible()` allows controlled Tier-2 implementation dirty paths when execute-safe patch hook env is set
- `execute_safe_checks()` attaches hook results after release governor dry-run refresh
- Autocycle cycle summaries include `tier2_patch_staging_execute_safe_hook`

## Tests run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_tier2_patch_staging_followups.py -q
python -m pytest tests/unit/test_tier2_patch_staging.py tests/unit/test_tier2_patch_staging_preview.py -q
python -m pytest tests/unit/test_instruction_packet_ticket_draft_handoff.py -q
```

**Result:** 44+ related unit tests passed (10 new follow-up tests).

## Safety audit

```powershell
python -m rge.modules.safety_auditor --audit full
```

**Result:** pass (2026-06-22T19:11:15Z)

## Public-site build

Not required — no `/atlas-preview` or public artifact schema changes in this packet.

## What remains blocked

- Push, merge, publish, canonical promotion (unchanged)
- Execute-safe hook off by default (`RGE_EXECUTE_SAFE_PATCH_STAGING=0`)
- Hook never applies patches or commits — stage/validate/preview only

## Next recommended packets

1. **Wire auto-sync into patch validate-only CLI path** — refresh preview after `--validate` re-runs gates
2. **Atlas panel freshness badge styling** — highlight stale preview in `/atlas-preview`
3. **Draft ticket backfill command** — re-infer `expected_files` for existing drafts without re-handoff

## Files touched

- `rge/modules/tier2_patch_staging.py`
- `rge/modules/instruction_packet_ticket_draft.py`
- `rge/modules/operator_loop.py`
- `rge/modules/operator_autocycle.py`
- `.env.example`
- `tests/unit/test_tier2_patch_staging_followups.py` (new)
- `tests/unit/test_tier2_patch_staging.py`
- `tests/unit/test_instruction_packet_ticket_draft_handoff.py`
