---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-066: Multi-fixture local live mini-run repeatability

- Date: 2026-06-12
- Branch: `phase-2/ticket-066-multi-fixture-mini-run-repeatability`
- Baseline HEAD: `0dc709c` (runbook on main)
- Risk level: low-medium

## Summary

Added `probe-mini-run-suite` — a report-only batch command that runs the hybrid
mini-run across four committed creativity source fixtures, writes individual
`probe_mini_run_*.json` reports for successes, and one `probe_mini_run_suite_*.json`
summary with per-fixture stage floors and `floors_met`. Confirms ticket-065
calibration generalizes to the default source only; other fixtures expose Qwen
brittleness at claim extraction and relationship drafting without weakening
validators or opening persistence paths.

## Files changed

| File | Change |
| ---- | ------ |
| `rge/modules/live_probe.py` | Suite fixtures manifest, floor helpers, `run_probe_mini_run_suite` |
| `rge/cli.py` | `probe-mini-run-suite` subcommand |
| `docs/agents/12_RUNTIME_CONFIG.md` | Suite operator docs |
| `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` | Suite section + filename table |
| `tests/unit/test_live_probe_mini_run_suite_cli.py` | 8 mock-only unit tests |
| `tickets/ticket-066.json`, `TICKET_QUEUE.md` | Done status |
| `agent_reports/2026-06-12_pre-ticket-066_multi-fixture-mini-run-repeatability.md` | Pre-ticket audit |
| `agent_reports/2026-06-12_live-probe-evidence-review.md` | Prior evidence review (committed with seed) |

## Command

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
python -m rge.cli probe-mini-run-suite
```

## Default fixture set

1. `fixtures/sources/live_probe_claim_calibration_short.txt`
2. `fixtures/sources/creativity_ai_diversity_short.txt`
3. `fixtures/sources/creativity_ai_diversity_followup_short.txt`
4. `fixtures/sources/creativity_ai_diversity_contradiction.txt`

## Live suite result (2026-06-12)

| Fixture | Status | Floors met | Notes |
| ------- | ------ | ---------- | ----- |
| calibration short | **ok** | yes | 1/1, 2/0, 1/0, 1/0 hybrid |
| creativity_ai_diversity_short | **error** | no | relationship_drafting: 0 accepted |
| followup short | **error** | no | relationship_drafting: 0 accepted |
| contradiction source | **error** | no | claim_extraction: 0 accepted |

Suite summary: `status: partial`, `fixtures_passed: 1`, `fixtures_failed: 3`
`db_writes: false`, `elapsed_ms: 109003`

Artifact: `data/reports/live_probes/probe_mini_run_suite_2026-06-12T215340Z.json`
(gitignored)

**Interpretation:** The suite fulfilled its purpose — detecting overfit to the
calibration fixture. Failures are worker-layer / prompt calibration signals, not
validator regressions. No code changes to acceptance rules in this ticket.

## Mock verification

| Check | Result |
| ----- | ------ |
| suite unit tests | **8 passed** |
| pytest | **273 passed**, 6 deselected |
| verify --skip-site | **pass** |

## Safety confirmations

- No default DB writes
- No public export
- No cloud/API keys
- No ticket drafting or queue promotion
- Live artifacts not committed
- Qwen has no ticket authority

## Principal audit cadence

Post-ticket-064 checkpoint; **2 done tickets** after (065, 066). Threshold 3 — **not due**.

## Merge

- Merge commit SHA: _(filled after merge)_
- Main push SHA: _(filled after push)_
- Golden Gate run: _(filled after CI)_

## Recommended next move

1. **Optional ticket-067:** Per-fixture prompt calibration or scoped fixture variants
   for relationship/claim stages on the three failing sources (report-only probes first).
2. **Defer scratch DB** until at least two sources pass suite floors consistently.
3. Keep ticket-059 OpenAI deferred.
