---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-073: Operator loop evidence review readiness action hint

- Date: 2026-06-13
- Branch: `phase-2/ticket-073-operator-loop-evidence-review-action`
- Baseline HEAD: `82c9781` (ticket-072 docs follow-up on main)
- Risk level: low

## Summary

When reviewed scratch rows exist and no higher-priority blocker applies,
`operator_loop --mode plan` now recommends `run_scratch_evidence_review`
(review_gated) with suggested `probe-scratch-evidence-review` commands.
Open queue tickets, improvement drafts, drift, dirty tree, and audit overdue
still take precedence.

## Audit gate

- Principal cadence: satisfied (2 done tickets since post-ticket-070; threshold 3)
- Pre-ticket audit: not required (`risk_level: low`)
- Gate check: `python -m rge.modules.principal_audit_gate --next-ticket ticket-073` → satisfied

## Scope

**In:** `_action_from_state()` evidence-review branch; runbook note; unit tests.

**Out:** No auto evidence review generation, no DB writes, no execute-safe runs.

## Files changed

| File | Change |
| ---- | ------ |
| `rge/modules/operator_loop.py` | `run_scratch_evidence_review` action when ready |
| `tests/unit/test_operator_loop.py` | 4 new unit tests |
| `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` | Plan-mode action hint section |
| `tickets/ticket-073.json`, `TICKET_QUEUE.md` | Done + ticket-074 seed |

## Acceptance criteria

| Criterion | Status |
| --------- | ------ |
| Evidence ready + not blocked → review_gated evidence review action | **pass** |
| Higher-priority blockers take precedence | **pass** |
| No scratch/graph writes or auto generation from plan | **pass** |
| Unit tests cover ready and not-ready selection | **pass** |

## Verification

| Command | Result |
| ------- | ------ |
| `pytest tests/unit/test_operator_loop.py -q` | **34 passed** |
| `pytest tests/golden -q` | **140 passed** |
| `pytest -q` | **326 passed**, 6 deselected |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |

## Manual CLI verification

Pre-run probe (user request):

```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m rge.cli probe-scratch-evidence-review --allow-empty --format json
python -m rge.cli probe-scratch-evidence-review --allow-empty `
  --out agent_reports/2026-06-13_scratch-evidence-review-probe.md
```

Scratch DB absent → zero-state review with `scratch_db_missing: true`.
Note: default markdown to stdout on Windows cp1252 consoles may fail on Unicode
arrow (`→`); use `--format json`, `--out`, or `PYTHONIOENCODING=utf-8`.

## Merge

- Implementation SHA: `568b246`
- Merge commit SHA: `a4c1589`
- Golden Gate run: `27467837127` (passed)

## Recommended next ticket

**ticket-074 (proposed)** — Windows-safe UTF-8 stdout for probe-scratch-evidence-review markdown.

## Suggested next prompt

Populate scratch DB via live probe persist workflow, re-run plan mode to see
`run_scratch_evidence_review`, or implement ticket-074 for Windows console encoding.
