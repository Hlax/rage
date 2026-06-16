---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-278
category: Phase 3 / Research Atlas export contract / product-risk
---

# Pre-Ticket Audit: ticket-278 Research Atlas Export Contract Inventory and Snapshot Schema v0

## Verdict: **GO** (contract + inventory only — no export wiring, no UI)

Operator direction supersedes narrow ticket-277 idempotency work. ticket-278 defines a
stable **public atlas snapshot** envelope and a deterministic repo inventory without
changing `export_public_cards` behavior or public-site routes.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export / card_exporter changes | **No** | No edits to `card_exporter.py` export path |
| Public site changes | **No** | Inventory documents readers only |
| Schema migrations | **No** | No SQL migrations |
| Theory / inference generation | **No** | Out of scope |
| Live Ollama | **No** | Mock tests only |

## Hardened scope

### In scope

1. `rge/contracts/atlas_snapshot_v0.py` — pydantic contract + fail-closed validator
2. `fixtures/atlas/atlas_snapshot_v0_minimal.json` — minimal tested fixture
3. `rge/modules/atlas_contract_inventory.py` — DB/schema/export/golden/gap inventory
4. `docs/contracts/research_atlas_export_contract_inventory_v0.md` (+ JSON sibling)
5. Unit tests in `tests/unit/test_atlas_snapshot_contract.py`

### Out of scope (explicit non-goals)

- Public atlas snapshot export CLI or DB population
- Public-site UI or routing changes
- `review_batch` / `synthesis_batch` implementation
- Domain link normalization tables
- Image/media_assets table
- ticket-277 module export idempotency (superseded)

## Safety

- Contract reserves `safety.public_safe` + `safety_audit_id`; no auto-publish
- Inventory classifies improvement tickets as `agent_lab_private`
- Existing fail-closed card export unchanged

## Recommendation

**GO** — implement contract + inventory report; seed follow-on tickets for atlas
export population and `review_batch` shape separately.
