---
template_id: pre_ticket_audit
status: GO
date: 2026-06-24
risk_level: medium
ticket: ticket-395
category: Phase 3 / self-improvement
---

# Pre-Ticket Audit: ticket-395 Evaluator instruction-packet draft bridge

## Verdict: **GO** (gitignored draft handoff only; no queue promotion; no code execution)

Bridge public-safe OpenAI synthesis evaluator artifacts into governor-style instruction
packets and existing `instruction_packet_ticket_draft` validation/writes. Draft tickets
remain under `data/operator/draft_tickets/` only.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | No export-public changes |
| Public site | **No** | No site changes |
| Schema migrations | **No** | No SQL |
| Theory / inference | **No** | Evaluator remediation text only |
| Live OpenAI in tests | **No** | Fixture evaluator JSON |

## Hardened scope

### In scope

1. **`openai_synthesis_evaluator.py`**
   - Build/write evaluator instruction packet markdown
   - `bridge_evaluator_to_instruction_draft()` orchestration

2. **`instruction_packet_ticket_draft.py`**
   - Evaluator-source validation path (allows PARTIAL/NO-GO; reuses content policy)
   - Draft payload enrichment from evaluator remediation

3. **`autonomous_synthesis_governor.py`**
   - Operator command cross-link for evaluator bridge

4. **Scripts**
   - `run_openai_synthesis_evaluator.py` bridge flags
   - `run_autonomous_synthesis_governor.py` help cross-link if needed

5. **Tests**
   - `test_instruction_packet_ticket_draft_handoff.py` evaluator bridge cases
   - Existing evaluator/governor tests remain green

### Out of scope

- Operator loop surfacing (396)
- Auto-promote to `tickets/` or `TICKET_QUEUE.md`
- Live HTTP
- self_improvement_status wiring (unless read-only import unavoidable)

## Safety checklist

| Risk | Control |
|------|---------|
| Auto-promote tickets | Draft dir only; `forbidden_actions` includes `edit_TICKET_QUEUE` |
| Secrets in drafts | `assert_no_private_fields` + `_content_policy_violations` |
| Model writes code | Instruction packet is markdown only; no shell/git automation |
| GO over-automation | GO defaults to instruction packet only; draft opt-in |

## Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_openai_synthesis_evaluator.py tests/unit/test_autonomous_synthesis_governor.py tests/unit/test_instruction_packet_ticket_draft_handoff.py -q
python -m pytest tests/unit/test_self_improvement_status.py -q
python -m rge.modules.safety_auditor --audit full
python -m rge.cli verify --skip-site
```
