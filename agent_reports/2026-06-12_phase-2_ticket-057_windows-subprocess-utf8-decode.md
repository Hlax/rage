# Phase 2 Ticket-057 — Windows Subprocess UTF-8 Decode

- Ticket: ticket-057
- Branch: `phase-2/ticket-057-windows-subprocess-utf8-decode`
- Date: 2026-06-12
- Status: done

## Summary

Fixed Windows subprocess output capture for `operator_loop --mode execute-safe` and `research verify`. Both modules now use `rge/subprocess_capture.run_captured`, which decodes stdout/stderr as UTF-8 with `errors="replace"` instead of relying on the locale default (`cp1252` on Windows). This prevents background `UnicodeDecodeError` in subprocess reader threads when npm/Next.js emit UTF-8 bytes.

## Root cause

`subprocess.run(..., capture_output=True, text=True)` without an explicit `encoding` uses `locale.getpreferredencoding(False)` — `cp1252` on Windows. Next.js/npm build output can include UTF-8 sequences (e.g. byte `0x8f`, checkmarks) that are invalid in cp1252. Python's `_readerthread` then raises `UnicodeDecodeError` even when the child process exits 0.

Observed during post-ticket-056 principal audit: execute-safe passed all checks but logged a background exception during `public_site_build` capture.

## Changes

| File | Update |
| ---- | ------ |
| `rge/subprocess_capture.py` | New `run_captured()` helper: UTF-8 + `errors="replace"`, `stdin=DEVNULL` |
| `rge/modules/operator_loop.py` | Default subprocess runners and `execute_safe_checks` use `run_captured` |
| `rge/modules/verify_runner.py` | Default command runner uses `run_captured` |
| `tests/unit/test_subprocess_capture.py` | 5 unit/integration tests for decode safety, tails, and exit codes |
| `tickets/ticket-057.json` | Ticket seed |
| `tickets/TICKET_QUEUE.md` | Queue row + notes |

## Commands run (mock only; no live envs)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_subprocess_capture.py tests/unit/test_operator_loop.py tests/unit/test_verify_runner.py -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
python -m rge.cli verify --skip-site
python -m rge.modules.operator_loop --mode execute-safe
```

## Test results

| Command | Result |
| ------- | ------ |
| Unit tests (subprocess_capture + operator_loop + verify_runner) | **32 passed** |
| Full pytest | **204 passed**, 1 deselected |
| Safety audit | **pass** |
| `verify --skip-site` | **pass** |
| `operator_loop --mode execute-safe` | **pass** (post-commit, clean tree on main) |

## UnicodeDecodeError status

**Gone.** Post-fix `execute-safe` on a clean tree completed with `execution_status: pass` and no background `UnicodeDecodeError` in stderr. `public_site_build` exit code 0 with captured output tails present.

## Live env confirmation

No live Ollama, no live smoke, no cloud credentials. `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0` throughout.

## Merge

- Branch commit: `aadbc59d1ecb7ef9193f50f1b870bf44a824c2a7`
- Merged to `main` via fast-forward from `dc2dd8f`
- Pushed to `origin/main`
- Golden Gate run **27431881399** → **success** at `aadbc59`

## Recommended next ticket family

**Cloud provider adapter** — next highest-value Phase 3 item per post-ticket-056 audit; requires pre-ticket audit (medium-high risk). Concept graph viz and embeddings remain deferred until after adapter boundary is proven.
