---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-039 Improvement-Ticket Round-Trip Readiness Audit

- Audit type: focused pre-ticket audit — self-improvement loop promotion with explicit review gate
- Date: 2026-06-12
- Agent/model: Cursor audit agent
- Scope: read-only audit of improvement-ticket generation, builder validation (GT21), queue conventions, and fixture orchestration before implementing ticket-039. No promotion logic implemented in this pass.

## Summary

Ticket-039 (validate improvement-ticket round-trip into the builder queue with review gate) is **safe to begin** with the hardened scope below. Generation and builder-consumption validation are real (`generate-improvement-tickets`, `validate_builder_ticket`, GT20/GT21), but **no promotion path exists**: draft tickets land in gitignored `data/tickets/` and SQLite `improvement_tickets` only. Fixture orchestration generates tickets but never writes `tickets/ticket-*.json` or edits `TICKET_QUEUE.md`. This audit also satisfies the **overdue principal-audit checkpoint** (three consecutive done tickets 036–038 since `pre-phase-2_principal-audit`).

**Recommendation: proceed with ticket-039 as an explicit `--confirm` promotion CLI + GT21 round-trip extension.**

## Repo / Main Status

| Check | Result |
|---|---|
| Branch | `main`, aligned with `origin/main` |
| Working tree | clean |
| Main tip | `51f02a5` |
| Consecutive done since principal audit | ticket-036, ticket-037, ticket-038 (3) — checkpoint overdue |
| ticket-039 JSON | exists, `proposed` |

## Ticket / Queue Status

| Ticket | Status | Notes |
|---|---|---|
| ticket-036–038 | done | Public polish, Ollama opt-in, live smoke gating |
| ticket-039 | proposed | Next implementation target |
| ticket-040+ | not seeded | CI merge gate per roadmap follows 039 |

## Current Improvement-Ticket Pipeline

### What exists and is verified

| Component | State |
|---|---|
| `rge/modules/ticket_writer.py` | Deterministic templates; `write_improvement_tickets`, `generate_improvement_tickets`, `validate_builder_ticket` |
| `rge/db/repositories.py` | `ImprovementTicketRepository`, idempotent insert per run+failure_reason |
| `research generate-improvement-tickets` | Persists drafts; writes `improvement_ticket_latest.json` |
| GT20 (`test_20_improvement_tickets.py`) | Rejection spine → draft tickets |
| GT21 (`test_21_builder_ticket_consumption.py`) | Builder field + vagueness validation |
| Fixture orchestration (`execute_fixture_mode_run`) | Calls `generate_improvement_tickets`; output under `data/tickets/` (gitignored) |

### What is missing (ticket-039 scope)

- No `promote-improvement-ticket` (or equivalent) CLI
- No `improvement_ticket → tickets/ticket-NNN.json` converter
- No explicit `--confirm` review gate
- No GT21 round-trip test proving queue JSON shape
- No documented promotion workflow in `11_AGENT_OPERATING_PROTOCOL.md`

### What must NOT happen

| Risk | Mitigation in hardened scope |
|---|---|
| Auto-insert into `TICKET_QUEUE.md` | CLI writes only `tickets/<id>.json`; human/agent edits queue separately |
| Implicit promotion during `run --fixture-mode` | Do not call promotion from orchestration or `generate_improvement_tickets` |
| Vague promoted tickets | Reuse `validate_builder_ticket` before write; fail closed |
| Overwrite existing queue JSON | Refuse if target file exists unless future ticket adds `--force` |

## Hardened Scope for Ticket-039

### In scope

1. **`promote_improvement_ticket()`** in `ticket_writer.py`:
   - Load source from `--from-json` **or** DB (`--run-id` + `--failure-reason` **or** `--improvement-ticket-id`)
   - Require `reviewed=True` (CLI `--confirm`)
   - Map to queue ticket shape: `id`, `title`, `problem`, `evidence`, `affected_modules`, `expected_files`, `acceptance_criteria`, `test_plan`, `non_goals`, `risk_level`, `rollback_plan`, `status: proposed`
   - Validate with `validate_builder_ticket` before write
   - Write `tickets/<queue-ticket-id>.json` (configurable `--output-dir` for tests)

2. **CLI** `research promote-improvement-ticket`:
   - Required: `--queue-ticket-id`, `--confirm`
   - Source: one of `--from-json`, (`--run-id` + `--failure-reason`), `--improvement-ticket-id`
   - Optional: `--db`, `--output-dir`
   - Machine-readable JSON stdout; non-zero exit on validation/confirm failures

3. **GT21 extension** in `test_21_builder_ticket_consumption.py`:
   - Round-trip: generate → promote to temp dir → assert queue JSON passes `validate_builder_ticket`
   - Assert promotion requires `--confirm`
   - Assert orchestration/generation paths do not call promotion

4. **Docs** `docs/agents/11_AGENT_OPERATING_PROTOCOL.md`:
   - Promotion workflow: generate → human/audit review → `promote-improvement-ticket --confirm` → manual `TICKET_QUEUE.md` row

5. **Scaffold** `test_00_scaffold.py`: help lists `promote-improvement-ticket`

### Out of scope (non-goals)

- CI workflow (ticket-040)
- Auto `TICKET_QUEUE.md` mutation
- Cloud providers, live discovery, public export changes

## Safety Boundaries

| Question | Answer |
|---|---|
| Does promotion touch public export/site? | **No** |
| Does promotion require Ollama? | **No** — mock-only golden path |
| Can model output write queue tickets? | **No** — Python validates; explicit `--confirm` required |
| Schema migration needed? | **No** |

## Test Plan (implementation)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden/test_21_builder_ticket_consumption.py
python -m pytest tests/golden
python -m pytest
python -m rge.modules.safety_auditor --audit full
```

Manual (temp DB):

```powershell
python -m rge.cli promote-improvement-ticket --help
# after generate-improvement-tickets on temp --db:
python -m rge.cli promote-improvement-ticket --queue-ticket-id ticket-991 --run-id <id> --failure-reason overgeneralized_scope --confirm --output-dir <tmp>/tickets --db <tmp>.sqlite
```

## Audit Gate Satisfaction

This report satisfies:

- ticket-039 `risk_level: medium` pre-ticket audit requirement
- Overdue principal checkpoint (≥3 done tickets since `agent_reports/2026-06-12_pre-phase-2_principal-audit.md`)

## Recommendation

**Proceed with ticket-039** on branch `phase-2/ticket-039-improvement-ticket-round-trip` using the hardened scope above.
