# Ticket-391 — Operator live orchestrator verification retry runbook v0

**Date:** 2026-06-23  
**Branch:** `phase-3/ticket-391-live-orchestrator-retry-runbook`  
**Ticket:** ticket-391  
**Audit gate:** satisfied — `agent_reports/2026-06-23_principal-audit-post-ticket-389.md`

## Summary

Focused operator retry runbook when the live staged orchestrator checklist (ticket-389)
does not pass because OpenAlex returns catalogs without mock-spine marker phrases. Documents
retry conditions, marker phrases, outcome interpretation, and topic-tuning guidance. README
orchestrator checklist cross-links this report.

No engine changes.

## Scope

**In:** Agent report; README retry cross-link after orchestrator checklist.

**Out:** CI live_network; env gate removal; pipeline features.

## When to use this runbook

Use after ticket-389 checklist returns **skip**, **fail with `unsuitable_live_artifact`**, or
**JSONDecodeError** from multiple stdout JSON blobs — when live network and env gates are
already set correctly.

| Symptom | Likely cause | This runbook? |
|---------|--------------|---------------|
| pytest **skipped** — missing `RGE_ALLOW_*` | Env gate not set | No — fix gates (ticket-389) |
| **FAILED** + `unsuitable_live_artifact` in output | Live fetch OK; no marker phrases | **Yes** |
| **FAILED** + timeout / connection error | Network blocked | Retry unrestricted network first |
| **1 passed** | Success | No retry needed |

## Required marker phrases

Live staged mock-spine proofs require fetched abstract/text to contain **both** phrases
(checksum-pinned fixture coupling):

| Marker | Role |
|--------|------|
| `human-ai co-creativity` | Rank-1 mock spine fixture alignment |
| `songwriting` | Rank-2 / dual-candidate mock spine alignment |

Preflight helper: `tests/unit/live_staged_proof_layers.py`
(`require_mock_spine_compatible_fetch_or_skip`).

## Retry procedure

### 1. Confirm prerequisites (unchanged from ticket-389)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
```

### 2. Run orchestrator proof (temp DB via pytest)

```powershell
python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q -s
```

Use `-s` to capture stdout when diagnosing `unsuitable_live_artifact` JSON.

### 3. Interpret outcome

| Result | Interpretation | Operator action |
|--------|----------------|-----------------|
| **1 passed** | Live OpenAlex + mock orchestrator succeeded | Record pass; re-plan with `operator_loop --mode plan` |
| **skipped** (env) | Missing gate | Set gate from skip message |
| **skipped** (`unsuitable_live_artifact`) | Acquisition healthy; catalog ≠ markers | See step 4 — **not a regression** |
| **failed** (other) | Spine or harness error | Inspect stderr; compare with layer-2 mock proof |

### 4. Retry strategies for `unsuitable_live_artifact`

| Strategy | Detail |
|----------|--------|
| **Retry later** | OpenAlex top-N for default creativity topic may change; retry on another day |
| **Topic tuning** | Use a research question closer to fixture domains, e.g. AI-assisted songwriting and creative diversity (see README live abstract smoke examples) |
| **Accept environmental NO-GO** | Mock product proof (GO) remains valid; live-research maturity stays partial until a passing run |
| **Do not** | Enable live Ollama, remove gates, or write to default graph DB |
| **Regression check** | Run patched layer-2: `python -m pytest tests/unit/test_staged_fixture_mode_run_spine.py -q` (default pytest, no network) |

### 5. Optional follow-on (same gate)

```powershell
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```

Same `unsuitable_live_artifact` skip semantics — not an atlas export regression.

## Example skip payload (ticket-389 operator run)

```json
{
  "reason": "unsuitable_live_artifact",
  "required_markers": ["human-ai co-creativity", "songwriting"],
  "assessment": "Not a fetch/reconcile/report regression — live OpenAlex catalog text does not match checksum-pinned mock fixture phrases for this query."
}
```

When the CLI prints ingest JSON **before** this skip body, pytest may fail with
`JSONDecodeError` (multiple JSON documents on stdout). Treat as environmental
`unsuitable_live_artifact`, not a harness regression requiring code change.

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Retry conditions, markers, pass/skip/fail documented | **PASS** |
| No engine changes | **PASS** |
| Temp DB only | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `python -m pytest tests/golden -q` | **165 passed** |

Safety audit not required (docs-only).

## Merge to main

Merge commit: `8c4523c`.

## Recommended next ticket

**ticket-392** — AGENTS.md live orchestrator retry runbook cross-link v0.
