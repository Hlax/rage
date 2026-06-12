# Model Escalation Policy

## Purpose

Define the local-first model runtime ladder, task-tier responsibility split, and
forbidden actions for the Research Graph Engine. This document complements
`03_MODEL_RUNTIME_SPEC.md` (adapter contract) and `12_RUNTIME_CONFIG.md`
(environment variables and operator runbook).

OpenAI, OpenRouter, and other cloud providers are **not implemented** in this
phase. Cloud escalation rules here are policy-only until a future ticket wires
adapters and config gates.

## Modes

| Mode | When | Environment |
| ---- | ---- | ----------- |
| **mock** | CI, golden tests, fixture runs, default verification, daily development | `RGE_LLM_MODE=mock` or live opt-in off |
| **ollama** | Real local research on an operator machine with Ollama running | `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, model reachable |
| **cloud** | Not implemented — future opt-in synthesis only | Deferred (ticket-059+) |

### mock (default for verification)

- Deterministic fixtures under `fixtures/`.
- Golden Gate CI sets `RGE_LLM_MODE=mock` and `RGE_ALLOW_LIVE_LLM=0`.
- Fixture-mode orchestration (`research run --fixture-mode`) **always** forces mock.
- `effective_llm_mode: mock` in `model-health` is **expected** and not a failure.

### ollama (local research, explicit opt-in)

Requires **both**:

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
```

Recommended local profile:

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
```

Verify readiness:

```powershell
python -m rge.cli model-health
```

Expect `reachable: true`, `model_available: true`, `live_llm_enabled: true`,
`effective_llm_mode: ollama`.

### cloud (future — not implemented)

- No OpenAI, OpenRouter, Anthropic, or Gemini adapters in the core engine today.
- Cloud calls must never run from CI, golden tests, or fixture paths.
- Future tickets will add `RGE_CLOUD_LLM_ENABLED=0` default, evidence thresholds,
  per-run budgets, and human confirmation for paid API calls.

## Safe verification env

Use this for agent verification, operator execute-safe, and CI parity:

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m rge.cli verify --skip-site
```

## Responsibility split

### Local Ollama/Qwen may handle (candidate JSON only)

| Task | Module / client | Live wired? |
| ---- | --------------- | ----------- |
| Query drafts | contract validation (deterministic today) | No |
| Chunk summaries | ingest (future) | No |
| Claim extraction | `claim_extractor` / `extract_claims` | **Yes** |
| Concept tagging / linking | `concept_linker` / `link_concepts` | **Yes** |
| Limitation extraction | partial — field in claim extraction schema | Partial |
| Relationship drafting | `relationship_builder` / `draft_relationships` | **Yes** |
| Contradiction detection | `contradiction_detector` / `detect_contradictions` | **Yes** |
| Small run summaries | `draft_run_summary` | Mock/fixture only |
| First-pass improvement ticket drafts | `draft_ticket` | Mock/fixture only |
| Card draft text | public cards from accepted claims (deterministic) | No |

Model output is **untrusted candidate JSON**. Python validates every field before
any accepted write.

### Python deterministic code must handle

- Source fetch, parse, chunk (`fetcher`, `parser`, `ingest`)
- Queue ranking, contract drift gating, score reconciliation
- Schema/Pydantic validation, quote-span checks, prompt-injection rejection
- Deduplication, DB writes via repositories
- Cluster/theory/ontology/domain threshold evaluation and report assembly
- Public export filtering, safety auditor, route audit
- Improvement ticket GT21 validation, promotion review gate
- Ticket queue status, Git operations, shell execution

### Future cloud/larger models may handle (after evidence thresholds)

Only when local evidence is insufficient and a future ticket enables cloud mode:

- Cluster report narrative synthesis
- Candidate theory wording refinement
- Ontology/domain pressure review memos
- Build-ticket refinement from run evidence
- Weekly/monthly synthesis, architecture review memos

Cloud outputs land in **draft/candidate** storage only. Python still validates
and never auto-accepts.

### Mock-only forever

- Golden tests (`pytest tests/golden`)
- CI Golden Gate
- Fixture-mode full MVP orchestration
- Default developer/operator runs unless explicit live opt-in

## Forbidden actions (non-negotiable)

Models and model adapters must **never**:

- Write directly to **accepted** graph DB records
- Call shell, Git, browser, or mutate repo files
- Approve public export or bypass safety audit
- Override safety checks or ticket promotion gates
- Fall back silently from live failure to mock in production paths
- Run cloud/paid calls from CI, golden, or fixture paths

See also `10_SAFETY_MODEL.md`.

## Cloud escalation thresholds (policy — code gates deferred)

Before any future cloud call, all of the following should apply unless a ticket
documents an exception:

1. Minimum accepted claims in target cluster/run (e.g. cluster threshold: 15
   claims / 3 sources).
2. Minimum independent sources in the evidence packet.
3. Mixed edge evidence: at least two of {support, contradict, qualify} OR
   explicit contradiction classification.
4. Cluster report threshold met — deterministic packet exists in `data/reports/`.
5. For ontology/domain cloud review: pressure counters met (migrations 0006/0007).
6. Explicit human approval for paid API calls (future CLI flag).
7. Safety audit pass on any export touched after cloud-assisted run.

## Output storage rules

| Output type | Storage | Accepted as fact? |
| ----------- | ------- | ----------------- |
| Local model candidates | Validated → accepted/rejected tables | Only after Python validation |
| Cloud synthesis (future) | `data/reports/` as candidate/draft JSON | **Never** auto-accepted |
| Theories | `theory_candidates` as candidate status | Never without review |
| Ontology/domain proposals | draft proposal rows | Never auto-activated |
| Improvement tickets | `data/tickets/` drafts; queue promotion requires `--confirm` | Never implicit |

## Operator runbook (summary)

1. Install and start Ollama (outside this repo).
2. Pull the configured model or set `RGE_LOCAL_LLM` to an already-pulled tag:
   - Default: `ollama pull qwen2.5:7b`
   - Alias: `RGE_LOCAL_LLM=qwen2.5-coder:7b` if that tag is already local
3. Copy `.env.example` → `.env.local` (gitignored) for daily settings.
4. Copy `.env.smoke.example` → `.env.smoke.local` for live probes only.
5. Run `python -m rge.cli model-health` — read `action_hint` if
   `model_available` is false.
6. For live structured pipeline tasks, set both `RGE_LLM_MODE=ollama` and
   `RGE_ALLOW_LIVE_LLM=1`.
7. After any export change, run `python -m rge.modules.safety_auditor --audit full`.

### Live structured probe (ticket-060)

Outside CI, with live opt-in set and Ollama ready:

```powershell
python -m rge.cli probe-extract-claims
```

Writes a report-only JSON artifact under `data/reports/live_probes/`. Does **not**
write to the default SQLite database or public exports. See `12_RUNTIME_CONFIG.md`.

End-to-end operator runbook (mini-run floors, `contradiction_input_mode`, evidence
accumulation for human-gated improvement proposals):
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md`.

## Related documents

- `03_MODEL_RUNTIME_SPEC.md` — adapter contract and task list
- `12_RUNTIME_CONFIG.md` — env vars, mock vs live, smoke marker
- `10_SAFETY_MODEL.md` — export and route safety boundaries
