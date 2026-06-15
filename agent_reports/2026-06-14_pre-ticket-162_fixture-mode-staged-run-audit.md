---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-162
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-162 Fixture-Mode Staged Research Run Orchestration

## Verdict: **GO**

Tickets 144–161 prove each staged CLI step and dual-candidate idempotency in unit tests.
ticket-162 may add **`execute_staged_fixture_mode_run`** in `rge/cli.py` plus a unit test
that patches network I/O — mirroring `test_staged_dual_candidate_idempotency.py` counts
without public export, theory, cluster report, or improvement tickets.

## 1. Hardened scope

### In

1. `execute_staged_fixture_mode_run(...)` — domain seed → discover → rank #1 spine → rank #2 spine → two run reports
2. `research run --fixture-mode --staged-spine` (optional `--staging-dir`, `--question-id`)
3. `tests/unit/test_staged_fixture_mode_run_spine.py` — patched OpenAlex + fetcher; assert dual-spine counts

### Out

- Live OpenAlex/network in default pytest collection
- Public export, public site, schema migrations
- Live Ollama paths
- Idempotency re-run of orchestrator (ticket-163 follow-on)

## 2. Expected stable counts (match ticket-161)

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

## 3. Contract decisions

| Decision | Choice |
|----------|--------|
| MVP `execute_fixture_mode_run` | Unchanged; staged path is separate |
| Rank #1 LLM routing | Auto mock (no `--fixture` on extract/link/build/detect) |
| Rank #2 LLM routing | Explicit `--fixture` bindings (same filenames as ticket-160) |
| Network env | Set `RGE_ALLOW_SOURCE_NETWORK=1` inside orchestrator; tests still patch `urlopen` |
| Run report IDs | `{run_id}_rank1` and `{run_id}_rank2` |
| Safety audit | Not invoked inside orchestrator (unlike MVP fixture run); full suite gate still runs in CI |

## 4. Audit gates

- Principal checkpoint: `agent_reports/2026-06-14_principal-audit-post-ticket-158.md` on `main`
- Pre-ticket audit: this report

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
| Implement ticket-162 | **GO** |
| Next | ticket-163 — staged fixture-mode run orchestrator idempotency |
