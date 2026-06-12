---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-064: Safe local live contradiction-detection probe CLI

- Date: 2026-06-12
- Branch: `phase-2/ticket-064-safe-local-live-contradiction-probe`
- Risk level: low-medium

## Summary

Added report-only `probe-detect-contradictions` for local Qwen contradiction detection
without SQLite or public exports. Default input is a committed GT07-shaped embedded
bundle (qualifying + opposing claims, base `may_reduce` / new `may_increase`
relationships). Optional `--from-report` and `--chain-relationship` supported.
Calibrated Ollama contradiction prompt; added `contradiction_rejection_diagnostic`
for rejected rows. `validate_contradiction_candidates` unchanged.

Prep hygiene from seed pass retained: `live_smoke` now covers the full probe chain
(extract, link, relationship, contradiction).

## Files changed

| File | Change |
| ---- | ------ |
| `rge/modules/live_probe.py` | `run_probe_detect_contradictions`, bundle loaders |
| `rge/modules/contradiction_detector.py` | `contradiction_rejection_diagnostic`, probe validation helpers |
| `rge/llm/ollama_client.py` | Calibrated contradiction-detection prompt |
| `rge/cli.py` | `probe-detect-contradictions` subcommand |
| `fixtures/probes/live_probe_contradiction_quality_bundle.json` | Default bundle |
| `fixtures/llm_outputs/contradiction_detection_live_probe_quality.json` | Mock fixture |
| `tests/unit/test_live_probe_detect_contradictions_cli.py` | Mock-only tests |
| `tests/unit/test_contradiction_rejection_diagnostics.py` | Validator tests |
| `tests/unit/test_ollama_contradiction_prompt.py` | Prompt tests |
| `tests/smoke/test_live_ollama_smoke.py` | Contradiction live smoke |
| `docs/agents/12_RUNTIME_CONFIG.md` | Contradiction probe docs |
| `tickets/ticket-064.json`, `TICKET_QUEUE.md` | Done status |

## Live probe command

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
python -m rge.cli probe-detect-contradictions
```

## model-health result

- `reachable: true`, `model_available: true`, `effective_llm_mode: ollama`

## Live probe result

- `accepted_count: 1`, `rejected_count: 0`, `db_writes: false`
- Classification: `apparent_contradiction_metric_or_condition_difference`
- Stance: `qualifies`
- Qualifying claim: `claim_live_probe_qualify_001`
- Opposing claim: `claim_live_probe_oppose_001`
- Artifact: `data/reports/live_probes/probe_detect_contradictions_2026-06-12T201304Z.json` (gitignored)

## Verification

| Check | Result |
| ----- | ------ |
| `pytest -q` (mock) | **257 passed**, 5 deselected |
| GT07 | **pass** |
| `python -m rge.cli verify --skip-site` | **pass** |
| Live `probe-detect-contradictions` | **pass** (accepted_count >= 1) |

## Merge / CI

- Merge commit: *(pending — working tree uncommitted at report time)*
- Golden Gate: *(pending after merge/push)*

## Non-goals honored

- No DB persistence or public export changes
- ticket-059 OpenAI remains deferred
- `validate_contradiction_candidates` rules unchanged

## Recommended next

- Principal audit due after one more done ticket (3 since post-061 checkpoint)
- Optional: end-to-end `--chain-relationship` live smoke (higher variability)
- ticket-059 OpenAI remains deferred until operator approves cloud adapter work
