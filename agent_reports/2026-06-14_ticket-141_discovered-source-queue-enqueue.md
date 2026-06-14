---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-141
---

# ticket-141: Enqueue Discovered Candidates to Staging Research Queue

## Summary

Added **`discover-sources --rank-only --enqueue --db <path>`** to persist ranked OpenAlex
candidates into staging **`candidate_sources`** and **`research_queue`** tables. Stable IDs
(`disc_{provider}_{provider_id}`), idempotent re-run per research question + provider, rejected
marketing candidates stored but not queued. **No accepted-table writes, no ingest, no fetch.**

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-141 |
| Branch | `phase-2/ticket-141-discovered-source-queue-enqueue` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-141_discovered-source-queue-enqueue-audit.md` (GO) |
| Main tip before branch | `03f68d9` |

## Scope

### In

- `discovered_candidate_source_id()` / `enqueue_discovered_candidates()` in `research_queue.py`
- CLI flags: `--enqueue`, `--db`, `--question` on `discover-sources` (requires `--rank-only`)
- 8 unit tests in `test_discovered_source_queue_enqueue.py`

### Out

- Fetch/ingest/extract, Playwright, schema, public site
- Accepted `sources` / `claims` writes

## Changed files

| File | Change |
|------|--------|
| `rge/modules/research_queue.py` | staging enqueue helpers |
| `rge/cli.py` | discover-sources enqueue flags + DB persist |
| `tests/unit/test_discovered_source_queue_enqueue.py` | 8 tests |
| `tickets/ticket-141.json` | status done |
| `tickets/ticket-142.json` | seeded fetch follow-on |
| `tickets/TICKET_QUEUE.md` | queue update |
| `agent_reports/2026-06-14_pre-ticket-141_discovered-source-queue-enqueue-audit.md` | audit on file |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `--rank-only --enqueue --db` persists staging rows | **PASS** |
| 2 | Idempotent re-run per question + provider | **PASS** |
| 3 | No accepted sources/claims writes | **PASS** |
| 4 | Mocked unit tests only | **PASS** |
| 5 | Golden mock-only pass | **PASS** (142) |
| 6 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_SOURCE_NETWORK = "0"
python -m pytest tests/unit/test_discovered_source_queue_enqueue.py -q   # 8 passed
python -m pytest tests/golden -q                                         # 142 passed
python -m pytest -q                                                      # 519 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                        # pass
```

## Manual CLI verification

```powershell
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
python -m rge.cli discover-sources --provider openalex --query "human AI creativity" `
  --rank-only --enqueue --db data/db/discover_enqueue.sqlite --question rq_creativity_ai_diversity
# status completed; enqueue_status completed; queue_count >= 1
# Re-run: enqueue_status already_queued
```

## Spec deviations

None.

## Merge to main

Merged to `main` as `511236d60bb3027ddcd42d732959af179db705bf` (2026-06-14).
Post-merge pytest: 519 passed, 6 deselected.

## Recommended next ticket

**ticket-142** — Fetch staged candidate source from queue URL (pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-142 audit, then `/rge-run-next-ticket` for ticket-142.
