---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-058 Local Model Runtime Readiness Audit

- Audit type: focused pre-ticket audit — local Ollama/Qwen runtime readiness and model escalation policy
- Date: 2026-06-12
- Scope: read-only. No ticket-058 implementation. No Ollama install, model pull, OpenAI code, or live smoke beyond safe health checks.
- Human architecture intent: local Qwen/Ollama for most research; cloud/larger models only after graph evidence thresholds; no model direct writes; OpenAI opt-in later; OpenRouter future stub only.

## 1. Executive verdict

**PARTIAL — local runtime needs manual setup first**

The **code boundary is release-ready** (ticket-037/038 merged; mock-only CI/golden; explicit live opt-in; `model-health` CLI; four pipeline Ollama structured tasks). On this audit machine, **Ollama is installed but the configured default model is missing** (`qwen2.5:7b` not pulled; `qwen2.5-coder:7b` is present instead). Ollama was not running until probed.

**Recommendation:** seed ticket-058 as **local-first runtime readiness + escalation policy** (docs/config/runbook + optional `model-health` hardening). Human should align `RGE_LOCAL_LLM` or pull the configured model **before** live research or live smoke. **Do not** implement OpenAI/OpenRouter adapters in ticket-058.

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` | `git checkout main` |
| Working tree | **clean** | `git status --short` → empty |
| Local HEAD | `408f262c559601fe9d6aa9f8c6f5e4d611cd4297` | `git rev-parse HEAD` |
| `origin/main` | `408f262c559601fe9d6aa9f8c6f5e4d611cd4297` | `git rev-parse origin/main` |
| Local equals remote | **yes** | HEAD == origin/main |
| Latest Golden Gate | **success** | run **27432023929** at `408f262` |
| Prior implementation gate | **success** | run **27431881399** (ticket-057 `aadbc59`) |
| ticket-057 | **done** | queue + agent report present |
| Principal audit cadence | **satisfied** | 1 done ticket since post-056 checkpoint |
| CI mock-only | **yes** | `golden-gate.yml`: `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0` |

## 3. Existing model runtime

| Area | Current behavior | Gap | Risk |
| ---- | ---------------- | --- | ---- |
| Config (`rge/config.py`) | Reads `OLLAMA_BASE_URL`, `RGE_LOCAL_LLM`, `RGE_LLM_MODE`, `RGE_ALLOW_LIVE_LLM`; defaults `qwen2.5:7b`, mode `ollama` in code defaults but `.env.example` recommends `mock` | No cloud provider vars wired; no escalation/threshold config | Low — fail-closed |
| Registry (`rge/llm/registry.py`) | `mock` → `MockModelClient`; `ollama` → `OllamaModelClient`; unknown → `LlmModeError`; **no silent fallback** | No `openai`/`openrouter` mode | Low |
| Effective mode (`rge/llm/mode.py`) | Live only when `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`; else mock | No separate “cloud mode” flag yet | Low |
| `ModelClient` (`rge/llm/base.py`) | Six structured tasks; returns typed candidates only; metadata dataclass | Cloud tasks not defined | Low |
| `OllamaModelClient` | `health_check()`, four live structured tasks (claims, concepts, relationships, contradictions); `draft_run_summary` / `draft_ticket` raise `OllamaNotAvailableInPhase0` | Higher-level synthesis still fixture/deterministic elsewhere | Medium — policy/doc gap |
| `MockModelClient` | Fixture JSON for all six tasks; golden/fixture deterministic | None for tests | Low |
| Pipeline modules | `claim_extractor`, `concept_linker`, `relationship_builder`, `contradiction_detector` use `effective_llm_mode()` | Chunk summaries, card drafts, query drafts not separate tasks | Medium — human intent vs task map |
| Synthesis modules | `cluster_reporter`, `theory_generator`, `ontology_pressure`, `domain_proposer` — **deterministic/fixture**; no LLM calls | Human wants local for small summaries/tickets; cloud for deep synthesis — **not encoded in code** | Medium |
| Improvement tickets | Template/deterministic failure modes (`ticket_writer.py`); no `get_model_client` | First-pass ticket drafts via model not wired | Low for now |
| Fixture orchestration (`rge/cli.py`) | `execute_fixture_mode_run()` **always forces mock** | Live discovery (`research run` without `--fixture-mode`) still `not_implemented` | Low |
| `model-health` CLI | Always exits 0; reports `reachable`, `model_available`, `live_llm_enabled`, `effective_llm_mode` | Does not fail when model missing; no model-alias hints | Low — runbook gap |
| Live smoke | `tests/smoke/test_live_ollama_smoke.py`; marker excluded from default pytest | Only health check; no structured task smoke | Low |
| Safety | Full audit pass; live export requires `--publish`; no model shell/Git | No cloud budget/rate caps | Medium when cloud added |
| Docs | `03_MODEL_RUNTIME_SPEC.md`, `12_RUNTIME_CONFIG.md`, `.env.example`, `.env.smoke.example` | **No escalation policy doc**; no task→tier assignment table | Medium |
| Cloud providers | **Zero code** for OpenAI/OpenRouter/Anthropic/Gemini | Intentionally absent | Low (correct) |

## 4. Local Ollama/Qwen readiness

| Check | Result | Blocking? | Notes |
| ----- | ------ | --------- | ----- |
| Ollama installed? | **yes** | no | `where ollama` → `C:\Users\guestt\AppData\Local\Programs\Ollama\ollama.exe` |
| Ollama running at audit start? | **no** (started on probe) | **yes for live calls until started** | `ollama --version` warned “could not connect”; `ollama list` started server |
| Ollama version | **0.21.0** | no | Update available: v0.30.7 (informational) |
| Configured base URL | `http://127.0.0.1:11434` | no | Matches `rge/config.py` default and `.env.example` |
| Configured local model (`RGE_LOCAL_LLM`) | **`qwen2.5:7b`** (default) | **yes for live structured calls** | Not in local model list |
| Models present locally | `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `glm-4.7-flash:latest`, `mistral:latest`, `llama3:latest` | — | Closest match: **`qwen2.5-coder:7b`** (4.7 GB) |
| `model-health` (mock env) | exit 0; `reachable=true`, `model_available=false`, `effective_llm_mode=mock` | no | Safe probe only |
| `model-health` (live env) | exit 0; `reachable=true`, `model_available=false`, `effective_llm_mode=ollama`, `live_llm_enabled=true` | **yes** | Live structured tasks would fail at generate until model aligned |
| Live smoke run | **not executed** | — | Per audit rules; health probe sufficient |
| Golden/CI Ollama required? | **no** | no | Mock-only gates |

### Recommended human commands (not run by this audit)

Choose **one** alignment path before live research:

**Option A — pull configured instruct model:**

```powershell
ollama pull qwen2.5:7b
# ensure Ollama app/service is running
python -m rge.cli model-health
```

**Option B — use an already-pulled Qwen variant:**

```powershell
# in .env.local (gitignored)
RGE_LLM_MODE=ollama
RGE_ALLOW_LIVE_LLM=1
RGE_LOCAL_LLM=qwen2.5-coder:7b
python -m rge.cli model-health
```

Expect `model_available: true` before any live `extract-claims` / pipeline step.

## 5. Local-first model policy

### What local Qwen/Ollama should handle (human intent → current code)

| Task tier | Human intent | Current RGE state |
| --------- | ------------ | ----------------- |
| Query / contract drafts | Local model | **Not implemented** — contract validation is deterministic |
| Chunk summaries | Local model | **Not a separate task** — could fold into future ingest step |
| Claim extraction | Local model | **Live wired** (`OllamaModelClient.extract_claims`) |
| Concept tagging / linking | Local model | **Live wired** (`link_concepts`) |
| Limitation extraction | Local model | **Partial** — field in claim extraction prompt/schema |
| Relationship drafting | Local model | **Live wired** (`draft_relationships`) |
| Contradiction detection | Local model | **Live wired** (`detect_contradictions`) |
| Card draft text | Local model | **Not wired** — public cards built deterministically from accepted claims |
| Small run summaries | Local model | **`draft_run_summary` not on Ollama** — mock/fixture only |
| First-pass improvement ticket drafts | Local model | **`draft_ticket` not on Ollama** — deterministic templates today |

### What Python handles (deterministic — must stay)

- Source fetch/parse/chunk (`fetcher`, `parser`, `ingest`)
- Queue ranking, contract drift gating, score reconciliation
- Schema/Pydantic validation, quote-span checks, prompt-injection rejection
- Deduplication, DB writes via repositories (claims, concepts, relationships)
- Cluster/theory/ontology/domain **threshold evaluation** and report assembly (today without model calls)
- Public export filtering, safety auditor, route audit
- Improvement ticket GT21 validation, promotion review gate

### What cloud/larger model should handle (future — not implemented)

Only **after evidence thresholds** (see §6):

- Cluster report **narrative synthesis** (today: deterministic packet assembly)
- Candidate **theory** wording refinement (today: fixture proposals + validation)
- Ontology/domain **pressure review** memos (today: deterministic counters)
- Build-ticket **refinement** from run evidence (today: templates)
- Weekly/monthly synthesis, architecture review memos

### What remains mock-only forever

- Golden tests (`pytest tests/golden`)
- CI Golden Gate
- Fixture-mode full MVP orchestration (`research run --fixture-mode`)
- Default developer/operator runs unless explicit live opt-in

### What is forbidden (non-negotiable)

- Model output writing directly to **accepted** graph tables
- Model calling **shell, Git, browser, or file mutation**
- Model approving **public export** or bypassing safety audit
- Silent fallback from live failure to mock in production paths
- Cloud/paid calls without explicit enable + threshold + human budget approval

## 6. Cloud escalation policy

Proposed policy for ticket-058 documentation (code gates deferred to ticket-059+):

### Mode ladder

| Mode | When | Env |
| ---- | ---- | --- |
| **mock** | Tests, CI, fixture runs, default safe verification | `RGE_LLM_MODE=mock` or live opt-in off |
| **local** | Normal real research on operator machine | `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, Ollama reachable + model available |
| **cloud** | Disabled by default; opt-in synthesis only | Future: `RGE_CLOUD_LLM_ENABLED=1` + provider key in gitignored env (not implemented) |

### Evidence thresholds before cloud call (all required unless noted)

1. **Minimum accepted claims** in target cluster/run (e.g. ≥ cluster threshold: 15 claims / 3 sources — matches `cluster_reporter` golden constants).
2. **Minimum independent sources** represented in evidence packet.
3. **Mixed edge evidence**: at least two of {support, contradict, qualify} relationship types OR explicit contradiction classification present.
4. **Cluster report threshold met** — deterministic packet exists in `data/reports/`.
5. **For ontology/domain cloud review**: ontology/domain pressure counters met (migrations 0006/0007 thresholds).
6. **Explicit human approval** for any paid API call (CLI flag or operator confirmation step — future ticket).
7. **Safety audit pass** on any export touched after cloud-assisted run.

### Output storage rules

| Output type | Storage | Accepted as fact? |
| ----------- | ------- | ----------------- |
| Local model candidates | Validated → accepted/rejected tables | Only after Python validation |
| Cloud synthesis | `data/reports/` as **candidate/draft** JSON + `model_invocations` metadata | **Never** auto-accepted |
| Theories | `theory_candidates` as **candidate** status | Never fact without review |
| Ontology/domain proposals | draft proposal rows | Never auto-activated |
| Improvement tickets | `data/tickets/` drafts; queue promotion requires `--confirm` | Never implicit |

### Overuse prevention (future)

- Separate `RGE_CLOUD_LLM_ENABLED` default `0`
- Per-run call budget counters in config (document in `12_RUNTIME_CONFIG.md`)
- Escalation audit log entry per cloud call with evidence packet hash
- No cloud calls from CI/golden/fixture paths

## 7. OpenAI/OpenRouter recommendation

| Question | Answer |
| -------- | ------ |
| Should OpenAI be implemented now? | **No.** Defer to **ticket-059 or later** after local-first policy doc + runbook land in ticket-058. |
| Should OpenRouter be stubbed now? | **No code stub.** Document as **future-compatible placeholder** in runtime docs only (`12_RUNTIME_CONFIG.md` “not implemented” section is sufficient). |
| Should API keys be required now? | **No.** No keys in repo, CI, or golden tests. |
| Where should keys live if/when used? | Gitignored `.env.local` / operator secret store; never committed; never in public export or agent reports. |
| How prevent cloud overuse? | Default off; evidence thresholds; human confirm for paid calls; budget counters; mock-only CI forever. |

## 8. Proposed ticket-058

Ticket-058 option **C** (local-first escalation policy) with **B** elements (runbook/model-health operator docs). **Not** D or E.

### Title

Local Ollama/Qwen runtime readiness and local-first model escalation policy

### Problem

Ticket-037/038 implemented live Ollama structured tasks and health/smoke gating, but operators lack a single **local-first runbook**, **task-tier assignment table**, and **escalation policy** matching human architecture. Default config points at `qwen2.5:7b` while many dev machines have other Qwen tags; `model-health` reports `model_available=false` without actionable guidance. No cloud escalation rules are documented or config-gated. Theory/cluster/ontology modules remain deterministic while human intent assigns synthesis tiers differently.

### Scope

- Add **`docs/agents/13_MODEL_ESCALATION_POLICY.md`** (or extend `03` + `12` if preferred single source): local vs Python vs cloud task matrix, mode ladder, evidence thresholds, forbidden actions.
- Add **operator runbook** section (README + `12_RUNTIME_CONFIG.md`): Ollama start, model pull vs alias, `.env.local` / `.env.smoke.local` profiles, `model-health` interpretation, when to use live vs fixture-mode.
- Optional small code hygiene (low risk): enhance `model-health` JSON with **`configured_model`**, **`available_models` sample**, and **`action_hint`** when `model_available=false` (no new dependencies).
- Document **`RGE_LOCAL_LLM` alias guidance** (e.g. `qwen2.5:7b` vs `qwen2.5-coder:7b`) in `.env.example` comments.
- Seed **`tickets/ticket-059.json`** as **proposed** placeholder for future OpenAI opt-in adapter (no implementation in 058).

### Expected files

- `docs/agents/13_MODEL_ESCALATION_POLICY.md` (new)
- `docs/agents/12_RUNTIME_CONFIG.md` (runbook cross-links)
- `docs/agents/03_MODEL_RUNTIME_SPEC.md` (task tier alignment note)
- `README.md` (short “Local research vs mock” pointer)
- `.env.example` / `.env.smoke.example` (model alias comments)
- Optional: `rge/llm/ollama_client.py` + `rge/cli.py` (`model-health` hints only)
- Optional: `tests/unit/test_ollama_structured_tasks.py` or new test for health hints
- `tickets/ticket-058.json`, `tickets/TICKET_QUEUE.md`, agent report

### Acceptance criteria

- Operator can follow docs to reach `model-health` with `model_available=true` on a machine with Ollama (document both pull and alias paths).
- Escalation policy states: mock default for CI/tests; local Ollama default for real research; cloud disabled until future ticket.
- Task tier table maps human intent to current modules and marks gaps (run summary, ticket draft, card draft) as future local tasks.
- Golden tests and CI remain mock-only; no OpenAI/OpenRouter code added.
- Explicit “models never write accepted records / never shell/Git” section matches `10_SAFETY_MODEL.md`.

### Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
python -m rge.cli verify --skip-site
```

Manual (operator): follow new runbook → `model-health` with aligned model → optional single live `extract-claims` on fixture chunk (outside CI).

### Safety considerations

- No cloud keys, no provider adapters, no CI Ollama dependency.
- Docs must not encourage `--publish` on unreviewed live exports.
- If `model-health` code changes, keep exit 0 for reachability probe (non-fatal) but surface clear `action_hint`.

### Non-goals

- OpenAI / OpenRouter adapter implementation
- Embeddings, concept graph viz, live discovery orchestration
- Wiring cloud escalation gates in Python (ticket-059+)
- Implementing `draft_run_summary` / `draft_ticket` on Ollama (ticket-060+ candidate)
- Pulling models or installing Ollama in agent automation
- Running live smoke in CI

### Rollback plan

Revert docs and optional `model-health` hint fields; no schema or export changes.

### Risk level

**low** (docs-primary; optional CLI hint is low)

### Pre-ticket audit required?

**Satisfied by this report.**

## 9. Final recommendation

**Seed ticket-058 local-first runtime readiness** — docs/config/escalation policy + operator runbook, with optional `model-health` hints.

**Human prerequisite (parallel, not blocking seed):** start Ollama and either `ollama pull qwen2.5:7b` or set `RGE_LOCAL_LLM=qwen2.5-coder:7b` in `.env.local`, then confirm `python -m rge.cli model-health` shows `model_available: true` before live pipeline work or live smoke.

**Do not** seed OpenAI adapter as ticket-058. **Defer OpenRouter** to documentation backlog only.

## Commands executed

```powershell
git checkout main
git pull origin main
git status --short
git rev-parse HEAD
git rev-parse origin/main
gh run list --limit 3

where.exe ollama
ollama --version
ollama list

$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m rge.cli model-health

$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health
```

No live smoke. No model pull. No OpenAI code. No secrets committed.
