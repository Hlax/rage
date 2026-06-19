# Agent Report: ticket-362 — Default research run mock staged-spine path

**Date:** 2026-06-19  
**Ticket:** ticket-362  
**Branch:** `phase-3/ticket-362-default-research-run-staged-spine`

## Summary

Bare `research run --topic --domain` now defaults to mock staged-spine orchestration
(exit 0 on temp `--db` with patched network). `--fixture-mode` without `--staged-spine`
still runs the full MVP fixture pipeline. Result JSON includes `default_run_mode:
staged_spine` when the default path is used.

## Changed files

| File | Change |
|------|--------|
| `rge/cli.py` | Default `_cmd_run` to staged spine; updated help text |
| `tests/golden/test_26_full_mvp_run.py` | Replaced not_implemented guard with default staged-spine test |
| `tests/unit/test_staged_fixture_mode_run_spine.py` | Added bare-run CLI test |
| `README.md` | Honest default-run note |
| `tickets/ticket-362.json` | Ticket record |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden/test_26_full_mvp_run.py tests/unit/test_staged_fixture_mode_run_spine.py -q
# 13 passed
python -m rge.cli verify --skip-site
```

## Recommended next ticket

**ticket-363** — Autonomous loop improvement promotion golden proof.
