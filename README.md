# Research Graph Engine

A local-first research infrastructure system. It turns sources into scoped claims, concept links, evidence relationships, score history, reports, public-safe research cards, and improvement tickets that builder agents can act on.

Core architecture:

```txt
General Research Graph Engine
+ Domain Packs
```

The first domain pack is `creativity` (in `domain_packs/creativity/`). The core engine stays domain-general; creativity-specific behavior lives only in the domain pack.

Core rule:

```txt
Qwen/Ollama proposes structured candidate output.
Python validates, scores, stages, writes, reports, and audits.
```

## Current Status

**Phase 1 MVP is complete.** The repo ships a runnable end-to-end research pipeline in deterministic mock/fixture mode, a static public site, 123 golden tests, a builder merge gate, and a full safety audit.

What is **real and executable today**:

- SQLite migration harness and private research graph (7 migrations)
- Source ingestion, claim extraction, concept linking, relationship building, contradiction detection, score reconciliation
- Research contract drift gating, queue ranking, cluster/theory/ontology/domain/run reports
- Improvement ticket generation with builder-consumption validation
- Fail-closed public card export and static Next.js public site
- Deterministic safety auditor and prompt-injection handling
- Full fixture-mode orchestration: `research run --fixture-mode` (Golden Test 26)

What is **mock or fixture-only**:

- Golden tests, CI, and `research verify` always use `RGE_LLM_MODE=mock`
- Fixture-mode orchestration forces mock regardless of `.env` settings
- Live discovery (`research run` without `--fixture-mode`) returns `not_implemented`
- Cloud providers (OpenAI, OpenRouter, Anthropic, Gemini, Vertex) are **not wired**

What requires **explicit live opt-in** (local Ollama only):

- Four pipeline structured tasks: claim extraction, concept linking, relationship
  building, contradiction detection (ticket-037)
- Requires `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`
- Run `python -m rge.cli model-health` before live pipeline work

See `docs/agents/13_MODEL_ESCALATION_POLICY.md` for mode profiles and task tiers.

Phase 2 work (live Ollama, UI polish, deployment) is tracked in `agent_reports/2026-06-12_phase-2_ticket-roadmap.md`.

## Install

```bash
python -m pip install -e ".[dev]"
cd apps/public-site && npm install
```

On Windows, `research.exe` is often not on PATH after editable install. Use
`python -m rge.cli <command>` (for example `python -m rge.cli verify`) instead
of bare `research …`. A missing `research` command is a PATH issue, not a failed
verification suite, when the module form succeeds.

## Operator Quickstart

Set mock mode for all verification (no Ollama required):

```powershell
# PowerShell
$env:RGE_LLM_MODE = "mock"
```

```bash
# bash
export RGE_LLM_MODE=mock
```

Run the default verification suite (preferred — one command):

```bash
export RGE_LLM_MODE=mock
python -m rge.cli verify
```

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify
```

Use `--skip-site` for Python-only checks when Node.js is unavailable:

```bash
python -m rge.cli verify --skip-site
```

Individual checks (same gates, decomposed):

```bash
python -m pytest tests/golden
python -m pytest
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

Run the full fixture-mode MVP pipeline:

```bash
python -m rge.cli run \
  --topic "Does AI improve creative output while reducing diversity?" \
  --domain creativity \
  --fixture-mode
```

Build the public site (static export):

```bash
cd apps/public-site && npm run build
```

After ticket-034, repeated fixture-mode runs leave `git status --short` empty. Runtime output goes under gitignored `data/`; only reviewed public snapshots under `apps/public-site/public/data/` are committed.

## Verification Commands

| Command | Purpose |
|---|---|
| `python -m rge.cli verify` | **Preferred:** mock-only golden + pytest + safety audit + site build |
| `python -m rge.cli verify --skip-site` | Same, without npm build (Python checks only) |
| `python -m pytest tests/golden` | Builder merge gate (mock LLM) |
| `python -m pytest` | Full test suite |
| `python -m rge.modules.safety_auditor --audit full` | Deterministic safety audit |
| `python -m rge.cli run --fixture-mode ...` | End-to-end fixture MVP |
| `python -m rge.cli export-public --limit 100` | Export public-safe cards |
| `cd apps/public-site && npm run build` | Static public site build |

On Windows, prefer `python -m rge.cli verify` over `research verify` when the
`research` script is not on PATH.

Golden tests always run in mock LLM mode and do not require Ollama.

## Artifact Paths

| Path | Git | Contents |
|---|---|---|
| `data/db/` | gitignored | Private SQLite database (default: `creative_research.sqlite`) |
| `data/reports/` | gitignored | Run, cluster, theory, and other private reports |
| `data/exports/` | gitignored | Generated export JSON copies |
| `data/tickets/` | gitignored | Generated improvement-ticket artifacts (not the queue) |
| `apps/public-site/public/data/` | committed | Reviewed public-safe JSON snapshots |
| `apps/public-site/out/` | gitignored | Static site build output |
| `tickets/ticket-*.json` | committed | Manually reviewed implementation queue |
| `agent_reports/` | committed | Builder audit and build reports (no secrets) |

Use CLI flags to override paths for tests: `--db`, `--output-dir`, `--export-dir`, `--ticket-dir`.

## Mock vs Live Providers

| Mode | Status |
|---|---|
| `RGE_LLM_MODE=mock` | **Default for tests, CI, and fixture runs.** Deterministic fixtures. |
| `RGE_LLM_MODE=ollama` + `RGE_ALLOW_LIVE_LLM=1` | Local research on operator machine. Four pipeline structured tasks live; Python validates all writes. |
| Cloud providers | **Not wired.** OpenAI/OpenRouter deferred to ticket-059+. |

**Local research env** (copy to gitignored `.env.local` or set in shell):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli model-health
```

**Safe verification env** (no Ollama required):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m rge.cli verify --skip-site
```

Copy `.env.example` to gitignored `.env.local` for daily settings. Full policy:
`docs/agents/13_MODEL_ESCALATION_POLICY.md`. Variable reference:
`docs/agents/12_RUNTIME_CONFIG.md`.

**Never commit** `.env`, `.env.local`, `.env.smoke.local`, API keys, tokens, or machine-specific paths.

## Public Site

The public site (`apps/public-site/`) is a read-only static export:

- Renders committed JSON from `apps/public-site/public/data/` only
- No write routes, no source ingestion, no agent execution
- Never connects to the private local engine or SQLite
- Does not read `NEXT_PUBLIC_*` or other build-time secrets

After changing accepted claims or export policy, run `export-public`, pass the safety audit, review the snapshot diff, then rebuild the site.

Deployment guide (build, pre-deploy checklist, static hosting): `docs/deployment/public-site-static-hosting.md`

Safety model: `docs/agents/10_SAFETY_MODEL.md`

## Repo Layout

```txt
rge/                  Python research engine package
  cli.py              `research` CLI entry point
  config.py           typed config from env / .env
  db/                 SQLite migrations, repositories, schema
  llm/                model runtime adapter (mock + ollama boundary)
  modules/            pipeline modules (ingest … safety auditor)
  safety/             export policy, route audit, prompt injection
domain_packs/         domain pack overlays (creativity first)
fixtures/             deterministic sources and mock LLM outputs
tests/golden/         golden tests (mock LLM, no Ollama required)
apps/public-site/     static read-only public export surface (Next.js)
docs/agents/          implementation specs (source of truth)
tickets/              implementation ticket queue
agent_reports/        end-of-run agent build reports
```

## Specs and Agent Workflow

Implementation follows `docs/agents/` in the priority order defined by `AGENTS.md`. Builder agents use `.cursor/commands/rge-run-next-ticket.md` for one-ticket-per-branch workflow.

Key operator docs:

- Model escalation policy: `docs/agents/13_MODEL_ESCALATION_POLICY.md`
- Runtime config: `docs/agents/12_RUNTIME_CONFIG.md`
- Safety model: `docs/agents/10_SAFETY_MODEL.md`
- Golden tests: `docs/agents/00_GOLDEN_TESTS.md`
- Phase 2 roadmap: `agent_reports/2026-06-12_phase-2_ticket-roadmap.md`

## Boundaries (non-negotiable)

- No model output writes directly to accepted DB tables.
- No public write, ingestion, or agent execution routes.
- No raw prompts, local paths, secrets, private notes, or raw source text in public exports.
- The public site builds from static JSON only; it never connects to the private local engine.
