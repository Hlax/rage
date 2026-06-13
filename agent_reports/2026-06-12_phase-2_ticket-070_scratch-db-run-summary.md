---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-070: Scratch DB run summary

- Date: 2026-06-12
- Branch: `phase-2/ticket-070-scratch-db-run-summary`
- Baseline HEAD: `5505698` (ticket-069 on main)
- Implementation SHA: `865d3a9`
- Risk level: low-medium

## Summary

Added deterministic read-only CLI `probe-scratch-summary` that aggregates
operator-reviewed rows from `reviewed_live_probe_reports` in isolated scratch
SQLite. Opens DB via SQLite `mode=ro`; never creates, migrates, or mutates scratch
or accepted graph databases. No LLM calls.

## Command

```powershell
python -m rge.cli probe-scratch-summary
python -m rge.cli probe-scratch-summary --format markdown
python -m rge.cli probe-scratch-summary --fixture claim_calibration --limit 10
python -m rge.cli probe-scratch-summary --allow-empty
python -m rge.cli probe-scratch-summary `
  --out data/reports/live_probes/scratch_summary.json
```

Default scratch path: `data/db/live_probe_scratch.sqlite`

## Files changed

| File | Change |
| ---- | ------ |
| `rge/modules/live_probe_scratch_summary.py` | Read-only aggregation, formatting, output validation |
| `rge/cli.py` | `probe-scratch-summary` subcommand |
| `rge/modules/safety_auditor.py` | Extended `live_probe_scratch_policy` for summary module |
| `tests/unit/test_live_probe_scratch_summary.py` | 16 unit tests |
| `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` | Scratch summary operator section |
| `tickets/ticket-070.json`, `TICKET_QUEUE.md` | Done status |

## Read-only / write behavior

| Surface | Writes? |
| ------- | ------- |
| Scratch DB | **No** — `mode=ro`; no schema bootstrap |
| Accepted graph DB | **No** |
| `--out` file | **Optional** — private paths only (`data/reports/`, `agent_reports/`) |
| stdout default | **Yes** (summary text only) |

Missing DB: fail closed. `--allow-empty`: deterministic empty summary without creating DB.
Empty valid DB: zero totals. Invalid schema: fail closed.

## Summary fields (examples)

- `total_reviewed_reports`, `first_reviewed_at`, `last_reviewed_at`
- `floors_passed` / `floors_failed`, `fixture_pass_rate`
- `reports_by_fixture`, `stage_totals`, `contradiction_input_mode_counts`
- `rejection_reason_counts` (diagnostic string counts, capped at persist time)
- `latest_report_path_by_fixture`, `operator_notes_count` (count only)
- `safety_flags`: `accepted_graph_writes`, `public_export`, `model_authority`, `raw_response_included` — all `false`

## Verification

| Command | Result |
| ------- | ------ |
| `pytest tests/unit/test_live_probe_scratch_summary.py -q` | **16 passed** |
| `pytest tests/unit/test_live_probe_scratch_persistence.py -q` | **11 passed** |
| `pytest tests/golden -q` | **140 passed** |
| `pytest -q` | **302 passed**, 6 deselected |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| `python -m rge.modules.principal_audit_gate --next-ticket ticket-071` | **satisfied** |

Public site / export **not touched** — no build re-run.

Live suite **not re-run** — not required for deterministic read-only summary ticket.

## Safety confirmations

- No LLM / OpenAI (ticket-059 still deferred)
- No public export coupling
- No accepted graph authority from scratch rows
- Ordinary mini-run/suite still report-only (`db_writes: false`)
- Scratch persist remains `--confirm-review` only

## Principal audit cadence

After ticket-070: **3 done tickets** since post-ticket-067 checkpoint (068, 069, 070).
**Next medium-risk ticket requires post-ticket-070 principal audit checkpoint** via
`/rge-principal-audit` and committed report before seeding.

## Remaining risks

- Summary quality depends on what operators persisted; empty scratch DB is expected until reviews are ingested
- Rejection counts aggregate diagnostic strings — not structured rejection codes
- `--out` path allowlist is prefix-based; operators must keep summaries out of export dirs

## Merge

- Implementation SHA: `865d3a9`
- Docs/report SHA: `e79d769`
- Golden Gate run: **27455038931** — **success** at `e79d769`

## Recommended next move

1. **Required:** post-ticket-070 principal audit checkpoint (`/rge-principal-audit`)
2. Then choose (human approval):
   - deterministic evidence review report over scratch summaries (still no model authority)
   - local run evaluator connection to scratch summaries (report-only)
   - defer OpenAI/ticket-059
