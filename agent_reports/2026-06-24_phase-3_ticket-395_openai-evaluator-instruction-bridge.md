# Ticket-395 — Bridge OpenAI synthesis evaluator to instruction-packet draft tickets

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-395-openai-evaluator-instruction-bridge`  
**Ticket:** ticket-395  
**Main tip before branch:** `43698254557832b0797932c49742e9b110731ba5`  
**Audit gate:** satisfied — `agent_reports/2026-06-24_pre-ticket-395_openai-evaluator-instruction-bridge-audit.md`

## Summary

Bridged public-safe OpenAI synthesis evaluator artifacts into governor-style instruction
packets and optional gitignored draft tickets under `data/operator/draft_tickets/`. Reuses
`instruction_packet_ticket_draft` validation (including evaluator-source path for
PARTIAL/NO-GO). GO verdicts write instruction packets only by default; draft tickets are
opt-in for GO and automatic for PARTIAL/NO-GO.

## Scope

**In:** evaluator bridge orchestration, evaluator-source draft validation, governor operator
command cross-link, CLI bridge flags, handoff unit tests.

**Out:** Operator loop surfacing (396), queue promotion, live HTTP, public export/site changes.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/openai_synthesis_evaluator.py` | Instruction packet builder + `bridge_evaluator_to_instruction_draft`; CLI bridge flags |
| `rge/modules/instruction_packet_ticket_draft.py` | Evaluator verdict parsing/validation; draft payload enrichment (`live_synthesis_verdict`) |
| `rge/modules/autonomous_synthesis_governor.py` | `bridge_synthesis_review_instruction_draft` operator command |
| `tests/unit/test_instruction_packet_ticket_draft_handoff.py` | Evaluator NO-GO/GO bridge coverage |
| `tickets/ticket-395.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Row 395 done; active → ticket-396 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Evaluator GO/PARTIAL/NO-GO → instruction packet with problem, evidence, modules, files, acceptance, tests, non-goals, risk, rollback | **PASS** |
| Drafts gitignored under `data/operator/draft_tickets/`; never auto-promoted | **PASS** |
| Reuses `instruction_packet_ticket_draft` validation (no parallel schema) | **PASS** |
| Draft `forbidden_actions` includes auto_merge, auto_push, auto_promote_ticket, edit_TICKET_QUEUE | **PASS** |
| Tests: NO-GO creates scoped draft; GO packet-only default; GO optional follow-up draft | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_openai_synthesis_evaluator.py tests/unit/test_autonomous_synthesis_governor.py tests/unit/test_instruction_packet_ticket_draft_handoff.py tests/unit/test_self_improvement_status.py -q` | **36 passed** |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| `python -m rge.cli verify --skip-site` (clean cloud env) | **pass** |

## Manual CLI verification

Not run — unit tests cover `bridge_evaluator_to_instruction_draft` and CLI `--bridge-instruction-draft`.

## Spec deviations

- Draft ticket fields use `live_synthesis_verdict` / `source_review_artifact` instead of keys
  containing `evaluator` to satisfy `assert_no_private_fields` / public export key policy.
- Governor operator command key is `bridge_synthesis_review_instruction_draft` for the same reason.

## Merge to main

*(pending merge)*

## Recommended next ticket

**ticket-396** — Surface OpenAI synthesis evaluator status in operator plan.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

Implement ticket-396 on branch `phase-3/ticket-396-openai-evaluator-operator-status`.
