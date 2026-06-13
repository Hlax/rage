---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-070 Scratch DB Run Summary Audit

- Audit type: focused pre-ticket readiness (deterministic read-only reporting)
- Date: 2026-06-12
- Baseline HEAD: `5505698` (ticket-069 on main)
- Human direction: deterministic scratch DB summary after ticket-068 persistence

## 1. Executive verdict

**GO — read-only deterministic summary over private scratch SQLite**

Ticket-068 added `reviewed_live_probe_reports` in isolated
`data/db/live_probe_scratch.sqlite` with operator-only persist CLI. Ticket-070 adds
a summary command that reads that table in SQLite read-only mode, aggregates
counts, and prints/writes operator-facing reports. No LLM, no graph writes, no
public export, no schema bootstrap from summary.

## 2. Scratch DB read surface

| Item | Detail |
| ---- | ------ |
| Table | `reviewed_live_probe_reports` only |
| Path default | `data/db/live_probe_scratch.sqlite` |
| Connection | SQLite URI `file:...?mode=ro` |
| Writes | **None** — summary never INSERT/UPDATE/CREATE |

## 3. Read-only enforcement

- Open via `mode=ro` URI; no `ensure_scratch_database()` in summary module
- No `executescript`, no migrations, no `commit` on scratch DB
- Missing file fails closed (unless `--allow-empty`)
- Invalid/missing table or columns fails closed
- `--out` restricted to private paths (`data/reports/`, `agent_reports/`); rejects public export dirs

## 4. Edge cases

| Case | Behavior |
| ---- | -------- |
| Missing DB | Fail closed with clear error |
| `--allow-empty` + missing DB | Deterministic empty summary JSON (no file creation) |
| Empty valid DB | Valid summary with zero totals |
| Invalid schema | Fail closed |

## 5. Output formats

- Default: JSON to stdout (deterministic key order)
- Optional: `--format markdown` for operator-readable stdout/`--out`
- `--out` optional; when omitted, no files written
- No raw prompts, model responses, or operator note bodies in summary (note **count** only)

## 6. Public export isolation

- Summary module must not import `card_exporter`
- Output paths validated away from `apps/public-site/public/` and `data/exports/`
- Safety flags in every summary: `accepted_graph_writes: false`, `public_export: false`, `model_authority: false`, `raw_response_included: false`
- Extend `live_probe_scratch_policy` audit to cover summary module

## 7. Required tests

- Seeded temp DB summary aggregation
- Deterministic repeated runs
- Missing DB fail closed / `--allow-empty`
- Empty DB valid summary
- Invalid schema fail closed
- Summary does not create or mutate scratch DB
- Forbidden content patterns absent from output
- JSON format; markdown if implemented
- Default graph DB untouched

## 8. Out of scope

- LLM synthesis or ticket recommendations
- Scratch DB schema changes
- Public site / export changes
- OpenAI / ticket-059
- Auto-persist from mini-run/suite
- Markdown-only if JSON alone satisfies acceptance (implement JSON + markdown if low cost)

## 9. Rollback plan

Revert summary module, CLI, tests, docs, safety audit extension.

## 10. Recommendation

Seed ticket-070 on branch `phase-2/ticket-070-scratch-db-run-summary`.

After completion: **3 done tickets** since post-ticket-067 checkpoint → run
post-ticket-070 principal audit before next medium-risk ticket.
