---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-055 Export Snapshot Versioning Readiness Audit

- Audit type: pre-ticket readiness — export snapshot versioning and scratch history
- Date: 2026-06-12
- Scope: read-only. No implementation. No queue edits. No ticket seeding.
- Prior checkpoint: `agent_reports/2026-06-12_principal-audit-post-ticket-053.md`
- Phase 2 queue: tickets 034–054 **done**; next item from Post-Phase-2 roadmap

## 1. Executive verdict

**GO — seed ticket-055**

Export snapshot versioning/history is the correct next Post-Phase-2 item. Gaps are real, bounded, and addressable without live envs or public-site schema expansion. Scope must stay narrow: scratch-only history under gitignored `data/exports/`, manifest metadata, documented `export_schema_version` bump procedure, and safety-auditor coverage for new history paths. Committed `apps/public-site/public/data/` must remain unchanged unless `--publish` or fixture-mode explicitly applies.

---

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Working tree | **clean** | `git status --short` → empty |
| Local `HEAD` | `b620fe3c0012235732100b3e05c13e49b0b2f883` | `git rev-parse HEAD` |
| `origin/main` | `b620fe3` (matches local) | `git rev-parse origin/main` |
| Golden Gate (current tip) | **success** | run **27429626355** on `b620fe3` |
| Golden tests | **139 passed** | reported local `pytest tests/golden -q` |
| Full pytest | **190 passed, 1 deselected** | reported local `pytest -q` |
| Safety audit | **pass** | `python -m rge.modules.safety_auditor --audit full` |
| Verify (Python-only) | **pass** | `python -m rge.cli verify --skip-site` with stderr progress |
| Operator loop cadence | **satisfied** | 1 done ticket since post-053 (ticket-054); threshold 3 |
| Pending improvement drafts | **none** | `improvement_ticket_latest.json` empty per prior operator loop |
| Tickets 053–054 | **landed on main** | `git log --oneline -5` |

---

## 3. Why this ticket now

Phase 2 roadmap tickets **034–054 are complete** (`tickets/TICKET_QUEUE.md` → “seed next ticket from Post-Phase-2 roadmap”). The Post-Phase-2 section names **export snapshot versioning/history** as the next unresolved core-engine / public-artifact item (`research verify` is already done in ticket-051).

**Why it is justified:**

1. **`export_schema_version` exists but is static** — `EXPORT_SCHEMA_VERSION = "0.1.0"` in `card_exporter.py`; written to `build_info.json`. MVP regression policy requires versioning when public export schema changes (`docs/agents/07_MVP_ACCEPTANCE_TESTS.md` §10). No documented bump workflow exists.
2. **Scratch exports overwrite in place** — default mock `export-public` writes three JSON files to `data/exports/` only (ticket-047). Each run replaces the prior bundle; operators cannot compare prior scratch snapshots before deciding to `--publish`.
3. **Review workflow is git-centric for committed data only** — `docs/deployment/public-site-static-hosting.md` instructs `git diff apps/public-site/public/data/`, but scratch exports live under gitignored `data/` (`.gitignore` → `data/`). History must live in scratch space with an operator-visible trail.
4. **Safety auditor gap for future history layout** — `_audit_data_exports()` scans only flat `data/exports/*.json`, not subdirectories. Any history design must extend this scan or history artifacts will bypass audit.
5. **Milestone trigger satisfied** — operator-loop and AGENTS protocol flag public-export / `card_exporter` changes for pre-ticket audit. This audit fulfills that gate.

**Why not other Post-Phase-2 items first:**

- Cloud provider / embeddings / concept graph: higher risk, live or export-policy surface expansion; not the smallest next unit.
- Self-improvement positive promotion: no pending drafts; audits warn against faking gaps.

---

## 4. Current export behavior

| Area | Current behavior | Gap | Risk |
| ---- | ---------------- | --- | ---- |
| `export_schema_version` | Constant `0.1.0` in `card_exporter.py`; emitted in `build_info.json` | No bump procedure doc; no test asserting version discipline on schema change | **medium** — silent schema drift |
| Scratch export target | Mock default → `data/exports/` only (`resolve_export_targets`) | Overwrites prior bundle; no retained history | **low** — operator review friction |
| `--publish` | Live mode requires explicit flag to write `apps/public-site/public/data/` | Working as designed (ticket-047 + unit tests) | **low** |
| Fixture-mode export | Writes both `data/exports/` and public-site with deterministic timestamps | Separate path; not history | **low** |
| Committed public-site JSON | `apps/public-site/public/data/{build_info,public_cards,public_memos}.json` — fixture timestamps, 2 cards | Updated only via `--publish` or fixture-mode; not churned by default mock export | **low** if guards hold |
| `export-public` CLI help | Description says export goes to “data/exports **and** the public site” | Misleading for default mock path (minor doc drift) | **low** |
| Safety auditor `data/exports` | Flat `*.json` scan + bundle validation when trio present | No subdirectory/history scan | **medium** if history added without audit extension |
| Deployment checklist | Safety audit + `git diff` on committed snapshots | No scratch history compare step | **low** — doc gap |
| Retained history | **None** | No manifest, no timestamped bundles | **medium** — pre-publish review gap |

---

## 5. Public/export safety assessment

| Check | Status | Notes |
| ----- | ------ | ----- |
| Raw prompts in export | **blocked** | `validate_public_export_bundle` + `FORBIDDEN_VALUE_PATTERNS` in safety auditor |
| Local paths | **blocked** | Golden private fields stripped; policy tests in GT11/GT23 |
| Secrets / API keys | **blocked** | Regex scan on public and scratch JSON |
| Full private source text | **blocked** | Curated field whitelist in `card_exporter` / `public_export_policy` |
| Hidden evaluator notes | **blocked** | `GOLDEN_PRIVATE_FIELDS` never exported |
| Unsafe HTML/script in static site | **not introduced by this ticket** | Site renders whitelisted JSON fields; ticket-055 must not add raw HTML fields |
| Public write / ingestion / agent routes | **none** | Static export only; no new routes proposed |
| Accidental committed data churn | **guarded** | ticket-047 publish gate; must preserve in ticket-055 |
| History duplication leak risk | **requires design discipline** | History copies must be the **same validated bundle** already written to scratch; no extra fields, no private DB columns |

**Conclusion:** Ticket-055 is safe to proceed if history artifacts are copies of fail-closed validated exports and safety auditor coverage extends to all new paths under `data/exports/`.

---

## 6. Snapshot/history design recommendation

**Smallest safe version (recommended):**

1. **Keep current “latest” scratch bundle** at `data/exports/{public_cards,public_memos,build_info}.json` (unchanged overwrite behavior).
2. **Add manifest file** `data/exports/snapshot_manifest.json` (append-only or replace-with-array) recording:
   - `export_schema_version`
   - `generated_at`
   - `card_count` / `memo_count`
   - `bundle_id` or relative path to history copy
   - `publish_public` / `fixture_mode` flags
3. **Add timestamped history copies** under `data/exports/history/<bundle_id>/` containing the same three JSON files (canonical serialization already used by `canonical_json_dumps`).
4. **Retention cap** — keep last N history bundles (e.g. 10) via simple pruning in `card_exporter`; avoid unbounded `data/` growth.
5. **Opt-out flag** — `--no-snapshot-history` on `export-public` for tests and CI determinism; default **on** for operator exports.
6. **Do not** change committed `apps/public-site/public/data/` unless `--publish` or `fixture_mode=True`.
7. **Document** `export_schema_version` bump checklist: constant change → golden test update → manifest notes → safety audit → optional `--publish` after human review.
8. **Extend** `_audit_data_exports()` to validate all `data/exports/history/**/*.json` bundles (or walk history subdirs and run `validate_public_export_bundle` per complete trio).

**Explicitly avoid in ticket-055:**

- New public JSON fields
- Auto-`--publish`
- UI for diffing snapshots
- Committing history to git (stays under gitignored `data/`)

---

## 7. Execute-safe / npm PATH note

**Classification: `separate small ticket`**

**Evidence:**

- `where.exe npm` and `shutil.which('npm')` resolve to `C:\Program Files\nodejs\npm.CMD`.
- `subprocess.run(['npm', 'run', 'build'], ...)` raises `FileNotFoundError: [WinError 2]` on Windows/Python 3.14 — reproducible in isolation.
- Root cause: Windows `.cmd` shims require `shell=True` or executable path from `shutil.which()`; `operator_loop.py` uses bare `argv: ['npm', 'run', 'build']` (same pattern as `verify_runner` for subprocess steps that succeed for `python.exe`).

**Why not blocking ticket-055:**

- Export/snapshot work validates via `python -m rge.cli verify --skip-site` and golden/safety gates.
- Golden Gate CI on Linux runs `npm run build` successfully (run 27429626355).
- Public-site build authority for release remains **CI** until Windows subprocess is fixed.

**Recommended follow-up (not ticket-055 core):**

- Small ticket: resolve `npm` on Windows in `operator_loop` / `verify_runner` via `shutil.which('npm')` or documented `shell=True` for site-build step only.
- Optional doc line in README/AGENTS: “if execute-safe fails on Windows at npm, use `verify --skip-site` and rely on CI for site build.”

---

## 8. Proposed ticket-055 scope

### Title
Export snapshot manifest and scratch history for operator review

### Problem
Default `export-public` overwrites gitignored scratch JSON without retained history or a version-bump workflow, making pre-publish review harder and leaving MVP regression policy (“schema changes require versioning”) undocumented in operator practice.

### Scope
- Append manifest + optional timestamped history copies under `data/exports/history/` on each export (with retention cap and `--no-snapshot-history` opt-out).
- Preserve ticket-047 publish-only semantics for committed public-site JSON.
- Document `export_schema_version` bump procedure.
- Extend safety auditor to scan history artifacts.
- Unit/golden tests for manifest, retention, opt-out, and unchanged mock default targets.

### Expected files
- `rge/modules/card_exporter.py`
- `rge/cli.py` (flag + help text accuracy)
- `rge/modules/safety_auditor.py`
- `tests/unit/test_export_snapshot_history.py` (or extend existing export tests)
- `tests/golden/test_11_public_card_export.py` or GT23 extension if needed
- `docs/deployment/public-site-static-hosting.md` and/or `README.md` (minimal operator section)
- `tickets/ticket-055.json`, agent report (on implementation — not in this audit pass)

### Acceptance criteria
- Mock default `export-public` still writes only `data/exports/` latest trio unless `--publish` / fixture-mode.
- Each export creates manifest entry + history copy unless `--no-snapshot-history`.
- Retention cap enforced; oldest pruned deterministically.
- `export_schema_version` bump steps documented.
- Safety audit passes with history directories present.
- Golden + full pytest pass in mock mode; no Ollama.

### Test plan
```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
python -m rge.cli verify --skip-site
```

### Safety considerations
- History bundles must pass same `validate_public_export_bundle` as latest scratch.
- No new public fields; no auto-publish; history stays gitignored.
- Auditor must cover all new JSON under `data/exports/`.

### Non-goals
- Cloud provider, embeddings, concept graph UI
- Live Ollama / live smoke
- DB schema migrations
- npm/execute-safe Windows fix (separate ticket)
- Committing scratch history to git

### Rollback plan
Revert ticket-055 branch; delete `data/exports/history/` and manifest locally; restore prior export behavior.

### Risk level
`medium`

---

## 9. Final recommendation

**Seed ticket-055 as drafted** (narrow scope per §6), on its own branch, after human approval of this audit.

Do **not** implement until:
1. Human confirms ticket-055 over other Post-Phase-2 items.
2. `tickets/ticket-055.json` is seeded from §8.
3. Implementation agent follows one-ticket-per-branch protocol.

Optional parallel follow-up: seed a **low-risk Windows npm subprocess ticket** (ticket-056) — independent of ticket-055.

---

## Commands executed

```powershell
cd C:\Users\guestt\OneDrive\Desktop\Kooya\rage
git status --short
git rev-parse HEAD
git rev-parse origin/main
gh run list --limit 5

# Code/doc inspection (read-only)
# rge/modules/card_exporter.py, rge/cli.py, rge/modules/safety_auditor.py
# apps/public-site/public/data/*.json
# tests/unit/test_export_publish_gate.py
# docs/deployment/public-site-static-hosting.md

# npm subprocess diagnosis
python -c "import subprocess; subprocess.run(['npm','--version'], capture_output=True)"
python -c "import shutil; print(shutil.which('npm'))"
where.exe npm
```

## Suggested human prompt

```txt
Pre-ticket-055 audit complete: GO — seed ticket-055 (export snapshot manifest + scratch history).
Read agent_reports/2026-06-12_pre-ticket-055_export-snapshot-versioning-readiness-audit.md.
If approved, seed tickets/ticket-055.json from §8 and implement on phase-2/ticket-055-export-snapshot-history.
Do not include npm/execute-safe Windows fix in ticket-055 unless scope is explicitly expanded.
Mock mode only; no --publish without review; no live envs.
```
