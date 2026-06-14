---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-155
category: Phase 3 / staged source spine / product-risk reduction
---

# Pre-Ticket Audit: ticket-155 Build Relationships on Second Staged Source

## Verdict: **GO**

ticket-154 leaves rank #2 with **1 accepted claim** and **3 concept links**
(constraint, AI assistance, human control). ticket-155 may add a mock relationship
fixture + unit test through **build-relationships** with explicit `--fixture` — no
production routing changes required.

## 1. What did ticket-154 persist for rank #2?

| Artifact | Count / detail |
| -------- | -------------- |
| Source | 1 (`Constraint management in AI-assisted creative teams`) |
| Accepted claims | 1 — improves AI-assisted creative team workflows |
| Concept links | 3 — constraint (subject), AI assistance (object), human control (context) |
| Relationships | 0 (this ticket) |

## 2. Which claim and concept links should relationship-building use?

- **Claim:** sole accepted claim from `staged_fetch_second_candidate_extract_claims.json`
- **Concept labels available:** `constraint`, `AI assistance`, `human control` (from link fixture)
- **Relationship edge (proposed):** `constraint` → `may_increase` → `human control`, scope `AI-assisted creative team workflows`, stance `supports`, evidence via placeholder claim id

Uses two of the three ticket-154 concepts; aligns with accepted claim scope text.

## 3. Existing command / module

- CLI: `python -m rge.cli build-relationships --source <id> [--fixture <name>] --db <path>`
- Module: `rge/modules/relationship_builder.py` — `build_relationships_for_source()`
- Re-run status: `already_built` when `relationship_repo.count_for_source(source_id) > 0`

Rank #1 auto-select: `_is_staged_fetch_spine_source()` — co-creativity + songwriting only; **rank #2 does not match**.

## 4. Existing fixture pattern

Rank #1: `fixtures/llm_outputs/staged_fetch_build_relationships.json`

```json
{
  "task_name": "relationship_drafting",
  "items": [{
    "subject_concept": "co-creation",
    "predicate": "may_increase",
    "object_concept": "semantic diversity",
    "stance": "supports",
    "scope": "songwriting workshops",
    "confidence": "medium",
    "supporting_claim_ids": ["placeholder"]
  }]
}
```

Mirror for rank #2 with ticket-154 concepts and claim scope.

## 5. Explicit `--fixture` without production changes?

**Yes.** Ticket JSON `affected_modules: []`. Follow ticket-153/154 pattern:

```text
build-relationships --fixture staged_fetch_second_candidate_build_relationships.json
```

No `relationship_builder.py` change unless auto-select test is added (out of scope).

## 6. Relationship fixture needed

`fixtures/llm_outputs/staged_fetch_second_candidate_build_relationships.json`

One accepted relationship draft linking `constraint` → `human control`.

## 7. Test proof

`tests/unit/test_staged_second_candidate_build_relationships_spine.py`

1. Helper: discover → fetch #2 → ingest-staged → extract (`--fixture`) → link (`--fixture`) — reuse ticket-154 constants
2. `build-relationships --fixture staged_fetch_second_candidate_build_relationships.json`
3. Assert ≥1 relationship for source; match constraint/human control/may_increase
4. Assert supports evidence row

## 8. Idempotency

Second `build-relationships` call → JSON `status: already_built`; relationship count unchanged.

## 9. Mock / golden determinism

- `RGE_LLM_MODE=mock`; network patched via existing rank #2 helpers
- No `tests/smoke/` in default collection
- Golden unchanged (no CLI/schema surface change)

## 10. Out-of-scope guardrails

| Risk | Guard |
| ---- | ----- |
| Live LLM | mock client + fixture only |
| Live network | urllib patches in test |
| Public export/site | no touched files |
| Schema migration | none |
| Broad relationship_builder refactor | forbidden |

## 11. Expected file changes

| File | Change |
| ---- | ------ |
| `fixtures/llm_outputs/staged_fetch_second_candidate_build_relationships.json` | new |
| `tests/unit/test_staged_second_candidate_build_relationships_spine.py` | new |
| `agent_reports/2026-06-14_pre-ticket-155_second-staged-build-relationships-audit.md` | this report |
| `agent_reports/2026-06-14_ticket-155_second-staged-build-relationships-spine.md` | implementation report |
| `tickets/ticket-155.json`, `tickets/ticket-156.json`, `TICKET_QUEUE.md` | queue |

## 12. Rollback plan

Remove rank #2 build-relationships fixture + test; retain ticket-154 link spine.

## Principal / cadence gate

| Gate | Status |
| ---- | ------ |
| Principal cadence | post-ticket-153 report on `main` (`agent_reports/2026-06-14_principal-audit-post-ticket-153.md`) |
| Pre-ticket-155 | **this report — GO** |

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-155 | **GO** |
| Next | ticket-156 — detect-contradictions on second staged source |
