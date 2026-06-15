---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-163
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-163 Staged Fixture-Mode Run Orchestrator Idempotency

## Verdict: **GO**

ticket-162 adds `execute_staged_fixture_mode_run` and `--staged-spine` CLI entry with dual-spine
count assertions. ticket-163 may add **unit tests only** proving a second orchestrator pass on
the same DB does not duplicate rows.

## 1. Hardened scope

### In

1. Extend `tests/unit/test_staged_fixture_mode_run_spine.py` with idempotency test(s)
2. URL-aware network mock must cycle staged HTML fetches (two candidates × two orchestrator passes)
3. Assert stable counts matching ticket-161 / ticket-162 after second `execute_staged_fixture_mode_run`

### Out

- Changes to `execute_staged_fixture_mode_run` step order or production logic
- Live network, schema, public export/site
- README / operator docs (ticket-164 follow-on)

## 2. Expected stable counts (unchanged after second pass)

| Metric | Expected |
|--------|----------|
| `sources` | 3 |
| `candidate_sources` / `research_queue` | 2 each |
| `score_events` | 2 |
| `run_reports` | 2 |
| `qualifies_evidence` | 2 |
| rank #1 accepted / rejected | 1 / 1 |
| rank #2 accepted / rejected | 1 / 1 |
| relationships with staged claim evidence (each rank) | 2 |

## 3. Test design

- `_orchestrator_counts(result)` — snapshot from orchestrator return dict
- Test A: `execute_staged_fixture_mode_run` twice under patched network → counts unchanged
- Optional Test B: CLI `--staged-spine` twice → exit 0; DB counts stable (if not redundant)

Refactor `_staged_network_urlopen` HTML branch to **cycle** `[RANK1_HTML, RANK2_HTML]` so four
fetch calls across two orchestrator passes receive correct HTML.

## 4. Audit gates

- Principal checkpoint: `agent_reports/2026-06-14_principal-audit-post-ticket-158.md` on `main`
- Pre-ticket audit: this report
- Cadence gate note: automated gate still surfaces post-ticket-149 filename sort; post-158 report exists

## 5. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_fixture_mode_run_spine.py -q
python -m pytest tests/unit/test_staged_dual_candidate_idempotency.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-163 | **GO** |
| Next | ticket-164 — README operator quickstart for staged Phase 3 `--staged-spine` |
