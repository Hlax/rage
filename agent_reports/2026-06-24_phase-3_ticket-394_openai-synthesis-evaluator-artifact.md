# Ticket-394 — Add deterministic live OpenAI synthesis evaluator artifact

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-394-openai-synthesis-evaluator`  
**Ticket:** ticket-394  
**Main tip before branch:** `11e8d67b8a2122f2f25cc94c356f201ba621d78b`  
**Audit gate:** satisfied — `agent_reports/2026-06-24_pre-ticket-394_openai-synthesis-evaluator-audit.md`

## Summary

Added a read-only deterministic evaluator for synthesis packet run and candidate synthesis
output JSON. Reuses `synthesis_grounding`, `synthesis_review_threshold_policy`, and
`autonomous_synthesis_governor` without live HTTP. Writes public-safe gitignored operator
artifact with `evaluator_verdict`, remediation suggestions, and gate summaries.

## Scope

**In:** `openai_synthesis_evaluator.py`, operator script, governor artifact resolver helper,
unit tests, README Operator Quickstart section.

**Out:** Operator loop surfacing (396), instruction-packet bridge (395), live HTTP in tests.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/openai_synthesis_evaluator.py` | Evaluator module + artifact writer |
| `rge/modules/autonomous_synthesis_governor.py` | `resolve_synthesis_packet_run_artifact` |
| `scripts/run_openai_synthesis_evaluator.py` | Operator wrapper |
| `tests/unit/test_openai_synthesis_evaluator.py` | GO / PARTIAL / NO-GO coverage |
| `README.md` | Live OpenAI synthesis evaluator quickstart |
| `tickets/ticket-394.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Row 394 done; active → ticket-395 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Deterministic evaluator reads synthesis output without network | **PASS** |
| Output includes provider, model, packet_id, usage, grounding, governor, verdict | **PASS** |
| Remediation suggestions reference modules/scope without secrets | **PASS** |
| Private-field policy blocks unsafe artifact content | **PASS** |
| Unit tests cover GO/PARTIAL/NO-GO without OPENAI_API_KEY | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_openai_synthesis_evaluator.py -q` | **6 passed** |
| `pytest tests/unit/test_autonomous_synthesis_governor.py -q` | **3 passed** |
| `pytest tests/golden -q` | **165 passed** |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |

## Manual CLI verification

Not run — injected-HTTP + fixture unit coverage satisfies ticket test plan.

## Spec deviations

None.

## Merge to main

Merge commit: _(record after merge)_.

## Recommended next ticket

**ticket-395** — Bridge OpenAI synthesis evaluator suggestions to instruction-packet draft tickets.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

Implement ticket-395 on branch `phase-3/ticket-395-openai-evaluator-instruction-bridge`.
