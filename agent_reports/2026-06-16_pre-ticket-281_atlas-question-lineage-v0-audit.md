---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-281
category: Phase 3 / Research Atlas / question lineage
---

# Pre-Ticket Audit: ticket-281 Atlas Snapshot Runs Question Lineage v0

## Verdict: **GO** (runs[] projection only — no schema migration)

Extends atlas `runs[]` entries with optional lineage fields sourced from existing
`research_contracts`, `research_queue`, and `cluster_reports` rows. No new tables,
no public export route changes, no public-site edits.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | Lineage uses opaque IDs; private-field scanner allowlists lineage keys |
| Public site | **No** | None |
| Schema migrations | **No** | None |
| Theory / inference | **No** | No theory writes |
| Live Ollama | **No** | Fixture MVP DB only |

## Hardened scope

### In scope

1. Optional lineage fields on `runs[]` in `atlas_snapshot_builder.py`
2. Lineage key constants in `atlas_snapshot_v0.py`
3. Updated creativity fixture + builder tests
4. Inventory gap note: partial closure (projection only)

### Out of scope

- `research_questions` table migration
- Public atlas export CLI
- UI work

## Safety

- `spawned_from_claim_ids` allowed as lineage key leaf (not raw claim text)
- Values are opaque IDs only; no prompt/source leakage
- Fail-closed private-field scan preserved for all other keys

## Recommendation

**GO** — implement runs lineage projection and regenerate fixture.
