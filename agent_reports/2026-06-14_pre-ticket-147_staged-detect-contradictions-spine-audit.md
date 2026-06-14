---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-147
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-147 Detect Contradictions on Staged-Ingested Source

## Verdict: **GO**

Scope stays narrow: one staged contradiction fixture, staged-source heuristic in
`contradiction_detector.py`, and a unit test extending the Phase 3 spine through
**detect-contradictions**. Mock LLM only. Test seeds a minimal opposing domain base graph
(GT7 pattern) before the staged spine so qualification has a base `may_reduce` edge and
opposing claim to compare against.

## 1. Tables / repositories

| Layer | Table | Repository |
|-------|-------|------------|
| Qualification evidence | `relationship_evidence` (stance `qualifies`) | `RelationshipEvidenceRepository` |
| Relationships (metadata patch) | `relationships.domain_metadata_json` | `RelationshipRepository` |
| Claims | `claims` | `ClaimRepository` |

## 2. Existing command / module

- CLI: `python -m rge.cli detect-contradictions --source <id> [--fixture] [--db]`
- Module: `rge/modules/contradiction_detector.py` — `detect_contradictions_for_source()`

## 3. Existing fixture pattern

Mock mode uses `_default_contradiction_fixture_for_source(source)`:

- Checksum-pinned manual_text → `contradiction_detection_manual_synthnote.json` + claim hints
- Unmapped manual_text → fail closed
- Default → `contradiction_detection_creativity_diversity.json`

Fixtures specify base/new relationship triples, placeholder claim ids, `qualification_stance`, and `contradiction_classification`.

## 4. How ticket-146 persisted staged relationships

- Fixture: `staged_fetch_build_relationships.json`
- Edge: co-creation `may_increase` semantic diversity (songwriting workshops)
- Heuristic: `_is_staged_fetch_spine_source()` on title pattern

## 5. Minimal staged contradiction fixture

`fixtures/llm_outputs/staged_fetch_detect_contradictions.json`:

- base: AI assistance `may_reduce` semantic diversity (from seeded domain base)
- new: co-creation `may_increase` semantic diversity (from staged build-relationships)
- classification: `apparent_contradiction_metric_or_condition_difference`
- stance: `qualifies`
- placeholder claim ids resolved via extended qualifying heuristic + standard opposing fragment

## 6. Test proof

`tests/unit/test_staged_ingest_contradiction_spine.py`:

1. Seed `creativity_ai_diversity_short.txt` through build-relationships (domain opposing context)
2. Run discover → enqueue → fetch → ingest-staged → extract → link → build-relationships
3. `detect-contradictions` on staged source
4. Assert ≥1 `qualifies` evidence row and contradiction metadata on relationship

## 7. Mock / golden determinism

- `RGE_LLM_MODE=mock`; staged heuristic only for staged title sources
- Golden GT07 and manual synthnote paths unchanged

## 8. Out of scope

No live LLM, network, schema, public export/site, score reconciliation, run report.

## 9. Expected file changes

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_detect_contradictions.json` | new |
| `rge/modules/contradiction_detector.py` | staged heuristic + qualifying claim fallback |
| `tests/unit/test_staged_ingest_contradiction_spine.py` | e2e spine test |
| tickets/queue/report | status + ticket-148 seed |

## 10. Rollback plan

Remove staged contradiction fixture/test; revert heuristic. ticket-146 relationship spine unchanged.

## Recommendation

**GO** — implement ticket-147; seed ticket-148 reconcile-scores on staged source next.
