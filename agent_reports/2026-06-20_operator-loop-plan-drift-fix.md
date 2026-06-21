# Agent Report: Operator Loop Plan Drift Fix

**Date:** 2026-06-20  
**Packet:** operator-loop-plan-drift-fix  
**Verdict:** GO

## Problem

`python -m rge.cli verify --skip-site` failed because plan mode recommended
`run_full_atlas_refresh_checklist` when only `atlas_source_health_run_latest.json`
was missing. The unit test expected `refresh_atlas_public_previews`.

## Decision

`run_full_atlas_refresh_checklist` should be recommended only when **both**:

1. Live abstract evidence operator work is detected in `agent_reports/`, and  
2. Source-health preview is stale or missing.

Missing source-health alone (without live abstract packet work) should continue
to recommend the staged single refresh + site build path
(`refresh_atlas_public_previews`).

Removed `operator_packet_validation != valid` as a trigger for full checklist in
plan mode — invalid packets are handled by the checklist runner itself, not plan
priority drift.

## Change

- `rge/modules/full_atlas_refresh_checklist.py` — narrowed
  `full_atlas_refresh_recommended` to `live_abstract_work and source_health_stale`.

## Verification

| Check | Result |
|-------|--------|
| `test_atlas_refresh_recommended_action_when_missing_source_health_artifact` | PASS |
| `python -m rge.cli verify --skip-site` | exit 0 |

## Next recommended packet

**one-button-research-run-v1**
