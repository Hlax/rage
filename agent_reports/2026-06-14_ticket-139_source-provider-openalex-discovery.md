---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-139
---

# ticket-139: Source Provider Registry and OpenAlex Discovery Proof

## Summary

Implemented the first **API-first source discovery provider** path: provider registry,
OpenAlex metadata discovery, `RGE_ALLOW_SOURCE_NETWORK=1` opt-in gate, and structured
CLI responses. Returns candidate metadata JSON only — **no ingest, fetch, scraping,
DB writes, or public surface changes**.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-139 |
| Branch | `phase-2/ticket-139-source-provider-openalex-discovery` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-139_source-provider-openalex-discovery-audit.md` (GO) |
| Principal audit gate | satisfied; pre-ticket audit on file |
| Main tip before branch | `069690c` |

## Scope

### In

- `source_providers/` registry + OpenAlex provider
- `RGE_ALLOW_SOURCE_NETWORK`, `OPENALEX_MAILTO`, `OPENALEX_API_KEY` config
- Extended `discover-sources` CLI (`--provider`, `--query`, `--limit`, `--domain`, `--health`)
- Mocked unit tests + OpenAlex fixture JSON

### Out

- HTTP in CI/golden default runs (mocked in tests)
- Fetch/ingest/extract, Playwright, schema, public site

## Changed files

| File | Change |
|------|--------|
| `rge/config.py` | source network + OpenAlex env |
| `rge/modules/source_network.py` | opt-in helper |
| `rge/modules/source_providers/*` | registry + OpenAlex |
| `rge/modules/source_discovery.py` | CLI orchestration |
| `rge/cli.py` | discover-sources args |
| `fixtures/source_providers/openalex_works_sample.json` | mock API fixture |
| `tests/unit/test_source_provider_openalex.py` | 9 tests |
| `.env.example` | documented new env vars |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Provider registry + discover/health | **PASS** |
| 2 | OpenAlex env config; no secrets printed | **PASS** |
| 3 | Mocked discover returns candidate metadata | **PASS** |
| 4 | Network blocked without opt-in | **PASS** |
| 5 | Structured errors (no stack traces to operator) | **PASS** |
| 6 | Mocked unit tests only in CI path | **PASS** |
| 7 | Golden mock-only pass | **PASS** (142) |
| 8 | Full pytest pass | **PASS** (499) |
| 9 | Safety audit pass | **PASS** |
| 10 | No DB/ingest/fetch/public changes | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"; $env:RGE_ALLOW_SOURCE_NETWORK = "0"
python -m pytest tests/unit/test_source_provider_openalex.py -q   # 9 passed
python -m pytest tests/unit/test_source_discovery_stub.py -q      # 3 passed
python -m pytest tests/golden -q                                  # 142 passed
python -m pytest -q                                             # 499 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                 # pass
```

## Manual CLI verification

**Health (no network):**

```powershell
python -m rge.cli discover-sources --provider openalex --health
# status ok; mailto_set/api_key_set booleans only
```

**Blocked without opt-in:**

```powershell
python -m rge.cli discover-sources --provider openalex --query "human AI creativity"
# status blocked; reason source_network_disabled; exit 1
```

**Live network verification:** skipped in this run (CI-safe). Operators may run with
`RGE_ALLOW_SOURCE_NETWORK=1` and mocked or real OpenAlex separately.

## Candidate metadata shape

Each candidate includes: `provider`, `provider_id`, `title`, `authors`, `year`, `doi`,
`open_access_url`, `landing_page_url`, `abstract`, `domain_pack`, `discovered_at`.

## Spec deviations

None.

## Merge to main

Merged to `main` as `ea9a4323421fa096999cf9f08f8732e2fe3e2a16` (2026-06-14).
Post-merge pytest: 499 passed, 6 deselected.

## Recommended next ticket

**ticket-140** — Research queue candidate ranking from discovered sources (product; pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-140 audit, then `/rge-run-next-ticket` for ticket-140.
