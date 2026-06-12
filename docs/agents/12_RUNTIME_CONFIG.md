# Runtime Configuration

## Purpose

Document every environment variable the Research Graph Engine reads today, where
to store local secrets, and how mock vs live modes interact. This doc supports
golden tests, fixture-mode runs, and future smoke tests without leaking secrets
into the repo or public exports.

Canonical model-runtime contract: `docs/agents/03_MODEL_RUNTIME_SPEC.md`.  
Safety boundaries: `docs/agents/10_SAFETY_MODEL.md`.

## Configuration loader

`rge/config.py` resolves settings in this order (later wins):

1. Built-in defaults in `_DEFAULTS`
2. Optional `.env` file in the repo root (simple `KEY=VALUE` lines)
3. Process environment variables (`os.environ`)

There is **no** `python-dotenv` dependency. Quoting/escaping is minimal.

Golden tests and the builder agent should set `RGE_LLM_MODE=mock` explicitly.

## Supported variables (implemented)

| Variable | Required | Secret | Local-only | Public build | Used by |
|---|---|---|---|---|---|
| `RGE_LLM_MODE` | optional (default `ollama` in code; use `mock` in `.env.local`) | no | yes | no | `rge/llm/registry.py`, all model client selection |
| `RGE_TEST_LLM_MODE` | optional (default `mock`) | no | yes | no | Documented for tests; golden tests set `mock` directly |
| `OLLAMA_BASE_URL` | optional | no | yes | no | `OllamaModelClient`, `rge/config.py` |
| `RGE_LOCAL_LLM` | optional | no | yes | no | Ollama model tag (not a filesystem path) |
| `RGE_LLM_TIMEOUT_SECONDS` | optional | no | yes | no | Ollama client timeout |
| `RGE_LLM_TEMPERATURE` | optional | no | yes | no | Ollama client temperature |
| `RGE_LLM_SCHEMA_VERSION` | optional | no | yes | no | Candidate JSON schema version |
| `RGE_EMBEDDING_MODE` | optional | no | yes | no | Future embeddings (not used in Phase 1) |
| `RGE_EMBEDDING_MODEL` | optional | no | yes | no | Future embeddings (not used in Phase 1) |

Valid `RGE_LLM_MODE` values: `mock`, `ollama` only. Anything else fails closed.

## Not implemented (do not add to committed `.env` yet)

These categories are **not** read by any `rge/` module today:

- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`
- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`
- `ANTHROPIC_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS`, Gemini / Vertex project/location vars
- `CURSOR_API_KEY` (Cursor IDE/CLI auth — operator-level, outside RGE runtime)
- `RGE_DB_PATH` (use CLI `--db` or default `data/db/creative_research.sqlite`)
- `RGE_SMOKE_*`, `RGE_DRY_RUN`, `RGE_LIVE_*` smoke gates

Add provider variables only when a ticket wires an adapter and documents them here.

## Database and artifact paths

| Path | Config var | Git | Notes |
|---|---|---|---|
| `data/` | none | gitignored | All local runtime output (db, reports, exports, generated tickets) |
| `data/db/creative_research.sqlite` | CLI `--db` only | gitignored | Default private DB |
| `data/reports/` | none | gitignored | Run/cluster/theory private reports |
| `data/exports/` | none | gitignored | Generated export JSON copies |
| `data/tickets/` | none | gitignored | Generated improvement-ticket artifacts (not the queue) |
| `apps/public-site/public/data/` | none | committed snapshots | Public-safe JSON only; review diffs before commit |
| `apps/public-site/out/` | none | gitignored | Static site build output |
| `tickets/ticket-*.json` | none | committed | Manually reviewed implementation queue |
| `agent_reports/` | none | committed | No secrets in reports |

## Mock vs live behavior (Phase 1 / Phase 2 boundary)

### Golden tests / CI

Always:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden
```

### Pipeline modules

Even if `RGE_LLM_MODE=ollama` in `.env`, these modules **force mock** before
calling the model client:

- `rge/modules/claim_extractor.py`
- `rge/modules/concept_linker.py`
- `rge/modules/relationship_builder.py`
- `rge/modules/contradiction_detector.py`

Fixture-mode golden runs and ticket-028 orchestration therefore do **not** need
API keys or a running Ollama instance.

### Ollama client

`rge/llm/ollama_client.py`:

- `health_check()` may call `OLLAMA_BASE_URL` when explicitly invoked.
- Structured tasks (`extract_claims`, etc.) raise `OllamaNotAvailableInPhase0`.

## Public site

The public site (`apps/public-site/`) uses static JSON imports only. It does
**not** read `process.env`, `import.meta.env`, `NEXT_PUBLIC_*`, or `VITE_*`.
No secret belongs in the public-site build.

## Cursor builder agent

This repo ships `.cursor/commands/*.md` slash-command instructions only. It does
**not** invoke `cursor-agent` or read `CURSOR_API_KEY`. Cursor authentication is
managed by the Cursor desktop app / operator environment, not RGE runtime config.

## Local file layout (recommended)

```txt
.env.example           # committed placeholders
.env.smoke.example     # committed smoke placeholders
.env.local             # gitignored — your daily settings (copy from .env.example)
.env.smoke.local       # gitignored — smoke profile (copy from .env.smoke.example)
```

Never commit `.env`, `.env.local`, `.env.smoke.local`, or any file containing
real keys, tokens, or private paths.

## Smoke test checklist (operator)

Before a future live-inference smoke (not golden tests):

1. Copy `.env.smoke.example` → `.env.smoke.local` (gitignored).
2. Set `OLLAMA_BASE_URL` and `RGE_LOCAL_LLM` to your local Ollama instance.
3. Ensure Ollama is running and the model is pulled.
4. Understand structured tasks still use mock until a later ticket implements them.
5. Run safety audit after any export: `python -m rge.modules.safety_auditor --audit full`

## Fixture-mode MVP run

`python -m rge.cli run --fixture-mode` orchestrates the full Phase 1 pipeline
using deterministic fixtures (Golden Test 26). Requirements:

- Set `RGE_LLM_MODE=mock` (explicit in tests; orchestrator forces mock).
- No provider keys or Ollama instance required.
- After ticket-034, repeated fixture runs use stable export serialization and
  leave `git status --short` empty; runtime output stays under gitignored `data/`.
- Committed public snapshots in `apps/public-site/public/data/` change only in
  deliberate review commits, not as a side effect of local demo runs.

Live discovery (`research run` without `--fixture-mode`) is not implemented.
