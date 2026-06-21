# Agent Report: Local Scheduled Research Loop

**Date:** 2026-06-20  
**Packet:** local-scheduled-research-loop  
**Verdict:** GO

## Goal

Local-safe scheduled runner for Windows Task Scheduler with `local_mock_daily`
profile.

## Implementation

- `rge/modules/scheduled_research_loop.py`
- `scripts/run_scheduled_research_loop.py`
- `scripts/run_scheduled_research_loop.ps1`
- README Operator Quickstart + `schtasks` example

### Profile: `local_mock_daily`

- Requires `RGE_LLM_MODE=mock`
- Blocks live network, live LLM, paid/cloud API env gates
- Runs one-button mock research + full safety audit
- Writes timestamped `agent_reports/` markdown + latest JSON
- Compact status under `data/reports/scheduled_research/`
- Refuses merge, push, ticket promotion, public publish

## Operator command

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_scheduled_research_loop.py --profile local_mock_daily
```

## Verification

| Check | Result |
|-------|--------|
| `tests/unit/test_scheduled_research_loop.py` | PASS |
| `python -m rge.cli verify --skip-site` | exit 0 |

## Next recommended packet

**live-ollama-abstract-extract-gate**
