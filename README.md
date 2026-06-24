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

**Internal MVP launch candidate (2026-06-23; ticket-388):** the repo is cleared for
**mock-first internal operator use** when `data/reports/researcher_product_proof_latest.json`
reports `product_verdict: GO`. This is **not** a public launch, paid-cloud launch, or live
arbitrary-source research product. Live OpenAI, unattended paid execution, and live OpenAlex
orchestrator proofs remain opt-in operator work.

Checkpoint report: `agent_reports/2026-06-23_phase-3_ticket-388_internal-mvp-launch-checkpoint-v0.md`

| Tier | Status | What it means |
|------|--------|---------------|
| **Internal MVP** | **launch candidate (mock-first)** | Operator proof chain (`prove-researcher-product`), verify/operator_loop/autocycle status surfaces, safety audit, and static Atlas preview on localhost. Default research prompt; no runtime link from CLI to the dev server — preview reads committed JSON under `apps/public-site/public/data/`. |
| **MVP-Engine** | **mock/fixture-proven** | Deterministic Python pipeline, validator gate, safety model, public export, golden tests (GT01–GT26), and fixture-mode orchestration are real and green. |
| **MVP-Research** | **partial — NM-1 + NM-4 evidence DB** | NM-1: first live validated claim write via `extract-claims-live` on gitignored `data/db/live_research_evidence.sqlite`. NM-4: operator-proven live manual_text spine through reconcile on that same evidence DB (tickets 127–133). Default graph DB synthnote path remains checksum-mock — not arbitrary live inference. |
| **Arbitrary-source pipeline** | **partial** | **Phase 3 staged spine (mock/fixture-proven):** discover → fetch → ingest-staged → extract → link → build → detect → reconcile → report for rank #1 and #2 OpenAlex candidates, dual-candidate idempotency, and `research run --staged-spine` orchestration (tickets 144–164). Unit tests patch OpenAlex/fetcher I/O; operator runs require `RGE_ALLOW_SOURCE_NETWORK=1`. **Opt-in operator proofs (not CI):** per-step live OpenAlex proofs (tickets 167–190) and single-command orchestrator proof via `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` (ticket-193) as `pytest -m live_network` — see Operator Quickstart. **Per-step live Ollama (rank-1 and rank-2; orchestrator still mock):** rank-1 extract/link/build/detect (204/208/212/217); rank-2 extract/link/build/detect (230/236/237/238) — each has a separate `RGE_ALLOW_LIVE_STAGED_*_LIVE_LLM` or `RGE_ALLOW_LIVE_STAGED_RANK2_*_LIVE_LLM` gate and CLI fallthrough flag; rank-2 surface **closed at detect** (ticket-240 checklist). **Detect seed operator doc triangle (245–247):** README **Domain seed**, AGENTS, and `docs/agents/12_RUNTIME_CONFIG.md` document GT7 `seed_domain_opposing_context` mock isolation for live detect (ticket-243). **Deterministic Python (no live LLM path):** `reconcile-scores` and `generate-run-report` on staged spine (tickets 184/187; pre-ticket audits 221/222). **`RGE_ALLOW_LIVE_STAGED_RECONCILE` / `_REPORT`** gate OpenAlex network spines only — not Ollama. **Not proven in CI/default pytest:** live OpenAlex (operator opt-in); live LLM on full staged orchestrator. **Evidence DB:** NM-4 live ingest → extract/link/relationship/contradiction fall-through + deterministic reconcile (`--evidence-db-reconcile`) on gitignored evidence DB. **Default graph DB:** committed synthnote files still use checksum-pinned mock fixtures. `research run` without `--fixture-mode` remains `not_implemented`. |
| **Cloud synthesis** | **mock-first wired** | `synthesize --packet` defaults to `mock_cloud` (ticket-059). Live OpenAI HTTP is opt-in only behind explicit env gates — not CI/default pytest. |

**Phase 1 MVP is complete** for the engine tier. The public site serves **committed fixture
snapshots** (`source_type: fixture` on cards; staged-spine Atlas preview JSON) — not a live
connection to the private SQLite graph at browse time.

### What is running today (internal MVP profile)

| Surface | Command / URL | Runtime link |
|---------|---------------|--------------|
| **Research CLI** | `python -m rge.cli` (alias `research` when on PATH) | Private SQLite, gitignored reports |
| **Verification gate** | `python -m rge.cli verify --skip-site` | Mock-only pytest + golden + safety |
| **Product proof** | `python -m rge.cli prove-researcher-product` | Scratch work dir → gitignored GO artifact |
| **Operator planning** | `python -m rge.modules.operator_loop --mode plan` | Read-only JSON recommendations |
| **Atlas preview UI** | `cd apps/public-site && npm run dev` → http://localhost:3000/atlas-preview | Static JSON imports only — **no API on :8000** |

### Non-launch blockers (explicit)

| Blocker | Status |
|---------|--------|
| Live OpenAI / paid cloud | Gated — explicit env + cost caps |
| Public site live graph | Fixture preview JSON only at browse time |
| Unattended autocycle implementation | Blocked — review-gated tickets |
| Bare `research run --topic --domain` | `not_implemented` without fixture/staged flags |
| Live OpenAlex orchestrator pass | Operator opt-in; may skip with `unsuitable_live_artifact` |

What is **real deterministic engine plumbing today**:

- SQLite migration harness and private research graph (7 migrations)
- Source ingestion, claim extraction, concept linking, relationship building, contradiction detection, score reconciliation
- Research contract drift gating, queue ranking, cluster/theory/ontology/domain/run reports
- Improvement ticket generation with builder-consumption validation
- Fail-closed public card export and static Next.js public site
- Deterministic safety auditor and prompt-injection handling
- Full fixture-mode orchestration: `research run --fixture-mode` (Golden Test 26)
- Phase 3 staged orchestration: `research run --staged-spine` (mock LLM; network env for discover/fetch; `--fixture-mode` optional legacy alias; see Operator Quickstart)

What is **mock or checksum-pinned fixture content** (not arbitrary live inference):

- Golden tests, CI, and `research verify` always use `RGE_LLM_MODE=mock`
- Fixture-mode orchestration forces mock regardless of `.env` settings
- Manual synthnote spine (`fixtures/manual_source_fixture_map.json`) ingests real bytes but resolves **canned** LLM candidate JSON by `raw_text_checksum` — the validator runs for real, the candidates are pinned fixtures
- Live discovery (`research run` without flags) defaults to mock staged-spine orchestration (ticket-362); use `--fixture-mode` for the full MVP export pipeline

What is **live report-only** (no graph writes unless operator explicitly opts in):

- `probe-extract-claims`, `probe-mini-run`, and related live probes write gitignored reports only (`db_writes: false`)
- **`extract-claims-live`** (NM-1) is the first explicit live validated write path; requires `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, a non-fixture-map source, and an explicit evidence DB (default `data/db/live_research_evidence.sqlite`, not the default graph DB)
- **NM-4 evidence DB spine** (tickets 127–133): live `--live-manual-*` fall-through on standard pipeline commands plus deterministic `reconcile-scores --evidence-db-reconcile` on the same gitignored evidence DB — see Operator Quickstart **NM-4 evidence DB operator spine**
- **Per-step live staged extract** (ticket-204): live Ollama `extract-claims --live-staged-fallthrough` on rank-1 staged OpenAlex ingest (temp `--db` only; separate env gate from mock-fixture extract) — see Operator Quickstart **Live staged extract (live Ollama)**
- **Per-step live staged link** (ticket-208): live Ollama `link-concepts --live-staged-link-fallthrough` after mock extract on rank-1 staged source (temp `--db` only; separate env gate from mock link) — see Operator Quickstart **Live staged link (live Ollama)**
- **Per-step live staged build** (ticket-212): live Ollama `build-relationships --live-staged-build-fallthrough` after mock extract + mock link on rank-1 staged source (temp `--db` only; separate env gate from mock build) — see Operator Quickstart **Live staged build (live Ollama)**
- **Per-step live staged detect** (ticket-217): live Ollama `detect-contradictions --live-staged-detect-fallthrough` after mock extract + mock link + mock build on rank-1 staged source (temp `--db` only; separate env gate from mock detect; domain opposing context seed required) — see Operator Quickstart **Live staged detect (live Ollama)**
- **Per-step live staged rank-2 extract/link/build/detect** (tickets 230/236/237/238): separate rank-2 `RGE_ALLOW_LIVE_STAGED_RANK2_*_LIVE_LLM` gates and CLI fallthrough flags; surface **closed at detect** — see Operator Quickstart **One-time rank-2 per-step live Ollama verification**
- **Staged reconcile and report** (tickets 184/187): `reconcile-scores` and `generate-run-report` are **deterministic Python** (`score_reconciler.py`, `run_evaluator.py`) — no live LLM fallthrough. `RGE_ALLOW_LIVE_STAGED_RECONCILE` / `RGE_ALLOW_LIVE_STAGED_REPORT` opt into **live OpenAlex network** pytest spines only (mock LLM upstream). Staged rank-1 and rank-2 model-assisted live Ollama steps end at detect (204–217; 230/236–238).

What requires **explicit live opt-in** (local Ollama only):

- Four pipeline structured tasks: claim extraction, concept linking, relationship
  building, contradiction detection (ticket-037)
- Requires `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`
- Run `python -m rge.cli model-health` before live pipeline work

**Live probe runbook** (mini-run stage floors, `contradiction_input_mode`, scratch
evidence workflow checklist, human-gated improvements):
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` — see **Scratch evidence workflow checklist**.

See `docs/agents/13_MODEL_ESCALATION_POLICY.md` for mode profiles and task tiers.

Phase 2 work (live Ollama, UI polish, deployment) is tracked in `agent_reports/2026-06-12_phase-2_ticket-roadmap.md`.

## System functions

All operator commands use `python -m rge.cli <subcommand>` (Windows: `research` may not be on
PATH after editable install).

### Research pipeline (private graph)

| Function | CLI | Notes |
|----------|-----|-------|
| Ingest sources | `ingest`, `ingest-staged`, `ingest-webpage` | Writes private SQLite only |
| Extract / link / build / detect | `extract-claims`, `link-concepts`, `build-relationships`, `detect-contradictions` | Mock default; live fallthrough flags opt-in |
| Score history | `reconcile-scores` | Deterministic Python |
| Queue / reports | `rank-research-queue`, `generate-cluster-report`, `generate-run-report`, `generate-theory`, … | Mock LLM where applicable |
| Full fixture MVP | `run --fixture-mode` | Golden Test 26 shape |
| Staged spine | `run --staged-spine` | Mock LLM; network env for discover/fetch |

Default research question (creativity domain): *Does AI improve creative output while reducing diversity?*

### Operator proof and verification

| Function | CLI / module | Artifact |
|----------|--------------|----------|
| Mock verification suite | `verify`, `verify --skip-site` | Exit code + JSON report |
| End-to-end product proof | `prove-researcher-product` | `data/reports/researcher_product_proof_latest.json` |
| Arbitrary-source bundle | `prove-arbitrary-source-bundle` | `data/reports/operator_proof_bundle/operator_proof_bundle.json` |
| Safety audit | `python -m rge.modules.safety_auditor --audit full` | stdout JSON |
| Operator plan | `python -m rge.modules.operator_loop --mode plan` | Recommended actions + status mirrors |
| Bounded autocycle | `python -m rge.modules.operator_autocycle --mode plan` | Cycle JSON; blocks risky automation |

Plan/verify/autocycle JSON includes `researcher_product_proof_status` (`product_verdict`,
`product_proof_recommended`, graph counts). See Operator Quickstart **Researcher product proof**.

### Synthesis (mock-first cloud boundary)

| Function | CLI / script | Notes |
|----------|--------------|-------|
| Packet synthesis | `synthesize --packet` | Default provider `mock_cloud` |
| Benchmark throughput | `scripts/run_synthesis_packet_benchmark.py` | Gitignored benchmark JSON |
| End-to-end synthesis loop | `scripts/run_end_to_end_synthesis_operator_loop.py` | Operator gates for live cloud |

### Public export (reviewed snapshots)

| Function | CLI | Output |
|----------|-----|--------|
| Public cards | `export-public` | `data/exports/` → copy to `apps/public-site/public/data/` |
| Atlas snapshot (operator) | `export-atlas-snapshot` | Private atlas JSON |
| Atlas preview refresh | `scripts/refresh_atlas_preview_from_staged_spine.py` | Updates committed `atlas_snapshot_preview.json` |

### Live / opt-in (not internal MVP default)

| Function | Gate | Notes |
|----------|------|-------|
| Live Ollama pipeline | `RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama` | Four structured tasks; `model-health` first |
| Live validated extract | `extract-claims-live` | NM-1 evidence DB only |
| Live OpenAlex staged proofs | `RGE_ALLOW_SOURCE_NETWORK=1`, per-step `RGE_ALLOW_LIVE_STAGED_*` | `pytest -m live_network` — not CI |
| Live OpenAI synthesis | `RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP=1`, … | Fail-closed; cost caps |

## Install

```bash
python -m pip install -e ".[dev]"
cd apps/public-site && npm install
```

On Windows, `research.exe` is often not on PATH after editable install. Use
`python -m rge.cli <command>` (for example `python -m rge.cli verify`) instead
of bare `research …`. A missing `research` command is a PATH issue, not a failed
verification suite, when the module form succeeds.

## Internal MVP launch (localhost)

Mock-first profile for browsing the Atlas preview after product proof. **No live OpenAI, no
live orchestrator, no paid cloud.**

```powershell
# 1. Repo root — mock-only env
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"

# 2. Refresh product proof (scratch paths only)
python -m rge.cli prove-researcher-product `
  --work-dir data/tmp/researcher_product_proof_work `
  --artifact-out data/reports/researcher_product_proof_latest.json `
  --benchmark-runs 25

# 3. Confirm GO
Get-Content data/reports/researcher_product_proof_latest.json | Select-String product_verdict

# 4. Start read-only preview (separate terminal)
cd apps/public-site
npm install   # first time only
npm run dev
```

Open **http://localhost:3000/atlas-preview** (Next.js default port; use the URL printed if
3000 is busy).

**Data boundary:** the dev server does **not** read the gitignored product-proof artifact at
runtime. `/atlas-preview` renders committed JSON from `apps/public-site/public/data/`
(primarily `atlas_snapshot_preview.json`, `atlas_coherence_preview.json`). Updating preview
from a new pipeline run requires an export/refresh script (see **Public export** in System
functions) — not automatic on `prove-researcher-product`.

Optional verification before launch:

```powershell
python -m rge.cli verify --skip-site
python -m rge.modules.safety_auditor --audit full
```

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

**Local operator env profile (ticket-213):** copy `.env.example` → `.env.local`
(gitignored). Set `RGE_LLM_MODE`, `RGE_ALLOW_LIVE_LLM`, `RGE_LOCAL_LLM`,
`OLLAMA_BASE_URL`, `RGE_ALLOW_SOURCE_NETWORK`, `OPENALEX_MAILTO`, and staged live
gates there for live operator runs. The repo reads optional root `.env` via
`rge/config.py`; shell exports override file values. Full variable table and staged
gate matrix: `docs/agents/12_RUNTIME_CONFIG.md` (**Live staged operator env profile**).
Run `python -m rge.cli model-health` before live pipeline work (does not print secrets).

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

**End-to-end synthesis operator loop** (mock-safe default; tickets grounded export + cloud synthesis + human-review UI): one command chains grounded packet staging/export → mock cloud synthesis → export scan → sign-off ledger merge → `atlas_synthesis_human_review_latest.json` sync. Review flagged sentences and sign-off status on `/atlas-preview` after site build.

Optional fixture sign-off during the loop:

```powershell
$env:RGE_ALLOW_END_TO_END_SYNTHESIS_OPERATOR_LOOP = "1"
$env:RGE_ALLOW_END_TO_END_SYNTHESIS_OPERATOR_LOOP_SIGN_OFF = "1"
$env:RGE_ALLOW_SYNTHESIS_REVIEW_SIGN_OFF = "1"
python scripts/run_end_to_end_synthesis_operator_loop.py --fixture-packet --with-sign-off --sync-public
```

```powershell
$env:RGE_ALLOW_END_TO_END_SYNTHESIS_OPERATOR_LOOP = "1"
$env:RGE_LLM_MODE = "mock"
$env:RGE_CLOUD_LLM_ENABLED = "1"
$env:RGE_ALLOW_OPENAI_SYNTHESIS = "1"
$env:OPENAI_API_KEY = "sk-operator-mock-or-live"

# Fixture packet + mock synthesis (no paid API calls)
python scripts/run_end_to_end_synthesis_operator_loop.py --fixture-packet

# Export from private graph DB instead of fixture
python scripts/run_end_to_end_synthesis_operator_loop.py --db data/db/creative_research.sqlite

# Validate only (dry-run synthesis; human-review falls back to fixture queue)
python scripts/run_end_to_end_synthesis_operator_loop.py --fixture-packet --dry-run-only
```

**Live cloud synthesis profiles** (`--profile live_openai` or `--profile live_openrouter`): operator opt-in only; enforces HTTP gates, cost caps (`RGE_CLOUD_MAX_USD_PER_RUN`, `RGE_CLOUD_MAX_TOKENS_PER_CALL`), and `RGE_ALLOW_LIVE_CLOUD_SYNTHESIS_OPERATOR_LOOP=1`. Not run in CI or scheduled mock loops.

```powershell
$env:RGE_ALLOW_END_TO_END_SYNTHESIS_OPERATOR_LOOP = "1"
$env:RGE_ALLOW_LIVE_CLOUD_SYNTHESIS_OPERATOR_LOOP = "1"
$env:RGE_CLOUD_LLM_ENABLED = "1"
$env:RGE_LLM_MODE = "cloud"
$env:RGE_CLOUD_MAX_USD_PER_RUN = "0.50"
$env:RGE_CLOUD_MAX_TOKENS_PER_CALL = "4096"

# Live OpenAI HTTP
$env:RGE_ALLOW_OPENAI_SYNTHESIS = "1"
$env:RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP = "1"
$env:OPENAI_API_KEY = "<operator key>"
python scripts/run_end_to_end_synthesis_operator_loop.py --profile live_openai --fixture-packet

# Live OpenRouter HTTP
$env:RGE_ALLOW_OPENROUTER_SYNTHESIS = "1"
$env:RGE_ALLOW_OPENROUTER_SYNTHESIS_LIVE_HTTP = "1"
$env:OPENROUTER_API_KEY = "<operator key>"
python scripts/run_end_to_end_synthesis_operator_loop.py --profile live_openrouter --fixture-packet
```

Legacy `--live-cloud` maps to `--profile live_openai` (or `--provider openrouter`). Decomposed CLI steps remain available: `export-grounded-synthesis-packet`, `synthesize`, and `run_synthesis_human_review_ui.py --scan-exports --sync-public`.

**Full Atlas refresh + optional synthesis loop:** the operator checklist can run a mock end-to-end synthesis loop before the human-review export scan when opted in. Default refresh skips this step; use `--with-synthesis-loop` or set `RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH_SYNTHESIS_LOOP=1`.

```powershell
$env:RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH = "1"
$env:RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH_SYNTHESIS_LOOP = "1"
$env:RGE_ALLOW_END_TO_END_SYNTHESIS_OPERATOR_LOOP = "1"
$env:RGE_LLM_MODE = "mock"
python scripts/run_full_atlas_refresh_checklist.py --fixture-only --skip-site --with-synthesis-loop
```

**Operator loop plan mode:** when `atlas_synthesis_human_review_latest.json` is missing, invalid, or older than unscanned `synthesis_output.json` files under `data/exports/`, `python -m rge.modules.operator_loop --mode plan` recommends `run_synthesis_operator_loop` (mock fixture loop + site build). Full atlas refresh recommendations append `--with-synthesis-loop` when synthesis artifacts are also stale.

**/atlas-preview alerts:** when the committed human-review artifact has flagged queue entries, the preview page shows an operator alert banner above the fold with packet id, provider, sentence preview, and primary grounding issue — scroll to **Synthesis human review (operator panel)** for full detail.

**Synthesis sign-off workflow** (operator CLI; private ledger under gitignored `data/operator/`):

```powershell
python scripts/run_synthesis_review_sign_off.py --list-pending
$env:RGE_ALLOW_SYNTHESIS_REVIEW_SIGN_OFF = "1"
python scripts/run_synthesis_review_sign_off.py --fixture-sign-off --sync-public
```

Plan mode recommends `run_synthesis_review_sign_off` when grounding-passed outputs await sign-off. `/atlas-preview` shows pending and signed-off rows in the human-review panel.

When synthesis artifacts are **also stale**, plan mode recommends `run_synthesis_operator_loop` with `--with-sign-off` instead of standalone sign-off. Full atlas refresh recommendations append both `--with-synthesis-loop` and `--with-synthesis-sign-off` when pending sign-offs exist.

**Operator autocycle blocking:** when plan mode recommends synthesis sign-off, a synthesis loop with sign-off, or researcher product proof (`run_researcher_product_proof`), `python -m rge.modules.operator_autocycle --mode plan` stops with `operator_action_blocked_automation` (same pattern as scratch evidence review and arbitrary-source proof bundle). Autocycle never runs sign-off, synthesis loop, or product proof commands without explicit operator review.

**Arbitrary-source operator proof bundle** (mock LLM only; temp/scratch paths): when the
principal audit checkpoint surfaces a **product-risk / live-research /
arbitrary-source drift warning** (for example: *"No product-risk or live-research proof
advanced in the last 3 completed tickets."*), operator plan mode may recommend
`run_arbitrary_source_proof_bundle` (`review_gated`) before ticket implementation when
no higher-priority open ticket blocks it. The action runs the mock-only staged-spine proof
on scratch paths — no live OpenAlex network, no live Ollama, and no `export-public
--publish`.

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli prove-arbitrary-source-bundle `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/operator_proof_bundle_scratch.sqlite `
  --output-dir data/reports/operator_proof_bundle `
  --staging-dir data/sources/staged/operator_proof_bundle `
  --export-dir data/exports/operator_proof_bundle `
  --bundle-out data/reports/operator_proof_bundle/operator_proof_bundle.json
```

Inspect `data/reports/operator_proof_bundle/operator_proof_bundle.json`:

| Field | Expected on success |
| --- | --- |
| `status` | `completed` |
| `usable_output` | `true` |
| `pipeline_mode` | `fixture_staged_rank1` |

**`arbitrary_source_proof_bundle_status`** (operator plan and autocycle JSON): read-only
inspection of the proof bundle artifact and drift recommendation.

| Field | When present |
| --- | --- |
| `proof_bundle_recommended` | `true` when principal-audit drift is active and the artifact is not yet satisfied |
| `proof_artifact_satisfied` | `true` when bundle JSON has `status: completed` and `usable_output: true` |
| `proof_artifact_path` | Absolute path to `operator_proof_bundle.json` |
| `proof_artifact_status` | `missing`, `present`, `satisfied`, or `invalid` |
| `operator_commands.proof_bundle` | Copy-paste mock-only shell command from plan JSON |

When `proof_artifact_satisfied` is `true`, plan mode sets `proof_bundle_recommended` to
`false` and Tier 2 autocycle no longer stops on product-risk drift for those warnings.
Autocycle still blocks with `operator_action_blocked_automation` while the proof bundle
remains recommended — same pattern as scratch evidence review.

Re-plan after a successful run:

```powershell
python -m rge.modules.operator_loop --mode plan
```

**Synthesis packet benchmark dry-run** (mock_cloud only; ticket-059 bridge): on synthesis
packet CLI feature branches (for example `phase-3/cloud-synthesis-packet-cli-throughput`),
measure mock throughput and review-threshold cadence without live OpenAI HTTP. Default
provider is `mock_cloud`; the benchmark script refuses `--provider openai`.

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_synthesis_packet_benchmark.py `
  --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json `
  --runs 25
```

Writes gitignored operator artifact `data/reports/synthesis_packet_benchmark_latest.json`
with `reports_per_hour_estimate`, review-threshold flags, and `cloud_call_made_any`
(always `false` under default mock). Single packet run (no repeat loop):

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli synthesize --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json
```

**`synthesis_packet_benchmark_status`** (operator plan JSON on synthesis CLI branches):
read-only inspection of the benchmark artifact.

| Field | When present |
| --- | --- |
| `benchmark_recommended` | `true` when the artifact is missing on an active synthesis CLI branch |
| `reports_per_hour_estimate` | Populated when artifact `status` is `available` |
| `artifact_path` | `data/reports/synthesis_packet_benchmark_latest.json` |
| `operator_commands.benchmark` | Copy-paste mock-only benchmark command from plan JSON |

When the artifact is missing, plan mode may recommend `run_synthesis_packet_benchmark`
(`safe_autonomous`). Execute-safe runs the benchmark hook after verification when that
action is recommended. Private `self_improvement_status` includes the same snapshot on
synthesis CLI branches. See also `docs/agents/12_RUNTIME_CONFIG.md` and AGENTS.md
Operator Loop (cloud synthesis maturity bullet).

**Live OpenAI synthesis evaluator** (read-only; ticket-394): after an opt-in
`synthesize --packet --provider openai --confirm` run, evaluate the generated synthesis
output JSON without making additional network calls. Writes gitignored operator artifact
`data/reports/openai_synthesis_evaluator_latest.json` with `evaluator_verdict`
(`GO`, `PARTIAL`, or `NO-GO`), grounding/governor summaries, and remediation suggestions.

```powershell
# Optional live canary (explicit gates + --confirm required)
python -m rge.cli synthesize `
  --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json `
  --provider openai --confirm --load-operator-env `
  --output-dir data/tmp/openai_synthesis_canary

# Deterministic evaluator (no live HTTP)
python scripts/run_openai_synthesis_evaluator.py `
  --artifact data/tmp/openai_synthesis_canary/synthesis_output_syn_packet_grounded_dry_run_fixture.json
```

Pass criteria for operator canary + evaluator: `grounding_passed: true`,
`governor_verdict: GO`, `no_accepted_graph_writes: true`, and `evaluator_verdict: GO`.
The evaluator reuses `synthesis_grounding`, `synthesis_review_threshold_policy`, and
`autonomous_synthesis_governor` checks; it does not auto-promote remediation suggestions
into `tickets/`.

**Researcher product proof** (mock LLM only; scratch work dir; tickets 381–384): end-to-end
mock-first proof that chains arbitrary-source proof bundle → synthesis packet → benchmark →
safety audit → public atlas preview visibility. Clears principal-audit **product-risk drift**
when the gitignored artifact reports `product_verdict: GO` (or `PARTIAL` with documented
gaps). No live OpenAlex network, no live Ollama, and no `export-public --publish`.

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli prove-researcher-product `
  --work-dir data/tmp/researcher_product_proof_work `
  --artifact-out data/reports/researcher_product_proof_latest.json `
  --benchmark-runs 3
```

Operator script wrapper (same gates):

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_researcher_product_proof.py `
  --work-dir data/tmp/researcher_product_proof_work `
  --benchmark-runs 3
```

Writes gitignored artifact `data/reports/researcher_product_proof_latest.json` with
traceable graph counts, synthesis/benchmark summaries, and `product_verdict` (`GO`,
`PARTIAL`, or `NO-GO`). Scratch SQLite and staged paths live under `--work-dir` only.

Inspect key artifact fields:

| Field | Expected on success |
| --- | --- |
| `status` | `completed` |
| `product_verdict` | `GO` (or `PARTIAL` when benchmark or atlas preview gaps remain) |
| `source_count` / `claim_count` / `evidence_count` | Non-zero after mock proof bundle |
| `benchmark.reports_per_hour_estimate` | Populated when benchmark step completes |

**`researcher_product_proof_status`** (operator plan, verify, and autocycle JSON):
read-only inspection of the product proof artifact and drift recommendation.

| Field | When present |
| --- | --- |
| `product_proof_recommended` | `true` when principal-audit product-risk drift is active and the artifact is missing |
| `product_verdict` | `GO`, `PARTIAL`, or `NO-GO` when artifact `status` is `available` |
| `artifact_path` | `data/reports/researcher_product_proof_latest.json` |
| `source_count` / `claim_count` / `evidence_count` | Populated from the latest artifact |
| `reports_per_hour_estimate` | Benchmark throughput from the chained run |
| `operator_commands.product_proof` | Copy-paste mock-only shell command from plan JSON |

When `product_verdict` is `GO`, plan mode sets `product_proof_recommended` to `false` and
autocycle no longer blocks on product-risk drift for those warnings. Autocycle still blocks
with `operator_action_blocked_automation: run_researcher_product_proof` while the artifact
is missing and drift is active — same pattern as arbitrary-source proof bundle.

`python -m rge.cli verify --skip-site` lists `prove-researcher-product` in the operator
checklist (not run automatically). Re-plan after a successful run:

```powershell
python -m rge.modules.operator_loop --mode plan
```

**Full atlas refresh sign-off step:** every checklist run executes `synthesis_review_sign_off_refresh` after the human-review export scan (ledger merge into `atlas_synthesis_human_review_latest.json`). Optional fixture sign-off during refresh:

```powershell
$env:RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH = "1"
$env:RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH_SYNTHESIS_SIGN_OFF = "1"
$env:RGE_ALLOW_SYNTHESIS_REVIEW_SIGN_OFF = "1"
python scripts/run_full_atlas_refresh_checklist.py --fixture-only --skip-site --with-synthesis-sign-off
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

**Staged Phase 3 fixture-mode spine** (mock LLM; tickets 144–163): run discover → fetch →
ingest-staged → extract → link → build → detect → reconcile → report for **two** OpenAlex
candidates on one DB. Uses mock LLM only (`RGE_LLM_MODE=mock`); **does not** run public
export, theory, cluster report, or improvement tickets (unlike the MVP fixture run above).
Requires live OpenAlex HTTP for `discover-sources` and `fetch-candidate` unless you are
running unit tests (which patch network I/O).

Use `--staged-spine` alone for Phase 3 live discovery entry; `--fixture-mode --staged-spine`
remains a backward-compatible alias. `--fixture-mode` without `--staged-spine` runs the
golden MVP fixture pipeline instead.

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m rge.cli run `
  --staged-spine `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/staged_spine_demo.sqlite `
  --staging-dir data/sources/staged `
  --output-dir data/reports/staged_spine_demo `
  --run-id run_staged_fixture_mode_spine
```

Expected stable counts after one pass (dual-candidate mock spine):

| Metric | Expected |
| --- | --- |
| `sources` | 3 (domain opposing context + 2 staged candidates) |
| `candidate_sources` / `research_queue` | 2 each |
| `score_events` | 2 |
| `run_reports` | 2 (`{run_id}_rank1`, `{run_id}_rank2`) |
| `qualifies` relationship evidence | 2 |

The **final** stdout JSON document from `research run --staged-spine` (after any
intermediate step JSON from sub-CLI invocations) also includes candidate wiring metadata:

| Field | Meaning |
| --- | --- |
| `rank1_candidate_id` | OpenAlex discover candidate id used for rank-1 fetch/spine steps |
| `rank2_candidate_id` | OpenAlex discover candidate id used for rank-2 fetch/spine steps |

On the default mock orchestrator path (without `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR`),
these are the fixed fixture ids `disc_openalex_W2741809807` (rank-1) and
`disc_openalex_W1234567890` (rank-2). With the live orchestrator gate enabled, the
orchestrator selects ids via `_staged_rank_candidate_ids` (rank-1 selection +
rank-2 title heuristic). Re-runs on the same `--db` keep the same candidate ids
(ticket-262).

Re-running the same command on the same `--db` is idempotent (stable row counts; ticket-163).
Rank #1 staged steps use auto mock routing; rank #2 uses explicit `--fixture` bindings
inside the orchestrator. Automated proof:
`tests/unit/test_staged_fixture_mode_run_spine.py`.

**Live staged proof layers (tickets 233–234)** — operator runbook for interpreting
live OpenAlex proofs. Default CI runs **layer 2 only** (network-free). Layers 1 and 3
require `-m live_network` and env gates below.

| Layer | What it proves | Typical signal | CI? |
|------:|----------------|----------------|-----|
| **1 — Live acquisition** | Real OpenAlex discover + top-N fetch writes a staged artifact | pytest **PASS** | No (`live_network`) |
| **2 — Mock spine** | Ingest → extract/link/build/detect → reconcile/report with checksum-pinned mock fixtures | default `pytest` **PASS** | Yes |
| **3 — Combined live mock spine** | Layer 1 + live ingest + mock-fixture downstream steps | pytest **PASS** or **SKIPPED** | No (`live_network`) |

**Layer 1 — run first to validate fetch resilience** (ticket-233: OA-first URL ordering,
multi-URL retry on 403/401/406, top-N candidates — rank-1 publisher 403 alone must not
fail acquisition):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_fetch_validation.py -m live_network -q
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py::test_live_openalex_source_acquisition_for_reconcile_spine -m live_network -q
```

Inspect successful `fetch-candidate` JSON for `selected_url_kind` and `attempted_urls`
when a publisher route was blocked but an OA route succeeded.

**Layer 2 — deterministic mock spine (default CI):** patched OpenAlex + HTML fixtures;
no live network. Examples: `tests/unit/test_staged_ingest_reconcile_spine.py`,
`tests/unit/test_staged_ingest_run_report_spine.py`, `tests/unit/test_staged_fixture_mode_run_spine.py`.

**Layer 3 — combined live mock spine:** full per-step proofs (extract through
reconcile/report) when a fetched live artifact also satisfies mock-spine marker phrases
(`human-ai co-creativity`, `songwriting` — checksum-pinned fixture text). Each spine
module exposes `test_live_openalex_combined_*` alongside `test_live_openalex_source_acquisition_*`.

Example (reconcile; requires `RGE_ALLOW_LIVE_STAGED_RECONCILE=1`):

```powershell
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py::test_live_openalex_combined_reconcile_mock_spine -m live_network -q
```

**Interpreting `unsuitable_live_artifact` (layer 3 skip — not a regression):** when live
discover + fetch succeed for one or more top-N candidates but **none** of the fetched
artifacts contain the mock-spine marker phrases, combined tests **skip** with structured
JSON (`reason: unsuitable_live_artifact`). This is **catalog/fixture coupling**, not a
fetch, reconcile, or report engine failure.

Example skip body (truncated):

```json
{
  "proof_layer": "combined_live_mock_spine",
  "reason": "unsuitable_live_artifact",
  "detail": "Live source acquisition succeeded for one or more candidates, but none of the fetched top-N artifacts satisfy mock-spine marker preconditions.",
  "required_markers": ["human-ai co-creativity", "songwriting"],
  "unsuitable_candidates": [{ "candidate_id": "disc_openalex_...", "missing_markers": ["songwriting"] }],
  "assessment": "Not a fetch/reconcile/report regression — live OpenAlex catalog text does not match checksum-pinned mock fixture phrases for this query."
}
```

| Observation | Likely meaning | Action |
|-------------|----------------|--------|
| Layer 1 **PASS**, layer 3 **SKIPPED** (`unsuitable_live_artifact`) | Acquisition healthy; today's OpenAlex results ≠ fixture phrases | **Expected** — treat as NO-GO for combined proof only; rely on layer 2 for CI |
| Layer 1 **FAIL** (`forbidden`, `paywall_blocked`, `no_fetchable_url`) | No fetchable URL in top-N | Retry from unrestricted network; inspect `attempted_urls`; adjust query toward OA works |
| Layer 3 **FAIL** (not skip) after layer 1 passed | Downstream spine regression | Investigate ingest/mock LLM/reconcile/report — not acquisition |
| Combined **PASS** | Live catalog returned fixture-compatible text | Full operator mock-spine proof succeeded |
| Atlas coherence **SKIPPED** (`unsuitable_live_artifact`) | Same layer-3 preflight as other combined proofs (ticket-285) | **Expected** — orchestrator/atlas export not attempted; not an atlas contract regression |
| Atlas coherence **PASS** | Staged orchestrator + private `export-atlas-snapshot` met coherence thresholds | Research Atlas v0 populated from live staged run (temp DB only) |

Helpers: `tests/unit/live_staged_proof_layers.py` (`require_mock_spine_compatible_fetch_or_skip`,
`run_live_source_acquisition`).

**Live staged network proofs** (operator opt-in; tickets 167–193): pytest proofs on
real OpenAlex HTTP with temp DB paths. **Not** run in CI or default `pytest`
(collection excludes `live_network`; see `pyproject.toml`). Default staged proofs use
mock LLM after live ingest; fetch/ingest proofs stop before `extract-claims`; tickets
172/175/178/181 add mock-fixture extract, link, build, and detect after live ingest;
tickets 184/187 add deterministic reconcile-scores and generate-run-report for rank-1;
ticket-190 adds rank-2 candidate discover through generate-run-report with
second-candidate mock fixtures; ticket-193 adds single-command
`research run --fixture-mode --staged-spine` on real OpenAlex via
`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` (orchestrator **always** forces mock LLM).
ticket-285 adds orchestrator → private **`export-atlas-snapshot`** coherence proof
(same orchestrator env gate; layer-3 `unsuitable_live_artifact` skip when live text
lacks mock-spine markers — see table above).
**Per-step live Ollama extract** on staged rank-1 ingest is a separate operator opt-in
(ticket-204; not orchestrator-wide). **Per-step live Ollama link** after mock extract is
a separate operator opt-in (ticket-208; not orchestrator-wide). These proofs write to temp DB and report paths
only — they do **not** public-export results. Patched-network orchestrator proof remains
`tests/unit/test_staged_fixture_mode_run_spine.py` (ticket-162).

*Discover + fetch* (ticket-167):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_fetch_validation.py -m live_network -q
```

*Discover + fetch + ingest-staged* (ticket-168; writes `sources` + `chunks`, no claims):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_INGEST = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_ingest_validation.py -m live_network -q
```

*Discover + fetch + ingest-staged + mock extract* (ticket-172; writes `claims` via fixture):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_extract_mock_spine.py -m live_network -q
```

**Live staged extract (live Ollama; ticket-204):** per-step rank-1 proof after live
OpenAlex ingest — uses `extract-claims --live-staged-fallthrough` (bypasses staged-fetch
auto-mock). Requires local Ollama; **not** the staged orchestrator path (orchestrator
still forces `RGE_LLM_MODE=mock`). Temp `--db` only — refuses default graph DB. Markers:
`live_network` **and** `live_smoke` (both excluded from default pytest).

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_extract_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after manual discover → fetch → ingest-staged on a temp DB (requires all
env gates above plus reachable Ollama):

```powershell
python -m rge.cli extract-claims --source <source_id> `
  --db <temp.sqlite> --live-staged-fallthrough
```

**Live staged rank-2 extract (live Ollama; ticket-230):** per-step rank-2 proof after live
OpenAlex discover (≥2 candidates) → fetch rank-2 → ingest-staged — uses
`extract-claims --live-staged-rank2-extract-fallthrough` (separate env gate from rank-1).
Requires `RGE_ALLOW_LIVE_STAGED_RANK2=1` plus rank-2 live extract gate. Temp `--db` only.
Markers: `live_network` **and** `live_smoke`.

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_rank2_extract_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after discover → fetch rank-2 → ingest-staged on a temp DB:

```powershell
python -m rge.cli extract-claims --source <source_id> `
  --db <temp.sqlite> --live-staged-rank2-extract-fallthrough
```

*Discover + fetch + ingest-staged + mock extract + mock link* (ticket-175; writes `claim_concepts` via fixture):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_LINK = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_link_mock_spine.py -m live_network -q
```

**Live staged link (live Ollama; ticket-208):** per-step rank-1 proof after live
OpenAlex ingest and **mock-fixture extract** — uses `link-concepts --live-staged-link-fallthrough`
(bypasses staged-fetch auto-mock). Requires local Ollama; orchestrator still forces mock LLM.
Temp `--db` only — refuses default graph DB. Markers: `live_network` **and** `live_smoke`.

```powershell
$env:RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_link_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after discover → fetch → ingest-staged → mock extract on a temp DB:

```powershell
python -m rge.cli link-concepts --source <source_id> `
  --db <temp.sqlite> --live-staged-link-fallthrough
```

**Live staged rank-2 link (live Ollama; ticket-236):** per-step rank-2 proof after live
discover (≥2 candidates) → fetch rank-2 → ingest → **mock extract**
(`staged_fetch_second_candidate_extract_claims.json`) — uses
`link-concepts --live-staged-rank2-link-fallthrough`. Requires `RGE_ALLOW_LIVE_STAGED_RANK2=1`.
Temp `--db` only. Markers: `live_network` **and** `live_smoke`.

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_rank2_link_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after discover → fetch rank-2 → ingest → mock extract on a temp DB:

```powershell
python -m rge.cli link-concepts --source <source_id> `
  --db <temp.sqlite> --live-staged-rank2-link-fallthrough
```

**Live staged rank-2 build (live Ollama; ticket-237):** per-step rank-2 proof after live
discover (≥2 candidates) → fetch rank-2 → ingest → **mock extract** + **mock link**
(`staged_fetch_second_candidate_extract_claims.json`,
`staged_fetch_second_candidate_link_concepts.json`) — uses
`build-relationships --live-staged-rank2-build-fallthrough`. Requires `RGE_ALLOW_LIVE_STAGED_RANK2=1`.
Temp `--db` only. Markers: `live_network` **and** `live_smoke`.

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_rank2_build_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after discover → fetch rank-2 → ingest → mock extract + mock link on a temp DB:

```powershell
python -m rge.cli build-relationships --source <source_id> `
  --db <temp.sqlite> --live-staged-rank2-build-fallthrough
```

**Live staged rank-2 detect (live Ollama; ticket-238):** per-step rank-2 proof after
`seed_domain_opposing_context` on temp DB, then live discover (≥2 candidates) → fetch rank-2
→ ingest → **mock extract** + **mock link** + **mock build** — uses
`detect-contradictions --live-staged-rank2-detect-fallthrough`. Requires
`RGE_ALLOW_LIVE_STAGED_RANK2=1`. Temp `--db` only. Markers: `live_network` **and** `live_smoke`.
Completes rank-2 per-step live Ollama surface (extract/link/build/detect).

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_rank2_detect_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after domain seed → discover → fetch rank-2 → ingest → mock upstream on temp DB:

```powershell
python -m rge.cli detect-contradictions --source <source_id> `
  --db <temp.sqlite> --live-staged-rank2-detect-fallthrough
```

**One-time rank-2 per-step live Ollama verification (operator checklist; ticket-240):**
after rank-2 live surface closure (tickets 230/236/237/238), use this checklist to
validate a fresh operator environment with local Ollama. **Not CI-enforced:** default
`pytest` and GitHub Golden Gate exclude `live_network` and `live_smoke`; operator opt-in only.

**Closure (post ticket-238):** rank-2 per-step live Ollama is **complete** at detect
(extract → link → build → detect). No further `RGE_ALLOW_LIVE_STAGED_RANK2_*_LIVE_LLM`
fallthrough flags are planned. **`reconcile-scores`** and **`generate-run-report`** on
both ranks remain **deterministic Python** — no live LLM path (pre-ticket audits 221/222).
The staged orchestrator still **forces** `RGE_LLM_MODE=mock`.

**Shared prerequisites (all rank-2 live steps):**

| Prerequisite | Required value |
| --- | --- |
| `RGE_ALLOW_LIVE_STAGED_RANK2` | `1` |
| `RGE_ALLOW_LIVE_LLM` | `1` |
| `RGE_LLM_MODE` | `ollama` |
| `RGE_ALLOW_SOURCE_NETWORK` | `1` |
| `OPENALEX_MAILTO` | valid contact email (OpenAlex polite pool) |
| `--db` | temp path only (pytest `tmp_path` or explicit gitignored evidence DB — never default graph DB) |
| Ollama | `python -m rge.cli model-health` should pass before live steps |

**Per-step rank-2 live gates and proofs:**

| Step | Live Ollama gate | CLI fallthrough | Pytest module | Mock upstream |
| --- | --- | --- | --- | --- |
| extract | `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1` | `--live-staged-rank2-extract-fallthrough` | `test_live_staged_rank2_extract_live_llm_spine.py` | — (live ingest) |
| link | `RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM=1` | `--live-staged-rank2-link-fallthrough` | `test_live_staged_rank2_link_live_llm_spine.py` | mock extract |
| build | `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1` | `--live-staged-rank2-build-fallthrough` | `test_live_staged_rank2_build_live_llm_spine.py` | mock extract + link |
| detect | `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1` | `--live-staged-rank2-detect-fallthrough` | `test_live_staged_rank2_detect_live_llm_spine.py` | `seed_domain_opposing_context` + mock through build |

Run each pytest with `-m "live_network and live_smoke"`. Rank-2 live proofs require ≥2
queued candidates (`select_rank2_candidate_id`) and rank-2 title heuristic
(`constraint management` marker).

**Domain seed (detect step; ticket-243):** live detect pytest calls
`seed_domain_opposing_context()` before live OpenAlex discover. That helper **forces mock LLM**
for GT7 seed spine steps (extract → link → build) even when operator env has
`RGE_LLM_MODE=ollama` — only the detect fallthrough step uses live Ollama. Implementation:
`tests/unit/staged_domain_seed.py` (`_mock_llm_seed_env`). A detect failure at
`link-concepts` with zero accepted claims under live env was a **pre-243 seed bug**, not catalog
drift.

**Not in scope for this checklist:**

| Item | Why |
| --- | --- |
| Staged orchestrator live LLM | Orchestrator forces mock; see orchestrator checklist below |
| Live LLM on reconcile/report | Deterministic only — no `*_LIVE_LLM` gate exists |
| Rank-1 live fallthrough flags | Separate `RGE_ALLOW_LIVE_STAGED_*_LIVE_LLM` gates (204/208/212/217) |
| Combined rank-1 + rank-2 all-live chain | Per-step proofs only — one step live at a time |
| Default graph DB | Temp `--db` only |

**Catalog drift:** rank-2 live network tests may skip with `unsuitable_live_rank2_artifact`
when fetched rank-2 text lacks the `constraint management` marker — see proof-layer
runbook above (`unsuitable_live_artifact` table). This is **not** a detect-engine regression.

**Checklist:**

1. Set shared prerequisites from the table above.
2. Run extract proof: `python -m pytest tests/unit/test_live_staged_rank2_extract_live_llm_spine.py -m "live_network and live_smoke" -q`
3. Run link proof (mock extract upstream in test): `python -m pytest tests/unit/test_live_staged_rank2_link_live_llm_spine.py -m "live_network and live_smoke" -q`
4. Run build proof: `python -m pytest tests/unit/test_live_staged_rank2_build_live_llm_spine.py -m "live_network and live_smoke" -q`
5. Run detect proof (domain seed inside test): `python -m pytest tests/unit/test_live_staged_rank2_detect_live_llm_spine.py -m "live_network and live_smoke" -q`
6. Confirm each step reports **1 passed** (not skipped) when Ollama and network are healthy.
7. Confirm live detect payload includes `"live_staged_rank2_detect_fallthrough": true` and `qualification_count >= 1`.

For rank-1 per-step live Ollama proofs, see **Live staged extract/link/build/detect**
sections above. For orchestrator mock-LLM network proof, see **One-time live orchestrator
verification** below.

*Discover + fetch + ingest-staged + mock extract + mock link + mock build* (ticket-178; writes `relationships` via fixture):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_BUILD = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_build_mock_spine.py -m live_network -q
```

**Live staged build (live Ollama; ticket-212):** per-step rank-1 proof after live
OpenAlex ingest and **mock-fixture extract + mock link** — uses
`build-relationships --live-staged-build-fallthrough` (bypasses staged-fetch auto-mock).
Requires local Ollama; orchestrator still forces mock LLM. Temp `--db` only — refuses
default graph DB. Markers: `live_network` **and** `live_smoke`.

```powershell
$env:RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_build_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after discover → fetch → ingest-staged → mock extract → mock link on a temp DB:

```powershell
python -m rge.cli build-relationships --source <source_id> `
  --db <temp.sqlite> --live-staged-build-fallthrough
```

**Live staged detect (live Ollama; ticket-217):** per-step rank-1 proof after live
OpenAlex ingest and **mock-fixture extract + mock link + mock build** — uses
`detect-contradictions --live-staged-detect-fallthrough` (bypasses staged-fetch auto-mock).
Requires **domain opposing context** seeded on the temp DB before live discover (pytest
uses `seed_domain_opposing_context()` from `tests/unit/staged_domain_seed.py`; same
requirement as ticket-181 mock detect spine). Requires local Ollama; orchestrator still
forces mock LLM. Temp `--db` only — refuses default graph DB. Markers: `live_network`
**and** `live_smoke`. Separate env gate from mock detect (`RGE_ALLOW_LIVE_STAGED_DETECT`).

```powershell
$env:RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_detect_live_llm_spine.py -m "live_network and live_smoke" -q
```

CLI equivalent after discover → fetch → ingest-staged → mock extract → mock link → mock build on a temp DB (with domain seed applied first):

```powershell
python -m rge.cli detect-contradictions --source <source_id> `
  --db <temp.sqlite> --live-staged-detect-fallthrough
```

*Discover + fetch + ingest-staged + mock extract + mock link + mock build + mock detect* (ticket-181; writes `relationship_evidence` qualifications via fixture; seeds domain opposing context locally before live discover):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_DETECT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_detect_mock_spine.py -m live_network -q
```

**Staged reconcile and report (deterministic Python; tickets 184/187):** no live Ollama
path exists for these steps. `reconcile-scores` applies domain-pack score rules and writes
append-only `score_events`; `generate-run-report` aggregates DB metrics into `run_reports`
and optional `run_report_latest.json`. Pre-ticket audits 221/222 document **NO-GO** for
live LLM fallthrough. **`RGE_ALLOW_LIVE_STAGED_RECONCILE`** and
**`RGE_ALLOW_LIVE_STAGED_REPORT`** are **network spine gates** (live OpenAlex through mock
LLM upstream) — not per-step live Ollama gates like `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM`.

*Discover + fetch + ingest-staged + mock extract + mock link + mock build + mock detect + reconcile-scores* (ticket-184; writes `score_events` via deterministic Python; no Ollama; seeds domain opposing context locally before live discover):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
```

*Discover + fetch + ingest-staged + mock extract + mock link + mock build + mock detect + reconcile-scores + generate-run-report* (ticket-187; deterministic report from DB metrics; no Ollama; writes `run_reports` + temp `run_report_latest.json`; seeds domain opposing context locally before live discover):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_REPORT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_report_mock_spine.py -m live_network -q
```

*Discover + fetch + ingest-staged + mock extract + mock link + mock build + mock detect + reconcile-scores + generate-run-report (rank-2 candidate)* (ticket-190; live OpenAlex discover selects rank-2 via `OFFSET 1`, then second-candidate mock fixtures through report; seeds domain opposing context locally before live discover; temp DB/output only):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_rank2_report_mock_spine.py -m live_network -q
```

*Single-command orchestrated discover → dual-candidate report* (ticket-193; `research run --fixture-mode --staged-spine` on real OpenAlex with env-gated dynamic candidate selection; mock fixtures after live ingest; temp DB/output only):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q
```

*Live staged orchestrator → private atlas snapshot coherence* (ticket-285; same
`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` gate as ticket-193; runs staged spine on temp
`--db`, exports operator-private atlas JSON via `export-atlas-snapshot` **without**
`--fixture-mode`, then audits `atlas_snapshot_v0.1.0` coherence — non-empty
cards/nodes/edges/runs, `validate_atlas_snapshot`, private-field scan; mock LLM upstream
only):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```

**Skip semantics:** layer-3 preflight uses the same mock-spine marker phrases as other
combined proofs (`human-ai co-creativity`, `songwriting`). When live discover + fetch
succeed but no top-N artifact contains those phrases, pytest **skips** with
`reason: unsuitable_live_artifact` (see **Interpreting `unsuitable_live_artifact`**
above) — **not** an atlas export or contract regression. On **PASS**, inspect temp
atlas JSON for coherence fields (`cards`, `nodes`, `edges`, `runs`); no
`export-public` or public-site writes.

**Public preview boundary (tickets 285, 320–326, 328–329):** this live layer-3 proof
writes **operator-private temp atlas JSON only** (`export-atlas-snapshot` on pytest
`tmp_path`). It does **not** refresh committed `/atlas-preview` JSON,
`fixtures/atlas/atlas_snapshot_staged_spine_preview.json`, or `export-public`. For the
static **mock** staged-spine public preview, use **Research Atlas public preview fixture
refresh** below (`scripts/refresh_atlas_preview_from_staged_spine.py`; patched OpenAlex
fixtures on a temp DB — not live catalog).

**One-time live orchestrator verification (operator checklist; ticket-199; refreshed
ticket-226; post internal MVP launch ticket-388/389):** after
`researcher_product_proof_latest.json` reports `product_verdict: GO`, advance
live-research maturity with this checklist (live OpenAlex + mock LLM only; temp DB).
Mock product proof does **not** substitute for orchestrator network proof. Full operator
report: `agent_reports/2026-06-23_phase-3_ticket-389_live-staged-orchestrator-checklist-v0.md`.
After per-step **network** proofs or when validating a fresh operator environment, run the
orchestrator proof once on a **temp `--db` path** (pytest `tmp_path` — never the default
graph DB). **Not CI-enforced:** default `pytest` and GitHub Golden Gate exclude
`live_network`; this is operator opt-in only.

**LLM boundary (post ticket-223 closure):** this checklist validates **live OpenAlex +
mock LLM** only. The orchestrator (`execute_staged_fixture_mode_run`) **always forces**
`RGE_LLM_MODE=mock` regardless of operator `.env`. It does **not** exercise per-step live
Ollama fallthrough (extract/link/build/detect — tickets 204/208/212/217); those are
separate operator proofs with `RGE_ALLOW_LIVE_STAGED_*_LIVE_LLM=1`. **`reconcile-scores`**
and **`generate-run-report`** inside the orchestrator path are **deterministic Python**
(`score_reconciler.py`, `run_evaluator.py`) — not model-assisted steps and not part of
per-step live Ollama proofs (pre-ticket audits 221/222).

| Prerequisite | Required value |
| --- | --- |
| `RGE_LLM_MODE` | `mock` (orchestrator forces mock; no live LLM on this path) |
| `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR` | `1` |
| `RGE_ALLOW_SOURCE_NETWORK` | `1` |
| `OPENALEX_MAILTO` | valid contact email (OpenAlex polite pool) |
| Network | outbound HTTPS to OpenAlex (may time out in restricted builder sandboxes) |

**Not in scope for this checklist:**

| Item | Why |
| --- | --- |
| Per-step live Ollama (204/208/212/217; rank-1) | Separate `RGE_ALLOW_LIVE_STAGED_*_LIVE_LLM` gates and CLI fallthrough flags |
| Per-step live Ollama (230/236/237/238; rank-2) | Separate `RGE_ALLOW_LIVE_STAGED_RANK2_*_LIVE_LLM` gates — see **One-time rank-2 per-step live Ollama verification** |
| Live LLM on reconcile/report | Deterministic only — no `*_LIVE_LLM` gate exists |
| Default graph DB | Temp `--db` only (pytest `tmp_path`) |

**Checklist:**

1. Set env vars from the orchestrator block above (`RGE_LLM_MODE=mock` — do not enable live Ollama for this proof).
2. Run: `python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q`
3. Confirm **1 passed** (not skipped). Skips mean a missing env gate — see test module docstring.
4. Confirm stdout JSON includes `"status": "completed"`, `"mode": "fixture_staged"`, `rank1_candidate_id` / `rank2_candidate_id` (candidate wiring metadata on the final run document), and stable dual-spine counts: `sources` 3, `candidate_sources` 2, `research_queue` 2, `score_events` 2, `run_reports` 2, `qualifies_evidence` 2. The `score_events` and `run_reports` rows come from deterministic reconcile/report — not Ollama.
5. Confirm temp report artifact: `run_report_latest.json` under the test temp output dir (not committed).

**Orchestrator retry runbook (ticket-391):** when step 2–3 does not yield **1 passed** because
live OpenAlex returned catalogs without mock-spine marker phrases (`human-ai co-creativity`,
`songwriting`), see **Interpreting `unsuitable_live_artifact`** above and
`agent_reports/2026-06-23_phase-3_ticket-391_live-orchestrator-retry-runbook-v0.md` for
retry timing, topic tuning, and environmental NO-GO acceptance. This is **not** an engine
regression; layer-2 mock proof remains `tests/unit/test_staged_fixture_mode_run_spine.py`.

If the run times out, retry from a network-unrestricted machine; do **not** enable live network in CI. Patched-network regression remains `tests/unit/test_staged_fixture_mode_run_spine.py`. For per-step live Ollama proofs after mock ingest, see **Live staged extract/link/build/detect** (rank-1) and **One-time rank-2 per-step live Ollama verification** (rank-2) above.

**Manual source ingestion** (Level-1): place operator `.txt`/`.md` files under gitignored `data/sources/manual/<domain>/` (e.g. `data/sources/manual/creativity/`) and ingest with:

```powershell
python -m rge.cli ingest data/sources/manual/creativity/note.md --domain creativity --source-type manual_text --source-title "My source title"
```

Omit `--source-type` to keep golden-test back-compat (`fixture`). Ingest writes only to the private SQLite DB; it does not export.

**Manual synthnote operator spine** (mock LLM; tickets 088–099): after placing
`synthnote.txt` under gitignored `data/sources/manual/creativity/`, run the full
pipeline with **checksum-pinned mock fixtures** (no `--fixture` flags for `manual_text`
sources — candidate JSON is keyed by `raw_text_checksum`, not live inference).
A committed test copy lives at `fixtures/sources/manual_synthnote.txt`.

```powershell
$env:RGE_LLM_MODE = "mock"

# 1. Ingest — idempotent by checksum; source_type manual_text
python -m rge.cli ingest data/sources/manual/creativity/synthnote.txt `
  --domain creativity --source-type manual_text `
  --source-title "Synthetic Source Note: AI-Assisted Ideation and Semantic Diversity"
# Expected: status ingested; source id src_2c53bfdfdf3c6853 (checksum-prefixed)

# 2. Extract claims — 2 accepted, 1 rejected (missing_quote_span)
python -m rge.cli extract-claims --source src_2c53bfdfdf3c6853

# 3. Link concepts — 4 links; alias AI-assisted brainstorming → AI assistance
python -m rge.cli link-concepts --source src_2c53bfdf3c6853

# 4. Build relationships — 2 active edges (may_reduce semantic diversity; may_increase variation volume)
python -m rge.cli build-relationships --source src_2c53bfdfdf3c6853

# 5. Detect contradictions — 1 qualifies edge linking the two relationship directions
python -m rge.cli detect-contradictions --source src_2c53bfdfdf3c6853
```

**Manual synthnote score reconciliation** (after steps 1–5): ingest a follow-up
`manual_text` source with stronger supporting evidence, then reconcile scores.
Committed test copy: `fixtures/sources/manual_synthnote_followup.txt`; operator copy:
`data/sources/manual/creativity/synthnote_followup.txt`.

```powershell
# 6. Ingest follow-up — checksum map resolves extract fixture automatically
python -m rge.cli ingest data/sources/manual/creativity/synthnote_followup.txt `
  --domain creativity --source-type manual_text `
  --source-title "Synthetic Follow-Up Note: AI Assistance and Semantic Diversity Replication"
# Expected: source id src_c5d1add68657e7ec (checksum-prefixed)

# 7. Extract claims — 1 accepted claim (confidence 0.85)
python -m rge.cli extract-claims --source src_c5d1add68657e7ec

# 8. Reconcile scores — 1 score_events row; may_reduce edge 0.5 → 0.62
python -m rge.cli reconcile-scores --source src_c5d1add68657e7ec
```

Re-running any step is idempotent (stable row counts). Fixture filenames resolve from
`fixtures/manual_source_fixture_map.json` keyed by `raw_text_checksum` (mock candidates
only — not arbitrary-source live extraction). Use `--db <path>` to target a non-default
SQLite file. Golden fixture sources still pass explicit `--fixture` flags and are unchanged.

**Creativity domain pack runtime loading (NM-5; tickets 113–122):** `load_domain_pack("creativity")`
loads every YAML overlay under `domain_packs/creativity/`. Domain-specific validation,
scoring, and export rules come from these files — not hardcoded creativity fields in
core engine modules.

| Pack file | Loaded at runtime | Primary consumer |
| --- | --- | --- |
| `domain.yaml` | yes | pack identity; `claim_validator` domain allowlist |
| `ontology.yaml` | yes | concept linking (canonical labels) |
| `aliases.yaml` | yes | concept linking (phrase → canonical) |
| `scoring.yaml` | yes | score reconciliation / relationship scoring |
| `evidence_types.yaml` | yes | `claim_validator` evidence_type allowlist |
| `claim_schema.yaml` | yes | `concept_linker` `domain_metadata` allowlists |
| `source_preferences.yaml` | yes | research queue credibility priors |
| `card_templates.yaml` | yes | public export template field checks |
| `search_templates.yaml` | yes | research planner follow-up query scoring |
| `safety_notes.yaml` | yes | full safety audit domain guidance themes |

**Overlap-domain claim labels:** candidate claims may use `domain` values declared in
`domain.yaml` as `primary_domains` or `overlap_domains`. For creativity that includes
`creativity`, `art`, `design`, `film`, `music`, and `digital_media`. During
`extract-claims`, the pipeline passes `source.domain` (the pack id, e.g. `creativity`)
into validation; `claim_validator` rejects candidate `domain` labels outside
`allowed_domains_for_pack()`. Out-of-scope labels fail with `unsupported_claim`.
Golden mock proof: `tests/golden/test_02_claim_extraction_overlap_domain.py` and fixture
`fixtures/llm_outputs/claim_extraction_overlap_domain_art.json`.

**Live validated extraction write** (NM-1; local Ollama; operator opt-in): prove real
inference on a source **not** in the checksum fixture map. Writes only to an explicit
gitignored evidence DB — never the default graph DB or public export.

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health

# Place a new .txt/.md under data/sources/manual/creativity/ (not synthnote checksums)
python -m rge.cli ingest data/sources/manual/creativity/your_new_note.txt `
  --domain creativity --source-type manual_text --source-title "Your note" `
  --db data/db/live_research_evidence.sqlite

python -m rge.cli extract-claims-live --source <source_id_from_ingest> `
  --db data/db/live_research_evidence.sqlite
```

**NM-4 evidence DB operator spine** (tickets 127–132; arbitrary `manual_text` on
gitignored `data/db/live_research_evidence.sqlite`): extends NM-1 with live
fall-through on the standard pipeline commands (not checksum-pinned synthnote fixtures).
Requires `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, and `--db
data/db/live_research_evidence.sqlite` on every step. Mock mode without the
`--live-manual-*` flags remains fail-closed for sources absent from
`fixtures/manual_source_fixture_map.json`.

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health

# 1. Ingest arbitrary manual_text (not in checksum fixture map)
python -m rge.cli ingest data/sources/manual/creativity/your_new_note.txt `
  --domain creativity --source-type manual_text --source-title "Your note" `
  --db data/db/live_research_evidence.sqlite
# Example proof source: fixtures/sources/ticket127_arbitrary_manual_live.txt
# Expected example id: src_1b8354e5f2203f82 (checksum-prefixed)

# 2. Extract claims — live Ollama fall-through
python -m rge.cli extract-claims --source <source_id> `
  --db data/db/live_research_evidence.sqlite --live-manual-fallthrough

# 3. Link concepts — live fall-through
python -m rge.cli link-concepts --source <source_id> `
  --db data/db/live_research_evidence.sqlite --live-manual-link-fallthrough

# 4. Build relationships — live fall-through
python -m rge.cli build-relationships --source <source_id> `
  --db data/db/live_research_evidence.sqlite --live-manual-relationship-fallthrough

# 5. Detect contradictions — live fall-through
python -m rge.cli detect-contradictions --source <source_id> `
  --db data/db/live_research_evidence.sqlite --live-manual-contradiction-fallthrough
```

**NM-4 evidence DB score reconciliation** (ticket-131; deterministic — no Ollama):
after the live spine above, ingest a follow-up `manual_text` source with stronger
supporting evidence, extract claims (mock fixture map or live per source), then
reconcile on the evidence DB only via `--evidence-db-reconcile` (blocks default
graph DB). Committed test copy:
`fixtures/sources/ticket131_nm4_evidence_followup.txt`.

```powershell
$env:RGE_LLM_MODE = "mock"

# 6. Ingest follow-up on evidence DB
python -m rge.cli ingest fixtures/sources/ticket131_nm4_evidence_followup.txt `
  --domain creativity --source-type manual_text `
  --source-title "Ticket-131 NM-4 evidence follow-up" `
  --db data/db/live_research_evidence.sqlite
# Expected example id: src_044a97ae8419e35a

# 7. Extract claims — mock fixture map (checksum-pinned candidate JSON)
python -m rge.cli extract-claims --source src_044a97ae8419e35a `
  --db data/db/live_research_evidence.sqlite

# 8. Reconcile scores — 1 score_events row; example edge 0.5 → 0.62
python -m rge.cli reconcile-scores --source src_044a97ae8419e35a `
  --db data/db/live_research_evidence.sqlite --evidence-db-reconcile
```

**NM-4 evidence DB plan visibility** (ticket-132): read-only spine status in operator
loop plan mode — no writes.

```powershell
python -m rge.modules.operator_loop --mode plan
```

Inspect `nm4_evidence_spine_status` in the JSON output: `evidence_db_path`,
`spine_stage` (`missing` | `empty` | `partial` | `reconciled`), table counts
(sources, accepted claims, active relationships, `score_event_count`), and
`spine_milestones`. When the local evidence DB has completed steps 1–8,
expect `spine_stage: reconciled` and `score_event_count: 1`.

**Evidence DB atlas population closure** (tickets 294–298; **operator-private only**): when
`export-atlas-snapshot` runs on a **non-fixture** evidence DB with accepted claims from
`manual_text` sources outside the checksum fixture map,
`rge/modules/evidence_db_atlas.py` hooks populate atlas sections before snapshot write:

| Atlas section | Hook (ticket) | Trigger |
| --- | --- | --- |
| `runs[]` + question lineage | `ensure_evidence_research_run_lineage` (294) | `--topic` on non-fixture export |
| `cards[]` (claim-backed) | `ensure_claim_backed_public_cards` (294) | non-fixture export; replaces golden placeholders when live claims exist |
| `reports[]` | `ensure_evidence_run_report` (295) | non-fixture export + non-fixture manual claims |
| `clusters[]` | `ensure_evidence_cluster_summary` (296) | same gate as reports |
| `edges[]` | `ensure_evidence_relationship_edges` (297) | same gate; seeds from claim–concept links |
| `follow_up_questions[]` | research_queue projection (284; lineage from 294) | populated when contract/queue rows exist |

**Public boundary (ticket-313):** non-fixture evidence DB atlas exports write to
operator-private paths under gitignored `data/` (for example `data/atlas/ticket293/…`).
They **do not** publish to the public site, `export-public`, or `/atlas-preview`. The
static public preview at `/atlas-preview` (ticket-300) reads committed fixture JSON only;
refresh via **Research Atlas public preview fixture refresh** below (fixture-mode
`export-atlas-snapshot` + `--coherence-preview-out`; tickets 300/308/312). There is no
live evidence-DB → public-site atlas pipeline in this phase.

Fixture-mode golden MVP paths (`export-atlas-snapshot --fixture-mode`) are unchanged.
Default graph DB synthnote export remains checksum-mock — not arbitrary live inference.

**Mock spine proof** (network-free; default `pytest`):

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_evidence_db_atlas_projection.py -q
python -m pytest tests/unit/test_evidence_db_run_report_projection.py -q
python -m pytest tests/unit/test_evidence_db_cluster_projection.py -q
python -m pytest tests/unit/test_evidence_db_relationship_projection.py -q
```

Expect `overall_coherence_verdict: pass` on the mock evidence spine after ticket-297
hooks. Regression layer remains `tests/unit/test_atlas_coherence_cli_pipeline_fixture.py`
(ticket-292 fixture-mode CLI chain).

**Operator re-export proof** (ticket-298; gitignored DB only; not CI): after live NM-1 +
NM-4 link/build on `data/db/ticket293_live_nm1_quality_proof.sqlite`, re-export upgraded
overall coherence **fail → pass** once 294–297 hooks ran. Full before/after table:
`agent_reports/2026-06-16_phase-3_ticket-298_operator-evidence-db-coherence-reexport.md`.

```powershell
$env:RGE_LLM_MODE = "mock"
$DB = "data/db/ticket293_live_nm1_quality_proof.sqlite"
$TOPIC = "Does AI-assisted songwriting reduce creative diversity in workshop drafts?"

python -m rge.cli export-atlas-snapshot --db $DB `
  --out data/atlas/ticket293/atlas_snapshot_v298.json `
  --topic $TOPIC --domain creativity

python -m rge.cli atlas-coherence-report `
  --snapshot data/atlas/ticket293/atlas_snapshot_v298.json `
  --out-json data/atlas/ticket293/atlas_coherence_report_v298.json `
  --out-md data/atlas/ticket293/atlas_coherence_report_v298.md
```

**Research Atlas public preview fixture refresh** (tickets 300, 308, 312, 320–325; see
**Public boundary** under Evidence DB atlas above): the static `/atlas-preview` page reads
committed JSON only — `atlas_snapshot_preview.json` and `atlas_coherence_preview.json`
under `apps/public-site/public/data/`. The **primary** refresh path is the mock
**staged-spine** operator script (ticket-320; temp DB only; no `export-public` changes):

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/refresh_atlas_preview_from_staged_spine.py
```

The script runs `research run --fixture-mode --staged-spine` on a temp SQLite DB (patched
OpenAlex fixtures), exports via `atlas_preview_curator` (maps `active` follow-ups to
`queued` for UI), writes both preview JSON files under `apps/public-site/public/data/`,
and **auto-syncs** the offline reference
`fixtures/atlas/atlas_snapshot_staged_spine_preview.json` (tickets 322, 325). By
default it also syncs `atlas_source_health_run_latest.json` from the staged temp DB
(`export_staged_spine_source_health_artifact`; disable with
`RGE_SYNC_STAGED_SOURCE_HEALTH=0`). Page copy labels the result as a mock
staged-spine preview (ticket-321). Regression:
`tests/unit/test_public_atlas_preview_fixture.py` (committed preview + fixture parity),
`tests/unit/test_staged_spine_source_health_sync.py` (source-health bridge).

**Atlas source-health preview refresh** (local-safe proof → public `/atlas-preview` source
health + gaps panels; temp DB only):

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/refresh_atlas_source_health_preview.py
```

The script runs the local-safe arbitrary source-health proof on a temp SQLite DB,
validates `atlas_source_health_run_v0.1.0` plus private-field policy, and writes
`apps/public-site/public/data/atlas_source_health_run_latest.json`. `/atlas-preview`
prefers this artifact for the **Source health** and **Gaps / next move** panels when
present; otherwise it falls back to `tiny_atlas_connection_preview.json`.

Copy an operator-generated artifact instead of regenerating:

```powershell
python scripts/refresh_atlas_source_health_preview.py `
  --input path/to/atlas_source_health_run_latest.json
```

Regression: `tests/unit/test_atlas_source_health_run_preview.py`,
`tests/unit/test_refresh_atlas_source_health_preview.py`.

**Operator loop atlas preview refresh hook** (plan mode only; no writes): when
`python -m rge.modules.operator_loop --mode plan` runs, inspect
`atlas_preview_refresh_status` for missing or stale public preview JSON and
`next_recommended_action.action_id == refresh_atlas_public_previews` when no open
ticket blocks refresh. When staged snapshot/coherence or synced source-health JSON
is stale, plan mode prefers the **single** staged refresh command
(`python scripts/refresh_atlas_preview_from_staged_spine.py`, which syncs all three
preview files by default) plus `cd apps/public-site && npm run build`. Set
`RGE_SYNC_STAGED_SOURCE_HEALTH=0` to fall back to separate source-health refresh.
Regression: `tests/unit/test_operator_loop_plan.py`.

**Operator loop combined live smoke hint** (plan mode only): when source-health
preview work is detected (`atlas_source_health_run_latest.json` committed or a
recent source-health/atlas agent report) but combined live smoke gates are unset,
plan mode surfaces `live_combined_source_health_smoke_status` and may recommend
`run_live_combined_source_health_smoke` with env setup commands. Regression:
`tests/unit/test_operator_loop_plan.py`.

**Live network query-expansion smoke** (operator opt-in; temp resolver only; no PDF
download; mock LLM):

```powershell
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_query_expansion_smoke.py -m live_network -q
```

Proves purpose-aware alternate OpenAlex/arXiv queries run when metadata-only records
dominate the first resolver pass. Not CI-enforced (`live_network` marker excluded in
default `pytest`).

**Live network combined source-health + query-expansion smoke** (operator opt-in; temp
DB + resolver; mock LLM):

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_combined_source_health_smoke.py -m live_network -q
```

Chains full-question `resolve_work_candidates` query expansion with the live
source-health persistence + Atlas-safe artifact writer. Requires **both**
`RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE=1` and `RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE=1`.
Not CI-enforced.

**Live staged spine source-health coherence** (mock staged orchestrator in default
pytest; opt-in live_network layer):

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_spine_source_health_coherence.py -q

# Opt-in live layer (same gates as live staged atlas coherence):
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_spine_source_health_coherence.py -m live_network -q
```

Asserts staged temp DB `source_health_preview` counts match
`export_staged_spine_source_health_artifact` output (schema, purpose, readiness
warnings, private-field policy).

**Live layer-3 boundary (tickets 285, 328–329):** the opt-in live OpenAlex +
`live_network` atlas coherence pytest
(`tests/unit/test_live_staged_atlas_snapshot_coherence.py`; see *Live staged orchestrator
→ private atlas snapshot coherence* in Operator Quickstart above) validates **private**
temp exports only — it **never** writes the committed public preview or `fixtures/atlas/`
paths listed here. Live catalog skips (`unsuitable_live_artifact`) are **not** public
preview regressions.

Verify before commit:

```powershell
python -m rge.modules.safety_auditor --audit full
cd apps/public-site; npm run build; cd ../..
python -m pytest tests/golden/test_12_public_site_static_render.py -q
python -m pytest tests/unit/test_public_atlas_preview_fixture.py -q
python -m pytest tests/unit/test_atlas_source_health_run_preview.py -q
```

Stage the refreshed snapshots for commit:

```powershell
git add apps/public-site/public/data/atlas_snapshot_preview.json `
  apps/public-site/public/data/atlas_coherence_preview.json `
  apps/public-site/public/data/atlas_source_health_run_latest.json `
  fixtures/atlas/atlas_snapshot_staged_spine_preview.json
```

If `git status` does not list those paths (local ignore rules), use `git add -f` on the
same files — ticket-300 used force-add when bootstrapping preview JSON.

**Legacy fixture-mode MVP refresh** (ticket-312; golden single-run shape — superseded for
public preview by staged-spine path above):

```powershell
$env:RGE_LLM_MODE = "mock"
$TOPIC = "Does AI improve creative output while reducing diversity?"
$DB = "data/db/atlas_preview_refresh.sqlite"
$STAGING = "data/atlas/preview_refresh"

# 1) Build fixture-mode MVP DB (gitignored under data/)
python -m rge.cli run --topic $TOPIC --domain creativity --fixture-mode --db $DB

# 2) Export snapshot + coherence preview sidecar (ticket-308 --coherence-preview-out)
New-Item -ItemType Directory -Force -Path $STAGING | Out-Null
python -m rge.cli export-atlas-snapshot `
  --db $DB `
  --out "$STAGING/atlas_snapshot.json" `
  --coherence-preview-out "$STAGING/atlas_coherence_preview.json" `
  --topic $TOPIC `
  --domain creativity `
  --fixture-mode

# 3) Copy into committed public-site preview paths
Copy-Item "$STAGING/atlas_snapshot.json" `
  "apps/public-site/public/data/atlas_snapshot_preview.json" -Force
Copy-Item "$STAGING/atlas_coherence_preview.json" `
  "apps/public-site/public/data/atlas_coherence_preview.json" -Force
```

Regression layer for fixture-mode chain:
`tests/unit/test_atlas_coherence_cli_pipeline_fixture.py` and
`tests/unit/test_atlas_coherence_preview_sync.py` (coherence preview sidecar).
Golden MVP contract fixture remains at
`fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`.

**Autonomous researcher loop operator visibility** (tickets 332–357; mock LLM only):
fixture-mode `autonomous-researcher-loop` proofs write to gitignored scratch paths only —
no queue writes, no `export-public`, no ticket promotion.

| Path | Git | Role |
| --- | --- | --- |
| `data/db/operator_autonomous_loop_scratch.sqlite` | gitignored | Scratch DB for operator loop proofs |
| `data/reports/operator_autonomous_loop/` | gitignored | Loop artifacts; inspect `autonomous_loop_report.json` |
| `data/reports/operator_autonomous_loop/tickets/improvement_ticket_latest.json` | gitignored | Draft improvement tickets from loop quality eval (ticket-333) |
| `data/reports/operator_autonomous_loop/recommended_improvement_ticket.json` | gitignored | Queue-style recommended ticket id/title from loop (not promoted) |
| `data/sources/staged/operator_autonomous_loop/` | gitignored | Staged sources for operator loop proofs |

When the implementation queue has no open tickets, operator plan mode recommends
`run_autonomous_researcher_loop` (`safe_autonomous`). Execute-safe runs the fixture
proof on the scratch DB when the working tree is clean.

```powershell
$env:RGE_LLM_MODE = "mock"

# Plan — read-only JSON (includes scratch status + recommended action)
python -m rge.modules.operator_loop --mode plan

# Execute-safe — mock verification + fixture autonomous loop proof when eligible
python -m rge.modules.operator_loop --mode execute-safe

# Autocycle plan — bounded audit + run-next-ticket safety (never merges or implements)
python -m rge.modules.operator_autocycle --mode plan --max-cycles 1
```

**`autonomous_loop_scratch_status`** (operator plan and autocycle JSON): read-only
inspection of the last `autonomous_loop_report.json` on the scratch path.

| Field | When present |
| --- | --- |
| `status` | `ok` when report exists and run completed; `not_run` when missing; `invalid` / `incomplete` otherwise |
| `research_quality_verdict` | From `research_quality.research_quality_verdict` (e.g. `GO`, `PARTIAL`) |
| `weakest_dimension` | Weakest quality dimension id from the loop eval |
| `weakest_dimension_score` | Score for weakest dimension (0–100) when present |
| `loop_report_path` | Relative path to the inspected report |

When `status` is `ok`, `next_recommended_action.reason` also appends the last scratch
quality verdict and weakest dimension (ticket-341). Operator autocycle plan/summary
JSON passes through the same `autonomous_loop_scratch_status` object (ticket-342).

**Execute-safe post-run refresh** (ticket-343): after a **successful** execute-safe run
when the recommended action is `run_autonomous_researcher_loop`, the execute-safe payload
re-reads `autonomous_loop_report.json` so `autonomous_loop_scratch_status` reflects the
proof just written. Failed or blocked execute-safe runs leave the pre-run inspection
unchanged.

**Execute-safe post-run reason refresh** (ticket-356): after a **successful** execute-safe
run when the recommended action is `run_autonomous_researcher_loop`, the execute-safe
payload also rebuilds `next_recommended_action.reason` from the post-proof scratch and
improvement summaries (tickets 341/354). Failed or blocked execute-safe runs leave the
pre-run reason unchanged.

**`autonomous_loop_improvement_status`** (operator plan and autocycle JSON; tickets
348–357): read-only inspection of improvement artifacts referenced from the scratch
`autonomous_loop_report.json` (`artifacts.improvement_tickets` and
`artifacts.recommended_improvement_ticket`). Paths resolve under the scratch artifact dir
— typically `data/reports/operator_autonomous_loop/tickets/` and
`data/reports/operator_autonomous_loop/recommended_improvement_ticket.json`.

| Field | When present |
| --- | --- |
| `status` | `ok` when referenced artifacts exist; `not_run` when loop report missing; `invalid` / `incomplete` otherwise |
| `recommended_ticket_id` | Id from `recommended_improvement_ticket.json` or loop report |
| `recommended_ticket_title` | Title from recommended ticket artifact |
| `recommended_ticket_status` | Status from recommended ticket (e.g. `proposed`, `draft`) |
| `source_weakness` | Quality weakness that drove the recommendation (e.g. `weak_concept_mapping`) |
| `quality_driven_ticket_ids` | Ids from loop `run_summary.quality_driven_ticket_ids` |
| `draft_count` / `draft_tickets` | Pending draft improvement tickets from `improvement_ticket_latest.json` |
| `improvement_tickets_path` / `recommended_improvement_ticket_path` | Relative paths inspected |
| `loop_report_path` | Relative path to the inspected loop report |

Operator autocycle plan/summary JSON passes through the same
`autonomous_loop_improvement_status` object (ticket-349). Autocycle summary also
surfaces `recommended_ticket_id` and `draft_count` at the top level when present.

When `status` is `ok`, `next_recommended_action.reason` also appends the recommended
improvement ticket id and `source_weakness` (or `draft_count` when weakness is absent;
ticket-354). When improvement status is `not_run`, the reason remains the scratch-only
baseline — scratch quality append from ticket-341 still applies when scratch `status` is
`ok`.

**Execute-safe post-run improvement refresh** (ticket-350): after a **successful**
execute-safe run when the recommended action is `run_autonomous_researcher_loop`,
`execute_safe_checks` re-inspects improvement artifacts alongside scratch refresh so
`autonomous_loop_improvement_status` reflects the proof just written. Failed or blocked
execute-safe runs leave the pre-run inspection unchanged.

**Autocycle execute-safe improvement sync** (ticket-351): after a **successful**
operator autocycle execute-safe run, `evaluation.autonomous_loop_improvement_status`
and the autocycle summary sync from the refreshed `execution` payload (same pattern as
scratch sync in ticket-346). Failed autocycle execute-safe leaves pre-run improvement
status unchanged.

**Autocycle execute-safe reason sync** (ticket-357): after a **successful** operator
autocycle execute-safe run, `evaluation.recommended_action.reason` and the top-level
summary `recommended_action` sync from the refreshed `execution.next_recommended_action`
payload (same pattern as improvement sync in ticket-351). Failed autocycle execute-safe
leaves the pre-run reason unchanged.

**Tier 2 patch staging operator spine** (local implementation autonomy; mock-safe default):
staged diff airlock under `data/operator/tier2_patch_staging/` (gitignored). Plan mode
surfaces backfill → validate → preview refresh → apply in priority order. Atlas operator
panels: `/atlas-preview` synthesis/draft governor row and Tier 2 patch staging panel.

| Step | Command / gate | Execute-safe hook |
| --- | --- | --- |
| Backfill draft `expected_files` | `python scripts/run_draft_expected_files_backfill.py --latest` | `RGE_EXECUTE_SAFE_DRAFT_BACKFILL=1` when backfill is the only plan blocker |
| Stage patch bundle | `python scripts/run_tier2_patch_staging.py --latest` | `RGE_EXECUTE_SAFE_PATCH_STAGING=1` on clean or controlled-dirty tree |
| Validate staged bundle | `python scripts/run_tier2_patch_staging.py --bundle PATH --validate` | Chained after backfill when tree becomes controlled-dirty (both hooks enabled) |
| Refresh Atlas preview | `python scripts/refresh_tier2_patch_staging_preview.py --latest --sync-public` | Auto via `RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW=1` (default on) after validate/stage |
| Apply staged patch (Tier 2 runner) | `python scripts/run_tier2_local_implementation.py --apply-staged` | Manual — not execute-safe |

**Execute-safe Tier 2 hook chain:** when `RGE_EXECUTE_SAFE_DRAFT_BACKFILL=1` and
`RGE_EXECUTE_SAFE_PATCH_STAGING=1`, a successful backfill that leaves a controlled-dirty
tree (typically `data/operator/draft_tickets/` writes) chains patch validate + Atlas
preview refresh in the same execute-safe pass. Payload keys: `execute_safe_tier2_hook_chain`,
`chained_patch_staging`, `tree_became_controlled_dirty`, `post_tier2_hook_replan`.

**Autocycle Tier 2 multi-cycle replan:** after a chained hook completes, autocycle
re-plans (when `max_cycles > 1`) to pick up the next Tier 2 `safe_autonomous` action
(e.g. validate → preview refresh → apply) without manual plan refresh.

Related env (see `.env.example`): `RGE_REVALIDATE_PATCH_AFTER_BACKFILL=1` (default on),
`RGE_REQUIRE_TIER2_PATCH_STAGING=0`, `RGE_TIER2_PATCH_MAX_FILES=20`,
`RGE_TIER2_PATCH_MAX_LINES=2000`.

Manual operator commands (not run by execute-safe allowlist):

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli autonomous-researcher-loop `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/operator_autonomous_loop_scratch.sqlite `
  --artifact-dir data/reports/operator_autonomous_loop `
  --staging-dir data/sources/staged/operator_autonomous_loop

# Staged-spine mock loop (network env required; operator manual)
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m rge.cli autonomous-researcher-loop --staged-spine `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/operator_autonomous_loop_scratch.sqlite `
  --artifact-dir data/reports/operator_autonomous_loop `
  --staging-dir data/sources/staged/operator_autonomous_loop
```

**One-button research run v1** (mock default; scratch paths; no auto-merge/publish):

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli run `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db data/db/scratch_research.sqlite `
  --artifact-dir data/reports/scratch_research `
  --export-atlas `
  --quality-report data/reports/scratch_research/research_quality.json
```

Optional flags (all fail closed unless env gates are set): `--live-network`,
`--live-llm-extract`, `--sync-atlas-public`, `--skip-site-build`, `--source-limit N`.

**Local scheduled research loop** (`local_mock_daily` profile — mock only; blocks live
network/LLM/paid APIs; no merge/push/promote/public publish):

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_scheduled_research_loop.py --profile local_mock_daily
# or: .\scripts\run_scheduled_research_loop.ps1
```

Windows Task Scheduler example (daily 06:00):

```powershell
schtasks /Create /TN "RGE Local Mock Daily" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\path\to\rage\scripts\run_scheduled_research_loop.ps1" /SC DAILY /ST 06:00
```

Writes timestamped reports under `agent_reports/` and compact status JSON under
`data/reports/scheduled_research/`.

**Live probe scratch evidence workflow** (local Ollama opt-in; report-only until
operator persist): use the numbered checklist in
[`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md`](docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md)
(**Scratch evidence workflow checklist**). Summary: `probe-mini-run` or
`probe-mini-run-suite` → `probe-persist-reviewed-report --confirm-review` →
`probe-scratch-summary` → `probe-scratch-evidence-review` →
`python -m rge.modules.operator_loop --mode plan`.

## Verification Commands

| Command | Purpose |
|---|---|
| `python -m rge.cli verify` | **Preferred:** mock-only golden + pytest + safety audit + site build |
| `python -m rge.cli verify --skip-site` | Mock-only golden + pytest + safety (no npm) |
| `python -m rge.cli prove-researcher-product ...` | Internal MVP product proof → gitignored GO artifact |
| `python -m pytest tests/golden` | Builder merge gate (mock LLM) |
| `python -m pytest` | Full test suite |
| `python -m rge.modules.safety_auditor --audit full` | Deterministic safety audit |
| `python -m rge.cli run --fixture-mode ...` | End-to-end fixture MVP |
| `python -m rge.cli run --staged-spine ...` | Phase 3 staged discover→report (mock LLM; network env required) |
| `python -m rge.cli run --fixture-mode --staged-spine ...` | Same staged spine (legacy alias) |
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
| `data/reports/operator_autonomous_loop/` | gitignored | Operator autonomous loop scratch report (`autonomous_loop_report.json`) and improvement drafts under `tickets/` |
| `data/reports/operator_proof_bundle/` | gitignored | Mock arbitrary-source proof bundle (`operator_proof_bundle.json`, run reports) |
| `data/reports/synthesis_packet_benchmark_latest.json` | gitignored | Mock synthesis packet throughput + review-threshold benchmark summary |
| `data/reports/researcher_product_proof_latest.json` | gitignored | Mock end-to-end researcher product proof (`product_verdict`, graph counts, synthesis/benchmark summary) |
| `data/tmp/researcher_product_proof_work/` | gitignored | Scratch work dir for `prove-researcher-product` (SQLite, staged sources, synthesis output) |
| `data/db/operator_proof_bundle_scratch.sqlite` | gitignored | Scratch DB for operator proof bundle |
| `data/sources/staged/operator_proof_bundle/` | gitignored | Staged OpenAlex fixture sources for proof bundle |
| `data/exports/operator_proof_bundle/` | gitignored | Proof-bundle public-card export scratch copy |
| `data/db/operator_autonomous_loop_scratch.sqlite` | gitignored | Scratch DB for operator autonomous loop proofs |
| `data/sources/staged/operator_autonomous_loop/` | gitignored | Staged sources for operator autonomous loop proofs |
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
| Cloud providers | **Mock-first** (`mock_cloud` default on `research synthesize --packet`; ticket-059). Live OpenAI opt-in only behind explicit env gates — not CI/default pytest. |

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

The public site (`apps/public-site/`) is a **read-only** Next.js surface:

- Renders committed JSON from `apps/public-site/public/data/` only (static imports at build/dev time)
- No write routes, no source ingestion, no agent execution
- Never connects to the private local engine, SQLite, or `python -m rge.cli` at runtime
- Does not require port **8000** or any backend API server
- Does not read `NEXT_PUBLIC_*` secrets for engine access

**Internal MVP browse:** `npm run dev` → http://localhost:3000/atlas-preview  
**Static production preview:** `npm run build` then `npm run preview:static` (serves `out/` on port 3000)

Primary Atlas preview files:

| File | Role |
|------|------|
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Graph snapshot (`snapshot_id`, clusters, cards, runs) |
| `apps/public-site/public/data/atlas_coherence_preview.json` | Coherence verdict for preview header |

After changing accepted claims or export policy, run `export-public`, pass the safety audit, review the snapshot diff, then rebuild the site. After changing atlas preview contract fields, follow **Research Atlas public preview fixture refresh** in Operator Quickstart (primary: `scripts/refresh_atlas_preview_from_staged_spine.py` auto-syncs public preview + `fixtures/atlas/`; tickets 320–325; legacy fixture-mode path tickets 300/308/312). Browse `/atlas-preview` after `npm run build` or during `npm run dev`.

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

- Live probe runbook (scratch evidence checklist): `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md`
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
