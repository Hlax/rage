# Runtime Configuration

## Purpose

Document every environment variable the Research Graph Engine reads today, where
to store local secrets, and how mock vs live modes interact. This doc supports
golden tests, fixture-mode runs, and future smoke tests without leaking secrets
into the repo or public exports.

Canonical model-runtime contract: `docs/agents/03_MODEL_RUNTIME_SPEC.md`.  
Local-first modes and escalation policy: `docs/agents/13_MODEL_ESCALATION_POLICY.md`.  
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
| `RGE_ALLOW_LIVE_LLM` | optional (default `0`) | no | yes | no | `rge/llm/mode.py`, pipeline effective-mode resolver |
| `RGE_TEST_LLM_MODE` | optional (default `mock`) | no | yes | no | Documented for tests; golden tests set `mock` directly |
| `OLLAMA_BASE_URL` | optional | no | yes | no | `OllamaModelClient`, `rge/config.py` |
| `RGE_LOCAL_LLM` | optional | no | yes | no | Ollama model tag (not a filesystem path) |
| `RGE_LLM_TIMEOUT_SECONDS` | optional | no | yes | no | Ollama client timeout |
| `RGE_LLM_TEMPERATURE` | optional | no | yes | no | Ollama client temperature |
| `RGE_LLM_SCHEMA_VERSION` | optional | no | yes | no | Candidate JSON schema version |
| `RGE_EMBEDDING_MODE` | optional | no | yes | no | Future embeddings (not used in Phase 1) |
| `RGE_EMBEDDING_MODEL` | optional | no | yes | no | Future embeddings (not used in Phase 1) |
| `RGE_ALLOW_SOURCE_NETWORK` | optional (default `0`) | no | yes | no | OpenAlex discover/fetch network gate |
| `OPENALEX_MAILTO` | optional | no | yes | no | Polite OpenAlex contact (not a secret) |
| `OPENALEX_API_KEY` | optional | yes | yes | no | OpenAlex authenticated tier (never commit) |
| `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama extract on rank-1 staged ingest |
| `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama extract on rank-2 staged ingest (ticket-230) |
| `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama link on rank-1 staged ingest |
| `RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama link on rank-2 staged ingest (ticket-236) |
| `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama build on rank-2 staged ingest (ticket-237) |
| `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama detect on rank-2 staged ingest (ticket-238) |
| `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama build on staged ingest |
| `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM` | optional (default `0`) | no | yes | no | Per-step live Ollama detect on staged ingest |
| `RGE_STAGED_RANK2_SCAN_MAX` | optional (default `10`) | no | yes | no | Rank-2 staged candidate title heuristic scan window (ticket-254); bounded 1–50 |
| `RGE_ALLOW_LIVE_STAGED_RECONCILE` | optional (default `0`) | no | yes | no | Live OpenAlex network spine through deterministic reconcile (ticket-184); **no live LLM gate** |
| `RGE_ALLOW_LIVE_STAGED_REPORT` | optional (default `0`) | no | yes | no | Live OpenAlex network spine through deterministic generate-run-report (ticket-187); **no live LLM gate** |
| `RGE_ALLOW_LIVE_STAGED_*` (other mock spine) | optional (default `0`) | no | yes | no | Live OpenAlex + mock LLM staged proofs: FETCH, INGEST, EXTRACT, LINK, BUILD, DETECT, RANK2, ORCHESTRATOR (see README) |

Valid `RGE_LLM_MODE` values: `mock`, `ollama` only. Anything else fails closed.

Valid `RGE_ALLOW_LIVE_LLM` values: `0`/`false`/`no` (default) or `1`/`true`/`yes`.
Any other value raises `ConfigError` (fail closed).

## Not implemented (do not add to committed `.env` yet)

These categories are **not** read by core pipeline modules unless a ticket wires them:

- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`
- `ANTHROPIC_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS`, Gemini / Vertex project/location vars
- `CURSOR_API_KEY` (Cursor IDE/CLI auth — operator-level, outside RGE runtime)
- `RGE_DB_PATH` (use CLI `--db` or default `data/db/creative_research.sqlite`)

### Cloud synthesis (ticket-059; mock-first default)

Operator-only cloud synthesis env vars are read by `rge/config.py` and
`rge/modules/operator_env_loader.py`. Defaults fail closed (`RGE_CLOUD_LLM_ENABLED=0`).
Live OpenAI HTTP additionally requires provider allowlist, cost caps, closed circuit
breaker, and `RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP=1`. Never commit real keys.

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `RGE_CLOUD_LLM_ENABLED` | `0` | Master cloud synthesis enable |
| `RGE_CLOUD_SYNTHESIS_PROVIDER` | `mock_cloud` | Provider id (`mock_cloud` or `openai`) |
| `RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST` | empty | Comma-separated allowlist; must include `openai` for live OpenAI |
| `RGE_ALLOW_OPENAI_SYNTHESIS` | `0` | OpenAI synthesis opt-in |
| `RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP` | `0` | Live HTTP opt-in (never CI) |
| `OPENAI_API_KEY` | unset | Operator credential in `.env.local` only; never logged |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model id |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `RGE_CLOUD_MAX_USD_PER_RUN` | unset | Per-run USD cap (required > 0 for live HTTP) |
| `RGE_CLOUD_MAX_TOKENS_PER_CALL` | unset | Per-call token cap (required > 0 for live HTTP) |

Load `.env.local` only through `operator_env_loader.load_operator_env()` or
`load_config()` — never from public-site code. Key availability may be reported as
`openai_key_available: true|false` only.

## Live smoke tests (ticket-038)

Optional live Ollama smoke tests live under `tests/smoke/` and are marked
`live_smoke`. Default pytest runs exclude them:

```txt
pyproject.toml → addopts = "-m 'not live_smoke'"
```

To run smoke tests explicitly (requires local Ollama):

```powershell
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
python -m pytest -m live_smoke tests/smoke
```

Without both env vars, collected smoke tests skip at runtime. `pytest` and
`pytest tests/golden` collect **zero** smoke tests by default.

## Model health CLI

```powershell
python -m rge.cli model-health
```

Always exits 0 with JSON reporting `reachable`, `model_available`, `configured_model`,
`available_models` (sample), `action_hint` (when unreachable or model missing),
`live_llm_enabled`, and `effective_llm_mode`. Does not run structured pipeline tasks.

**Interpretation:** `effective_llm_mode: mock` is **expected** when
`RGE_ALLOW_LIVE_LLM` is not set — this is not a verification failure. For live
research, set both `RGE_LLM_MODE=ollama` and `RGE_ALLOW_LIVE_LLM=1` and confirm
`model_available: true`. See `13_MODEL_ESCALATION_POLICY.md` for profiles.

## Local-first mode profiles

### Safe verification (CI / golden / agents)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m rge.cli verify --skip-site
```

### Local research (operator machine)

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli model-health
```

Copy `.env.smoke.example` → `.env.smoke.local` for a committed smoke profile
template. Cloud synthesis uses `mock_cloud` by default (ticket-059); live OpenAI
HTTP is operator opt-in only and is excluded from CI, golden tests, and execute-safe.

## Live staged operator env profile (ticket-213)

For per-step live Ollama proofs on staged rank-1 OpenAlex ingest (extract/link/build/detect),
operators typically set env vars in a gitignored `.env.local` (copy from
`.env.example`) or export them in the shell. The repo loader reads optional root
`.env` automatically; process env always wins. No `python-dotenv` dependency.

**Base live model settings:**

```powershell
# Copy once: cp .env.example .env.local  (PowerShell: Copy-Item .env.example .env.local)
# Edit .env.local — never commit it.

$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RGE_LOCAL_LLM = "qwen3.5:9b-q4_K_M"   # or qwen2.5:7b; must match `ollama list`
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health
```

`model-health` reports reachability and model tags only — it does **not** print
API keys, mailto values, or other secrets.

**Staged network + per-step live LLM gates** (rank-1 and rank-2 extract; temp `--db` required):

| Step | Live Ollama gate | Mock spine gate (live OpenAlex + mock LLM) |
|------|------------------|--------------------------------------------|
| extract (rank-1) | `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_EXTRACT=1` |
| extract (rank-2) | `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |
| link (rank-1) | `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_LINK=1` |
| link (rank-2) | `RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |
| build (rank-1) | `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_BUILD=1` |
| build (rank-2) | `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |
| detect (rank-1) | `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_DETECT=1` |
| detect (rank-2) | `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |
| reconcile-scores | — (deterministic Python; **no** `*_LIVE_LLM` gate) | `RGE_ALLOW_LIVE_STAGED_RECONCILE=1` |
| generate-run-report | — (deterministic Python; **no** `*_LIVE_LLM` gate) | `RGE_ALLOW_LIVE_STAGED_REPORT=1` |

**Reconcile/report boundary (tickets 184/187; pre-ticket audits 221/222):** `reconcile-scores`
(`score_reconciler.py`) and `generate-run-report` (`run_evaluator.py`) are deterministic
Python — no model client, no CLI fallthrough flags. `RGE_ALLOW_LIVE_STAGED_RECONCILE` and
`RGE_ALLOW_LIVE_STAGED_REPORT` opt into **live OpenAlex network** pytest spines only (mock
LLM upstream through detect). On **both ranks**, reconcile and report remain deterministic —
no `RGE_ALLOW_LIVE_STAGED_RECONCILE_LIVE_LLM` or `RGE_ALLOW_LIVE_STAGED_REPORT_LIVE_LLM`
without a new pre-ticket audit.

**Staged per-step live Ollama closure:** rank-1 surface is **closed at detect**
(204/208/212/217); rank-2 surface is **closed at detect** (230/236/237/238). No further
`RGE_ALLOW_LIVE_STAGED_*_LIVE_LLM` or `RGE_ALLOW_LIVE_STAGED_RANK2_*_LIVE_LLM` fallthrough
flags are planned. For rank-2 shared prerequisites, per-step gate table, pytest commands,
and operator checklist, see README **Operator Quickstart** → **One-time rank-2 per-step live
Ollama verification** (ticket-240). Rank-1 per-step proofs: README **Live staged
extract/link/build/detect** sections.

All staged proofs also require `RGE_ALLOW_SOURCE_NETWORK=1` and `OPENALEX_MAILTO`.
Per-step live Ollama gates are **separate** from mock-spine gates. Live detect
requires domain opposing context seeded on the temp DB before live discover (see
README **Live staged detect (live Ollama)**). **`seed_domain_opposing_context()`**
(`tests/unit/staged_domain_seed.py`) **forces mock LLM** for GT7 seed extract/link/build
even when operator env has `RGE_LLM_MODE=ollama` — only the detect fallthrough step uses
live Ollama (ticket-243). See README **One-time rank-2 per-step live Ollama verification**
→ **Domain seed** note (ticket-245) and AGENTS rank-1/rank-2 live detect sections
(ticket-246). The staged orchestrator
orchestrator (`research run --staged-spine`) always forces `RGE_LLM_MODE=mock`.

See README **Operator Quickstart** for pytest commands (`live_network` + `live_smoke`
markers excluded from default pytest), including **One-time rank-2 per-step live Ollama
verification** for consolidated rank-2 closure env tables and checklist steps.

## Live structured probe (ticket-060)

Report-only live claim extraction (no default DB writes):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health
python -m rge.cli probe-extract-claims
python -m rge.cli probe-link-concepts
python -m rge.cli probe-draft-relationships
python -m rge.cli probe-detect-contradictions
python -m rge.cli probe-mini-run
python -m rge.cli probe-mini-run-suite
```

Claim probe optional fixture: `--fixture fixtures/sources/live_probe_claim_calibration_short.txt`
(legacy GT02 source: `fixtures/sources/creativity_ai_diversity_short.txt`)

Concept-link probe default input:
`fixtures/claims/live_probe_concept_link_quality_claim.json`.
Optional: `--from-report data/reports/live_probes/probe_extract_claims_<stamp>.json`
or `--chain-extract` (runs claim probe first; variability applies).

Relationship probe default input:
`fixtures/probes/live_probe_relationship_quality_bundle.json`.
Optional: `--from-report data/reports/live_probes/probe_link_concepts_<stamp>.json`
or `--chain-link` (runs concept-link probe first; variability applies).

Contradiction probe default input:
`fixtures/probes/live_probe_contradiction_quality_bundle.json`.
Optional: `--from-report data/reports/live_probes/probe_draft_relationships_<stamp>.json`
(qualifying claim overlay) or `--chain-relationship` (runs relationship probe first;
variability applies).

Mini-run probe chains extract → link → relationship live from the default calibration
source, then contradiction detection with hybrid overlay by default:

```powershell
python -m rge.cli probe-mini-run
python -m rge.cli probe-mini-run --strict-chain
```

`--strict-chain` skips stage 4 when upstream outputs lack contradiction-suitable inputs.

Multi-fixture repeatability batch (default four committed creativity sources):

```powershell
python -m rge.cli probe-mini-run-suite
python -m rge.cli probe-mini-run-suite --strict-chain
```

Repeat `--fixture-source` to override the default set. Writes individual
`probe_mini_run_*.json` reports plus one `probe_mini_run_suite_*.json` summary.

Full stage floors, `contradiction_input_mode` semantics, and evidence-accumulation
workflow: `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md`.

Reports land in gitignored `data/reports/live_probes/`. Excluded from CI/golden.
Optional smoke (`tests/smoke/test_live_ollama_smoke.py`) covers individual probes and
`probe-mini-run` when Ollama is available:

```powershell
python -m pytest -m live_smoke tests/smoke
```

## Live-mode public export publish gate

When effective LLM mode is `ollama` (`RGE_LLM_MODE=ollama` and
`RGE_ALLOW_LIVE_LLM=1`), `export-public` writes to `data/exports/` only unless
`--publish` is passed. Explicit `--output-dir` pointing at
`apps/public-site/public/data/` is blocked without `--publish`.

Fixture-mode runs (`--fixture-mode`) and mock/default mode continue to write
both export directories (Golden Test 26 unchanged).

## Database and artifact paths

| Path | Config var | Git | Notes |
|---|---|---|---|
| `data/` | none | gitignored | All local runtime output (db, reports, exports, generated tickets) |
| `data/db/creative_research.sqlite` | CLI `--db` only | gitignored | Default private accepted graph DB |
| `data/db/live_probe_scratch.sqlite` | `probe-persist-reviewed-report` only | gitignored | Reviewed live probe metadata (not accepted graph) |
| `data/reports/` | none | gitignored | Run/cluster/theory private reports |
| `data/exports/` | none | gitignored | Generated export JSON copies |
| `data/tickets/` | none | gitignored | Generated improvement-ticket artifacts (not the queue) |
| `apps/public-site/public/data/` | none | committed snapshots | Public-safe JSON only; review diffs before commit |
| `apps/public-site/out/` | none | gitignored | Static site build output |
| `tickets/ticket-*.json` | none | committed | Manually reviewed implementation queue |
| `agent_reports/` | none | committed | No secrets in reports |

**Scratch evidence workflow:** after persisting reviewed live probe reports to
`data/db/live_probe_scratch.sqlite`, follow the numbered checklist in
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` (**Scratch evidence workflow
checklist**). Operator loop plan mode surfaces `scratch_evidence_status` and may
recommend `run_scratch_evidence_review`. See also README Operator Quickstart and
`AGENTS.md` Operator Loop.

**Manual synthnote operator spine** (mock LLM; tickets 088–099): operator
`.txt`/`.md` sources for Level-1 `manual_text` research live under gitignored
`data/sources/manual/<domain>/` (e.g. `data/sources/manual/creativity/synthnote.txt`).
Follow the five-step CLI sequence in README **Operator Quickstart**
(**Manual synthnote operator spine**): ingest → extract-claims → link-concepts →
build-relationships → detect-contradictions. Private graph DB:
`data/db/creative_research.sqlite` (or `--db`). **Checksum-pinned mock fixtures**
resolve from `fixtures/manual_source_fixture_map.json` (not live inference). See also
`AGENTS.md` Operator Loop.

**Live validated extraction write** (NM-1): `extract-claims-live` requires
`RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, a source **not** in the checksum
fixture map, and an explicit evidence DB (default `data/db/live_research_evidence.sqlite`).
Refuses the default `creative_research.sqlite` graph path. See README **Live validated
extraction write**.

**Manual synthnote score reconciliation** (after the five-step spine): ingest a
follow-up `manual_text` source (e.g. `data/sources/manual/creativity/synthnote_followup.txt`),
extract claims, then run `reconcile-scores`. See README **Operator Quickstart**
(**Manual synthnote score reconciliation**) for steps 6–8 (follow-up ingest →
extract-claims → reconcile-scores; expected 1 `score_events` row and `may_reduce`
confidence 0.5 → 0.62). Test copy: `fixtures/sources/manual_synthnote_followup.txt`.
See also `AGENTS.md` Operator Loop and
`docs/agents/11_AGENT_OPERATING_PROTOCOL.md` Operator Loop.

**Manual synthnote pipeline proof tests** (mock LLM; tickets 092–093, 105–106):
automated validation lives in `tests/unit/test_manual_source_pipeline_e2e.py`
(full spine through reconcile-scores) and
`tests/unit/test_manual_source_pipeline_idempotency.py` (spine and reconcile
re-run idempotency). Run with `RGE_LLM_MODE=mock`; no Ollama required. See also
`AGENTS.md` Operator Loop.

## Mock vs live behavior (Phase 1 / Phase 2 boundary)

### Golden tests / CI

Always:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden
```

### Pipeline modules

Pipeline modules resolve **effective mode** via `rge/llm/mode.py`:

```txt
effective_mode = mock
  unless RGE_LLM_MODE=ollama AND RGE_ALLOW_LIVE_LLM=1
    then effective_mode = ollama
```

Modules using effective mode:

- `rge/modules/claim_extractor.py`
- `rge/modules/concept_linker.py`
- `rge/modules/relationship_builder.py`
- `rge/modules/contradiction_detector.py`

Without `RGE_ALLOW_LIVE_LLM=1`, behavior is identical to pre-ticket-037 (mock
fixtures). With opt-in set but Ollama unreachable, structured calls raise a
clear error and do **not** silently fall back to mock.

Fixture-mode orchestration (`execute_fixture_mode_run` in `rge/cli.py`) **always**
forces mock regardless of operator `.env` settings.

Golden tests and fixture runs therefore do **not** need a running Ollama instance.

### Ollama client

`rge/llm/ollama_client.py`:

- `health_check()` may call `OLLAMA_BASE_URL` when explicitly invoked.
- Structured pipeline tasks (`extract_claims`, `link_concepts`,
  `draft_relationships`, `detect_contradictions`) call Ollama when effective mode
  is `ollama`.
- Non-pipeline tasks (`draft_run_summary`, `draft_ticket`) remain unimplemented
  on the live client.

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
4. Understand structured tasks require `RGE_ALLOW_LIVE_LLM=1` (ticket-037).
5. Run `python -m rge.cli model-health` to verify Ollama reachability.
6. Run safety audit after any export: `python -m rge.modules.safety_auditor --audit full`

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
