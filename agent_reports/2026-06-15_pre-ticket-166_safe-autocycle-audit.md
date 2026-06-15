---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-166
category: operator loop / workflow safety
---

# Pre-Ticket Audit: ticket-166 Safe Autocycle Command

## Verdict: **GO** (bounded planner only; **NO-GO** for blind 10-ticket autonomous execution)

## 1. `/rge-run-next-ticket` today

| Question | Answer |
|----------|--------|
| Real CLI command? | **No** — Cursor command / agent prompt workflow (`.cursor/commands/rge-run-next-ticket`) |
| Callable Python entry? | **No** — agents follow documented steps manually |
| Safe to fake full automation? | **No** |

## 2. What can be automated safely today

- `principal_audit_gate.checkpoint_status()` — machine-readable cadence + implementation gate
- `operator_loop.build_operator_plan()` — dirty tree, drift, recommended action
- `operator_loop.execute_safe_checks()` — mock golden + pytest + safety + optional site build
- Structured **plan** output with `next_command` pointing to `/rge-principal-audit` or `/rge-run-next-ticket`

## 3. What must remain human/agent-mediated

- Ticket implementation (code, tests, reports)
- Pre-ticket / principal audit authorship
- git merge, push, queue edits
- Medium/high risk tickets without explicit flags
- Live network / Ollama / cloud / browser tickets

## 4. Gate + drift surfaces

- `python -m rge.modules.principal_audit_gate --next-ticket <id>`
- `classify_ticket_value()` + `drift_warning` / `recommended_override` in gate payload
- `operator_loop.detect_documentation_git_drift()`

## 5. Docs-only streak detection

- `classify_ticket_value(next_title)` in `docs_corrective` / `docs_crosslink` / `checkpoint_only`
- Compare to last **done** ticket title in queue rows
- Stop unless `--allow-docs-streak`

## 6. Verification commands (execute-safe allowlist)

Reuse `operator_loop.safe_verification_commands()` — golden, full pytest, safety audit, optional site build.

## 7. Minimal safe implementation

New module `rge.modules.operator_autocycle`:

- `--mode plan` (read-only, default)
- `--mode execute-safe` (verification only when gate is `safe_autonomous`)
- `--max-cycles` default 1, cap 10
- `--allow-medium` / `--allow-high` for **planning eligibility only** (still stops before implementation)
- JSON: status, cycles_*, current_ticket, gate_status, audit_required, drift_warning, stop_reason, next_command

**Does not:** merge, push, edit queue, implement tickets.

## 8. Hard stop conditions (all 15)

Implemented as ordered checks in `evaluate_autocycle_cycle()`.

## 9. Expected files

- `rge/modules/operator_autocycle.py`
- `tests/unit/test_operator_autocycle.py`
- Reports only

## 10. Out of scope

- Autonomous merge/push
- Internal `/rge-run-next-ticket` runner
- Safety auditor semantic changes
- Principal gate filename sort fix (ticket-167+)

## Recommendation

**GO** — implement bounded autocycle planner/orchestrator; seed ticket-167 live staged fetch validation.
