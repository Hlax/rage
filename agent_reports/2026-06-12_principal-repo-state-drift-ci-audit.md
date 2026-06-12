---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Principal Repo State / Drift / CI Audit

- Date: 2026-06-12
- Auditor: principal engineer / release auditor / adversarial truth-check
- Scope: full repo-state, git-truth, CI-parity, drift, and ticket-honesty audit before ticket-045
- Environment note: GitHub API/Actions **inaccessible** (`gh` CLI installed but not authenticated; no `GH_TOKEN`). All CI conclusions below are from local CI-parity reproduction of `.github/workflows/golden-gate.yml` steps.

## 1. Executive verdict

`PARTIAL — local gates pass but release/remote truth is unverified`

Every local gate passes in a clean venv (install, 175 pytest, 135 golden, safety audit, public-site build). But the **committed** CI workflow on `origin/main` contains a step that is guaranteed to fail on every run, the fix for it sits **uncommitted** in the working tree, and remote CI status cannot be queried from this environment. Release truth is therefore blocked-by-construction until the CI fix is committed, pushed, and a green run is confirmed on GitHub.

## 2. Current git truth

| Field | Value |
|---|---|
| Branch | `main` |
| Local HEAD SHA | `4e32d440bf72ebcd50770ea73c694fdd7eaad2a5` |
| `origin/main` SHA | `4e32d440bf72ebcd50770ea73c694fdd7eaad2a5` |
| Divergence | **None** — local `main` == `origin/main` |
| Dirty files | 3 modified, uncommitted: `.github/workflows/golden-gate.yml`, `tests/unit/test_ci_golden_gate.py`, `.cursor/commands/rge-principal-audit.md` |
| Untracked | None tracked-worthy. `__pycache__/*.pyc` files exist on disk but are correctly gitignored (`git check-ignore` confirms) |
| `.gitignore` | Correct: covers `__pycache__/`, `*.egg-info/`, `build/`, `dist/`, venvs, `.pytest_cache/`, `.env*` local files, `data/`, `node_modules/`, `.next/`, `out/` |

Claimed commits verified (all exist locally **and** on `origin/main`):

| Claim source | Commit | Exists local | Exists remote |
|---|---|---|---|
| ticket-043 implementation | `cc1c17c` "Extend safety auditor to validate data exports" | yes | yes |
| ticket-044 implementation | `b43b009` | yes | yes |
| ticket-044 merge | `8822e1d` | yes | yes |
| README UTF-8 hotfix | `2548a98` | yes | yes |
| Hotfix merge | `ac0189b` | yes | yes |
| Hotfix doc | `4e32d44` (current tip) | yes | yes |

Latest relevant commits on `origin/main`: `4e32d44` (hotfix doc), `ac0189b` (hotfix merge), `2548a98` (README UTF-8 fix), `daeeeb6`/`8822e1d`/`b43b009` (ticket-044), `cc1c17c` (ticket-043).

**The uncommitted dirty files are themselves the next release blocker's fix** (see section 3). They were left in the working tree by a prior session with no commit, no report, and no ticket — this is the only undocumented state in the repo.

## 3. CI / install truth

**`python -m pip install -e ".[dev]"`: PASS** in a fresh venv (Python 3.14.3; pip/setuptools/wheel upgraded first). Python 3.11 is **not installed** on this machine (only 3.10 and 3.14), so exact CI interpreter parity could not be reproduced; the failure mode being tested (setuptools reading README as UTF-8) is interpreter-version-independent.

**UTF-8 packaging failure: FIXED.** `README.md` now begins `23 20 52 65` ("# Re", UTF-8, no BOM). `python scripts/validate_packaging_utf8.py` passes. The fix (`2548a98`) is merged and pushed to `origin/main`.

**However, CI cannot be green at `origin/main` even with the install fixed.** Exact root cause of the next failure, reproduced locally:

- The committed workflow step "Confirm live_smoke not collected by default" runs:
  `python -m pytest --collect-only -q 2>&1 | grep -q live_smoke` and exits 1 on a match.
- The collect-only output **always** contains the string `live_smoke`, because ticket-040's own meta-tests are named `tests/unit/test_ci_golden_gate.py::test_pyproject_excludes_live_smoke_by_default` and `::test_default_pytest_deselects_live_smoke`.
- Local reproduction: collect-only output matches `live_smoke` = True, matches `tests/smoke/` = False. The actual smoke test (`tests/smoke/test_live_ollama_smoke.py`) is correctly deselected.
- Conclusion: **this CI step has been self-defeating since ticket-040 merged.** Prior runs never reached it (they died earlier at the README install step). After the hotfix push, CI advances to this step and fails there.

The uncommitted working-tree changes fix exactly this (grep for `tests/smoke/` instead of `live_smoke`, plus a hardened subprocess-based meta-test). I verified the fixed meta-tests pass (4/4) and the fixed grep condition does not match. The fix is correct but **not committed, not pushed, not reported**.

**GitHub/online checks: INACCESSIBLE.** `gh` is unauthenticated; no token in the environment. I cannot confirm any remote run status, branch protection rules, or PR state. Per audit rules, release status is therefore not claimable as PASS.

## 4. Verification commands

All run from a fresh venv (`.venv-audit`, Python 3.14.3) with `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0`, against the working tree (which includes the 3 uncommitted CI-fix files).

| Command | Result | Evidence / notes |
| ------- | ------ | ---------------- |
| `python -m pip install -U pip setuptools wheel` | pass | clean venv |
| `python -m pip install -e ".[dev]"` | **pass** | `Successfully installed ... rge-0.1.0`; UTF-8 failure fixed |
| `python scripts/validate_packaging_utf8.py` | pass | "packaging metadata UTF-8 validation: pass" |
| `python -m pytest -q` | **175 passed, 1 deselected** | 36s; deselected = live_smoke |
| `python -m pytest tests/golden -q` | **135 passed** | mock-only, no Ollama |
| `pytest --collect-only -q` grep check | committed grep **FAILS**, fixed grep passes | root cause in section 3 |
| `python -m pytest tests/unit/test_ci_golden_gate.py -q` | 4 passed | includes uncommitted hardened test |
| `python -m rge.modules.safety_auditor --audit full` | **pass** | status `pass`, all checks |
| `python -m rge.modules.principal_audit_gate --next-ticket ticket-045` | cadence `satisfied`; status **`blocked`** | `blocked_missing_pre_ticket_audit` — ticket-045 is medium risk, no pre-ticket-045 audit exists |
| `python -m rge.modules.operator_loop --mode plan` | **`blocked`** | dirty tree + `done_without_implementation_commit` drift flag for ticket-043 (false positive, see section 7) |
| `research --help` | pass | CLI entry point works from clean install |
| `research run --topic ... --fixture-mode` | pass, all steps; `safety_audit_status: pass` | repo stays clean after run (ticket-034 holds) |
| `research export-public --limit 100` | pass, **but dirties committed files** | rewrites `updated_at`/`generated_at` timestamps in `apps/public-site/public/data/*.json`; restored via `git checkout --` (see section 7) |
| `cd apps/public-site && npm run build` | **pass** | 12 static pages (`/`, `/about`, 404, 2 cards, 6 concepts) |
| GitHub Actions status | **INACCESSIBLE** | `gh` unauthenticated; no `GH_TOKEN` |

## 5. Operating protocol compliance

| Rule / expectation | Source doc | Compliant? | Evidence | Fix needed |
| ------------------ | ---------- | ---------- | -------- | ---------- |
| One ticket per branch | AGENTS.md | yes | every ticket has its own `phase-N/ticket-NNN-*` branch | none |
| Ticket done requires report in `agent_reports/` | TICKET_QUEUE.md rules | yes | reports exist for all 44 done tickets | none |
| Merge + push after done ticket (temp step 9) | AGENTS.md step 9 | yes | ticket-043/044 + hotfix merged and pushed; merge hashes recorded | none |
| Every implementation run writes a report | AGENTS.md / 11_PROTOCOL | **no** | the 3-file CI grep fix in the working tree has **no commit, no report, no ticket** | commit as hotfix with report (this audit documents it) |
| Don't claim success without running commands | AGENTS.md | partial | ticket-044 report claimed health while CI was failing remotely (already corrected by release-integrity audit) | cultural: require CI-green before "done" claims |
| Principal audit cadence (≥3 done tickets) | 11_PROTOCOL | yes | post-ticket-042 checkpoint; only 2 done since (043, 044); gate says `satisfied` | none |
| Medium/high tickets need pre-ticket audit | 11_PROTOCOL / gate | yes (enforced) | gate returns `blocked_missing_pre_ticket_audit` for ticket-045 | write pre-ticket-045 audit before starting it |
| Operator loop never merges/pushes/promotes | 11_PROTOCOL | yes | code inspection + plan-mode output lists forbidden actions | none |
| Improvement drafts promoted only with `--confirm` review | 11_PROTOCOL | yes | draft still sits in `data/tickets/improvement_ticket_latest.json`, unpromoted | none |
| No raw prompts/paths/secrets in public export | AGENTS.md / safety model | yes | safety audit full pass; export validation in place | none |
| CI enforces mock-only golden gates | 11_PROTOCOL | **broken in practice** | workflow exists but has never completed green (install failure, then self-defeating grep step) | commit + push the CI grep fix; confirm green run |

## 6. Ticket/report honesty audit

| Claim | Verified true? | Evidence | Correction |
| ----- | -------------- | -------- | ---------- |
| ticket-043: "Status: done (await merge to main)", commit `6abcc1c` on branch, "no merge/push performed in this run" | **yes (honest)** | report explicitly said not merged/pushed; work later reached main as `cc1c17c` and is on `origin/main` | none — note the main-line commit message lacks "ticket-043", which trips the operator-loop drift detector (false positive) |
| ticket-043: "169 passed, 1 deselected; safety audit pass" | yes (local) | consistent with current 175-test suite minus later additions; current suite passes | none |
| ticket-044: "Done, committed, merged to main, and pushed" | **yes for git, no for release** | `b43b009`/`8822e1d` exist on `origin/main`; but GitHub CI was failing at install step at that moment | already corrected by `2026-06-12_release-integrity-audit-ticket-044-ci-failure.md` |
| ticket-044: "pytest 174 passed" | yes-with-caveat | true on pre-installed env; fresh venv could not even install until README hotfix | corrected in release-integrity audit |
| Release-integrity audit: "README was UTF-16 LE; hotfix converts to UTF-8; fresh venv install passes" | **yes** | README now UTF-8 (`23 20 52 65`); validator passes; clean-venv install reproduced pass | none |
| Release-integrity audit: "Post-hotfix: PENDING CI" | yes — and now **superseded** | even post-hotfix, CI cannot pass: the live_smoke grep step is self-defeating (section 3) | this audit identifies the next concrete CI failure |
| ticket-040 report: "Ready to merge; GitHub Actions first run pending push" | misleading in hindsight | the workflow it added contained the always-failing grep step; "pending" became "failing" | fixed by committing the working-tree changes |
| Queue notes: "Operator loop cadence now satisfied after post-ticket-042 audit" | yes | gate output: `cadence_status: satisfied`, 2 done since checkpoint | none |

Overall: reports were **honest about local results** and the most recent release-integrity audit was genuinely adversarial and accurate. The systemic gap was treating "merged and pushed" as release-healthy without a green remote run — which the rules now explicitly forbid.

## 7. Drift / false wiring findings

| Finding | Severity | Evidence | Why it matters | Recommended fix |
| ------- | -------- | -------- | -------------- | --------------- |
| CI "live_smoke not collected" step always fails (greps its own meta-test names) | **High** | `pytest --collect-only -q` output contains `test_pyproject_excludes_live_smoke_by_default`; committed grep matches; reproduced locally | Golden Gate CI can never go green at `origin/main`; every push/PR appears broken; blocks merge truth | Commit + push the existing working-tree fix (grep `tests/smoke/` instead) as a hotfix with report |
| CI fix exists only as uncommitted working-tree changes, no ticket/report | **High** | `git status`: 3 modified files; no report mentions them | Violates "every implementation run writes a report"; risk of silent loss or confusion about repo state | Same hotfix commit; this audit serves as its documentation |
| `research export-public` dirties committed public-site JSON (non-deterministic `updated_at`/`generated_at`) | Medium | running it during this audit modified `apps/public-site/public/data/{build_info,public_cards}.json` (timestamps only); restored via `git checkout --` | ticket-034's repo-clean guarantee covers fixture-mode runs only; any operator running plain export-public creates spurious diffs and possible accidental commits | Small follow-up ticket: deterministic/fixture timestamps for committed snapshot, or write only to `data/exports/` unless `--publish` |
| Operator loop `done_without_implementation_commit` false positive for ticket-043 | Medium | plan mode reports drift; commit `cc1c17c` exists on main/origin but message lacks "ticket-043" | operator loop reports `blocked` even on a healthy tree, training operators to ignore it (alarm fatigue) | Seed small ticket (already suggested as ticket-046 candidate): match commits via ticket JSON/branch metadata, not message substring |
| Old `test_default_pytest_deselects_live_smoke` ran nested in-process `pytest.main()` | Low | committed version of `tests/unit/test_ci_golden_gate.py` | nested pytest is flaky and only asserted exit code, not the actual property | already fixed in the uncommitted hardened subprocess test |
| Local Python (3.14/3.10) ≠ CI Python (3.11) | Low | `py -0p`: 3.11 not installed | "works locally" never exactly equals CI; contributed to install failure going unnoticed | optional: install 3.11 locally or accept documented divergence |
| No GitHub access from agent environment | Medium (structural) | `gh` unauthenticated | every release claim ends at "pending CI"; remote truth permanently unverifiable by agents | human authenticates `gh auth login` (or sets `GH_TOKEN`) so audits can read Actions status |

Checked and **not** found: no stubs/placeholders wired into production paths (mock LLM mode is an explicit, gated design, not a stub leak); golden tests assert real DB writes and export contents, not no-ops; safety auditor checks routes/exports/secrets/raw-html/model-tools and now `data/exports/`; tickets marked done all have matching implementation commits on `origin/main`.

## 8. Environment readiness

All RGE configuration has code-level defaults (`rge/config.py`); `.env` files and env vars only override. **No secrets are required for local tests, CI, or fixture runs.** No missing keys are blocking anything — current blockers are CI-workflow logic, not environment.

| Env var / dependency | Required for | Present? | Blocking? | Notes |
| -------------------- | ------------ | -------- | --------- | ----- |
| `RGE_LLM_MODE` | local tests + CI (set to `mock`) | defaulted; CI sets explicitly | no | mock is default; fail-closed registry |
| `RGE_ALLOW_LIVE_LLM` | live smoke only (`1` to opt in) | defaulted `0` | no | live calls require this AND `RGE_LLM_MODE=ollama` |
| `RGE_TEST_LLM_MODE` | CI/tests (force mock) | defaulted; CI sets explicitly | no | |
| `OLLAMA_BASE_URL` | live smoke only | defaulted `http://127.0.0.1:11434` | no | not needed for any gate |
| `RGE_LOCAL_LLM` | live smoke only | defaulted `qwen2.5:7b` | no | |
| `RGE_LLM_TIMEOUT_SECONDS` / `RGE_LLM_TEMPERATURE` / `RGE_LLM_SCHEMA_VERSION` | optional | defaulted | no | |
| `RGE_EMBEDDING_MODE` / `RGE_EMBEDDING_MODEL` | optional (later phases) | defaulted | no | unused in Phase 1/2 |
| `GH_TOKEN` / `gh auth login` | remote CI truth (audits) | **absent** | **yes, for release verification only** | name-only; human action required |
| Python 3.11 | exact CI parity | absent (3.10/3.14 present) | no (3.14 reproduces gates) | optional install |
| Node 22 + npm deps | public-site build | present | no | build passes, 12 pages |

No secret values were read, printed, or committed during this audit.

## 9. Current release status

`RELEASE BLOCKED`

Plain language: the code on `origin/main` is good — it installs cleanly, all 175 tests pass, the safety audit passes, and the public site builds. But the CI workflow committed on `origin/main` contains a check that fails by construction (it greps for `live_smoke` and finds its own test names), so GitHub's Golden Gate cannot go green on any push or PR. The fix is already written and verified in this working tree but has not been committed or pushed. Until that fix lands and a green GitHub Actions run is confirmed by a human (or an authenticated `gh`), no merge can honestly be called release-healthy.

## 10. Next safest move

**Repair CI/install/git blocker** (exactly one move): commit the three working-tree files as a hotfix, push, and confirm the GitHub Golden Gate run goes green end-to-end.

Draft repair ticket:

- **Title:** hotfix: fix self-defeating live_smoke grep in Golden Gate CI
- **Branch:** `hotfix/ci-live-smoke-grep`
- **Problem:** CI step "Confirm live_smoke not collected by default" greps collect-only output for `live_smoke`, which always matches ticket-040's own meta-test names, failing every run.
- **Changes (already in working tree, verified):** grep `tests/smoke/` instead of `live_smoke` in `.github/workflows/golden-gate.yml`; hardened subprocess meta-test in `tests/unit/test_ci_golden_gate.py`; matching doc line in `.cursor/commands/rge-principal-audit.md`.
- **Acceptance criteria:**
  1. `python -m pytest --collect-only -q 2>&1` does not contain `tests/smoke/`, and the workflow grep matches nothing.
  2. `pytest -q` passes (175+, 1 deselected) and `pytest tests/unit/test_ci_golden_gate.py -q` passes.
  3. After push, the GitHub Golden Gate workflow completes **green through all steps** (validate UTF-8 → install → golden → pytest → grep check → safety audit → npm build), confirmed by a human or authenticated `gh run list`.
- **Rollback:** revert the hotfix commit.

After CI is green, the order is: (1) seed small ticket for the operator-loop ticket-043 drift false positive, (2) small ticket for `export-public` timestamp churn in committed JSON, (3) write the required pre-ticket-045 audit (medium risk), and only then (4) start ticket-045. **Do not start ticket-045 now** — it is blocked by both the CI repair and the missing pre-ticket audit.
