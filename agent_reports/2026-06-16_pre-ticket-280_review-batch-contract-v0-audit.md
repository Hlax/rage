---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-280
category: Phase 3 / Agent Lab / product contract
---

# Pre-Ticket Audit: ticket-280 Agent Lab review_batch Contract v0

## Verdict: **GO** (private contract shape only — no persistence or public export)

ticket-280 defines `review_batch_v0.1.0` for principal larger-model review loops in the
**Agent Lab private layer**. No DB migrations, no public atlas export, no live Ollama wiring.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | `public_safe: false`, `classification: agent_lab_private` |
| Public site | **No** | None |
| Schema migrations | **No** | None |
| Theory / inference generation | **No** | Batch holds review metadata only; no theory writes |
| Live Ollama | **No** | Fixture uses `llm_mode: mock` |

## Hardened scope

### In scope

1. `rge/contracts/review_batch_v0.py` — pydantic contract + validator
2. `fixtures/agent_lab/review_batch_v0_minimal.json`
3. `tests/unit/test_review_batch_contract.py`
4. Inventory note update classifying contract as `agent_lab_private`

### Out of scope

- review_batch DB table or CLI persistence
- Stronger-model / cloud synthesis wiring
- Public atlas snapshot export changes

## Safety

- Contract defaults `public_safe: false` and `operator_only: true`
- No raw prompts or model responses in fixture
- Aligns with reporting spec `model_runtime` required fields

## Recommendation

**GO** — implement contract + tests; seed ticket-281 for review_batch persistence sketch.
