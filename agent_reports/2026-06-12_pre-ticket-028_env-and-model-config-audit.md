---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-028 Audit: Environment and Model Configuration Discovery

- Audit type: secrets/config/model-location discovery (no ticket-028 implementation)
- Date: 2026-06-12
- Agent/model: Cursor builder agent (GPT-5.5)
- Scope: env vars, local secret storage, mock vs live modes, provider readiness, public-site exposure, ticket-028 gate

## Summary

The repo is **safe and ready to start ticket-028** as a **mock/fixture-only** Golden Test 26 implementation. No committed secrets were found. Full safety audit passes; 114/114 tests pass.

**Key finding:** RGE today supports only **`mock`** and **`ollama`** via `rge/config.py` / `.env.example`. There is **no** OpenAI, OpenRouter, Anthropic, Gemini, or Vertex wiring in code. Pipeline modules **hard-force `RGE_LLM_MODE=mock`** for structured LLM tasks, and Ollama structured tasks raise `OllamaNotAvailableInPhase0`. Real provider smoke tests are **not possible** in Phase 1 without future tickets.

This audit adds placeholder docs (`.env.smoke.example`, `docs/agents/12_RUNTIME_CONFIG.md`), tightens `.gitignore` for local env files, and documents operator setup — **no real secrets committed**.

## Repo State

| Check | Result |
|---|---|
| Branch | `main` |
| Working tree | clean (`## main...origin/main`) |
| Main tip | `49e83fb` |
| ticket-027 | `done`, merged and pushed |
| ticket-028 | `proposed` — lowest-order next ticket |
| `research run` | Phase 0 placeholder (`not_implemented` exit 2) — ticket-028 will implement |

## Discovered Environment Variables

### Implemented and read by `rge/config.py`

| Variable | Required | Secret | Local-only | Public build | Used by | Safe example | Recommended storage |
|---|---|---|---|---|---|---|---|
| `RGE_LLM_MODE` | optional | no | yes | no | `rge/llm/registry.py`, pipeline modules | `mock` | `.env.local` or session `$env:` |
| `RGE_TEST_LLM_MODE` | optional | no | yes | no | documented / tests | `mock` | `.env.local` |
| `OLLAMA_BASE_URL` | optional | no | yes | no | `OllamaModelClient` | `http://127.0.0.1:11434` | `.env.local` / `.env.smoke.local` |
| `RGE_LOCAL_LLM` | optional | no | yes | no | Ollama model tag | `qwen2.5:7b` | `.env.local` / `.env.smoke.local` |
| `RGE_LLM_TIMEOUT_SECONDS` | optional | no | yes | no | Ollama client | `60` | `.env.local` |
| `RGE_LLM_TEMPERATURE` | optional | no | yes | no | Ollama client | `0` | `.env.local` |
| `RGE_LLM_SCHEMA_VERSION` | optional | no | yes | no | validators / clients | `0.1.0` | `.env.local` |
| `RGE_EMBEDDING_MODE` | optional | no | yes | no | future | `local_sentence_transformer` | `.env.local` |
| `RGE_EMBEDDING_MODEL` | optional | no | yes | no | future | `sentence-transformers/all-MiniLM-L6-v2` | `.env.local` |

### CLI / path conventions (not env vars)

| Item | Mechanism | Default | Secret | Notes |
|---|---|---|---|---|
| SQLite DB | `--db` CLI flag | `data/db/creative_research.sqlite` | no (local private) | gitignored; no `RGE_DB_PATH` env |
| Export output | `--output-dir` | `data/exports/` + public-site data dir | no | Must pass safety validation |
| Fixture selection | `--fixture` / auto markers | fixture files under `fixtures/` | no | Golden/mock path |

### Not implemented (searched; zero code references)

| Category | Variables | Status |
|---|---|---|
| OpenAI | `OPENAI_API_KEY`, model, base URL | **Not wired** |
| OpenRouter | `OPENROUTER_API_KEY`, model, base URL | **Not wired** |
| Anthropic | `ANTHROPIC_API_KEY` | **Not wired** |
| Google / Vertex / Gemini | `GOOGLE_APPLICATION_CREDENTIALS`, ADC, API keys | **Not wired** |
| Cursor CLI | `CURSOR_API_KEY`, `--api-key` | **Outside RGE runtime** |
| Smoke gates | `RGE_SMOKE_*`, `RGE_DRY_RUN`, `RGE_LIVE_*` | **Not present** |
| Public site | `NEXT_PUBLIC_*`, `VITE_*`, `process.env` | **Not used** |

## Mock vs Live / Smoke Behavior

### Golden tests and CI (required)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden
```

Every golden test module sets `RGE_LLM_MODE=mock` in autouse fixtures or monkeypatch.

### Pipeline modules (forces mock regardless of `.env`)

These set `os.environ["RGE_LLM_MODE"] = "mock"` before `get_model_client()`:

- `rge/modules/claim_extractor.py`
- `rge/modules/concept_linker.py`
- `rge/modules/relationship_builder.py`
- `rge/modules/contradiction_detector.py`

**Implication:** Setting `RGE_LLM_MODE=ollama` in `.env.smoke.local` does **not** enable live inference for claim extraction today.

### Ollama

- Config: `OLLAMA_BASE_URL`, `RGE_LOCAL_LLM`, timeout, temperature.
- **No filesystem model path** — Ollama uses model tags (e.g. `qwen2.5:7b`).
- Only `health_check()` performs network I/O when explicitly called.
- Structured tasks raise `OllamaNotAvailableInPhase0`.

### `research run --fixture-mode` (ticket-028)

Golden Test 26 command per `00_GOLDEN_TESTS.md`:

```bash
research run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
```

Currently returns `not_implemented`. Ticket-028 should orchestrate existing CLI steps in **fixture/mock mode** — **no provider keys required**.

## Cursor CLI / Builder Agent

| Finding | Detail |
|---|---|
| Repo integration | `.cursor/commands/*.md` markdown slash commands only |
| `cursor-agent` on PATH | **Not found** on this machine (`CommandNotFoundException`) |
| `CURSOR_API_KEY` in repo | **Not referenced** |
| Recommendation | Keep Cursor auth in IDE/operator environment; do **not** store in repo `.env` |

## Public Site / Export Safety

| Check | Result |
|---|---|
| `NEXT_PUBLIC_*` / `VITE_*` | none in `apps/public-site/` |
| Committed `public_cards.json` | whitelisted fields only; includes GT25 debug fields |
| Forbidden patterns in export | none detected |
| `dangerouslySetInnerHTML` | absent from public-site source |
| Safety audit | `pass` |

## Secret Safety Verification

| Check | Result |
|---|---|
| `.gitignore` covers `.env` | yes (extended to `.env.local`, `.env.*.local`, `.env.smoke.local`) |
| Real `.env` files in repo | none (only `.env.example`, new `.env.smoke.example`) |
| Committed API-key-like strings | **none found** (`sk-...` pattern search clean) |
| `GOLDEN_PRIVATE_FIELDS` in export | blocked by `curated_public_card()`; GT25 asserts no leak |
| Staged secrets | none |

## Tests Run

| Command | Result |
|---|---|
| `git status --short --branch` | clean `main...origin/main` |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | `status: pass`, exit 0 |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | **114 passed** |
| `RGE_LLM_MODE=mock python -m pytest` | **114 passed** |

## Missing Config Docs (addressed in this audit)

| Gap | Resolution |
|---|---|
| No smoke env example | Added `.env.smoke.example` |
| `.gitignore` incomplete for local env variants | Updated `.gitignore` |
| Runtime config scattered across `03_MODEL_RUNTIME_SPEC.md` | Added `docs/agents/12_RUNTIME_CONFIG.md` |
| No `RGE_DB_PATH` env | Documented CLI `--db` pattern; optional future ticket |

## Recommended Local Files

Create on your machine only (gitignored):

### `.env.local` (daily development)

Copy from `.env.example`:

```env
RGE_LLM_MODE=mock
OLLAMA_BASE_URL=http://127.0.0.1:11434
RGE_LOCAL_LLM=qwen2.5:7b
RGE_TEST_LLM_MODE=mock
RGE_LLM_TIMEOUT_SECONDS=60
RGE_LLM_TEMPERATURE=0
RGE_LLM_SCHEMA_VERSION=0.1.0
```

### `.env.smoke.local` (optional Ollama reachability probes)

Copy from `.env.smoke.example` when you want to test Ollama `health_check` in a future ticket — **not for golden tests**.

## What NOT to Commit

- `.env`, `.env.local`, `.env.smoke.local`, any `*.local` env file with real values
- API keys, tokens, service account JSON, `GOOGLE_APPLICATION_CREDENTIALS` paths
- Real local filesystem paths in reports or public JSON
- `data/db/*.sqlite` (already gitignored)
- Raw prompts, private evaluator notes, injected source text in exports

## PowerShell Setup (session-only, no real values)

```powershell
# Golden tests / ticket-028 CI path (recommended default)
$env:RGE_LLM_MODE = "mock"

# Optional: point at default DB explicitly
$db = "data\db\creative_research.sqlite"

# After ticket-028 implements research run:
python -m rge.cli run `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --fixture-mode

# Verification gates
python -m pytest tests/golden
python -m rge.modules.safety_auditor --audit full
cd apps\public-site; npm run build
```

### Optional persistent user env (use sparingly)

```powershell
setx RGE_LLM_MODE "mock"
setx OLLAMA_BASE_URL "http://127.0.0.1:11434"
```

Do **not** `setx` API keys on shared machines; prefer session `$env:` for secrets.

### Optional Ollama smoke probe (when health_check CLI exists)

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
# python -m rge.cli model-health   # not implemented yet
```

## Ticket-028 Gate Decision

| Question | Answer |
|---|---|
| Safe to start ticket-028 now? | **Yes** |
| Env/config docs missing before ticket-028? | **Resolved** by this audit (`.env.smoke.example`, `12_RUNTIME_CONFIG.md`) |
| ticket-028 mock-only or optional live smoke? | **Mock/fixture-only** per ticket-028 JSON non-goals and current code reality |
| Env vars needed for GT26 implementation? | **`RGE_LLM_MODE=mock` only** (explicit in tests; pipeline forces mock anyway) |
| Env vars for future real smoke (post-MVP)? | `OLLAMA_BASE_URL`, `RGE_LOCAL_LLM`, `RGE_LLM_MODE=ollama` — after live inference ticket removes mock forcing |

## Exact Next Prompt

```txt
/rge-run-next-ticket
```

Implement ticket-028 on branch `phase-1/ticket-028-full-mvp-run` with fixture-mode `research run` orchestration and Golden Test 26. Keep `RGE_LLM_MODE=mock`; do not require Ollama or provider keys.

## Artifacts Added by This Audit

| File | Purpose |
|---|---|
| `agent_reports/2026-06-12_pre-ticket-028_env-and-model-config-audit.md` | This report |
| `.env.smoke.example` | Placeholder smoke profile |
| `docs/agents/12_RUNTIME_CONFIG.md` | Canonical runtime config reference |
| `.env.example` | Updated comments for local file layout |
| `.gitignore` | Ignore `.env.local`, `.env.*.local`, `.env.smoke.local` |
