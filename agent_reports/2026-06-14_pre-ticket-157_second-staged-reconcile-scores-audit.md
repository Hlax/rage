---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-157
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-157 Reconcile Scores on Second Staged Source

## Verdict: **GO**

`score_reconciler` is deterministic (no LLM). Rank #2 reconcile requires the same pattern as
ticket-148: a **staged edge matcher** plus accepted-claim confidence ≥ pack threshold (0.8).
Reconcile contract fixture documents expected score delta for tests.

## 1. Upstream state (ticket-156)

| Artifact | Detail |
| -------- | ------ |
| Rank #2 relationship | constraint → may_increase → human control |
| Scope | AI-assisted creative team workflows |
| Initial confidence | 0.5 |
| Accepted claim | Constraint management improves AI-assisted creative team workflows. |
| Claim confidence | 0.7 (below threshold — must bump to 0.85) |
| Qualifications | ≥1 qualifies row on base may_reduce edge |

Generic `_claim_supports_active_relationship_edge` **does not match** (claim lacks `human control`;
predicate `improves` ≠ `may_increase`). Mirror ticket-148 with dedicated matcher.

## 2. Reconcile contract fixture

File: `fixtures/llm_outputs/staged_fetch_second_candidate_reconcile_scores.json`

| Field | Value |
| ----- | ----- |
| subject | constraint |
| predicate | may_increase |
| object | human control |
| scope | AI-assisted creative team workflows |
| initial_confidence | 0.5 |
| expected_boost | 0.12 |
| expected_confidence | 0.62 |

## 3. Minimal production changes (ticket-148 precedent)

| File | Change |
| ---- | ------ |
| `rge/modules/score_reconciler.py` | `_matches_staged_second_candidate_may_increase_human_control()` |
| `fixtures/llm_outputs/staged_fetch_second_candidate_extract_claims.json` | accepted claim confidence 0.7 → 0.85 |

No CLI changes; `reconcile-scores --source <id>` sufficient.

## 4. Test design

`tests/unit/test_staged_second_candidate_reconcile_spine.py`

1. Reuse ticket-156 spine helper through detect-contradictions (explicit fixtures)
2. `reconcile-scores --source <rank_2_id>`
3. Assert relationship confidence 0.62, one `score_events` row
4. Idempotent re-run (no duplicate events)

## 5. Out of scope

Run report, live LLM/network, schema, public export/site.

## 6. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_reconcile_spine.py -q
python -m pytest tests/unit/test_staged_second_candidate_detect_contradictions_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-157 | **GO** |
| Next | ticket-158 — generate run report on second staged source |
