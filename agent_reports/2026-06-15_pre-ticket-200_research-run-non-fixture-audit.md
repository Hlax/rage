---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-201
category: Phase 3 / research run contract / product-risk reduction
---

# Pre-Ticket Audit: ticket-201 Live Staged Run Without `--fixture-mode`

## Verdict: **GO** (narrow CLI contract — staged spine only; full live MVP remains out of scope)

## Context

`research run` without `--fixture-mode` returns structured `not_implemented` today
(`rge/cli.py` `_cmd_run`). Golden Test 26 explicitly requires bare
`run --topic --domain` to remain unimplemented
(`tests/golden/test_26_full_mvp_run.py::test_non_fixture_run_remains_unimplemented`).

Meanwhile Phase 3 **live staged discovery** is already implemented behind
`research run --fixture-mode --staged-spine` → `execute_staged_fixture_mode_run`
(tickets 144–164, 193). That path performs real OpenAlex discover/fetch when network
env is set, but **forces mock LLM** and still requires the misleading `--fixture-mode`
flag. Per-step and orchestrator live proofs exist (tickets 167–193, 199 runbook).

The product gap is **CLI contract clarity**, not missing staged spine code.

## Audit answers

### 1. What does `research run` without `--fixture-mode` mean today?

```python
# rge/cli.py _cmd_run (lines 890–896)
if not args.fixture_mode:
    return _not_implemented(
        "run",
        "Live discovery runs are not implemented. Use --fixture-mode for the "
        "deterministic MVP pipeline.",
    )
```

Two distinct run shapes exist when `--fixture-mode` **is** set:

| Flags | Executor | Network | LLM |
|-------|----------|---------|-----|
| `--fixture-mode` | `execute_fixture_mode_run` | No (committed sources) | mock (forced) |
| `--fixture-mode --staged-spine` | `execute_staged_fixture_mode_run` | Yes (OpenAlex discover/fetch) | mock (forced) |

Bare non-fixture run = **full live MVP discovery** (replace golden fixture sources in
`execute_fixture_mode_run`) — **not implemented**.

### 2. What is already proven?

| Layer | Status |
|-------|--------|
| Fixture MVP orchestration | GT26 / ticket-028 |
| Patched staged orchestrator | `test_staged_fixture_mode_run_spine.py` |
| Live per-step staged proofs | tickets 167–190 |
| Live orchestrator proof | ticket-193 + env `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR` |
| Operator verification runbook | ticket-199 |
| NM-1 live extract on evidence DB | separate path; not `research run` |
| Full live MVP (`execute_fixture_mode_run` with live sources + live LLM) | **not proven** |

### 3. What should the first non-fixture implementation include?

**Staged spine CLI entry only** — allow `research run --staged-spine` **without**
`--fixture-mode`, routing to existing `execute_staged_fixture_mode_run`.

**Reject for ticket-201:**

- Replacing golden fixtures in full MVP run (`execute_fixture_mode_run` live variant)
- Live Ollama inside run orchestration
- Public export / site changes
- Schema migrations
- Removing bare `run --topic --domain` not_implemented (GT26 must stay)

### 4. Mock vs live boundaries

| Surface | ticket-201 |
|---------|------------|
| OpenAlex discover/fetch | Same as today — requires `RGE_ALLOW_SOURCE_NETWORK=1` + `OPENALEX_MAILTO`; dynamic candidate IDs when `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` |
| LLM tasks after ingest | **mock only** — orchestrator continues to force `RGE_LLM_MODE=mock` |
| Live LLM (`RGE_ALLOW_LIVE_LLM=1`) | **Out of scope** — requires separate pre-ticket audit |
| CI / default pytest | Patched-network unit test only; no new `live_network` requirement |

### 5. Required env gates (unchanged from staged orchestrator)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
# Optional for dynamic rank selection (operator live proof):
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
```

Do **not** set `RGE_ALLOW_LIVE_LLM=1` in ticket-201 tests or docs.

### 6. Prevent accidental live network in CI/default pytest

- Extend existing patched `test_staged_fixture_mode_run_spine.py` (or sibling) to call
  `run --staged-spine` without `--fixture-mode`
- Keep `pytest.mark.live_network` proofs in separate opt-in tests (167–193)
- No CI workflow changes
- `pyproject.toml` addopts unchanged

### 7. Golden Test 26 impact

| Test | ticket-201 action |
|------|-------------------|
| `test_non_fixture_run_remains_unimplemented` | **Keep** — bare `run --topic --domain` stays `not_implemented` |
| `test_research_run_cli_matches_golden_command` | **Unchanged** — fixture MVP path |
| New unit test | `run --staged-spine` without `--fixture-mode` succeeds on patched network |

Update `_not_implemented` hint JSON to mention `--staged-spine` for Phase 3 live
discovery (docs-only string change in same ticket).

### 8. Temp DB / output behavior

Same as ticket-162/193: `--db`, `--staging-dir`, `--output-dir` on temp paths in tests;
never default graph DB or committed export dirs in automated tests.

### 9. Backward compatibility

Keep `research run --fixture-mode --staged-spine` working (alias). Parser help text
should clarify:

- `--fixture-mode` alone → golden MVP fixtures
- `--staged-spine` → Phase 3 discover→report (mock LLM; network env for discover/fetch)
- `--fixture-mode --staged-spine` → deprecated alias; same as `--staged-spine`

### 10. Rollback plan

Revert `_cmd_run` routing and parser help; remove new unit test assertion; restore
prior not_implemented message. Retain all existing staged spine and live_network proofs.

## Hardened scope (ticket-201 implementation)

### In

1. `_cmd_run`: if `--staged-spine`, route to `execute_staged_fixture_mode_run` without requiring `--fixture-mode`
2. If neither `--fixture-mode` nor `--staged-spine`, keep `_not_implemented` (update hint text)
3. Unit test: patched `run --staged-spine --topic … --domain …` (no `--fixture-mode`)
4. README/AGENTS one-line contract clarification (optional if minimal diff; prefer small docs note)
5. Agent report for ticket-201

### Out

- Full live MVP run replacing `execute_fixture_mode_run` fixtures
- Live Ollama in orchestration
- Public export / public site
- Schema migrations
- CI live OpenAlex
- Cloud providers

## Deferred — requires future pre-ticket audit

| Milestone | Why deferred |
|-----------|--------------|
| `execute_live_mvp_run` (full GT26-shaped run with live discover + live LLM) | Touches live Ollama orchestration, export, theory — milestone trigger |
| Bare `research run --topic --domain` success | Supersedes GT26 not_implemented contract |
| Non-fixture live LLM on staged spine | Escalation policy: fixture-mode paths force mock today |

## Safety

- Staged path: real OpenAlex only when network env set; mock LLM after ingest
- Temp DB/output in tests; no public export in staged executor
- Bare non-fixture run remains fail-closed `not_implemented`
- No model direct writes; Python validates and repositories persist

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-201 (staged CLI entry without `--fixture-mode`) | **GO** |
| Full live MVP without fixtures in one ticket | **NO-GO** |
| Live LLM inside `research run` orchestration | **NO-GO** (separate audit) |
| Next docs follow-on after 201 | Optional README/AGENTS contract table (can fold into 201) |

## Operator note

After ticket-201, operators run Phase 3 live staged discovery as:

```powershell
python -m rge.cli run --staged-spine --topic "…" --domain creativity --db <temp.sqlite> …
```

without `--fixture-mode`. Live OpenAlex verification remains opt-in per ticket-199 runbook.

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-201**.
