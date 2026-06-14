---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-146
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-146 Build Relationships on Staged-Ingested Source

## Verdict: **GO**

Scope stays narrow: one staged relationship fixture, a staged-source title heuristic in
`relationship_builder.py` (mirroring ticket-145 `concept_linker`), and a unit test extending
the Phase 3 spine through **build-relationships**. Mock LLM only; no schema, export, or live paths.

## 1. Tables / repositories for concept links and relationships

| Layer | Table | Repository |
|-------|-------|------------|
| Concept links | `claim_concepts` | `ClaimConceptRepository` |
| Relationships | `relationships` | `RelationshipRepository` |
| Evidence edges | `relationship_evidence` | `RelationshipEvidenceRepository` |

Concept labels resolve via `ConceptRepository` / domain pack ontology (`domain_packs/creativity/ontology.yaml`).

## 2. Existing command / module

- CLI: `python -m rge.cli build-relationships --source <id> [--fixture <name>] [--db <path>]`
- Module: `rge/modules/relationship_builder.py` — `build_relationships_for_source()`, `propose_relationship_drafts()`, `validate_relationship_candidates()`

## 3. Existing relationship-builder fixture pattern

Mock mode selects fixture via `_default_relationship_fixture_for_source(source)`:

- Checksum-pinned `manual_text` → `fixtures/manual_source_fixture_map.json` → e.g. `relationship_drafting_manual_synthnote.json`
- Unmapped `manual_text` → fail closed (ValueError)
- Default golden path → `relationship_drafting_creativity_diversity.json`

Fixtures live under `fixtures/llm_outputs/` with `task_name: relationship_drafting`, placeholder `supporting_claim_ids`, and Python-side claim-id resolution via `_resolve_supporting_claim_ids()`.

## 4. How ticket-145 persisted staged concept links

- Fixture: `fixtures/llm_outputs/staged_fetch_link_concepts.json`
- Heuristic: `_is_staged_fetch_spine_source()` — title contains `"human-ai co-creativity"` and `"songwriting"`
- Claim resolution: diversity heuristic maps placeholder claim ids to the accepted co-creativity claim
- Test: `tests/unit/test_staged_ingest_link_spine.py` runs discover → enqueue → fetch → ingest-staged → extract → link

## 5. Minimal fixture for staged-source relationships

Add `fixtures/llm_outputs/staged_fetch_build_relationships.json`:

- One edge: **co-creation** → **semantic diversity** (`may_increase`, stance `supports`, scope `songwriting workshops`)
- Uses concepts already linked by ticket-145 fixture
- `supporting_claim_ids: ["placeholder"]` resolved to the accepted co-creativity claim

## 6. Test proof (full spine)

New `tests/unit/test_staged_ingest_relationship_spine.py`:

1. Mock OpenAlex discover + HTML fetch (same as ticket-144/145)
2. `ingest-staged` → `extract-claims` → `link-concepts` → **`build-relationships`**
3. Assert `relationships` count ≥ 1 and evidence row with stance `supports` linking co-creation claim

## 7. Mock / golden determinism

- `RGE_LLM_MODE=mock` in test autouse fixture
- Staged heuristic selects fixture only for staged title pattern; golden/manual paths unchanged
- No new live_smoke tests; golden GT06 unchanged

## 8. Live LLM / network / fetch out of scope

- No `RGE_ALLOW_LIVE_LLM`, no Ollama paths
- Network mocked via `urllib.request.urlopen` patches (same as ticket-145)
- No OpenAlex live calls, Playwright, Scrapfly, or fetcher expansion
- No public export / site / schema migration

## 9. Expected file changes

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_build_relationships.json` | new mock fixture |
| `rge/modules/relationship_builder.py` | staged heuristic + claim-id fallback |
| `tests/unit/test_staged_ingest_relationship_spine.py` | e2e spine test |
| `tickets/ticket-146.json` | status |
| `tickets/TICKET_QUEUE.md` | queue update |
| `agent_reports/2026-06-14_ticket-146_staged-build-relationships-spine.md` | implementation report |

## 10. Rollback plan

Remove staged relationship fixture, revert `relationship_builder.py` heuristic, delete new unit test. ticket-144/145 spine tests remain valid without ticket-146.

## Hardened scope

### In

1. `staged_fetch_build_relationships.json`
2. `relationship_builder._is_staged_fetch_spine_source()` + fixture routing + staged claim fallback
3. `test_staged_ingest_relationship_spine.py` — full spine through build-relationships

### Out

- detect-contradictions, reconcile-scores, run report, public export/site, schema, live Ollama, network fetch expansion

## Recommendation

**GO** — implement ticket-146; seed ticket-147 detect-contradictions on staged source next (pre-ticket audit required).
