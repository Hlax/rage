---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-279
category: Phase 3 / Research Atlas / snapshot population
---

# Pre-Ticket Audit: ticket-279 Atlas Snapshot v0 Population from Fixture-Mode DB

## Verdict: **GO** (read-only DB projection — no new public export route)

ticket-279 projects accepted graph rows into `atlas_snapshot_v0.1.0` using the same
**curated public card** path as `card_exporter` (allowlisted fields only). No writes to
`apps/public-site`, no `export-public` CLI changes, no schema migrations.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export / card_exporter changes | **No** | Read-only reuse of curation helpers; no export file writes |
| Public site changes | **No** | None |
| Schema migrations | **No** | None |
| Theory / inference generation | **No** | Report summaries whitelist public fields only |
| Live Ollama | **No** | Fixture-mode MVP temp DB in tests |

## Hardened scope

### In scope

1. `rge/modules/atlas_snapshot_builder.py` — project cards, concept nodes, edges, runs
2. `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` — deterministic golden snapshot
3. `tests/unit/test_atlas_snapshot_builder.py` — fixture MVP DB + leak checks

### Out of scope

- Atlas snapshot CLI or auto-publish
- `review_batch` / Agent Lab export
- Domain link normalization tables
- Images / `media_assets`
- Raw claim text or `claim_id` in snapshot nodes/edges

## Safety

- Cards pass `validate_public_card` + `curated_public_card`
- Snapshot tree scanned for forbidden export key substrings
- Cluster/report projections omit `evidence_packet` and private envelopes

## Recommendation

**GO** — implement builder + tests; seed ticket-280 for optional atlas export CLI.
