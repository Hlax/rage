---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-065 Local Live Mini-Run Chain Audit

- Audit type: focused pre-ticket readiness (live Ollama milestone + live smoke)
- Date: 2026-06-12
- Scope: read-only design audit. No implementation. No ticket seeding in this invocation.
- Baseline HEAD: `b1a135fd9fe42929f622e51dff75b87dcd61d960`
- Prior probes: ticket-060–064 (individual report-only live probes)
- Human architecture note: Qwen/local worker is **not** the strategic self-improvement or ticket-authoring brain

## 1. Executive verdict

**PARTIAL — chain design must be narrowed**

Stages 1–3 (extract → link → relationship) can be **fully live-chained** from a
controlled fixture source with proven acceptance floors. Stage 4 (contradiction
detection) **cannot** be safely required to consume only upstream chained outputs
today: chained relationship drafts produce `supports`/`ideation` edges, while
contradiction validation requires GT07-shaped `may_reduce` / `may_increase`
relationship triples plus opposing/qualifying claim fragments. A **hybrid mini-run**
(stages 1–3 chained live; stage 4 via committed contradiction overlay when chain
inputs are insufficient) is the narrowed design for ticket-065. Pure single-source
full chain through contradiction is **not stable enough** for default acceptance.

**Proceed to seed ticket-065 only with the hybrid design in §5–§8.**

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` | `git checkout main` |
| Working tree | **clean** (at audit start after principal-audit commit) | `git status --short` empty |
| Local HEAD | `b1a135f` | `git rev-parse HEAD` |
| `origin/main` | `b1a135f` | `git push origin main` after principal audit |
| Principal audit committed | **yes** | `Record post-ticket-064 principal audit.` |
| Latest Golden Gate | **success** (prior tip) | run **27441243382** at `bd11e36`; new run pending for `b1a135f` |
| Golden Gate URL | https://github.com/Hlax/rage/actions/runs/27441243382 | prior green run |
| `principal_audit_gate --next-ticket ticket-065` | **satisfied** | `cadence_status: satisfied`; checkpoint post-ticket-064 |
| ticket-059 OpenAI | **proposed / deferred** | placeholder only |
| ticket-065 JSON | **absent** | not seeded yet |

## 3. Current local live spine

| Stage | Probe exists? | Live accepted output proven? | Validator authoritative? | Notes |
| ----- | ------------- | ---------------------------- | ------------------------ | ----- |
| Claim extraction | **yes** — `probe-extract-claims` | **yes** — `accepted_count >= 1` on `live_probe_claim_calibration_short.txt` (ticket-061) | **yes** — `claim_validator` | Report-only; diagnostics on reject |
| Concept linking | **yes** — `probe-link-concepts` | **yes** — 3 accepted on quality claim fixture (ticket-062) | **yes** — `validate_concept_links` | `--chain-extract` supported |
| Relationship drafting | **yes** — `probe-draft-relationships` | **yes** — 1 accepted on quality bundle (ticket-063) | **yes** — `validate_relationship_candidates` | `--chain-link` supported |
| Contradiction detection | **yes** — `probe-detect-contradictions` | **yes** — 1 accepted on GT07-shaped bundle (ticket-064) | **yes** — `validate_contradiction_candidates` | Default bundle ≠ chained stage-3 output |

**Per-stage chain flags today:** `chain_extract`, `chain_link`, `chain_relationship`
exist on individual probes but **no unified orchestrator** writes one combined report.

**Live smoke:** 5 tests deselected by default (health + four probes); no mini-run smoke yet.

## 4. Research-agent readiness assessment

### How close are we to actual local research?

**Close for structured evidence extraction report-only; not close for persisted local discovery runs.**

Individual live probes prove Qwen can produce **candidate JSON** that passes Python
validators for each spine task. That is the correct worker-layer boundary. A mini-run
proves **orchestration + stage handoff + unified audit artifact** without opening
DB/export/cloud surfaces.

### What is proven?

- Live opt-in gates (`RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, health check)
- Four structured tasks accept on controlled fixtures with `db_writes: false`
- Calibrated Ollama prompts + rejection diagnostics per stage
- Mock-only CI/golden unchanged (257 pytest, 140 golden, 5 `live_smoke` deselected)
- Principal audit cadence satisfied (post-ticket-064)

### What is still report-only?

- All four probes and the proposed mini-run
- No live `research run` without `--fixture-mode`
- No live ingestion → SQLite persistence path
- No live public export or card mutation

### What is not yet persisted?

- Claims, concept links, relationships, contradiction evidence, scores, queue ranks
- Improvement ticket drafts from live evidence (mock/fixture only today)
- Theories, cluster narratives, domain proposals from live worker output

### What is needed before a real research run?

1. Mini-run chain report (ticket-065) — unified operator proof
2. Scratch-DB or explicit persist opt-in ticket (separate; review-gated)
3. Evidence accumulation policy before any strategic synthesis (principal/API layer)
4. Human confirmation gates for promotion/export (already plumbed for improvement tickets)
5. **Not** OpenAI/ticket-059 until operator explicitly approves cloud adapter work

## 5. Recommended mini-run design

### CLI command

**Preferred:** `python -m rge.cli probe-mini-run`

(Alternative `live-probe mini-run` is acceptable but inconsistent with existing
`probe-*` naming; recommend single subcommand `probe-mini-run`.)

### Default fixture/source

```txt
fixtures/sources/live_probe_claim_calibration_short.txt
```

Rationale: ticket-061 calibrated source; contains both quality-increase and
semantic-diversity-reduction sentences; short and committed; no private paths.

### Stage sequence (narrowed hybrid)

| Order | Stage | Input | Live call | Failure mode |
| ----- | ----- | ----- | --------- | ------------ |
| 1 | Claim extraction | default fixture source | `run_probe_extract_claims` (in-process; no per-stage report file required) | **fatal** if 0 parseable candidates |
| 2 | Concept linking | accepted claims from stage 1 | `run_probe_link_concepts` with in-memory handoff | **fatal** if 0 accepted links |
| 3 | Relationship drafting | claim + accepted links → concept dicts | `run_probe_draft_relationships` handoff | **fatal** if 0 accepted relationships |
| 4 | Contradiction detection | see below | `run_probe_detect_contradictions` | **partial-OK** — see §5 partial behavior |

**Stage 4 input policy (narrowed):**

1. **Try** contradiction using chained stage-3 outputs **only if** probe-local
   relationships include resolvable `may_reduce` and `may_increase` triples and
   domain claims include qualifying + opposing fragments.
2. **Else (expected default):** use committed overlay
   `fixtures/probes/live_probe_contradiction_quality_bundle.json` for
   `domain_claims` + `relationships`, optionally overlay qualifying `source_claim`
   from stage 1 when IDs/text align.
3. Record `contradiction_input_mode`: `chained` | `overlay_bundle` | `skipped_insufficient_inputs`.

This matches human preference for chained stages 1–3 while avoiding false failure
when stage 3 cannot produce GT07 tension edges.

### Output artifact

Single JSON report:

```txt
data/reports/live_probes/probe_mini_run_<UTC-stamp>.json
```

Do **not** write four separate per-stage probe files by default (optional debug flag later).

### Report schema (minimum fields)

```json
{
  "report_type": "live_probe_mini_run_report",
  "command": "probe-mini-run",
  "status": "ok | partial | error",
  "created_at": "...",
  "fixture_source": "fixtures/sources/live_probe_claim_calibration_short.txt",
  "domain_pack": "creativity",
  "provider": "ollama",
  "model": "...",
  "effective_llm_mode": "ollama",
  "schema_version": "0.1.0",
  "db_writes": false,
  "public_export": false,
  "cloud_calls": false,
  "elapsed_ms": 0,
  "stages": {
    "claim_extraction": { "status": "ok", "accepted_count": 0, "rejected_count": 0, "elapsed_ms": 0, "diagnostics_summary": "..." },
    "concept_linking": { "...": "..." },
    "relationship_drafting": { "...": "..." },
    "contradiction_detection": { "status": "ok|skipped|error", "input_mode": "overlay_bundle", "...": "..." }
  },
  "probe_local_ids": { "claims": [], "concepts": [], "relationships": [] },
  "health": { }
}
```

Embed rejected-row `validation_diagnostic` samples in each stage (cap list length).

### Failure behavior

- **Fail closed (exit 1):** live opt-in missing, Ollama unhealthy, fixture missing, stage 1–3 catastrophic (0 candidates or unparseable structured response).
- **Partial success (exit 0 with `status: partial`):** stages 1–3 OK; stage 4 skipped because inputs insufficient **and** overlay disabled by flag (non-default).
- **Default:** stage 4 uses overlay bundle → expect `status: ok` when overlay accepts (proven in ticket-064).

### Partial-success behavior

Allowed **only** for stage 4 when:

- Operator passes `--strict-chain` (requires chained contradiction inputs; no overlay), or
- Overlay bundle file missing (fail closed)

Document skip reason in `stages.contradiction_detection.skip_reason`.

### What must not happen

- Default DB writes or `connect()` to default SQLite
- Public export / `apps/public-site/public/data/` mutation
- Cloud/API keys or OpenAI/OpenRouter adapters
- Model shell/Git/file/repo mutation
- Writing improvement tickets to `tickets/` or promoting queue rows
- Calling `draft_ticket` / `generate-improvement-tickets` in live mini-run path
- Committing `data/reports/live_probes/` artifacts
- Live execution in CI/golden/default pytest

## 6. Self-improvement architecture

### Qwen / local worker responsibilities (bounded)

- Emit **structured candidate JSON** for: claims, concept links, relationships,
  contradictions, and (future) small summaries
- Operate only through `OllamaModelClient` structured calls inside probe/pipeline modules
- Produce **evidence and diagnostics** — never authoritative graph state

### Python validator responsibilities

- Reject/accept every candidate via existing validators (`claim_validator`,
  `concept_linker`, `relationship_builder`, `contradiction_detector`)
- Attach `validation_diagnostic` / rejection reasons for operator reports
- Gate all persistence paths (unchanged; mini-run bypasses persistence)

### Principal / API reasoning model responsibilities

- Decide when enough evidence exists for larger theories, domain exploration, or architecture changes
- Synthesize improvement **proposals** from accumulated reports (future; not ticket-065)
- Run principal audits and pre-ticket readiness reviews
- Classify gate status (`safe_autonomous`, `review_gated`, `blocked`)

### Human approval responsibilities

- Seed tickets, approve scope, merge to `main`
- Promote improvement drafts (`--confirm` gate)
- Approve cloud escalation (ticket-059+) when implemented
- Decide whether worker prompt/skill expansion is warranted

### Why Qwen must not create/promote implementation tickets yet

- `draft_ticket` is mock/fixture-only; GT21 validates consumption, not live authority
- Improvement tickets affect Git scope, safety boundaries, and queue order — strategic decisions
- Local worker lacks cross-run evidence memory in ticket-065 scope; premature ticket emission would conflate **diagnostics** with **roadmap authority**
- `13_MODEL_ESCALATION_POLICY.md` assigns ticket queue/Git/shell to deterministic code + human review
- Mini-run output should feed **reports**, not `tickets/ticket-*.json` or `TICKET_QUEUE.md`

**Ticket generation from evidence remains principal/human/API-reasoning-layer controlled.**

## 7. Safety controls

| Control | Status |
| ------- | ------ |
| No default DB writes | **Confirmed** — orchestrator calls in-process probe helpers; no repository inserts |
| No accepted graph mutation | **Confirmed** — bypass `extract-claims`, `link-concepts`, `build-relationships`, `detect-contradictions` DB paths |
| No public export | **Confirmed** — no `export-public` / card_exporter |
| No committed live artifacts | **Confirmed** — `data/reports/` gitignored |
| No OpenAI/OpenRouter/API keys | **Confirmed** — ticket-059 deferred |
| No model shell/Git/file mutation | **Confirmed** — structured JSON only |
| CI/golden mock-only | **Confirmed** — unit tests mock client; optional `live_smoke` env-gated |
| Python validation authoritative | **Confirmed** — reuse existing validators per stage |
| Qwen not ticket authority | **Confirmed** — non-goal for ticket-065 |
| `live_smoke` milestone | **Triggered** — adding mini-run smoke requires this pre-ticket audit before implementation |

**Scratch DB vs report-only:** remain report-only for ticket-065. Scratch SQLite is a separate future ticket.

## 8. Proposed ticket-065

### Title

Report-only local live mini-run chain

### Problem

Tickets 060–064 proved individual live structured probes. Operators lack a single
command that runs the local research spine end-to-end and writes one auditable
report without DB/export/cloud surfaces.

### Scope

- Add `probe-mini-run` CLI and `run_probe_mini_run` in `live_probe.py`
- Chain stages 1–3 live from default calibration fixture source
- Stage 4 hybrid: overlay `live_probe_contradiction_quality_bundle.json` when chained inputs insufficient (default); optional `--strict-chain` for experimentation
- Single combined JSON report with per-stage counts, diagnostics, timings, `db_writes: false`
- Mock-only unit tests; optional `live_smoke` test (env-gated, non-default pytest)
- Update `docs/agents/12_RUNTIME_CONFIG.md` and `13_MODEL_ESCALATION_POLICY.md` worker-boundary note if needed

### Expected files

- `rge/modules/live_probe.py`
- `rge/cli.py`
- `docs/agents/12_RUNTIME_CONFIG.md`
- `tests/unit/test_live_probe_mini_run_cli.py`
- `tests/smoke/test_live_ollama_smoke.py` (optional mini-run smoke)
- `tickets/ticket-065.json`
- `agent_reports/2026-06-12_phase-2_ticket-065_local-live-mini-run-chain.md`

### Acceptance criteria

- `probe-mini-run` requires `RGE_LLM_MODE=ollama` and `RGE_ALLOW_LIVE_LLM=1`
- Live run on default fixture: stages 1–3 each `accepted_count >= 1`
- Stage 4 `accepted_count >= 1` via default overlay mode
- One report under `data/reports/live_probes/`; `db_writes: false`
- No default DB mtime change; no public export
- Mock pytest + CI remain green without Ollama
- Mini-run does not call ticket drafting or queue promotion APIs

### Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_live_probe_mini_run_cli.py -q
python -m pytest -q
python -m rge.cli verify --skip-site
```

Manual live:

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli model-health
python -m rge.cli probe-mini-run
```

### Safety considerations

- Reuse `assert_live_probe_env` + single upfront health check
- In-process stage handoff; no intermediate report files required
- Cap embedded diagnostic payload size in combined report
- Explicit non-goals: ticket authoring, DB, export, cloud

### Non-goals

- Persist claims/relationships/contradictions to SQLite
- Public export or site JSON changes
- OpenAI/OpenRouter (ticket-059)
- Qwen-driven improvement ticket creation or promotion
- Full `research run` live discovery
- Weakening stage validators
- Pure chained contradiction as default acceptance gate (defer to `--strict-chain` experiments)

### Rollback plan

Revert CLI, orchestrator, tests, docs. No schema migrations.

### Risk level

low-medium

### Pre-ticket audit required?

**Satisfied by this report.** Re-run `python -m rge.modules.principal_audit_gate --next-ticket ticket-065` after seeding.

## 9. Final recommendation

**Seed ticket-065 as drafted** (hybrid stage-4 design) after human review of this audit.

Sequence:

1. Human reviews §5 hybrid contradiction policy.
2. Seed `tickets/ticket-065.json` and queue row.
3. Implement on branch `phase-2/ticket-065-local-live-mini-run-chain`.
4. Keep **ticket-059 OpenAI deferred**.
5. Do **not** wire Qwen to author/promote implementation tickets.

Do **not** pursue pure full-chain contradiction as the default acceptance gate until
a dedicated two-source fixture or stable chained GT07 tension is proven in live runs.

---

*Audit complete. No ticket-065 implementation in this invocation.*
