# Agent Report: ticket-264 — Staged spine CLI stdout asserts rank candidate ids

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-264  
**Branch:** `phase-3/ticket-264-staged-spine-cli-stdout-candidate-ids`  
**Main tip before branch:** `fc8a2b20a28eb6564fc9eb8e71355cf042a848b5`  
**Status:** done

## Summary

Extended `test_staged_fixture_mode_run_spine.py` CLI entry tests to capture stdout and
assert `rank1_candidate_id` / `rank2_candidate_id` in the final `fixture_staged` run
JSON for both `--fixture-mode --staged-spine` and `--staged-spine` entry paths. Added
helpers to parse multi-document CLI stdout (sub-step JSON plus final run payload).

## Audit gate

- **Satisfied:** `agent_reports/2026-06-16_principal-audit-post-ticket-262.md`; cadence satisfied; `risk_level: low`

## Scope in / out

**In:** Unit test assertions + stdout JSON parsing helpers.

**Out:** Production logic changes, live Ollama, public export/site.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_staged_fixture_mode_run_spine.py` | CLI stdout candidate-id assertions for both entry paths |
| `tickets/ticket-264.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-265.json` | Follow-on README docs seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | CLI staged-spine entry test captures stdout and asserts rank candidate ids | **PASS** |
| 2 | Both `--fixture-mode --staged-spine` and `--staged-spine` paths covered | **PASS** |
| 3 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_fixture_mode_run_spine.py -q  # 4 passed
python -m pytest tests/golden -q                                    # 142 passed
python -m pytest -q                                                 # 689 passed, 30 deselected
```

Safety audit not required — test-only ticket.

## Manual CLI verification

Not performed — unit tests exercise `main()` with mocked network.

## Spec deviations

None. CLI stdout includes intermediate step JSON; tests parse the final `fixture_staged` document.

## Merge to main

- Merge commit: `fa8632e92057a6c6c8560e4c84ee367b4d6ebdf5`
- Post-merge pytest: `689 passed, 30 deselected`

## Recommended next ticket

**ticket-265** — README documents staged run rank candidate id output fields.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
