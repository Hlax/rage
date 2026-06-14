---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-138
---

# ticket-138: Source Discovery Stub CLI (Phase 3 Entry)

## Summary

Added `discover-sources` CLI returning structured Phase 3 `not_implemented` JSON
(exit code 2). Centralized payload in `source_discovery.py`. **No network, HTTP,
provider APIs, fetcher, Ollama, schema, or public surface changes.**

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-138 |
| Branch | `phase-2/ticket-138-source-discovery-stub-cli` |
| Date | 2026-06-14 |
| Risk | low |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-138_source-discovery-stub-cli-readiness-audit.md` (GO) |
| Principal audit gate | cadence satisfied |
| Main tip before branch | `f768214` |

## Scope

### In

- `discover-sources` subcommand
- `build_discover_sources_not_implemented_payload()` helper
- Unit tests (3)
- Golden scaffold command list update

### Out

- Network/API/fetcher/Playwright/Ollama/schema/public export/operator_loop

## Changed files

| File | Change |
|------|--------|
| `rge/cli.py` | `discover-sources` command + handler |
| `rge/modules/source_discovery.py` | stub payload helper |
| `tests/unit/test_source_discovery_stub.py` | new (3 tests) |
| `tests/golden/test_00_scaffold.py` | list `discover-sources` |
| `tickets/ticket-138.json` | status done |
| `tickets/ticket-139.json` | seeded |
| `tickets/TICKET_QUEUE.md` | ticket-138 done |

## Command output shape

```json
{
  "status": "not_implemented",
  "command": "discover-sources",
  "phase": "3",
  "detail": "Phase 3 source discovery is not implemented yet."
}
```

Exit code: **2**

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Structured not_implemented JSON | **PASS** |
| 2 | Exit code 2 | **PASS** |
| 3 | Unit tests | **PASS** (3) |
| 4 | Golden mock-only pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |
| 6 | Public export/site untouched | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_source_discovery_stub.py -q   # 3 passed
python -m pytest tests/golden -q                               # 142 passed
python -m pytest -q                                            # 490 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full              # pass
python -m rge.cli discover-sources                             # JSON above, exit 2
```

## Manual CLI verification

`python -m rge.cli discover-sources` → valid JSON, `$LASTEXITCODE = 2`.

## Spec deviations

None. Source discovery is **not** implemented — command surface only.

## Merge to main

Merged @ **`6fd0356`** (`Merge branch 'phase-2/ticket-138-source-discovery-stub-cli'`).
Pushed to `origin/main`.

## Recommended next ticket

**ticket-139** — Source provider registry and OpenAlex discovery proof (medium risk; pre-ticket audit GO).

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-139** (first real API-first provider — not docs/checkpoint/stub).
