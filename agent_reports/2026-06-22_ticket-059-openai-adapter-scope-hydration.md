# Ticket-059 OpenAI Adapter Scope Hydration

- Date: 2026-06-22
- Ticket: `ticket-059`
- Scope: ticket hydration only
- Verdict: implementable as a scoped Tier 2 builder ticket

## Summary

`tickets/ticket-059.json` is no longer a placeholder. It now describes a mock-first OpenAI opt-in cloud adapter contract with concrete expected files, acceptance criteria, test plan, safety notes, non-goals, rollback plan, env gates, cloud cost caps, `.env.local` handling policy, and explicit live-call opt-in rules.

No adapter implementation was added in this packet. No live OpenAI call was made.

## Expected Files Added

The hydrated ticket now points the future builder at:

- `rge/llm/cloud_synthesis_registry.py`
- `rge/llm/openai_synthesis_client.py`
- `rge/modules/operator_env_loader.py`
- `rge/modules/openai_synthesis_adapter_spec.py`
- `rge/modules/autonomous_synthesis_governor.py`
- `rge/modules/release_governor.py`
- `rge/config.py`
- `scripts/run_openai_synthesis_adapter_spec.py`
- `tests/unit/test_openai_synthesis_adapter_spec.py`
- `tests/unit/test_openai_synthesis_adapter_contract.py`
- `tests/unit/test_operator_env_loader.py`
- `tests/unit/test_autonomous_synthesis_governor.py`
- `tests/unit/test_release_governor.py`
- `docs/agents/12_RUNTIME_CONFIG.md`
- `docs/agents/13_MODEL_ESCALATION_POLICY.md`
- `.env.example`
- `tickets/ticket-059.json`
- `agent_reports/YYYY-MM-DD_ticket-059-openai-adapter.md`

## Acceptance Criteria

The ticket now requires mock-first default behavior, explicit OpenAI provider registration, evidence-packet-only input, deterministic validation before downstream writes, safe `.env.local` loading through the existing safe env path, redacted boolean-only key availability, provider allowlist checks, budget cap validation, closed circuit breaker gating, release governor compatibility, and tests proving fail-closed behavior.

## Test Plan

The ticket test plan now includes:

- OpenAI adapter spec unit tests in mock mode
- Future adapter contract and operator env loader tests
- Governor and release governor regression tests
- Golden tests in mock mode
- `verify --skip-site`
- `operator_loop --mode plan`
- `run_release_governor.py --inspect`
- full safety audit
- optional operator-only live smoke documentation behind explicit env gates and budget caps

## `.env.local` Policy

`.env.local` may be loaded only through the repo's safe operator env-loading path, preferably by extending `rge/modules/operator_env_loader.py` as the operator-facing wrapper over `rge/config.py`. It must remain gitignored and must never be included in patch bundles, release batches, public artifacts, reports, logs, prompts, Atlas JSON, or serialized model inputs/outputs.

The implementation must never print or serialize the OpenAI key value. If key presence is checked, only a boolean such as `openai_key_available: true/false` may be reported.

## Env And Cost Gates

Any live OpenAI HTTP call must require all of:

- `RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST` includes `openai`
- `RGE_CLOUD_LLM_ENABLED=1`
- `RGE_ALLOW_OPENAI_SYNTHESIS=1`
- `RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP=1`
- OpenAI key is present but never printed
- `RGE_CLOUD_MAX_USD_PER_RUN` is present and greater than zero
- `RGE_CLOUD_MAX_TOKENS_PER_CALL` is present and greater than zero
- autonomy circuit breaker status is closed

Suggested operator smoke caps remain `0.50` USD and `4096` tokens per call. Missing, invalid, zero, or exceeded caps must fail closed before request construction.

## Non-Goals

This ticket does not implement OpenRouter or other providers, does not require a real API key in normal tests, does not allow live HTTP in default tests or execute-safe paths, does not weaken release or circuit-breaker gates, does not write model output directly to accepted graph tables, does not add public write/source-ingestion/agent/model endpoints, does not mutate synthesis ledgers or unrelated tickets, and does not edit `TICKET_QUEUE.md`.

## Live Call Status

No live OpenAI call was made. No `.env.local` file or secret value was read, printed, copied, committed, or serialized.

## Commands Run

```powershell
RGE_LLM_MODE=mock RGE_ALLOW_LIVE_LLM=0 python -m pytest tests/unit/test_openai_synthesis_adapter_spec.py -q
```

Result: pass, `7 passed`.

```powershell
python -m rge.modules.operator_loop --mode plan
```

Result: exit 0. Plan mode recognized `ticket-059` as the current proposed ticket and reported the working tree dirty because `tickets/ticket-059.json` changed.

```powershell
python scripts/run_release_governor.py --inspect
```

Result: exit 0. Inspect completed with draft autonomy tier. The generated Atlas release-governor status artifact was restored afterward because public artifact churn is outside this hydration packet.

```powershell
python -m rge.modules.safety_auditor --audit full
```

Result: pass.

## Changed Files

- `tickets/ticket-059.json`
- `agent_reports/2026-06-22_ticket-059-openai-adapter-scope-hydration.md`

## Rollback

Revert `tickets/ticket-059.json` and delete this report. No code, DB schema, public export contract, or live provider state was changed.

## Next Command

After reviewing this hydration packet, run:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.modules.operator_loop --mode execute-safe
```

For Tier 2 planning/autocycle, use:

```powershell
python -m rge.modules.operator_autocycle --mode plan --max-cycles 10
```
