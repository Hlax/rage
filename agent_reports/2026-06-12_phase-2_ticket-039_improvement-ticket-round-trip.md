---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 2 / ticket-039 / improvement-ticket-round-trip

## 1. Summary

Validated the self-improvement loop round-trip by adding explicit promotion from draft improvement tickets to builder queue JSON. Implemented `promote_improvement_ticket()` with a mandatory `--confirm` review gate, `research promote-improvement-ticket` CLI, GT21 round-trip tests, and promotion workflow docs. Pipeline and generation paths do not auto-promote. All 132 golden tests and 143 total pytest pass without Ollama; safety audit passes.

## 2. Ticket

- Ticket ID: ticket-039
- Ticket title: Validate improvement-ticket round-trip into the builder queue with review gate
- Branch: `phase-2/ticket-039-improvement-ticket-round-trip`
- Phase: 2
- Agent/model: Cursor builder agent
- Date: 2026-06-12
- Main tip before branch: `bb4e817` (includes pre-ticket-039 audit commit)
- Audit gate satisfied by:
  - `agent_reports/2026-06-12_pre-ticket-039_improvement-ticket-round-trip-readiness-audit.md` (2026-06-12)
  - Overdue principal checkpoint (tickets 036–038 since pre-phase-2 audit)

## 3. Scope

### In Scope

- `improvement_ticket_to_queue_ticket()` and `promote_improvement_ticket()` in `ticket_writer.py`
- `research promote-improvement-ticket` CLI (`--confirm`, DB or `--from-json` sources)
- GT21 extension: round-trip, confirm gate, no auto-promotion in orchestration
- `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` promotion workflow
- Scaffold help lists `promote-improvement-ticket`

### Out of Scope / Non-goals

- Auto `TICKET_QUEUE.md` edits, CI workflow (ticket-040), cloud providers, public export changes

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/ticket_writer.py` | Queue ticket mapping, promotion with review gate, source loaders |
| `rge/cli.py` | `promote-improvement-ticket` subcommand |
| `tests/golden/test_21_builder_ticket_consumption.py` | +3 round-trip / gate tests (7 total) |
| `tests/golden/test_00_scaffold.py` | Help includes promote command |
| `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` | Documented promotion workflow |
| `tickets/ticket-039.json` | Status done |
| `tickets/ticket-040.json` | Seeded follow-on (proposed) |
| `tickets/TICKET_QUEUE.md` | ticket-039 done; ticket-040 proposed |

## 5. Implementation Notes

- Promotion writes `tickets/<queue-ticket-id>.json` only; refuses existing files and missing `--confirm`.
- Reuses `validate_builder_ticket` before write (GT21 rules).
- Sources: `--from-json` OR DB via `--improvement-ticket-id` OR (`--run-id` + `--failure-reason`).
- `generate_improvement_tickets` and `execute_fixture_mode_run` do not call promotion.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Promote to valid queue JSON via explicit reviewed step | PASS | CLI + module + GT21 round-trip |
| Promotion never implicit during pipeline runs | PASS | Source inspection test |
| Promoted format passes GT21 validation | PASS | `validate_builder_ticket` on output |
| Documented promotion workflow | PASS | `11_AGENT_OPERATING_PROTOCOL.md` |
| Golden + default pytest without Ollama | PASS | 132 golden, 143 total |

## 7. Commands Run and Results

| Command | Result |
|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_21_builder_ticket_consumption.py` | PASS — 7 passed |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS — 132 passed |
| `RGE_LLM_MODE=mock python -m pytest` | PASS — 143 passed, 1 deselected |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS |

## 8. Manual CLI Verification

- `promote-improvement-ticket --help` exposes `--confirm`, source flags, `--output-dir`.
- GT21 exercises promote via temp `--output-dir` after rejection spine.

## 9. Spec Deviations

None.

## 10. Merge to Main

- Merge commit: `96b35e7`
- Branch: `phase-2/ticket-039-improvement-ticket-round-trip` merged to `main` with `--no-ff`
- Post-merge pytest on `main`: PASS — 143 passed, 1 deselected

## 11. Recommended Next Ticket

**ticket-040**: Add CI golden gate workflow and `rge-principal-audit` command doc (Phase 2 roadmap).

## 12. Suggested Next Prompt

```
/rge-run-next-ticket
```

Implement only ticket-040 (CI golden gate + principal-audit command doc).
