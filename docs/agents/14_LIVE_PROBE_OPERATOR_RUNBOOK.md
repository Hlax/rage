# Live Probe Operator Runbook

## Purpose

Operator guide for **report-only** local live structured probes (tickets 060–065).
These commands prove the Qwen/Ollama worker layer without SQLite writes, public
exports, or cloud API keys.

Canonical runtime env: `docs/agents/12_RUNTIME_CONFIG.md`.  
Responsibility split: `docs/agents/13_MODEL_ESCALATION_POLICY.md`.

## Core rule

```txt
Qwen/Ollama emits structured candidate JSON and diagnostics only.
Python validators accept or reject every candidate.
Principal/API reasoning and humans own strategic decisions and tickets.
```

**Never** treat live probe output as authority to:

- edit `tickets/ticket-*.json` or `TICKET_QUEUE.md`
- call `promote-improvement-ticket` without human review
- write to the default SQLite database or public export paths
- run `draft_ticket` / `generate-improvement-tickets` in live mini-run paths

## Live opt-in (all probes)

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
```

Expect `reachable: true`, `model_available: true`, `effective_llm_mode: ollama`.

`effective_llm_mode: mock` when opt-in is off is **expected**, not a failure.

## Artifact location

All probe reports write under:

```txt
data/reports/live_probes/
```

- Gitignored — do **not** commit probe JSON to the repo.
- Safe to accumulate locally for operator review.
- CI/golden tests never read these files.

Filename patterns:

| Command | Prefix |
| ------- | ------ |
| `probe-extract-claims` | `probe_extract_claims_<UTC>.json` |
| `probe-link-concepts` | `probe_link_concepts_<UTC>.json` |
| `probe-draft-relationships` | `probe_draft_relationships_<UTC>.json` |
| `probe-detect-contradictions` | `probe_detect_contradictions_<UTC>.json` |
| `probe-mini-run` | `probe_mini_run_<UTC>.json` |
| `probe-mini-run-suite` | `probe_mini_run_suite_<UTC>.json` (plus per-fixture `probe_mini_run_*.json`) |

Every report must include `db_writes: false`.

## Individual probe acceptance floors

Documented from controlled fixtures on qwen2.5:7b (2026-06-12). Use as
**operator signals**, not CI gates.

| Probe | Default input | Expected floor | Typical live result |
| ----- | ------------- | -------------- | ------------------- |
| `probe-extract-claims` | `fixtures/sources/live_probe_claim_calibration_short.txt` | `accepted_count >= 1` | 1 accepted, 1 rejected (scope verbatim on diversity claim) |
| `probe-link-concepts` | `fixtures/claims/live_probe_concept_link_quality_claim.json` | `accepted_count >= 1` | 3 accepted |
| `probe-draft-relationships` | `fixtures/probes/live_probe_relationship_quality_bundle.json` | `accepted_count >= 1` | 1 accepted (`AI assistance` supports `ideation`) |
| `probe-detect-contradictions` | `fixtures/probes/live_probe_contradiction_quality_bundle.json` | `accepted_count >= 1` | 1 accepted (GT07-shaped overlay) |

Rejected rows should include `validation_diagnostic` — use these for worker
calibration notes, not validator weakening.

## `probe-mini-run` (preferred end-to-end check)

Single command chaining stages 1–3 live, then stage 4 with hybrid policy.

```powershell
python -m rge.cli probe-mini-run
python -m rge.cli probe-mini-run --strict-chain
```

Default source: `fixtures/sources/live_probe_claim_calibration_short.txt`.

### Stage floors (mini-run report `stages` object)

| Stage | Key | Fail closed? | Acceptance floor | Notes |
| ----- | --- | -------------- | ---------------- | ----- |
| 1 | `claim_extraction` | **yes** | `accepted_count >= 1` | Catastrophic if zero parseable candidates |
| 2 | `concept_linking` | **yes** | `accepted_count >= 1` | Uses accepted claims from stage 1 |
| 3 | `relationship_drafting` | **yes** | `accepted_count >= 1` | Uses accepted links → concept dicts |
| 4 | `contradiction_detection` | hybrid only | `accepted_count >= 1` in default mode | May **skip** only with `--strict-chain` |

**Documented live floors (2026-06-12):**

| Stage | Default run | Strict-chain run |
| ----- | ----------- | ---------------- |
| claim_extraction | 1 / 1 | 1 / 1 |
| concept_linking | 2 / 0 | 2 / 0 |
| relationship_drafting | 1 / 0 | 1 / 0 |
| contradiction_detection | 1 / 0 | skipped |

Overall report `status`:

- `ok` — stages 1–3 passed; stage 4 accepted (default hybrid) or chain-suitable
- `partial` — stages 1–3 passed; stage 4 skipped under `--strict-chain` only

## `probe-mini-run-suite` (multi-fixture repeatability)

Batch the hybrid mini-run across controlled creativity sources to detect
fixture-specific brittleness. Still report-only.

```powershell
python -m rge.cli probe-mini-run-suite
python -m rge.cli probe-mini-run-suite --strict-chain
```

### Default fixture set

| Fixture | Purpose |
| ------- | ------- |
| `fixtures/sources/live_probe_claim_calibration_short.txt` | ticket-061 calibration baseline |
| `fixtures/sources/live_probe_diversity_calibration_short.txt` | GT02-style scoped calibration (ticket-067) |
| `fixtures/sources/creativity_ai_diversity_followup_short.txt` | replication-style short source (opposing-only; hybrid overlay uses bundle qualifying claim — ticket-069) |
| `fixtures/sources/live_probe_contradiction_calibration_short.txt` | divergent-condition calibration (ticket-067) |

The long golden passages (`creativity_ai_diversity_short.txt`,
`creativity_ai_diversity_contradiction.txt`) remain for mock/golden tests but are
not default suite fixtures.

Repeat `--fixture-source` to override the default list.

### Suite summary fields

| Field | Meaning |
| ----- | ------- |
| `fixture_count` | Number of fixtures attempted |
| `fixtures_passed` | Runs where all stage floors met |
| `fixtures_failed` | Runs missing a floor or raising an error |
| `runs[].floors_met` | Per-fixture floor check |
| `runs[].report_path` | Link to individual mini-run JSON |

Suite `status`: `ok` when all fixtures pass floors; `partial` when some pass;
`error` when none pass.

### `contradiction_input_mode` semantics

Top-level field on `probe_mini_run` reports. Records how stage 4 sourced its inputs.

| Value | Meaning | When |
| ----- | ------- | ---- |
| `hybrid_overlay` | Stage 4 used committed `fixtures/probes/live_probe_contradiction_quality_bundle.json` for domain claims + relationship triples; qualifying claim overlaid from stage 3 input | **Default** — upstream chain lacks GT07 `may_reduce` / `may_increase` tension |
| `chain` | Stage 4 used only upstream chain claims and relationship drafts | Chain outputs include opposing + qualifying claim fragments **and** `may_reduce` + `may_increase` predicates |
| `skipped_strict_chain_insufficient_inputs` | Stage 4 not run | `--strict-chain` and chain inputs unsuitable |

**Why hybrid exists:** chained relationship drafts typically produce `supports`
edges (e.g. `AI assistance` → `brainstorming`), not the `may_reduce` /
`may_increase` diversity tension that `validate_contradiction_candidates`
expects. Hybrid overlay proves stage 4 live structured calls without falsely
failing the mini-run when stages 1–3 succeed.

Stage 4 hybrid reports may include `overlay_bundle_path` pointing at the
committed contradiction bundle.

### `--strict-chain` operator interpretation

Use when testing whether upstream outputs alone could ever feed contradiction
detection. Expect `status: partial` and stage 4 `skip_reason` today. This is
**not** a regression by itself — it documents a known spine gap until a
two-source or richer chain fixture is proven live.

## Optional smoke tests

Excluded from default pytest/CI (`live_smoke` marker):

```powershell
python -m pytest -m live_smoke tests/smoke
```

Requires the same live opt-in env vars as CLI probes.

## Accumulating evidence for improvement proposals

Live probes produce **worker-layer evidence**, not implementation tickets.

### What to keep locally

After each probe session, retain reports under `data/reports/live_probes/`.
Optionally copy **summaries** (not full raw dumps) into a dated operator note in
`agent_reports/` when preparing a principal or human review — for example:

```txt
agent_reports/YYYY-MM-DD_live-probe-evidence-review.md
```

Include per run:

- command and fixture source
- `accepted_count` / `rejected_count` per stage
- `contradiction_input_mode` (mini-run)
- sample `validation_diagnostic` strings from rejections
- `db_writes`, `public_export`, `cloud_calls` confirmations

Do **not** commit `data/reports/live_probes/*.json`.

### Scratch DB (operator-reviewed metadata only)

After reviewing a mini-run or suite report locally, optionally persist **sanitized
metadata** to an isolated scratch SQLite file (not the accepted graph DB):

```powershell
python -m rge.cli probe-persist-reviewed-report `
  --report data/reports/live_probes/probe_mini_run_<UTC>.json `
  --confirm-review `
  --note "reviewed ok for evidence log"
```

Default scratch path: `data/db/live_probe_scratch.sqlite` (gitignored under `data/`).

**Rules:**

- `--confirm-review` is **required** — fail closed without operator confirmation
- Mini-run / suite commands **never** write scratch DB automatically
- Scratch rows are metadata only (counts, modes, diagnostics summary) — not accepted claims
- No public export reads scratch DB; no Qwen/model authority over persist

### Scratch DB summary (read-only, deterministic)

Summarize reviewed rows without LLM calls or DB writes:

```powershell
python -m rge.cli probe-scratch-summary
python -m rge.cli probe-scratch-summary --format markdown
python -m rge.cli probe-scratch-summary --fixture live_probe_claim_calibration_short.txt
python -m rge.cli probe-scratch-summary `
  --out data/reports/live_probes/scratch_summary_<UTC>.json
```

**Rules:**

- Opens scratch DB with SQLite read-only mode (`mode=ro`)
- Never creates, migrates, or mutates scratch DB
- Missing DB fails closed unless `--allow-empty`
- `--out` must be under `data/reports/` or `agent_reports/` (not public export paths)
- Summary includes counts and safety flags only — no raw prompts, model responses, or operator note bodies

### Scratch evidence review (read-only, deterministic)

Compose a principal/operator evidence review from scratch summary data:

```powershell
python -m rge.cli probe-scratch-evidence-review
python -m rge.cli probe-scratch-evidence-review --format json
python -m rge.cli probe-scratch-evidence-review `
  --out agent_reports/YYYY-MM-DD_scratch-evidence-review.md
```

**Rules:**

- Reuses `probe-scratch-summary` aggregation (read-only scratch DB)
- Default output is markdown for human review
- No LLM calls; **no automated ticket recommendations** in report body
- `--out` must be under `data/reports/` or `agent_reports/`
- Operator note bodies are not included (count only via summary)

### Who does what

| Role | Responsibility |
| ---- | ---------------- |
| **Qwen / local worker** | Structured candidates + diagnostics per stage |
| **Python validators** | Accept/reject; attach rejection reasons |
| **Operator** | Run probes, archive reports locally, file evidence summaries |
| **Principal / API reasoning agent** | Synthesize improvement **proposals** after enough evidence; run `/rge-principal-audit`; draft pre-ticket audits |
| **Human** | Seed `tickets/ticket-*.json`, approve queue rows, merge, promote improvement drafts with `--confirm` |

### Improvement ticket path (human-gated)

```txt
live probe reports (local, gitignored)
  → operator/principal evidence review (agent_reports/)
  → human-approved pre-ticket audit (if live-smoke or milestone triggered)
  → human seeds tickets/ticket-NNN.json + TICKET_QUEUE.md
  → builder agent implements one ticket per branch
```

**Not in scope for live probes:**

- `research generate-improvement-tickets` in live mode
- `draft_ticket` via Ollama (mock/fixture only today)
- automatic `promote-improvement-ticket`
- Qwen editing Git, queue, or DB

Cloud/API ticket synthesis (ticket-059+) remains **deferred** until explicit
operator approval and a focused pre-ticket audit.

### When to open an improvement proposal

Consider a principal review or new ticket when **patterns repeat** across
multiple saved probe reports, for example:

- same `validation_diagnostic` on >3 live runs (prompt calibration ticket)
- stage 1–3 floors met but strict-chain never reaches `chain` mode (chain fixture ticket)
- new live smoke constraint (pre-ticket audit required before implementation)
- evidence that hybrid overlay masks a regression in stages 1–3 (investigate upstream)

Single-run rejections are diagnostics, not automatic tickets.

## Quick reference commands

```powershell
# Individual probes (debug one stage)
python -m rge.cli probe-extract-claims
python -m rge.cli probe-link-concepts
python -m rge.cli probe-draft-relationships
python -m rge.cli probe-detect-contradictions

# End-to-end spine (one report)
python -m rge.cli probe-mini-run
python -m rge.cli probe-mini-run --strict-chain

# Multi-fixture repeatability (suite summary + per-fixture reports)
python -m rge.cli probe-mini-run-suite
python -m rge.cli probe-mini-run-suite --strict-chain
```

## Related documents

- `docs/agents/12_RUNTIME_CONFIG.md` — env vars and probe CLI list
- `docs/agents/13_MODEL_ESCALATION_POLICY.md` — worker vs Python vs cloud tiers
- `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` — promotion and audit gates
- `agent_reports/2026-06-12_pre-ticket-065_local-live-mini-run-chain.md` — hybrid design audit
