---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-148
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-148 Reconcile Scores on Staged-Ingested Source

## Verdict: **GO**

`score_reconciler` is **deterministic** (no LLM). `staged_fetch_reconcile_scores.json` is a
**reconcile contract fixture** (expected edge + score delta), not model output. Scope: staged
claim-to-edge matcher in `score_reconciler.py`, bump staged extract claim confidence to meet pack
threshold (0.8), unit test extending ticket-147 spine through `reconcile-scores` on the staged source.

## 1. Tables / repositories

| Layer | Table | Repository |
|-------|-------|------------|
| Score history | `score_events` | `ScoreEventRepository` |
| Relationship confidence | `relationships.confidence` | `RelationshipRepository` / `persist_relationship_score_update` |

## 2. Existing command / module

- CLI: `python -m rge.cli reconcile-scores --source <id> [--db]`
- Module: `rge/modules/score_reconciler.py` — `reconcile_scores_for_source()` (no mock LLM)

## 3. Fixture pattern

Golden/manual reconcile uses follow-up **claim extraction** fixtures (high-confidence supporting
claims). Reconcile itself reads accepted claims + active relationships and applies pack overlay
(`domain_packs/creativity/scoring.yaml`: boost 0.12, threshold 0.8).

Staged contract fixture documents expected reconcile target for tests.

## 4. ticket-147 state

Staged source has co-creation `may_increase` semantic diversity (0.5) and qualification on base
`may_reduce` edge. Staged claim: co-creativity supports diverse songwriting outputs.

## 5. Minimal staged reconcile path

1. Extend `claim_supports_relationship()` with staged co-creation / may_increase / diversity matcher
2. Raise staged extract claim confidence to 0.85 (≥ threshold)
3. `reconcile-scores --source <staged_id>` boosts co-creation edge 0.5 → 0.62

## 6. Test proof

`test_staged_ingest_reconcile_spine.py`: domain seed → staged spine through detect → reconcile-scores on staged source → assert 1 `score_events` row.

## 7. Determinism

No LLM; golden GT08 unchanged; staged extract confidence change is deterministic.

## 8. Out of scope

Live LLM, run report, schema, public export/site.

## 9. Expected files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_reconcile_scores.json` | reconcile contract |
| `fixtures/llm_outputs/staged_fetch_extract_claims.json` | confidence 0.85 |
| `rge/modules/score_reconciler.py` | staged edge matcher |
| `tests/unit/test_staged_ingest_reconcile_spine.py` | e2e test |

## 10. Rollback

Revert matcher + extract confidence + test; retain ticket-147 spine.

## Recommendation

**GO** — implement ticket-148; seed ticket-149 run-report on staged source next.
