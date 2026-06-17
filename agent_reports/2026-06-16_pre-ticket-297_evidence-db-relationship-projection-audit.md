---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-297
category: Phase 3 / Research Atlas / live-derived population
---

# Pre-Ticket Audit: ticket-297 Evidence DB Relationship Edge Projection

## Verdict: **GO** (operator-private DB-only relationship seeding; mock-only pytest)

Seeds minimal active `relationships` (+ `relationship_evidence`) rows from claim–concept links on
evidence DBs so atlas `edges[]` populates and coherence `missing_fields_create_refactor_risk`
clears the empty-edges warn — enabling **overall_coherence_verdict: pass** on the mock evidence spine.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | DB-only inserts; no `export-public` change |
| Public site | **No** | |
| Schema migrations | **No** | Uses existing `relationships` / `relationship_evidence` tables |
| Theory / inference | **No** | Deterministic concept-pair edges from existing claim links |
| Live Ollama | **No** | Mock-only tests; reuse ticket-294 spine stubs |

## Hardened scope

### In scope

1. **`ensure_evidence_relationship_edges(conn, topic, domain_pack)`** in `evidence_db_atlas.py`:
   - Requires non-fixture manual claims with ≥2 linked concepts per claim
   - Derives subject/object concept pair from claim_concept roles (method → context/object)
   - Inserts active `relationships` with `domain_metadata.evidence_db_atlas=true`
   - Links supporting `relationship_evidence` to the source claim
   - **No** LLM `build-relationships`; **no** golden relationship fixtures
   - Idempotent when evidence-tagged active relationships already exist
2. **Hook** in `build_atlas_snapshot_from_db` after run report, **before** cluster summary (so cluster counts relationships)
3. **`tests/unit/test_evidence_db_relationship_projection.py`**: mock spine → `edges[]>=1`, overall coherence **pass**

### Out of scope

- Public atlas UI, live default pytest, schema migration
- Full build-relationships LLM spine in default pytest
- Changing golden MVP relationship builder behavior

## Safety

- Relationships use concept ids and claim ids already in DB — no raw source text
- Tagged via `domain_metadata` for rollback isolation from golden graph
- Atlas export remains operator-private

## Recommendation

**GO** — implement minimal deterministic relationship seeding for evidence atlas overall coherence pass.
