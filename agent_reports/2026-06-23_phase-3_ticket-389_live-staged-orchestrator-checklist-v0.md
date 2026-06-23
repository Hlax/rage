# Ticket-389 — Operator one-time live staged orchestrator verification checklist v0

**Date:** 2026-06-23  
**Branch:** `phase-3/ticket-389-live-staged-orchestrator-checklist`  
**Ticket:** ticket-389  
**Context:** Post internal MVP launch checkpoint (ticket-388); researcher product proof GO artifact on disk

## Summary

Documented the operator one-time live staged orchestrator verification checklist with env
gates, pytest command, pass/skip/fail interpretation, and expected stdout JSON counts.
Added a README cross-link from the existing orchestrator checklist section to this report
and the post-launch sequence (mock product proof GO → live OpenAlex orchestrator proof).

No engine or safety gate changes.

## Scope

**In:** Agent report; README orchestrator checklist header refresh.

**Out:** CI live_network enforcement; live Ollama; new pipeline features.

## Operator checklist

### Prerequisites

| Variable | Required value |
|----------|----------------|
| `RGE_LLM_MODE` | `mock` (orchestrator forces mock LLM) |
| `RGE_ALLOW_LIVE_LLM` | `0` (recommended for this checklist) |
| `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR` | `1` |
| `RGE_ALLOW_SOURCE_NETWORK` | `1` |
| `OPENALEX_MAILTO` | valid contact email |
| Network | outbound HTTPS to OpenAlex |

**Temp DB only:** pytest uses `tmp_path` — never `data/db/creative_research.sqlite`.

### Command

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q
```

### Pass interpretation

| Outcome | Meaning |
|---------|---------|
| **1 passed** | Live OpenAlex discover/fetch + mock spine orchestrator succeeded on temp DB |
| **skipped** | Missing env gate — see skip reason in pytest output |
| **failed** (unsuitable_live_artifact) | Live network OK but no fixture-compatible OpenAlex artifact — retry or treat as environmental skip per README |

**Expected stdout JSON** (from `research run --fixture-mode --staged-spine`):

| Field | Expected |
|-------|----------|
| `status` | `completed` |
| `mode` | `fixture_staged` |
| `sources` | `3` |
| `candidate_sources` | `2` |
| `research_queue` | `2` |
| `score_events` | `2` |
| `run_reports` | `2` |
| `qualifies_evidence` | `2` |

Temp artifact: `run_report_latest.json` under pytest temp report dir (not committed).

### Skip reasons (from test module)

| Skip message | Fix |
|--------------|-----|
| `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` missing | Set orchestrator gate |
| `RGE_ALLOW_SOURCE_NETWORK=1` missing | Enable source network |
| `OPENALEX_MAILTO` missing | Set polite-pool email |

### Not in scope

- Per-step live Ollama (tickets 204/208/212/217; rank-2 230/236/237/238)
- Live LLM on reconcile/report (deterministic Python only)
- `export-public`, public-site writes, default graph DB
- CI / Golden Gate ( `live_network` excluded in `pyproject.toml` )

### Optional follow-on (same orchestrator gate)

```powershell
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```

Skips with `unsuitable_live_artifact` when live fetch lacks mock-spine marker phrases — not an atlas regression.

## Post-launch sequence (ticket-388 → ticket-389)

1. Confirm `data/reports/researcher_product_proof_latest.json` has `product_verdict: GO` (mock-only).
2. Run this orchestrator checklist (live OpenAlex + mock LLM).
3. Re-plan: `python -m rge.modules.operator_loop --mode plan`.

## Operator run (this session)

Attempted on operator machine with all env gates set:

```powershell
python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q
```

**Result:** **FAILED** (7.3s) — live discover/fetch ran but no mock-spine-compatible artifact
in scan window. CLI emitted ingest JSON plus `unsuitable_live_artifact` skip payload on
stdout (multiple JSON documents), causing `JSONDecodeError` in the test harness. This matches
README **Interpreting `unsuitable_live_artifact`** — not an orchestrator regression.

**Operator action:** retry from a network-unrestricted machine when OpenAlex returns
fixture-compatible abstracts (`human-ai co-creativity`, `songwriting` markers), or accept
skip as environmental. Patched-network regression remains
`tests/unit/test_staged_fixture_mode_run_spine.py` (default pytest).

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Report records commands, env gates, pass/skip interpretation | **PASS** |
| No engine changes unless wiring bug | **PASS** (docs only) |
| Temp DB only; no export-public | **PASS** (documented) |

## Commands run

| Command | Result |
|---------|--------|
| `python -m pytest tests/golden -q` | **165 passed** |
| Live orchestrator pytest (operator opt-in) | **FAILED** — `unsuitable_live_artifact` (environmental) |

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

**ticket-387** — AGENTS.md researcher product proof cross-link.
