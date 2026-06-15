---
template_id: audit_report
template_version: 1.0.0
status: current
date: 2026-06-15
phase: 2
checkpoint_after: ticket-194
---

# Principal Audit Post-Ticket-194

- Audit type: principal audit — live staged orchestrator docs checkpoint
- Date: 2026-06-15
- Baseline HEAD: `7d2f144` (`main`, post ticket-194 merge-hash doc)
- Prior checkpoint: `agent_reports/2026-06-15_principal-audit-post-ticket-193.md`
- Trigger: cadence **not_due** — 1 done ticket since post-ticket-193 (ticket-194 only)

## Executive summary

**GO — release-healthy; live staged opt-in layer documented through orchestrator**

| Ticket | Deliverable |
|--------|-------------|
| 194 | Orchestrator opt-in docs (`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR`) |

```text
Live network proofs (operator opt-in, not CI):
  per-step rank-1 / rank-2 report     ✓ 187 / 190
  single-command orchestrator         ✓ 193 (code); docs ✓ 194
  live OpenAlex CI verification       ✗ operator opt-in only
  research run without --fixture-mode ✗ not_implemented
```

Local gates: **142 golden**, **599 pytest** (16 deselected), **safety audit pass**, **public-site build pass**.

**Cadence:** satisfied. **ticket-195** (low-risk hygiene) may proceed without pre-ticket audit.

## Checkpoint status (pre-audit)

```json
{
  "status": "satisfied",
  "cadence_status": "satisfied",
  "done_tickets_since_latest_checkpoint": 1,
  "done_ticket_ids_since_latest_checkpoint": ["ticket-194"],
  "next_ticket_id": "ticket-195",
  "next_ticket_risk_level": "low",
  "implementation_gate": "satisfied",
  "pre_ticket_audit_report": null
}
```

## Repo and queue

| Check | Status |
|-------|--------|
| `main` aligned with `origin/main` | **PASS** (`7d2f144`) |
| Working tree clean | **PASS** |
| Active ticket | ticket-195 (proposed, hygiene) |
| Queue vs reports | **PASS** (191–194 done with reports) |

## Verification (2026-06-15)

```powershell
git checkout main
git pull origin main   # already up to date
git status             # clean

$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q              # 142 passed in 40.12s
python -m pytest -q                           # 599 passed, 16 deselected in 129.53s
python -m pytest --collect-only -q              # tests/smoke/ not collected
python -m rge.modules.safety_auditor --audit full  # pass
cd apps/public-site && npm run build          # pass (static/SSG)
```

## Safety boundaries

| Area | Finding |
|------|---------|
| Public write routes | None observed; safety audit **pass** |
| Live LLM in CI/default pytest | Mock-only; `live_smoke` + `live_network` excluded in `pyproject.toml` |
| Live staged proofs | 11 opt-in `live_network` unit tests; per-stage + orchestrator env gates |
| Model → DB direct writes | Unchanged; Python validates, repositories persist |
| Public export / site | Unchanged this window |

## Golden gate / CI

| Check | Status |
|-------|--------|
| `.github/workflows/golden-gate.yml` | Present; mock env + golden + pytest + smoke exclusion + safety + site |
| GT22 inventory | Unchanged |
| Ollama / live credentials in CI | Not required |

## Hygiene / drift notes

1. **Value drift:** last 4 done tickets (191–194) are infrastructure/docs; gate emits `drift_warning` for no product-risk advance — acceptable post-orchestrator milestone.
2. **Must-fix before live operator runs:** nine per-step `live_network` tests still use `ORDER BY rank ASC` on `candidate_sources`, but schema has no `rank` column (ticket-193 fixed orchestrator to `priority_score DESC`). **ticket-195** addresses this.
3. **Live orchestrator:** implemented in ticket-193; operator live OpenAlex run not verified in CI (timeout in builder environment); documented in ticket-194.

## Live staged operator spine (current)

| Stage | Opt-in env | Proof |
|-------|------------|-------|
| fetch | `RGE_ALLOW_LIVE_STAGED_FETCH` | ticket-167 |
| ingest | `RGE_ALLOW_LIVE_STAGED_INGEST` | ticket-168 |
| extract (mock) | `RGE_ALLOW_LIVE_STAGED_EXTRACT` | ticket-172 |
| link (mock) | `RGE_ALLOW_LIVE_STAGED_LINK` | ticket-175 |
| build (mock) | `RGE_ALLOW_LIVE_STAGED_BUILD` | ticket-178 |
| detect (mock) | `RGE_ALLOW_LIVE_STAGED_DETECT` | ticket-181 |
| reconcile | `RGE_ALLOW_LIVE_STAGED_RECONCILE` | ticket-184 |
| report (rank-1) | `RGE_ALLOW_LIVE_STAGED_REPORT` | ticket-187 |
| report (rank-2) | `RGE_ALLOW_LIVE_STAGED_RANK2` | ticket-190 |
| orchestrator (dual) | `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR` | ticket-193 |

Shared prerequisites: `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`, domain opposing-context seed (orchestrator ingests fixture base), temp DB only.

## Hardened scope — ticket-195 (next)

| Field | Value |
|-------|-------|
| Risk | low — test SQL only |
| Pre-ticket audit | not required |
| Files | nine `test_live_staged_*.py` files |
| Change | Replace `ORDER BY rank ASC` with `ORDER BY priority_score DESC` (rank-2: `LIMIT 1 OFFSET 1` after DESC sort) |
| Non-goals | schema, CI live network, public export |
| Verification | golden + full pytest + safety audit |

## Phase / roadmap (brief)

| Layer | Status |
|-------|--------|
| MVP-Engine (mock/fixture) | **Proven** — 142 golden, 599 unit tests |
| Live staged per-step + orchestrator | **Code proven** (operator opt-in); per-step SQL hygiene pending (195) |
| Live OpenAlex operator verification | **Not CI-enforced** |
| `research run` without `--fixture-mode` | **not_implemented** |
| Cloud providers | **deferred** (ticket-059) |

## Recommendation

**GO** — implement **ticket-195** (candidate ordering hygiene), then consider product-risk work (NM-4 expansion, theory, or source discovery) per queue priorities.

After this report is on `main`, re-run:

```powershell
python -m rge.modules.principal_audit_gate --next-ticket ticket-195
```

Expected: `cadence_status: satisfied`.
