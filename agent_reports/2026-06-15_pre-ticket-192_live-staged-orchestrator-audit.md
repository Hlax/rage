---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-193
category: Phase 3 / live staged orchestration / product-risk reduction
---

# Pre-Ticket Audit: ticket-193 Single-Command Live Staged Orchestrator Proof

## Verdict: **GO** (narrow opt-in live-network orchestrator pytest only)

## Context

Per-step operator opt-in proofs cover rank-1 through generate-run-report (ticket-187)
and rank-2 through generate-run-report (ticket-190). `execute_staged_fixture_mode_run`
and `research run --fixture-mode --staged-spine` are **fixture-proven** with patched
network I/O (`tests/unit/test_staged_fixture_mode_run_spine.py`, ticket-162). The product
gap is a **single-command** proof on **real OpenAlex** without `urlopen` patches.

## Audit answers

### 1. What does `research run --fixture-mode --staged-spine` currently orchestrate?

`execute_staged_fixture_mode_run` in `rge/cli.py`:

1. Force `RGE_LLM_MODE=mock` and `RGE_ALLOW_SOURCE_NETWORK=1`
2. Ingest domain opposing-context fixture (`creativity_ai_diversity_short.txt`)
3. Extract/link/build on base source (auto mock)
4. `discover-sources` (OpenAlex, `--rank-only --enqueue`)
5. For rank #1 and rank #2 staged candidate IDs: `fetch-candidate` → `ingest-staged`
6. Rank #1 spine: extract → link → build → detect → reconcile → generate-run-report (auto mock)
7. Rank #2 spine: extract/link/build/detect with explicit `--fixture` bindings → reconcile → generate-run-report
8. Return JSON summary with stable counts (3 sources, 2 candidates, 2 score_events, 2 run_reports)

Does **not** run public export, theory, cluster report, or improvement tickets.

### 2. What live per-step proofs already exist?

| Rank | Env gate | Proof |
|------|----------|-------|
| Rank-1 report | `RGE_ALLOW_LIVE_STAGED_REPORT=1` | ticket-187 |
| Rank-2 report | `RGE_ALLOW_LIVE_STAGED_RANK2=1` | ticket-190 |
| Earlier stages | `RGE_ALLOW_LIVE_STAGED_*` per stage | tickets 167–184 |

All are chained CLI steps inside individual `pytest -m live_network` tests with temp DB.

### 3. What would a single-command live staged proof need to do?

Invoke the **existing orchestrator entry** (`research run --fixture-mode --staged-spine` or direct `execute_staged_fixture_mode_run`) against **real OpenAlex** on a **temp `--db`** and temp `--output-dir` / `--staging-dir`, asserting the same stable dual-spine counts as ticket-162 without patching `urlopen`.

### 4. Reuse per-step tests or new explicit flag?

**Reuse orchestrator** — do not duplicate the step chain. Add a **new opt-in env gate**
(e.g. `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1`) checked by a **new** `pytest.mark.live_network`
test that calls the CLI orchestrator. Avoid changing default `execute_staged_fixture_mode_run`
behavior for unpatchable CI runs.

Alternative rejected: composing existing per-step tests in one mega-test — duplicates logic and does not prove orchestrator wiring.

### 5. Required env gates

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"   # new gate (proposed name)
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
```

Orchestrator already forces mock LLM internally; test must not set `RGE_ALLOW_LIVE_LLM=1`.

### 6. Prevent accidental live network in CI/default pytest

- `pytest.mark.live_network` on the new test
- `pyproject.toml` `addopts = "-m 'not live_smoke and not live_network'"`
- `tests/unit/test_ci_golden_gate.py` deselect assertion for new test name
- No workflow changes requiring OpenAlex

### 7. Keep live LLM out of scope

Orchestrator sets `RGE_LLM_MODE=mock`; rank #1 uses auto mock routing; rank #2 uses
explicit fixture files. Test must assert mock mode and must not enable `RGE_ALLOW_LIVE_LLM`.

### 8. Keep public export/site out of scope

Staged orchestrator does not call `export-public` or touch `apps/public-site`. Test uses
temp DB and temp report dir only; no committed public JSON.

### 9. Rank-1 only, rank-2 only, or both?

**Both ranks in one orchestrator run** — matches `execute_staged_fixture_mode_run`
contract and ticket-162 stable counts. Per-step rank proofs remain as regression anchors;
orchestrator proof validates end-to-end wiring.

### 10. Temp DB/output-dir behavior

- `tmp_path` SQLite via `--db`
- `tmp_path` subdirs for `--staging-dir` and `--output-dir`
- No writes to default `data/db/creative_research.sqlite` or committed export paths
- Assert `run_report_latest.json` under temp output dir only

### 11. Idempotency expectations

Ticket-163 proves idempotency for **patched** orchestrator. For live orchestrator proof:

- **Minimum:** one successful pass with stable counts
- **Stretch (same ticket if small):** second CLI invocation on same temp DB yields stable row counts (no duplicate score_events/run_reports)
- Document honestly if re-run flakes on live discover ordering

### 12. Expected files to change (implementation ticket-193)

| File | Change |
|------|--------|
| `tests/unit/test_live_staged_orchestrator_mock_spine.py` (proposed name) | New `live_network` test + env gate skip test |
| `tests/unit/test_ci_golden_gate.py` | Deselect assertion for new test |
| `agent_reports/pre-ticket-193` gate alias | If audit ticket id differs from implementation id |

Optional follow-on docs ticket (low risk): README/AGENTS `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR`.

### 13. Rollback plan

Remove new test file and CI deselect entry; retain ticket-162 patched orchestrator and per-step live proofs (167–190).

## Hardened scope (ticket-193 implementation)

### In

1. One `pytest.mark.live_network` test calling `research run --fixture-mode --staged-spine` on temp paths
2. Env gate `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` (or equivalent; keep naming consistent with existing `RGE_ALLOW_LIVE_STAGED_*` family)
3. Assert dual-spine counts matching ticket-162 table
4. Skip test without opt-in; `test_ci_golden_gate.py` deselect

### Out

- Public export, public site, schema migrations
- Live LLM / Ollama
- Cloud providers, browser scraping
- Changing MVP `execute_fixture_mode_run`
- Proving `research run` without `--fixture-mode`

## Safety

- Real OpenAlex discover/fetch for two candidates; mock LLM only after ingest
- Temp DB and temp output paths; no public export
- Operator opt-in only; not CI

## Operator opt-in (proposed)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q
```

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-193 live orchestrator proof | **GO** |
| Public export / live LLM / cloud / scraping | **NO-GO** |
| Next docs ticket after 193 | README/AGENTS orchestrator opt-in (ticket-194 pattern) |
