---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-140
---

# ticket-140: Research Queue Candidate Ranking from Discovered Sources

## Summary

Added deterministic **discovered-source ranking** using domain-pack `source_preferences.yaml`
credibility priors and the existing `golden_v0.1.0` queue-priority formula. The
`discover-sources --rank-only` flag attaches `ranked_candidates[]` to CLI JSON — **no DB
writes, no ingest, no fetch**.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-140 |
| Branch | `phase-2/ticket-140-discovered-source-queue-ranking` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-140_discovered-source-queue-ranking-audit.md` (GO) |
| Main tip before branch | `80cb883` |

## Scope

### In

- `rank_discovered_candidates()` / `score_discovered_candidate()` in `research_queue.py`
- Deterministic `source_type` inference, relevance token overlap, recency from year
- `discover-sources --rank-only` CLI flag
- 12 unit tests in `test_discovered_source_queue_ranking.py`

### Out

- Staging DB enqueue (deferred to ticket-141)
- Fetch/ingest/extract, schema, public site
- LLM relevance scoring
- Changes to GT09 fixture ranking path

## Changed files

| File | Change |
|------|--------|
| `rge/modules/research_queue.py` | discovered candidate inference, scoring, ranking |
| `rge/modules/source_discovery.py` | `--rank-only` overlay on discover payload |
| `rge/cli.py` | `--rank-only` argument |
| `tests/unit/test_discovered_source_queue_ranking.py` | 12 tests |
| `tickets/ticket-140.json` | status done |
| `tickets/ticket-141.json` | seeded follow-on enqueue ticket |
| `tickets/TICKET_QUEUE.md` | queue update |
| `agent_reports/2026-06-14_pre-ticket-140_discovered-source-queue-ranking-audit.md` | audit on file |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Ranked candidates via source_preferences (mocked tests) | **PASS** |
| 2 | `--rank-only` returns credibility/recency signals; no ingest | **PASS** |
| 3 | Network gate unchanged (ticket-139) | **PASS** |
| 4 | No DB writes to accepted sources/claims | **PASS** |
| 5 | Golden mock-only pass | **PASS** (142) |
| 6 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_SOURCE_NETWORK = "0"
python -m pytest tests/unit/test_discovered_source_queue_ranking.py -q   # 12 passed
python -m pytest tests/golden -q                                         # 142 passed
python -m pytest -q                                                      # 511 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                        # pass
```

## Manual CLI verification

With `RGE_ALLOW_SOURCE_NETWORK=1` and live OpenAlex (operator env):

```powershell
python -m rge.cli discover-sources --provider openalex --query "human AI creativity" --rank-only
# status ok; ranked_candidates[] sorted by priority_score; no DB writes
```

Blocked without opt-in (unchanged from ticket-139):

```powershell
python -m rge.cli discover-sources --provider openalex --query "human AI creativity" --rank-only
# status blocked; reason source_network_disabled; exit 1
```

## Spec deviations

- Staging `--enqueue` deferred to ticket-141 per pre-ticket audit hardened scope (rank-only primary path still satisfies acceptance).

## Merge to main

Pending merge.

## Recommended next ticket

**ticket-141** — Enqueue discovered candidates to staging research queue (pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-141 audit, then `/rge-run-next-ticket` for ticket-141.
