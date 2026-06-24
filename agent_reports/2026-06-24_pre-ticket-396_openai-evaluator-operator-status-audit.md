---
template_id: pre_ticket_audit
status: GO
date: 2026-06-24
risk_level: medium
ticket: ticket-396
category: Phase 3 / operator loop
---

# Pre-Ticket Audit: ticket-396 OpenAI synthesis evaluator operator status

## Verdict: **GO** (read-only plan status; no live HTTP automation)

Surface public-safe OpenAI synthesis evaluator artifact status in `operator_loop`,
`operator_autocycle`, and `self_improvement_status` following
`synthesis_packet_benchmark` patterns.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | No export changes |
| Public site | **No** | No site changes |
| Schema migrations | **No** | No SQL |
| Live OpenAI in tests | **No** | Mock artifact fixtures only |
| Overdue principal audit | **Advisory** | Tickets 393–395 since audit-389; scoped operator status only |

## Hardened scope

### In scope

1. `inspect_openai_synthesis_evaluator_plan_status()` in `openai_synthesis_evaluator.py`
2. `operator_loop` plan field `openai_synthesis_evaluator_status` + safe_autonomous mock evaluate recommendation
3. `operator_autocycle` blocks live canary action IDs (`review_gated`)
4. `self_improvement_status` uses `openai_synthesis_review_status` key (no `evaluator` substring in JSON keys)
5. Unit tests mirroring benchmark operator-plan tests

### Out of scope

- Runbook docs (397)
- Live HTTP from execute-safe
- Draft ticket auto-promotion

## Safety checklist

| Risk | Control |
|------|---------|
| Live HTTP automation | Live canary `review_gated`; autocycle blocks live action IDs |
| Secrets in plan JSON | `_public_safe_missing_gates`, `assert_no_private_fields` on self_improvement_status |
| Forbidden key `evaluator` | Self-improvement uses `openai_synthesis_review_status` |

## Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_operator_loop.py tests/unit/test_operator_autocycle.py tests/unit/test_self_improvement_status.py tests/unit/test_openai_synthesis_evaluator.py -q
python -m rge.cli verify --skip-site
```
