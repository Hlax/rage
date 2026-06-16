# Agent Report: ticket-270 — Verify CLI lists prove-arbitrary-source-bundle in mock gate

**Date:** 2026-06-16  
**Ticket:** ticket-270  
**Branch:** `phase-3/ticket-270-verify-proof-bundle-checklist`  
**Main tip before branch:** `144d377b1784f6e5df2909bb528bf7c08a756562`  
**Audit gate:** Not required — `risk_level: low`; cadence satisfied (2 done since pre-ticket-267)

## Summary

`research verify` JSON now includes `operator_checklist` with the optional `prove-arbitrary-source-bundle` command (not run automatically) plus `arbitrary_source_proof_bundle_status` mirroring operator loop plan mode.

## Scope

**In:** `verify_runner.py` checklist helper, verify CLI description, `test_cli_verify.py`.

**Out:** Running proof bundle inside verify, README/AGENTS.md, public site, live LLM.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/verify_runner.py` | `mock_gate_operator_checklist`, plan fields in report |
| `rge/cli.py` | Verify help mentions operator checklist |
| `tests/unit/test_cli_verify.py` | New — checklist + CLI stdout tests |
| `tickets/ticket-270.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-271.json` | Principal audit follow-on seeded |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| verify --skip-site JSON references prove-arbitrary-source-bundle | **PASS** |
| No live LLM or live_network changes | **PASS** |
| Golden pass | **PASS** — 142 |
| Full pytest pass | **PASS** — 705 |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_cli_verify.py -q  # 3 passed
python -m pytest tests/golden -q                 # 142 passed
python -m pytest -q                              # 705 passed, 30 deselected
```

Safety audit not required — verify output metadata only; no export/site changes.

## Manual CLI verification

```powershell
python -m rge.cli verify --skip-site
```

Stdout JSON includes `operator_checklist[0].command == "prove-arbitrary-source-bundle"`.

## Spec deviations

Checklist logic lives in `verify_runner.py` (verify implementation module) rather than duplicating in `cli.py`; `_cmd_verify` remains a thin delegate.

## Merge to main

_Pending merge._

## Recommended next ticket

**ticket-271** — Principal audit post-ticket-270 (cadence: three done tickets 268–270 since pre-ticket-267).

## Suggested next prompt

```txt
/rge-principal-audit
```
