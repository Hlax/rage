---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-132
---

# ticket-132: Operator Loop NM-4 Evidence DB Spine Status

## Summary

Added read-only `nm4_evidence_spine_status` to `operator_loop --mode plan`. Operators can
see gitignored evidence DB spine counts (sources, claims, relationships, score_events)
and a coarse stage (`missing` | `empty` | `partial` | `reconciled`). Fixed default path
resolution to use a repo-relative path so plan mode and unit tests honor the configured
`root` instead of always opening the absolute default evidence DB.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-132 |
| Branch | `phase-2/ticket-132-operator-loop-nm4-evidence-spine-status` |
| Date | 2026-06-14 |
| Risk | low |
| Pre-ticket audit | Not required (`pre_ticket_audit_required: false`) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-130.md` (cadence satisfied; 2 done since: 131, 132) |
| Main tip before branch | `331d967` |

## Scope

### In

- `inspect_nm4_evidence_spine_status()` in `operator_loop.py`
- Plan output key `nm4_evidence_spine_status`
- Unit tests in `test_operator_loop.py`

### Out

- Live LLM flags
- Public export/site changes
- Writes from plan mode
- Docs cross-link chain

## Changed files

| File | Change |
|------|--------|
| `rge/modules/operator_loop.py` | NM-4 evidence spine inspector + plan wiring |
| `tests/unit/test_operator_loop.py` | 3 tests (missing, reconciled, plan includes block) |
| `tickets/ticket-132.json` | status done |
| `tickets/ticket-133.json` | seeded next step |
| `tickets/TICKET_QUEUE.md` | ticket-132 done |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Plan surfaces read-only NM-4 evidence DB spine status | **PASS** |
| 2 | No writes from plan mode | **PASS** (read-only SQLite `mode=ro`) |
| 3 | Golden tests mock-only pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |
| 5 | Public export/site untouched | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_operator_loop.py -q   # 40 passed
python -m pytest tests/golden -q                       # 142 passed
python -m pytest -q                                    # 487 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full      # pass
python -m rge.modules.operator_loop --mode plan          # nm4 block present
```

## Manual CLI verification

`python -m rge.modules.operator_loop --mode plan` on repo with local evidence DB:

| Field | Value |
|-------|-------|
| `evidence_db_path` | `data/db/live_research_evidence.sqlite` |
| `spine_stage` | `reconciled` |
| `score_event_count` | **1** |
| `status` | `ok` |

## Spec deviations

Default evidence DB path now resolves relative to `root` (matching scratch DB pattern)
instead of using the absolute `default_live_evidence_db()` path. Operator-visible path
unchanged for real repo runs; fixes test isolation and any non-default project root.

## Merge to main

Merged @ **`b7152b9`** (`Merge branch 'phase-2/ticket-132-operator-loop-nm4-evidence-spine-status'`).
Pushed to `origin/main`.

## Recommended next ticket

**ticket-133** — README NM-4 evidence DB operator quickstart (document tickets 127–132 spine).

## Suggested next prompt

`/rge-run-next-ticket` for ticket-133, or `/rge-principal-audit` after two consecutive done tickets (131–132) if cadence review desired before docs.
