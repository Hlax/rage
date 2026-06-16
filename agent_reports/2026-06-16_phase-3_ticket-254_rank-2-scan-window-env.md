# Agent Report: ticket-254 — Configurable rank-2 staged candidate scan window env

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-254  
**Branch:** `phase-3/ticket-254-rank-2-scan-window-env`  
**Main tip before branch:** `a7ad1c02d95780c7be4623323a2e21202436f1ca`  
**Status:** implemented

## Summary

Added `RGE_STAGED_RANK2_SCAN_MAX` (default 10, bounded 1–50) to `rge/config.py` with
`parse_staged_rank2_scan_max()`. Rank-2 staged candidate selection and live pytest
helpers honor env when `max_scan` is omitted. Documented in `12_RUNTIME_CONFIG.md`.

## Audit gate

- **Satisfied:** cadence satisfied (2 done since checkpoint-251 before this ticket); `risk_level: low`

## Scope in / out

**In:** Config parsing, staged selection env resolution, unit tests, runtime config doc.

**Out:** Live Ollama proofs, heuristic marker changes, orchestrator live LLM.

## Changed files

| File | Change |
|------|--------|
| `rge/config.py` | `RGE_STAGED_RANK2_SCAN_MAX`, `parse_staged_rank2_scan_max`, `RgeConfig` field |
| `rge/modules/staged_candidate_selection.py` | Env-backed default scan window |
| `tests/unit/live_staged_candidates.py` | `max_scan=None` honors env |
| `tests/unit/test_staged_rank2_candidate_heuristic_scan.py` | Env override + bounds tests |
| `docs/agents/12_RUNTIME_CONFIG.md` | Env table row |
| `tickets/ticket-254.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-255.json` | Principal audit seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `RGE_STAGED_RANK2_SCAN_MAX` overrides default with sane bounds | **PASS** |
| 2 | CLI and live pytest helpers honor override | **PASS** |
| 3 | Unit tests cover default and override | **PASS** |
| 4 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_rank2_candidate_heuristic_scan.py -q  # 8 passed
python -m pytest tests/golden -q                                              # 142 passed
```

Safety audit not required — staged selection config only.

## Manual CLI verification

Not performed — unit tests cover env resolution; orchestrator uses same helper.

## Spec deviations

None.

## Merge to main

- Merge commit: _(pending)_
- Post-merge pytest: _(pending)_

## Recommended next ticket

**ticket-255** — Principal audit post-ticket-254 (cadence threshold after merge).

## Suggested next prompt

`/rge-principal-audit` or `/rge-run-next-ticket` for **ticket-255**.
