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

Honest two-tier maturity (see ticket-084 master alignment audit and the 2026-06-14
third-party repo-direction audit):

| Tier | Status | What it means |
|------|--------|---------------|
| **MVP-Engine** | **mock/fixture-proven** | Deterministic Python pipeline, validator gate, safety model, public export, golden tests (GT01–GT26), and fixture-mode orchestration are real and green. |
| **MVP-Research** | **partial — NM-1 + NM-4 evidence DB** | NM-1: first live validated claim write via `extract-claims-live` on gitignored `data/db/live_research_evidence.sqlite`. NM-4: operator-proven live manual_text spine through reconcile on that same evidence DB (tickets 127–133). Default graph DB synthnote path remains checksum-mock — not arbitrary live inference. |
| **Arbitrary-source pipeline** | **partial** | **Phase 3 staged spine (mock/fixture-proven):** discover → fetch → ingest-staged → extract → link → build → detect → reconcile → report for rank #1 and #2 OpenAlex candidates, dual-candidate idempotency, and `research run --fixture-mode --staged-spine` orchestration (tickets 144–164). Unit tests patch OpenAlex/fetcher I/O; operator runs require `RGE_ALLOW_SOURCE_NETWORK=1`. **Opt-in operator proofs (not CI):** live OpenAlex discover→fetch (ticket-167), discover→fetch→ingest-staged (ticket-168), discover→fetch→ingest→mock extract (ticket-172), discover→fetch→ingest→extract→mock link (ticket-175), discover→fetch→ingest→extract→link→mock build (ticket-178), discover→fetch→ingest→extract→link→build→mock detect (ticket-181), and discover→fetch→ingest→extract→link→build→detect→reconcile-scores (ticket-184) via `pytest -m live_network` with explicit env gates — see Operator Quickstart. **Not proven:** live arbitrary-source staged discover→report on real network without test patches or live LLM. **Evidence DB:** NM-4 live ingest → extract/link/relationship/contradiction fall-through + deterministic reconcile (`--evidence-db-reconcile`) on gitignored evidence DB. **Default graph DB:** committed synthnote files still use checksum-pinned mock fixtures. `research run` without `--fixture-mode` remains `not_implemented`. |
| **Cloud providers** | **deferred** | OpenAI/OpenRouter/etc. are not wired (ticket-059 placeholder). |

**Phase 1 MVP is complete** for the engine tier. The public site still serves **fixture
cards** (`source_type: fixture`); do not treat it as live research output.

What is **real deterministic engine plumbing today**:

- SQLite migration harness and private research graph (7 migrations)
- Source ingestion, claim extraction, concept linking, relationship building, contradiction detection, score reconciliation
- Research contract drift gating, queue ranking, cluster/theory/ontology/domain/run reports
- Improvement ticket generation with builder-consumption validation
- Fail-closed public card export and static Next.js public site
- Deterministic safety auditor and prompt-injection handling
- Full fixture-mode orchestration: `research run --fixture-mode` (Golden Test 26)
- Phase 3 staged fixture-mode orchestration: `research run --fixture-mode --staged-spine` (mock LLM; network env for discover/fetch; see Operator Quickstart)

What is **mock or checksum-pinned fixture content** (not arbitrary live inference):

- Golden tests, CI, and `research verify` always use `RGE_LLM_MODE=mock`
- Fixture-mode orchestration forces mock regardless of `.env` settings
- Manual synthnote spine (`fixtures/manual_source_fixture_map.json`) ingests real bytes but resolves **canned** LLM candidate JSON by `raw_text_checksum` — the validator runs for real, the candidates are pinned fixtures
- Live discovery (`research run` without `--fixture-mode`) returns `not_implemented`

What is **live report-only** (no graph writes unless operator explicitly opts in):

- `probe-extract-claims`, `probe-mini-run`, and related live probes write gitignored reports only (`db_writes: false`)
- **`extract-claims-live`** (NM-1) is the first explicit live validated write path; requires `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, a non-fixture-map source, and an explicit evidence DB (default `data/db/live_research_evidence.sqlite`, not the default graph DB)
- **NM-4 evidence DB spine** (tickets 127–133): live `--live-manual-*` fall-through on standard pipeline commands plus deterministic `reconcile-scores --evidence-db-reconcile` on the same gitignored evidence DB — see Operator Quickstart **NM-4 evidence DB operator spine**

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

**Staged Phase 3 fixture-mode spine** (mock LLM; tickets 144–163): run discover → fetch →
ingest-staged → extract → link → build → detect → reconcile → report for **two** OpenAlex
candidates on one DB. Uses mock LLM only (`RGE_LLM_MODE=mock`); **does not** run public
export, theory, cluster report, or improvement tickets (unlike the MVP fixture run above).
Requires live OpenAlex HTTP for `discover-sources` and `fetch-candidate` unless you are
running unit tests (which patch network I/O).

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m rge.cli run `
  --fixture-mode `
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

Re-running the same command on the same `--db` is idempotent (stable row counts; ticket-163).
Rank #1 staged steps use auto mock routing; rank #2 uses explicit `--fixture` bindings
inside the orchestrator. Automated proof:
`tests/unit/test_staged_fixture_mode_run_spine.py`.

**Live staged network proofs** (operator opt-in; tickets 167–184): pytest proofs on
real OpenAlex HTTP with temp DB paths. **Not** run in CI or default `pytest`
(collection excludes `live_network`; see `pyproject.toml`). No live LLM; fetch/ingest
proofs stop before `extract-claims`; tickets 172/175/178/181 add mock-fixture extract,
link, build, and detect after live ingest; ticket-184 adds deterministic reconcile-scores.

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

*Discover + fetch + ingest-staged + mock extract + mock link* (ticket-175; writes `claim_concepts` via fixture):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_LINK = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_link_mock_spine.py -m live_network -q
```

*Discover + fetch + ingest-staged + mock extract + mock link + mock build* (ticket-178; writes `relationships` via fixture):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_BUILD = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_build_mock_spine.py -m live_network -q
```

*Discover + fetch + ingest-staged + mock extract + mock link + mock build + mock detect* (ticket-181; writes `relationship_evidence` qualifications via fixture; seeds domain opposing context locally before live discover):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_DETECT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_detect_mock_spine.py -m live_network -q
```

*Discover + fetch + ingest-staged + mock extract + mock link + mock build + mock detect + reconcile-scores* (ticket-184; writes `score_events` via deterministic Python; seeds domain opposing context locally before live discover):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
```

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
| `python -m rge.cli verify --skip-site` | Same, without npm build (Python checks only) |
| `python -m pytest tests/golden` | Builder merge gate (mock LLM) |
| `python -m pytest` | Full test suite |
| `python -m rge.modules.safety_auditor --audit full` | Deterministic safety audit |
| `python -m rge.cli run --fixture-mode ...` | End-to-end fixture MVP |
| `python -m rge.cli run --fixture-mode --staged-spine ...` | Phase 3 staged discover→report (mock LLM; network env required) |
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
