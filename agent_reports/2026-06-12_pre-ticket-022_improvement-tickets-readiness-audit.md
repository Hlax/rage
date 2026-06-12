---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-022 Audit: Improvement Ticket Readiness

- Audit type: pre-implementation readiness audit (no ticket-022 code changes)
- Date: 2026-06-12
- Agent/model: Cursor builder agent (Auto)
- Scope: Git/main state after ticket-021, run report spine, schema/repository/module support for Golden Test 20, ticket-022 scope hardening, safety boundaries

## 1. Summary

The repo is **ready for ticket-022 (improvement ticket generation / Golden Test 20)** with hardening folded into the ticket. Main is aligned with `origin/main` at `08f49e80aa7fe56a9b546f903de023e960f625eb`. All **89** golden tests pass without Ollama. Ticket **021** is merged and pushed. **`ticket_writer.py` is a Phase 0 stub**; **`ImprovementTicketRepository` and Golden Test 20 are absent** — expected pre-implementation state.

**Contract decisions for ticket-022:**

1. **No new migration** — `improvement_tickets` exists in `0001_initial.sql` per `05_DATA_MODEL.md` §4.25.
2. Add `ImprovementTicketRepository` with idempotent insert keyed on stable ticket ID per `(run_id, failure_reason)`.
3. Implement deterministic ticket templates in **`ticket_writer.py`** mapped from `run_report.top_failure_modes` (no Ollama).
4. CLI: `generate-improvement-tickets` with `--run-id`, `--db`, optional `--output-dir`.
5. Primary golden ticket for `overgeneralized_scope`: title **"Improve claim extractor scope preservation"**, priority `high`.
6. Golden Test 20 spine: ingest + rejection fixtures → `generate-run-report` → `generate-improvement-tickets`.
7. Write `improvement_ticket_latest.json` under report dir; tickets remain `status: draft`.
8. No public export/site changes; no LangGraph orchestrator.

**Recommendation: proceed with ticket-022 as the next smallest safe ticket** — after this audit report is committed to `main`.

## 2. Git / Main Status

| Check | Result |
|---|---|
| Current branch | `main` |
| Working tree | **dirty (local artifacts)** — `apps/public-site/public/data/*`, untracked `data/`. Not blockers. |
| `main` vs `origin/main` | **aligned** at `08f49e8` |
| ticket-021 merged & pushed | **yes** — merge `ac1c11e` |

## 3. Ticket / Queue

| Ticket | Status | Next |
|---|---|---|
| ticket-021 | `done` | — |
| ticket-022 | `proposed` | **correct next ticket** |

**Risk / audit gate:** ticket-022 `risk_level: medium` — this audit satisfies.

## 4. Readiness

| Component | Status |
|---|---|
| `ticket_writer.py` | Phase 0 stub |
| `improvement_tickets` table | Present in `0001_initial.sql` |
| `ImprovementTicketRepository` | Absent |
| `generate-improvement-tickets` CLI | Absent |
| `tests/golden/test_20_improvement_tickets.py` | Absent |
| `generate-run-report` + `top_failure_modes` | **Ready** (ticket-021) |

## 5. Tests Run

| Command | Result |
|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | **89 passed** |

## 6. Hardened Ticket-022 Scope

- [ ] `ImprovementTicketRepository` in `repositories.py`
- [ ] Full `ticket_writer.py` with failure-mode → ticket templates
- [ ] CLI `generate-improvement-tickets`
- [ ] `tests/golden/test_20_improvement_tickets.py` (4 tests)
- [ ] Update `test_00_scaffold.py` CLI help scan
- [ ] Idempotent re-run; evidence cites `run_report:{run_id}:{reason}=N`
- [ ] No Ollama, no public export, no schema migration

## 7. Blocking Issues

| ID | Issue | Resolution |
|---|---|---|
| B1 | Audit not on main | Commit this report before implementation |

---

**Recommendation: proceed with ticket-022** (post-commit).
