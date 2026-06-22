# Agent Report: Autonomous Release Governor + Batch Promotion Policy

**Date:** 2026-06-22  
**Packet:** Autonomous Release Governor + Batch Promotion Policy  
**Verdict:** GO

## Summary

Added a tiered autonomy policy and deterministic release governor that gates push, merge, publish, and canonical ticket promotion behind batch evaluation, circuit-breaker state, safety audit, verify, and explicit env tier flags. Mainline changes remain blocked until release governor returns GO.

## Autonomy tiers implemented

| Tier | Name | Default | Env flag |
|------|------|---------|----------|
| 0 | read_only | | always available |
| 1 | draft_autonomy | **default** | none |
| 2 | branch_autonomy | | `RGE_ALLOW_BRANCH_AUTONOMY=1` + `RGE_AUTONOMY_TIER>=2` |
| 3 | feature_branch_push | | `RGE_ALLOW_FEATURE_BRANCH_PUSH=1` + tier >= 3 |
| 4 | batch_mainline | | `RGE_ALLOW_BATCH_MERGE=1` + tier >= 4 |
| 5 | publish_autonomy | | `RGE_ALLOW_PUBLISH_AUTONOMY=1` + tier >= 5 |

**Default tier:** 1 (`RGE_AUTONOMY_TIER=1`)

## Allowed and forbidden actions (effective tier 1)

**Allowed:** instruction packets, draft tickets, Atlas refresh, operator reports, release governor inspect/dry-run, batch report generation.

**Forbidden:** push, merge, publish, canonical ticket promotion, branch creation (until tier 2+).

## Release governor checks

Before push/merge/publish/promote:

- Working tree clean (or controlled dirty flag in batch)
- Unsafe dirty paths rejected
- Safety audit pass (when enabled)
- Verify pass (when enabled; skip-site when no public artifact changes)
- Agent report markdown + latest JSON present
- Circuit breaker closed
- No PARTIAL/NO-GO synthesis ledger reviews
- No forbidden synthesis instruction language
- Rollback plan present
- Batch size within `RGE_RELEASE_BATCH_MAX_ITEMS`
- Changed-file allowlist respected
- Batch test_results.passed and safety_results.status pass

Failed irreversible attempts advance the autonomy circuit breaker.

## Batch queue behavior

- Path: `data/operator/release_batches/*.json`
- Schema: `release_batch_v0.1.0` with draft ids, instruction refs, branches, commits, test/safety results, reports, rollback plan, changed files
- Promotion path: draft → `data/operator/canonical_ticket_candidates/` (not `TICKET_QUEUE.md`) → batch → release governor → tier-gated push/merge/publish
- Status report: `data/operator/release_governor_report_latest.json`
- Audit log: `data/operator/release_governor_audit.jsonl`

## CLI commands

```powershell
python scripts/run_release_governor.py --inspect
python scripts/run_release_governor.py --candidate data/operator/release_batches/BATCH_ID.json --dry-run
python scripts/run_release_governor.py --candidate PATH --promote-tickets --confirm
python scripts/run_release_governor.py --candidate PATH --push-branches --confirm
python scripts/run_release_governor.py --candidate PATH --merge-batch --confirm
python scripts/run_release_governor.py --candidate PATH --publish --confirm
```

Irreversible commands require GO verdict, matching autonomy tier, and `--confirm`. Git push/merge/publish commands are recommended but not auto-executed.

## Operator loop behavior

New recommendations (after higher-priority blockers):

1. `create_implementation_branch` — draft ticket, no feature branch, tier 2+
2. `create_release_batch_candidate` — branch exists, no batch
3. `run_release_governor_dry_run` — batch exists (safe_autonomous)
4. `run_release_governor_push/merge/publish` — dry-run GO + tier (review_gated)

Execute-safe refreshes release governor status; runs lightweight dry-run evaluation when recommended. Does not push, merge, publish, reset breaker, or call paid APIs.

## Files added/changed

| File | Change |
|------|--------|
| `rge/modules/autonomy_tier_policy.py` | Tier 0–5 policy |
| `rge/modules/release_governor.py` | Batch evaluation, CLI, plan status |
| `scripts/run_release_governor.py` | Standalone CLI |
| `rge/modules/operator_loop.py` | Release recommendations + execute-safe refresh |
| `rge/modules/operator_autocycle.py` | Safe/blocked action sets |
| `.env.example` | Autonomy tier env documentation |
| `tests/unit/test_release_governor.py` | 19 acceptance tests |

## Tests run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_release_governor.py -q
python -m pytest tests/unit/test_instruction_packet_ticket_draft_handoff.py -q
python -m rge.modules.safety_auditor --audit full
```

| Check | Result |
|-------|--------|
| Release governor tests (19) | PASS |
| Instruction packet handoff tests (18) | PASS |
| Safety audit full | PASS |

Public-site build not required — no public Atlas artifact surface changes in this packet.

## Safety audit result

**PASS**

## What is now autonomous (tier 1 default)

- Release governor inspect and dry-run
- Batch report generation
- Draft ticket and instruction packet flows (unchanged)
- Release status refresh in execute-safe

## What remains blocked

- Git push, merge, publish without tier env + GO + `--confirm`
- Canonical `TICKET_QUEUE.md` edits
- Direct writes to `tickets/` queue without governor GO + tier 4
- Circuit-breaker reset (human)
- Paid API calls in execute-safe
- Mainline merge/publish until full release governor GO at tier 4/5

## Next recommended packets

1. **Release batch assembler CLI** — build batch JSON from draft ticket + branch + test artifacts
2. **Operator autocycle execute-safe release dry-run hook** — mirror circuit-breaker refresh pattern
3. **Atlas operator visibility for release governor tier and batch status**
