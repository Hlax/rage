# Phase 2 Ticket-054 — Operator Verify Docs + Windows Local Verify Reliability

- Ticket: ticket-054
- Branch: `phase-2/ticket-054-operator-verify-docs`
- Date: 2026-06-12
- Status: done

## Summary

Ticket-054 became **operator verify docs + Windows local verify reliability**.

1. Documented `python -m rge.cli verify` as the preferred mock-only verification entry point in `AGENTS.md` and `README.md`, with Windows `python -m rge.cli` fallback when `research` is off PATH.
2. Repaired Windows-local verification:
   - `test_default_pytest_deselects_live_smoke` uses temp-file stdout/stderr and `stdin=subprocess.DEVNULL` for nested pytest (fixes WinError 6 under pytest capture on Windows/Python 3.14).
   - `verify_runner` prints `[verify] running …` / result lines to stderr so `python -m rge.cli verify --skip-site` shows progress during ~80s runs.

## Root cause

- **Pytest failure:** Meta-test spawns `python -m pytest --collect-only` to assert `tests/smoke/` is not collected by default. With default stdin inheritance inside an active pytest session on Windows, `subprocess.Popen._make_inheritable` raised `OSError: [WinError 6] The handle is invalid`. Test passed in isolation; failed only in full `pytest -q`.
- **Verify “hang”:** Not a deadlock — `verify --skip-site` runs golden (~36s) + full pytest (~38s) + safety audit sequentially with stdout buffered until final JSON. No progress made it look stuck.

## Changes

| File | Update |
| ---- | ------ |
| `AGENTS.md` | Default verification leads with `python -m rge.cli verify` / `--skip-site` |
| `README.md` | Quickstart, verification table, Install section for verify + Windows fallback |
| `tests/unit/test_ci_golden_gate.py` | Windows-stable nested pytest subprocess capture |
| `rge/modules/verify_runner.py` | Stderr progress lines per verification check |
| `tickets/ticket-054.json` | Scope and acceptance criteria |
| `tickets/TICKET_QUEUE.md` | Ticket-054 row and queue notes |

## Commands run (mock only)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_ci_golden_gate.py -q   # 4 passed
python -m pytest tests/golden -q                        # 139 passed
python -m pytest -q                                     # 190 passed, 1 deselected
python -m rge.modules.safety_auditor --audit full       # pass
python -m rge.cli verify --skip-site                    # pass (~80s, stderr progress visible)
python -m rge.modules.operator_loop --mode plan         # pass
```

## Merge

Pending commit hash below after merge to `main` and push.

## Recommended next ticket

Post-Phase-2 roadmap item requiring pre-ticket audit, or low-risk operator doc polish if gaps remain.
