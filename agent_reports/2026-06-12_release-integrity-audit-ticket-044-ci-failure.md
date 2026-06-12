---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Release Integrity Audit — Ticket-044 CI / Packaging Failure

- Date: 2026-06-12
- Auditor: principal engineer / adversarial truth-check
- Scope: verify ticket-044 completion claims against GitHub CI reality; fix release-blocking `pip install -e ".[dev]"` failure
- `main` SHA audited (pre-hotfix): `daeeeb666c3a9fc5f51764068fc3392c464890aa`

## Executive summary

The ticket-044 agent report claimed a healthy merge and verification, but **GitHub Golden Gate CI was failing** at the first packaging step because `README.md` was encoded as **UTF-16 LE** (`BOM 0xFF 0xFE`) while `pyproject.toml` declares `readme = "README.md"` and setuptools reads it as UTF-8.

**Previous release status was BLOCKED** despite local pytest passing on a pre-installed environment.

Hotfix applied on branch `hotfix/packaging-readme-utf8`: convert README to UTF-8, add `scripts/validate_packaging_utf8.py`, CI pre-install check, unit regression test.

## Claim-by-claim honesty review (ticket-044 report)

| Previous claim | Verified true? | Evidence | Correction needed? |
|---|---|---|---|
| "Done, committed, merged to main, and pushed" | **Partially** | `git log` shows merge `8822e1d` and push to `origin/main` at `daeeeb6`. Commits exist on remote. | Yes — merge existed but **release was not healthy** because required CI step failed online. |
| "pytest -q: 174 passed, 1 deselected" | **Partially** | Reproduced locally on Python 3.14 with existing dev env before hotfix. Fresh venv **could not** `pip install -e ".[dev]"` until README fix. | Yes — count was true only where package was already installed; **not CI-parity**. Post-hotfix fresh venv: **175 passed**, 1 deselected. |
| "safety_auditor --audit full: pass" | **Yes (local)** | Ran successfully locally pre- and post-hotfix. | No for local runs. **Not verified in GitHub CI** (job never reached this step). |
| "principal_audit_gate --next-ticket ticket-044: satisfied" | **Yes (local)** | `cadence_status: satisfied` with post-ticket-042 checkpoint. | No for logic correctness. Unrelated to CI packaging failure. |
| "Next trustworthy actions: run pre-ticket audit before ticket-045" | **Yes** | ticket-045 is `medium` risk; gate returns `blocked_missing_pre_ticket_audit`. | No. |
| "Human approval not required for ticket-044" | **Partially** | Merge/push did occur without extra human gate. | Yes — **should have required CI green** before declaring release healthy. |
| Implied repo safe to proceed despite CI failing | **No — misleading** | User report: CI fails at `pip install -e ".[dev]"`. Local reproduction: `UnicodeDecodeError` reading README via setuptools `expand.read_files`. `gh` unavailable (not authenticated); relied on user report + local CI-parity reproduction. | **Yes — critical correction.** Release was blocked; ticket-045 must not start until CI passes post-hotfix. |

## Root cause

| Field | Detail |
|---|---|
| **File** | `README.md` |
| **Encoding** | UTF-16 LE with BOM (`0xFF 0xFE` at offset 0) |
| **Why setuptools reads it** | `pyproject.toml` line 9: `readme = "README.md"` → setuptools `expand._read_file()` opens with default UTF-8 during editable install metadata expansion |
| **CI failure point** | `.github/workflows/golden-gate.yml` step `python -m pip install -e ".[dev]"` on `ubuntu-latest` Python 3.11 |
| **Local reproduction** | Fresh venv + `pip install -e ".[dev]"` failed identically before fix; succeeds after UTF-8 conversion |

## Hotfix changes

| File | Change |
|---|---|
| `README.md` | Converted UTF-16 LE → UTF-8 |
| `scripts/validate_packaging_utf8.py` | Pre-install UTF-8/BOM validation |
| `tests/unit/test_packaging_metadata_utf8.py` | Regression test |
| `.github/workflows/golden-gate.yml` | Run validator before `pip install` |
| `.gitattributes` | Pin `README.md` / `pyproject.toml` as UTF-8 text, LF |

## Verification (post-hotfix, fresh venv, CI-parity install path)

```powershell
python scripts/validate_packaging_utf8.py          # pass
python -m venv .venv-ci-test
.\.venv-ci-test\Scripts\python -m pip install -U pip setuptools wheel
.\.venv-ci-test\Scripts\python -m pip install -e ".[dev]"   # pass
$env:RGE_LLM_MODE="mock"
.\.venv-ci-test\Scripts\python -m pytest -q                 # 175 passed, 1 deselected
.\.venv-ci-test\Scripts\python -m pytest tests/golden -q    # 135 passed
.\.venv-ci-test\Scripts\python -m rge.modules.safety_auditor --audit full  # pass
.\.venv-ci-test\Scripts\python -m rge.modules.principal_audit_gate --next-ticket ticket-045
# cadence_status: satisfied; status: blocked (medium risk, no pre-ticket-045 audit)
```

**GitHub Actions:** not directly queried (`gh auth login` required). CI pass on remote **not confirmed in this environment** until post-push workflow completes.

## Current release status

| State | Status |
|---|---|
| `main` at `daeeeb6` (pre-hotfix) | **BLOCKED** — CI packaging step fails |
| Hotfix commit | `2548a98` on `hotfix/packaging-readme-utf8` |
| Merge on `main` | `ac0189b` pushed to `origin/main` |
| Post-hotfix | **PENDING CI** — install path verified locally; GitHub Golden Gate not queried (`gh` unauthenticated) |

## Next safest move

1. Merge and push `hotfix/packaging-readme-utf8` to `main`.
2. Confirm GitHub Golden Gate workflow is green end-to-end (install → golden → pytest → safety → npm build).
3. Do **not** start ticket-045 until CI is green and pre-ticket-045 audit is written (medium risk).
4. Optionally seed ticket-046 for operator-loop `done_without_implementation_commit` false positive on ticket-043 commit message pattern.
