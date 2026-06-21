# Agent Report: One-Button Research Run v1

**Date:** 2026-06-20  
**Packet:** one-button-research-run-v1  
**Verdict:** GO

## Goal

Collapse the manual operator chain into one safe CLI command with mock defaults,
scratch paths, private atlas export, and research quality JSON.

## Implementation

- `rge/modules/one_button_research_run.py` — orchestrator
- `rge/cli.py` — extended `run` subcommand flags

### Default behavior

- Mock LLM, no network (`fixture_mode` pipeline)
- Scratch DB + artifact dir under `data/db/` and `data/reports/`
- Private run report, atlas snapshot, coherence sidecar, quality JSON
- Recommended improvement ticket JSON (no auto-promotion)
- No merge/push/public publish

### Optional flags (fail closed)

| Flag | Gate |
|------|------|
| `--live-network` | `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO` |
| `--live-llm-extract` | `RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`, staged extract gate |
| `--sync-atlas-public` | operator fixture packet refresh (review-gated) |

## Operator command

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli run `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/scratch_research.sqlite `
  --artifact-dir data/reports/scratch_research `
  --export-atlas `
  --quality-report data/reports/scratch_research/research_quality.json
```

## Verification

| Check | Result |
|-------|--------|
| `tests/unit/test_one_button_research_run.py` | PASS |
| `python -m rge.cli verify --skip-site` | exit 0 |

## Next recommended packet

**local-scheduled-research-loop**
