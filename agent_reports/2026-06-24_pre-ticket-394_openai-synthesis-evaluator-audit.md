---
template_id: pre_ticket_audit
status: GO
date: 2026-06-24
risk_level: medium
ticket: ticket-394
category: Phase 3 / cloud synthesis
---

# Pre-Ticket Audit: ticket-394 OpenAI synthesis evaluator artifact

## Verdict: **GO** (read-only artifact over synthesis output JSON; no live HTTP; no graph writes)

Deterministic evaluator reads `synthesis_packet_run` or candidate synthesis output JSON,
reuses `synthesis_grounding`, `synthesis_review_threshold_policy`, and
`autonomous_synthesis_governor` checks, and writes a public-safe gitignored operator artifact.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | Read-only; no export-public changes |
| Public site | **No** | No site changes |
| Schema migrations | **No** | No SQL |
| Theory / inference | **No** | Evaluates existing candidate output only |
| Live Ollama / OpenAI in tests | **No** | Fixture JSON only |

## Hardened scope

### In scope

- `rge/modules/openai_synthesis_evaluator.py` — load artifact, evaluate, write artifact
- `scripts/run_openai_synthesis_evaluator.py` — operator wrapper
- Minimal `resolve_synthesis_packet_run_artifact` helper in `autonomous_synthesis_governor.py`
- Unit tests: GO / PARTIAL / NO-GO fixtures
- README Operator Quickstart section

### Out of scope

- Operator loop surfacing (ticket-396)
- Instruction-packet draft bridge (ticket-395)
- Live HTTP from evaluator
- Auto-promote to tickets/

## Safety checklist

| Risk | Control |
|------|---------|
| Secrets in artifact | `_private_value_violations`; remap credential gate keys |
| Live HTTP | Evaluator makes no network calls |
| Graph writes | Read-only |
| Raw prompts / source text | Remediation references modules only |

## Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_openai_synthesis_evaluator.py -q
python -m pytest tests/unit/test_autonomous_synthesis_governor.py -q
python -m rge.modules.safety_auditor --audit full
python -m rge.cli verify --skip-site
```
