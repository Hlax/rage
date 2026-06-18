---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-06-18
phase: 3
ticket: ticket-333
---

# Pre-Ticket Audit: ticket-333 — Autonomous loop quality-driven improvement ticket seeding v0

**Verdict: GO**

## Scope

Wire quality-evaluator weakest dimension → draft improvement ticket persistence when
standard `generate_improvement_tickets` suppresses golden-covered failure modes.
No schema migrations, no public export, no auto-promotion.

## Risk

| Area | Assessment |
|------|------------|
| Golden test 20 regression | **Low** — `write_improvement_tickets` unchanged; new path is autonomous-loop-only |
| Auto-promotion | **None** — draft status only; human `--confirm` still required |
| Public surface | **None** |

## Hardened scope

- Add `generate_quality_driven_improvement_tickets` in `ticket_writer.py`
- Call from `autonomous_researcher_loop.py` when standard tickets empty
- Extend unit test assertions for draft + failure_reason mapping
- Seed ticket-334 follow-on if new gap observed

## Out of scope

- Changing golden-covered suppression in default pipeline
- Live Ollama ticket drafting
- Queue auto-promotion
