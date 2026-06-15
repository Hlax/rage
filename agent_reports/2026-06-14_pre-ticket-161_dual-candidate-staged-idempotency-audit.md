---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-161
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-161 Dual-Candidate Staged Idempotency

## Verdict: **GO**

Tickets 151 and 160 prove idempotency for rank #1 and rank #2 **in isolation** (each re-seeds domain).
ticket-161 may add **unit tests only** that:

1. Seed domain **once**
2. Discover **once** (both OpenAlex fixture candidates)
3. Run rank #1 full spine then rank #2 full spine on the **same DB**
4. Re-run both spines without re-seeding; assert stable global and per-source counts

Rank #2 steps use explicit `--fixture` bindings (same as ticket-160).

## 1. Expected stable counts (after first dual pass)

| Metric | Expected |
|--------|----------|
| `sources` | 3 (domain base + rank #1 + rank #2) |
| `candidate_sources` | 2 |
| `research_queue` | 2 |
| `score_events` | 2 |
| `run_reports` | 2 (distinct run ids per candidate) |
| `qualifies_evidence` | 2 |
| rank #1 staged accepted / rejected | 1 / 1 |
| rank #2 staged accepted / rejected | 1 / 1 |

Per-source relationship evidence counts mirror tickets 151/160 (2 each).

## 2. Test design

File: `tests/unit/test_staged_dual_candidate_idempotency.py`

- `_run_dual_spine(..., seed_domain: bool)` — rank #1 auto fixtures, rank #2 explicit fixtures
- Test A: dual spine twice → `_DualCounts` unchanged
- Test B: spot-check discover + one command per candidate after baseline

## 3. Out of scope

Live network, schema, public export/site, `research run` orchestration.

## 4. Audit gates

- Principal checkpoint: `agent_reports/2026-06-14_principal-audit-post-ticket-158.md` on `main`
- Pre-ticket audit: this report

## 5. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_dual_candidate_idempotency.py -q
python -m pytest tests/unit/test_staged_second_candidate_idempotency.py -q
python -m pytest tests/unit/test_staged_ingest_idempotency.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-161 | **GO** |
| Next | ticket-162 — live OpenAlex fetch env-gate hardening or fixture-mode staged `research run` |
