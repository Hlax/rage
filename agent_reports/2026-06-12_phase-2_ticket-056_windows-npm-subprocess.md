# Phase 2 Ticket-056 — Windows npm Subprocess

- Ticket: ticket-056
- Branch: `phase-2/ticket-056-windows-npm-subprocess`
- Date: 2026-06-12
- Status: done

## Summary

Fixed Windows `FileNotFoundError` for `operator_loop --mode execute-safe` public-site build by resolving `npm` with `shutil.which()` and using the full executable path in subprocess argv. Omits `public_site_build` when npm is absent. `verify` inherits the fix via `safe_verification_commands`.

## Changes

| File | Update |
| ---- | ------ |
| `rge/modules/operator_loop.py` | `resolve_npm_executable()`; resolved argv |
| `tests/unit/test_operator_loop.py` | +3 unit/integration tests |
| `AGENTS.md` | execute-safe npm / `--skip-site` note |

## Commands run (mock only)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_operator_loop.py -q   # 24 passed
python -m pytest -q                                    # 199 passed, 1 deselected
python -m rge.modules.safety_auditor --audit full      # pass
python -m rge.cli verify --skip-site                   # pass
python -m rge.modules.operator_loop --mode execute-safe  # pass (post-commit, clean tree)
```

## Non-goals honored

- No verify_runner separate change
- No shell=True globally
- No CI workflow edits

## Merge

Pending commit hash after merge to `main` and push.

## Recommended next ticket

Pause for human review — principal audit cadence at 3/3 done tickets since post-053 (054–056); run `/rge-principal-audit` before next Post-Phase-2 feature ticket.
