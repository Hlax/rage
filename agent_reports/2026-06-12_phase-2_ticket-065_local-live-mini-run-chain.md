---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-065: Report-only local live mini-run chain

- Date: 2026-06-12
- Branch: `phase-2/ticket-065-local-live-mini-run-chain`
- Baseline HEAD: `2518922` (pre-ticket audit) + seed
- Risk level: low-medium

## Summary

Added `probe-mini-run` — a single report-only command chaining live claim
extraction, concept linking, relationship drafting, and contradiction detection.
Stages 1–3 run live from `fixtures/sources/live_probe_claim_calibration_short.txt`.
Stage 4 defaults to **hybrid overlay** (`live_probe_contradiction_quality_bundle.json`)
when chain outputs lack GT07-shaped tension. `--strict-chain` skips stage 4 with
documented reason when insufficient. Qwen remains bounded worker only; no ticket
authoring or persistence paths.

## Files changed

| File | Change |
| ---- | ------ |
| `rge/modules/live_probe.py` | `run_probe_mini_run`, chain helpers |
| `rge/cli.py` | `probe-mini-run` subcommand |
| `docs/agents/12_RUNTIME_CONFIG.md` | Mini-run operator docs |
| `tests/unit/test_live_probe_mini_run_cli.py` | Mock-only tests |
| `tests/smoke/test_live_ollama_smoke.py` | Optional mini-run smoke |
| `tickets/ticket-065.json`, `TICKET_QUEUE.md` | Done status |

## Mini-run command

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
python -m rge.cli probe-mini-run
python -m rge.cli probe-mini-run --strict-chain
```

## model-health result

- `reachable: true`, `model_available: true`, `effective_llm_mode: ollama`

## Live default mini-run result

| Field | Value |
| ----- | ----- |
| status | **ok** |
| elapsed_ms | 44521 |
| contradiction_input_mode | **hybrid_overlay** |
| claim_extraction | accepted 1, rejected 1 |
| concept_linking | accepted 2, rejected 0 |
| relationship_drafting | accepted 1, rejected 0 |
| contradiction_detection | accepted 1, rejected 0 |
| db_writes | **false** |

## Live strict-chain result

| Field | Value |
| ----- | ----- |
| status | **partial** |
| elapsed_ms | 30226 |
| contradiction_input_mode | **skipped_strict_chain_insufficient_inputs** |
| contradiction_detection | skipped (upstream lacks may_reduce/may_increase tension) |
| stages 1–3 | same acceptance floors as default run |
| db_writes | **false** |

## Report artifact paths

- Default: `data/reports/live_probes/probe_mini_run_2026-06-12T210226Z.json`
- Strict: `data/reports/live_probes/probe_mini_run_2026-06-12T210256Z.json`

(gitignored under `data/`)

## Mock verification

| Check | Result |
| ----- | ------ |
| mini-run unit tests | **8 passed** |
| pytest | **265 passed**, 6 deselected |
| safety audit | **pass** |
| verify --skip-site | **pass** |

## Safety confirmations

- No default DB writes
- No public export churn
- No cloud/API keys
- No ticket drafting or queue promotion calls
- Python validators unchanged per stage
- Live artifacts not committed

## Principal audit cadence

Post-ticket-064 checkpoint satisfied; **1 done ticket** after (065). Threshold 3 — **not due**.

## Merge

- Pre-ticket audit commit: `2518922`
- Implementation commit SHA: `bb4e661`
- Main push SHA: `bb4e661` (fast-forward)
- Golden Gate run: **27442963753** — **success** at `bb4e661`

## Recommended next move

1. Optional docs/runbook: operator sequence + expected stage floors.
2. Evidence accumulation for principal/API improvement proposals (no Qwen ticket authority).
3. Keep ticket-059 OpenAI deferred until operator approves cloud adapter work.
