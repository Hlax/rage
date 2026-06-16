---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-294
category: Phase 3 / Research Atlas / live-derived population
---

# Pre-Ticket Audit: ticket-294 Evidence DB Run Lineage + Live-Derived Atlas Cards

## Verdict: **GO** (operator-private atlas projection; mock-only default pytest)

Closes ticket-293 PARTIAL gaps: populate `research_runs[]` with question lineage on evidence DB
spine and project claim-backed cards into private atlas export instead of golden fixture
placeholders when non-fixture manual claims exist.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export / card_exporter | **Partial** | New claim-backed seed for **private atlas** path only; `export-public` golden path unchanged unless DB has only non-fixture claims and no cards (atlas-only call site) |
| Public site | **No** | No site changes |
| Schema migrations | **No** | Uses existing tables |
| Live Ollama | **No** | Mock-only unit tests; optional operator re-run |
| Theory / inference | **No** | |

## Hardened scope

### In scope

1. **`rge/modules/evidence_db_atlas.py`** (new) or equivalent helpers:
   - `ensure_evidence_research_run_lineage(conn, topic, domain_pack)` — contract + queue question row + `research_runs` with `research_question_id` lineage
   - `ensure_claim_backed_public_cards(conn)` — seed `public_cards` from accepted non-fixture-map manual claims + linked concepts
2. **`atlas_snapshot_builder._build_curated_cards`**: when **not** `--fixture-mode`, call lineage + claim-backed seed before projection; fixture-mode golden path unchanged
3. **`tests/unit/test_evidence_db_atlas_projection.py`**: network-free mock spine on temp DB; assert `runs[]>=1`, `research_question_id`, claim-backed card ids (not `card_golden_*`)
4. **Agent report**; optional operator re-export on ticket-293 DB for improved coherence

### Out of scope

- Public atlas UI/routes
- Default pytest live Ollama
- Schema migrations / review_batch
- Full research_queue follow-up generation
- Changing staged OpenAlex spine

### Detection rule (claim-backed vs golden)

Use existing `manual_text_lacks_extract_fixture(source)` / checksum fixture map — same signal as NM-1 live path. Golden seed only when fixture-mode **or** no non-fixture manual claims.

## Safety

- Claim text in cards must pass existing `validate_public_card` / private-field scan
- No raw chunk text, claim_id, or source_id in export JSON keys
- Operator-private atlas paths only for optional re-run

## Recommendation

**GO** — implement minimal projection module + atlas builder hook + unit test.
