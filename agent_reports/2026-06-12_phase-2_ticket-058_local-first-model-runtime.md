---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-058: Local-first model runtime readiness and escalation policy

- Date: 2026-06-12
- Branch: `phase-2/ticket-058-local-first-model-runtime`
- Baseline HEAD: `408f262c559601fe9d6aa9f8c6f5e4d611cd4297`
- Risk level: low-medium

## Summary

Documented the local-first model runtime ladder (mock / ollama / future cloud),
task-tier responsibility split, and forbidden actions in
`docs/agents/13_MODEL_ESCALATION_POLICY.md`. Updated operator runbooks in
README, `12_RUNTIME_CONFIG.md`, `03_MODEL_RUNTIME_SPEC.md`, `.env.example`,
and AGENTS.md. Enhanced `model-health` with `configured_model`, `available_models`,
and `action_hint` when the configured tag is missing or Ollama is unreachable.
Seeded ticket-059 as a proposed OpenAI placeholder (no implementation).

No OpenAI/OpenRouter adapters. No API keys. Live LLM remains opt-in only.
Live smoke was **not** run.

## Manual setup evidence (human completed)

| Check | Result |
| ----- | ------ |
| `ollama pull qwen2.5:7b` | Completed successfully (human) |
| `where ollama` | `C:\Users\guestt\AppData\Local\Programs\Ollama\ollama.exe` |
| `ollama --version` | 0.21.0 |
| `ollama list` | `qwen2.5:7b` present (4.7 GB, pulled ~2026-06-12) |

## model-health results

### Safe verification env (mock)

```json
{
  "status": "ok",
  "provider": "ollama",
  "base_url": "http://127.0.0.1:11434",
  "model": "qwen2.5:7b",
  "configured_model": "qwen2.5:7b",
  "reachable": true,
  "model_available": true,
  "live_llm_enabled": false,
  "effective_llm_mode": "mock"
}
```

`effective_llm_mode: mock` is expected and not a failure.

### Live-health probe (opt-in env only — not live smoke)

Env: `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, `RGE_LOCAL_LLM=qwen2.5:7b`

```json
{
  "reachable": true,
  "model_available": true,
  "live_llm_enabled": true,
  "effective_llm_mode": "ollama"
}
```

## Files changed

| File | Change |
| ---- | ------ |
| `docs/agents/13_MODEL_ESCALATION_POLICY.md` | New — modes, responsibility split, forbidden actions, cloud policy |
| `docs/agents/12_RUNTIME_CONFIG.md` | Runbook profiles, model-health interpretation |
| `docs/agents/03_MODEL_RUNTIME_SPEC.md` | Task-tier alignment cross-link |
| `README.md` | Local vs mock profiles, updated live/mock status |
| `AGENTS.md` | Source priority includes 12/13 runtime docs |
| `.env.example` | Model alias guidance |
| `.env.smoke.example` | Model tag comment |
| `rge/llm/ollama_client.py` | Health check hints |
| `rge/cli.py` | model-health help text |
| `tests/unit/test_ollama_health_check.py` | 3 unit tests |
| `tickets/ticket-058.json` | Ticket seed |
| `tickets/ticket-059.json` | Proposed OpenAI placeholder |
| `tickets/TICKET_QUEUE.md` | Queue rows 58–59 |
| `agent_reports/2026-06-12_pre-ticket-058_local-model-runtime-readiness-audit.md` | Pre-ticket audit (referenced) |

## Commands run

```powershell
git checkout main; git pull origin main
git rev-parse HEAD  # 408f262
gh run list --limit 3  # Golden Gate success at 408f262

where.exe ollama; ollama --version; ollama list

$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m rge.cli model-health

$env:RGE_LLM_MODE = "ollama"; $env:RGE_ALLOW_LIVE_LLM = "1"; $env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli model-health

python -m pytest -q                    # 207 passed, 1 deselected
python -m rge.modules.safety_auditor --audit full  # pass
python -m rge.cli verify --skip-site   # pass
python -m rge.modules.operator_loop --mode execute-safe  # blocked (dirty tree during impl)
```

## Verification results

| Check | Result |
| ----- | ------ |
| pytest | **207 passed**, 1 live_smoke deselected |
| safety audit | **pass** |
| verify --skip-site | **pass** (140 golden + 207 pytest + safety) |
| operator execute-safe | **blocked** during implementation (dirty tree); individual gates passed |
| Live smoke | **not run** (not approved) |

## Confirmations

- **No API keys** were used or added.
- **OpenAI/OpenRouter** adapters were **not** implemented; ticket-059 is proposed placeholder only.
- **Live LLM is opt-in only** (`RGE_ALLOW_LIVE_LLM=1` required); mock remains CI/golden default.
- **Golden Gate baseline** green at `408f262` (run 27432023929).

## Merge

- Ticket commit SHA: _(filled after commit)_
- Main push SHA: _(filled after push)_
- Golden Gate run: _(filled after push)_

## Recommended next move

1. **ticket-059** (when promoted): OpenAI opt-in cloud adapter with evidence thresholds and budget gates — or wire `draft_run_summary` / `draft_ticket` on Ollama as a separate low-risk local task ticket.
2. Run optional manual live structured task probe (`extract-claims` on a fixture chunk) outside CI if operator wants end-to-end Ollama validation.
3. Principal audit checkpoint due after 2 more done tickets (1 since post-056).
