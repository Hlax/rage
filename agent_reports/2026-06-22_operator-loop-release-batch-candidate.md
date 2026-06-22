# Agent Report — Operator loop release batch candidate + golden gate

**Date:** 2026-06-22  
**Verdict:** **GO**

## Summary

Closed the gap between draft tickets and release-governor dry runs by wiring operator loop plan recommendations, batch assembly dirty-tree guards, candidate metadata, and Atlas golden/static-render coverage for the release governor panel.

## Operator loop behavior

Plan mode (`build_operator_plan`) now:

- Detects the latest draft ticket under `data/operator/draft_tickets/`.
- When no batch exists for that draft id, recommends `create_release_batch_candidate` with:
  `python scripts/run_release_batch_assembler.py --latest`
- When a batch exists for the draft, recommends `run_release_governor_dry_run`.
- Circuit breaker open (`run_circuit_breaker_inspection`) keeps higher priority.
- Unsafe or non-operator dirty paths block with `resolve_unsafe_working_tree` before batch actions.
- Controlled dirty paths under `agent_reports/`, `data/operator/`, etc. allow batch recommendations.
- Documentation drift and other higher-priority blockers unchanged.

`inspect_release_governor_plan_status` accepts an optional `working_tree` so plan recommendations and release status stay aligned in tests and operator surfaces.

## Batch candidate behavior

`release_batch_assembler.py` now:

- Refuses assembly when unsafe dirty paths or non-operator dirty paths are present (unless `--allow-controlled-dirty`).
- Filters forbidden changed files (`.env.local`, `data/sources/`, etc.).
- Writes `candidate_metadata` with draft path, instruction packet path, branch, commit, changed files, reports, rollback plan, test/safety status, and next-action tier hints.
- Never writes to `tickets/TICKET_QUEUE.md` or canonical queue.

## Dirty-tree guard behavior

| State | Plan recommendation | Batch assembly |
|-------|---------------------|----------------|
| Clean | Allowed | Allowed |
| Controlled dirty (operator artifacts only) | Allowed | Allowed |
| Unsafe dirty (`rge/`, `.env`, etc.) | Blocked | Blocked |
| Non-operator dirty | Blocked | Blocked |

Execute-safe still requires a fully clean tree.

## Atlas golden gate coverage

- Extended `tests/golden/test_12_public_site_static_render.py` for release governor panel source + static HTML assertions (autonomy tier, batch status, governor verdict, next release action).
- Atlas preview page shows **Next release action** and **Blocked reasons** when present.
- `atlas_release_governor_latest.json` added to safety auditor `ATLAS_PREVIEW_PUBLIC_DATA_FILES`.

## Verification

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_operator_loop_release_batch_candidate.py tests/unit/test_release_batch_assembler.py tests/unit/test_release_governor.py tests/unit/test_safety_auditor_atlas_preview.py tests/golden/test_12_public_site_static_render.py -q` | **57 passed** |
| `python -m rge.modules.safety_auditor --audit full` | **pass** (includes `atlas_release_governor_latest.json`) |
| `cd apps/public-site && npm run build` | **pass** |

## Tier-gated (unchanged)

Push, merge, publish, and canonical ticket promotion remain tier-gated and require explicit `--confirm`. Execute-safe never performs them.

## Suggested next packets

1. Auto-attach execute-safe verification results to `release_batch_test_results_latest.json` before batch assembly.
2. Operator autocycle summary row for `next_release_action` + batch assembly block reasons.
3. Golden test fixture sync for committed `atlas_release_governor_latest.json` after real operator dry-run.
