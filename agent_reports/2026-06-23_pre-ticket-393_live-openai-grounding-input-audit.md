---
template_id: pre_ticket_audit
status: GO
date: 2026-06-23
risk_level: medium
ticket: ticket-393
category: Phase 3 / cloud synthesis
---

# Pre-Ticket Audit: ticket-393 Hydrate live OpenAI synthesis grounding input

## Verdict: **GO** (mock-first defaults preserved; no accepted-graph writes; injected-HTTP tests only)

Hydrate OpenAI synthesis request bodies with public-safe grounded text already present in
v0.2.0 packets; tighten prompt instructions; normalize `source_refs` on parse. Does not
loosen `synthesis_grounding` thresholds or enable live HTTP in default pytest/verify.

**Cadence note:** three `done` tickets since `agent_reports/2026-06-23_principal-audit-post-ticket-389.md`
(390–392). This pre-ticket audit includes mock-only verification below and resets
implementation gate for ticket-393 only; follow-on principal audit post-393 recommended after merge.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | No export-public or card_exporter changes |
| Public site | **No** | No `apps/public-site/**` changes |
| Schema migrations | **No** | No SQL migrations |
| Theory / inference | **No** | Synthesis candidate output only |
| Live Ollama | **No** | Cloud OpenAI path; mock-first unchanged |
| Live OpenAI default | **Controlled** | Live HTTP remains gated; tests use injected urlopen |

## Hardened scope

### In scope

1. **`OpenAISynthesisClient._build_request_body`**
   - Include `claim_text`, `stance`, `scope`, `limitations`, atom `canonical_text`, and
     public-safe `source_refs` metadata from v0.2.0 packets.

2. **System prompt**
   - Require citing provided IDs and reusing significant wording from grounded text.

3. **`_parse_candidate_output`**
   - Normalize `source_refs` objects → `source_id` strings; reject unresolvable citations.

4. **Tests**
   - Request-body contract assertions on injected HTTP.
   - End-to-end `run_synthesis_packet` with grounded fixture → `grounding_passed`,
     `governor_verdict: GO`, `no_accepted_graph_writes: true`.

### Out of scope

- Loosening `min_overlap` or bypassing `synthesis_grounding`
- Live OpenAI in default pytest/golden/verify/execute-safe
- Accepted graph writes from model output
- Public-site JSON publish
- Evaluator artifact / operator_loop surfacing (393–397 follow-ons)

## Safety checklist

| Risk | Control |
|------|---------|
| Raw source text in HTTP payload | Only packet fields already validated as operator-safe grounded text |
| Secrets in logs/artifacts | No API key logging; existing `_private_value_violations` on run result |
| Model → accepted graph | `no_accepted_graph_writes: true` unchanged |
| Live HTTP in CI | Injected urlopen only in unit tests |

## Verification baseline (main pre-branch)

| Command | Expected |
|---------|----------|
| `pytest tests/golden -q` | pass (mock) |
| `pytest tests/unit/test_openai_synthesis_adapter_contract.py -q` | pass |

## Implementation test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_openai_synthesis_adapter_contract.py tests/unit/test_synthesis_packet_runner.py -q
python -m pytest tests/golden -q
python -m rge.cli verify --skip-site
```
