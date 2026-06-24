---
template_id: pre_ticket_audit
status: GO
date: 2026-06-24
risk_level: medium
ticket: ticket-400
category: Phase 3 / operator loop
---

# Pre-Ticket Audit: ticket-400 Execute-safe mock OpenAI synthesis evaluator seed hook

## Verdict: **GO** (mock-only execute-safe hook; no live HTTP)

Seed gitignored `openai_synthesis_evaluator_latest.json` from existing canary JSON or
mock-cloud `synthesize --packet` when plan recommends mock evaluate, mirroring
`synthesis_packet_benchmark` execute-safe hook patterns.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | Gitignored operator artifacts only |
| Public site | **No** | No site changes |
| Schema migrations | **No** | No SQL |
| Live OpenAI in tests | **No** | `mock_cloud` synthesis + deterministic evaluator only |
| Operator loop automation | **Yes (scoped)** | Hook runs only after execute-safe verification passes and `action_id == run_openai_synthesis_evaluator`; never live HTTP |

## Hardened scope

### In scope

1. `run_openai_synthesis_evaluator_execute_safe_hook()` in `openai_synthesis_evaluator.py`
2. `execute_safe_checks` wiring when recommended action is mock evaluate (post-verify pass)
3. Input resolution: prefer `data/tmp/openai_synthesis_canary/...json`; else mock-cloud synthesize from grounded fixture
4. Replan `openai_synthesis_evaluator_status` + `next_recommended_action` after successful seed
5. Unit tests: seed path, skip when artifact present, skip when not recommended; no host `OPENAI_API_KEY`

### Out of scope

- Live OpenAI HTTP or `--load-operator-env` in execute-safe
- Autocycle auto-execution of live canary
- Draft ticket bridge or queue promotion
- Accepted graph / DB writes

## Safety checklist

| Risk | Control |
|------|---------|
| Live HTTP from execute-safe | `provider="mock_cloud"` only for synthesis fallback; evaluator is read-only Python |
| Secrets in artifacts | Existing `write_evaluator_artifact` + private-field policy |
| Graph writes | Synthesis runner sets `no_accepted_graph_writes: true`; evaluator does not persist graph |
| Autocycle bypass | `run_openai_synthesis_evaluator` not in autocycle safe-autonomous execute list without medium flag |

## Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_openai_synthesis_evaluator_operator_plan.py tests/unit/test_operator_loop.py -q
python -m rge.cli verify --skip-site
```

## Principal checkpoint

Cadence **satisfied** (ticket-398 principal audit 2026-06-24). Medium-risk ticket requires this pre-ticket audit before implementation.
