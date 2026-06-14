---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-142
---

# ticket-142: Fetch Staged Candidate Source from Queue URL

## Summary

Added **`fetch-candidate`** CLI to load a `candidate_sources` row by id, fetch its URL
bytes when `RGE_ALLOW_SOURCE_NETWORK=1`, and write a gitignored artifact under
`data/sources/staged/` (or `--out`). Returns structured JSON with checksum, content-type,
and byte count. **No ingest, no claims extraction, no accepted-table writes.**

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-142 |
| Branch | `phase-2/ticket-142-staged-candidate-fetch` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-142_staged-candidate-fetch-audit.md` (GO) |
| Main tip before branch | `75e8f16` |

## Scope

### In

- `fetch-candidate` CLI (`--candidate`, `--db`, `--out`)
- `fetcher.py` staged URL fetch + artifact write + idempotent checksum check
- `CandidateSourceRepository.get_by_id()`
- 8 unit tests; scaffold help lists `fetch-candidate`

### Out

- Playwright/Scrapfly, ingest, claim extraction, schema, public site
- `sources` / `claims` writes

## Changed files

| File | Change |
|------|--------|
| `rge/modules/fetcher.py` | staged URL fetch helpers |
| `rge/db/repositories.py` | `get_by_id` for candidate_sources |
| `rge/cli.py` | `fetch-candidate` command |
| `tests/unit/test_staged_candidate_fetch.py` | 8 tests |
| `tests/golden/test_00_scaffold.py` | help includes fetch-candidate |
| `tickets/ticket-142.json` | status done |
| `tickets/ticket-143.json` | seeded ingest follow-on |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | fetch-candidate loads row, fetches to gitignored path with network opt-in | **PASS** |
| 2 | JSON reports status, checksum, content-type | **PASS** |
| 3 | Mocked unit tests only | **PASS** |
| 4 | No accepted sources/claims writes | **PASS** |
| 5 | Golden mock-only pass | **PASS** (142) |
| 6 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_SOURCE_NETWORK = "0"
python -m pytest tests/unit/test_staged_candidate_fetch.py -q   # 8 passed
python -m pytest tests/golden -q                                # 142 passed
python -m pytest -q                                             # 527 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full               # pass
```

## Manual CLI verification

```powershell
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
python -m rge.cli fetch-candidate --candidate disc_openalex_W2741809807 `
  --db data/db/discover_enqueue.sqlite --out data/sources/staged
# status completed; artifact_path + checksum in JSON
```

## Spec deviations

- `research_queue.py` unchanged (file artifact only; no queue status DB updates).

## Merge to main

Merged to `main` as `a2a3e89e99f7b7574b50ce77e57e6cf30996abdb` (2026-06-14).
Post-merge pytest: 527 passed, 6 deselected.

## Recommended next ticket

**ticket-143** — Ingest from staged fetch artifact (pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-143 audit, then `/rge-run-next-ticket` for ticket-143.
