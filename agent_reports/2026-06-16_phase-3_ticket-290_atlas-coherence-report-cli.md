# Agent Report: ticket-290 — Atlas coherence report CLI

**Date:** 2026-06-16  
**Ticket:** ticket-290  
**Branch:** `phase-3/ticket-290-atlas-coherence-report-cli`  
**Main tip before branch:** `939833f`  
**Audit gate:** Not required — low-risk operator-private CLI; no public export/site/schema changes.

## Summary

Added `atlas-coherence-report` CLI subcommand: reads private atlas snapshot JSON
(`--snapshot`), writes coherence verdict JSON (`--out-json`) and optional markdown
(`--out-md`). Stdout emits machine-readable status with `overall_coherence_verdict`.

## Scope

**In:** CLI handler + parser, unit tests, golden scaffold command list.

**Out:** Public export/site, schema migrations, live_network CI, live Ollama.

## Changed files

| File | Change |
|------|--------|
| `rge/cli.py` | `_cmd_atlas_coherence_report` + argparse |
| `tests/unit/test_atlas_coherence_report_cli.py` | CLI happy path + error path (3 tests) |
| `tests/golden/test_00_scaffold.py` | Register subcommand in help inventory |
| `tickets/ticket-290.json` | Status `done` |
| `tickets/ticket-291.json` | Seeded live pipeline follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| CLI `--snapshot` → `--out-json` (+ optional `--out-md`) | **PASS** |
| Stdout JSON includes verdict and output paths | **PASS** |
| Creativity fixture CLI run passes; golden + full pytest | **PASS** — 142 golden, 743 full |
| No public export/site/schema changes | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_coherence_report_cli.py -q  # 3 passed
python -m pytest tests/golden -q                                   # 142 passed
python -m pytest -q                                                # 743 passed, 32 deselected

python -m rge.cli atlas-coherence-report `
  --snapshot fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json `
  --out-json $env:TEMP/atlas_coherence_cli_test.json `
  --out-md $env:TEMP/atlas_coherence_cli_test.md
```

Safety audit not required — reads operator-private snapshot; writes temp operator reports only.

## Manual CLI verification

Creativity fixture run returned `"status": "completed"` and `overall_coherence_verdict: pass`.

## Spec deviations

None.

## Drift note

Operator tooling only — keeps ticket-289 product proof usable without custom scripts.
Next ticket should stay product/live centered (chained live pipeline), not docs cross-links.

## Recommended next ticket

**ticket-291** — Live staged export + coherence report CLI pipeline proof (`live_network`).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `042a07a`
