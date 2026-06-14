---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-156
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-156 Detect Contradictions on Second Staged Source

## Verdict: **GO**

ticket-155 leaves rank #2 with **constraint may_increase human control** and domain
can be pre-seeded with **AI assistance may_reduce semantic diversity** (GT7-style base
graph, same pattern as ticket-147). ticket-156 may add a mock detect fixture + unit test
with explicit `--fixture` — no production changes required.

## 1. Upstream state (ticket-155)

| Artifact | Detail |
| -------- | ------ |
| Rank #2 accepted claim | Constraint management improves AI-assisted creative team workflows. |
| Rank #2 relationship | constraint → may_increase → human control |
| Domain base (when seeded) | AI assistance → may_reduce → semantic diversity |
| Qualifications | 0 |

## 2. Contradiction fixture contract

File: `fixtures/llm_outputs/staged_fetch_second_candidate_detect_contradictions.json`

Cross-edge qualification (apparent metric/condition difference):

| Role | Triple |
| ---- | ------ |
| base (domain) | AI assistance may_reduce semantic diversity |
| new (rank #2) | constraint may_increase human control |

Claim resolution (deterministic without code changes):

- **qualifying_claim_id:** rank #2 sole accepted claim (fallback in `_resolve_qualifying_claim_id`)
- **opposing_claim_id:** domain claim containing `reduced semantic diversity` (`OPPOSING_CLAIM_FRAGMENT`)

## 3. Test design

`tests/unit/test_staged_second_candidate_detect_contradictions_spine.py`

1. `_seed_domain_opposing_context()` — mirror ticket-147
2. Rank #2 spine through build with ticket-153/154/155 explicit fixtures
3. `detect-contradictions --fixture staged_fetch_second_candidate_detect_contradictions.json`
4. Assert ≥1 `qualifies` row; classification `apparent_contradiction_metric_or_condition_difference`
5. Assert both active relationship triples present
6. Re-run → `already_detected`

## 4. Explicit `--fixture` only

Ticket JSON `affected_modules: []`. No `_is_staged_fetch_spine_source` extension for rank #2 title.

## 5. Out of scope

Reconcile/report, live LLM/network, schema, public export/site.

## 6. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_detect_contradictions_spine.py -q
python -m pytest tests/unit/test_staged_second_candidate_build_relationships_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-156 | **GO** |
| Next | ticket-157 — reconcile-scores on second staged source |
