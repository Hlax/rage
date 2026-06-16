# Agent Report: ticket-273 — CLI prove-arbitrary-source-bundle second-run idempotency test

**Date:** 2026-06-16  
**Ticket:** ticket-273  
**Branch:** `phase-3/ticket-273-cli-proof-bundle-idempotency`  
**Main tip before branch:** `0cb03b28e74c4f31b5bf4359678bf67f67fa6624`  
**Audit gate:** `agent_reports/2026-06-16_principal-audit-post-ticket-270.md` (GO; 2 done since audit: 272, 273)

## Summary

Added `test_proof_bundle_cli_second_run_is_idempotent_on_same_temp_paths` proving two
`main(["prove-arbitrary-source-bundle", ...])` invocations on the same temp DB/paths
emit stable stdout bundle payloads (`_stable_bundle_snapshot`) with `usable_output: true`.
Refactored shared CLI argv into `_proof_bundle_cli_argv` for happy-path and idempotency tests.

## Scope

**In:** CLI idempotency unit test + argv helper in `test_operator_proof_bundle.py`.

**Out:** Production code changes, README/AGENTS.md, live LLM, public site.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_operator_proof_bundle.py` | CLI idempotency test + `_proof_bundle_cli_argv` |
| `tickets/ticket-273.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-274.json` | Follow-on seeded |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Unit test invokes prove-arbitrary-source-bundle via main() twice on same temp paths | **PASS** |
| Second stdout bundle payload matches stable counts and usable_output from first run | **PASS** |
| Mock LLM only; no live_network | **PASS** |
| Golden pass | **PASS** — 142 |
| Full pytest pass | **PASS** — 707 |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_operator_proof_bundle.py -q  # 10 passed
python -m pytest tests/golden -q                              # 142 passed
python -m pytest -q                                           # 707 passed, 30 deselected
```

Safety audit not required — test-only change.

## Manual CLI verification

Not performed — covered by unit test with patched network and `capsys` stdout parsing.

## Spec deviations

None.

## Merge to main

Merge commit: `e9ca08863ac13f11fa38e892dfb477e16a374dc0`

## Recommended next ticket

**ticket-274** — Operator proof bundle on-disk `bundle-out` JSON stable across CLI second run.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
