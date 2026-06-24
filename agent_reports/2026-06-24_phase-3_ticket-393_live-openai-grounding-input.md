# Ticket-393 — Hydrate live OpenAI synthesis grounding input

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-393-live-openai-grounding-input`  
**Ticket:** ticket-393  
**Main tip before branch:** `ebc5a1bb030cde6383cf5f608122c9350eac7e04`  
**Audit gate:** satisfied — `agent_reports/2026-06-23_pre-ticket-393_live-openai-grounding-input-audit.md`

## Summary

Hydrated `OpenAISynthesisClient` live HTTP request bodies with public-safe grounded
`claim_text`, atom `canonical_text`, stance, scope, limitations, and source metadata from
v0.2.0 synthesis packets. Tightened the system prompt to require ID citations and significant
word reuse. Normalized provider `source_refs` objects to `source_id` strings on parse while
rejecting unresolvable citations. Injected-HTTP tests prove the grounded dry-run fixture can
reach `grounding_passed: true`, `governor_verdict: GO`, and `no_accepted_graph_writes: true`.

## Scope

**In:** `openai_synthesis_client.py` request hydration, citation normalization, unit tests.

**Out:** Grounding threshold changes, live HTTP in default pytest/CI, accepted graph writes,
public export, evaluator artifact (ticket-394).

## Changed files

| File | Change |
|------|--------|
| `rge/llm/openai_synthesis_client.py` | Grounding payload builder, prompt, source_ref normalization |
| `tests/unit/test_openai_synthesis_adapter_contract.py` | Request-body and parse contract tests |
| `tests/unit/test_synthesis_packet_runner.py` | End-to-end injected-HTTP governor GO test |
| `agent_reports/2026-06-23_pre-ticket-393_live-openai-grounding-input-audit.md` | Pre-ticket audit |
| `tickets/ticket-393.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Row 393 done; active → ticket-394 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Request body includes grounded claim/atom text, stance, scope, source metadata | **PASS** |
| Prompt requires citations and significant wording reuse | **PASS** |
| `source_refs` normalized to strings; unresolvable rejected | **PASS** |
| Injected-HTTP test: grounding_passed, governor GO, no_accepted_graph_writes | **PASS** |
| Mock-first defaults unchanged; no OPENAI_API_KEY in default pytest | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_openai_synthesis_adapter_contract.py tests/unit/test_synthesis_packet_runner.py -q` | **21 passed** |
| `pytest tests/golden -q` | **165 passed** |
| `python -m rge.cli verify --skip-site` | **pass** (1358 passed full pytest) |

## Manual CLI verification

Not run — optional operator live canary requires explicit gates and `--confirm`. Injected-HTTP
unit coverage satisfies ticket test plan.

## Spec deviations

None.

## Merge to main

Merge commit: _(record after merge)_.

## Recommended next ticket

**ticket-394** — Deterministic live OpenAI synthesis evaluator artifact.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

Implement ticket-394 on branch `phase-3/ticket-394-live-openai-synthesis-evaluator`.
