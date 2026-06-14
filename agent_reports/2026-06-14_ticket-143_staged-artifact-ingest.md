---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-143
---

# ticket-143: Ingest from Staged Fetch Artifact

## Summary

Added **`ingest-staged`** CLI to load ticket-142 fetch artifacts (by `--candidate` or
`--artifact`), verify optional `--checksum`, extract text from HTML, and persist
**sources + chunks** via `ingest_local_source`. **No automatic claim extraction.**

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-143 |
| Branch | `phase-2/ticket-143-staged-artifact-ingest` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-143_staged-artifact-ingest-audit.md` (GO) |
| Main tip before branch | `51c6634` |

## Scope

### In

- `ingest-staged` CLI (`--domain`, `--candidate`, `--artifact`, `--checksum`, `--staging-dir`, `--db`)
- `fetcher.py` artifact resolution, checksum verify, HTML text extraction, `ingest_staged_artifact()`
- 9 unit tests; scaffold help lists `ingest-staged`

### Out

- extract-claims automation, live LLM, Playwright, schema, public site

## Changed files

| File | Change |
|------|--------|
| `rge/modules/fetcher.py` | staged ingest helpers |
| `rge/cli.py` | `ingest-staged` command |
| `tests/unit/test_staged_artifact_ingest.py` | 9 tests |
| `tests/golden/test_00_scaffold.py` | help includes ingest-staged |
| `tickets/ticket-143.json` | status done |
| `tickets/ticket-144.json` | seeded extract spine follow-on |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | ingest-staged by candidate/path + checksum verify | **PASS** |
| 2 | Persists sources/chunks only; no auto extract | **PASS** |
| 3 | Mocked/fixture unit tests | **PASS** |
| 4 | Golden mock-only pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_artifact_ingest.py -q   # 9 passed
python -m pytest tests/golden -q                              # 142 passed
python -m pytest -q                                           # 536 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full               # pass
```

## Manual CLI verification

```powershell
python -m rge.cli ingest-staged --domain creativity `
  --candidate disc_openalex_W2741809807 --checksum <sha256> `
  --staging-dir data/sources/staged --db <path.sqlite>
# status ingested; source + chunk_count in JSON; claims table empty
```

## Spec deviations

None.

## Merge to main

Pending merge.

## Recommended next ticket

**ticket-144** — Extract claims from staged-ingested source (mock spine; pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-144 audit, then `/rge-run-next-ticket` for ticket-144.
