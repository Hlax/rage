# AGENTS.md

## Purpose

This file is the root operating guide for AI builder agents working in the Research Graph Engine repo.

The repo implements a local-first Research Graph Engine. The system turns sources into scoped claims, concept links, evidence relationships, reports, public cards, and improvement tickets.

Agents must follow the implementation specs in `docs/agents/`.

## Source Priority

Read sources in this order:

1. `docs/agents/01_RESEARCH_GRAPH_ENGINE_CANONICAL_CONTEXT_v1.md`
2. `docs/agents/00_GOLDEN_TESTS.md`
3. `docs/agents/02_ARCHITECTURE.md`
4. `docs/agents/03_MODEL_RUNTIME_SPEC.md`
5. `docs/agents/04_CURSOR_BUILD_LOOP.md`
6. `docs/agents/05_DATA_MODEL.md`
7. `docs/agents/06_DOMAIN_PACK_SPEC.md`
8. `docs/agents/07_MVP_ACCEPTANCE_TESTS.md`
9. `docs/agents/08_REPORTING_SPEC.md`
10. `docs/agents/09_RESEARCH_RUN_CONTRACT.md`
11. `docs/agents/10_SAFETY_MODEL.md`
12. `docs/agents/11_AGENT_OPERATING_PROTOCOL.md`
13. `docs/agents/12_RUNTIME_CONFIG.md`
14. `docs/agents/13_MODEL_ESCALATION_POLICY.md` — local-first modes and escalation policy
15. `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` — live probe operator runbook
16. `docs/agents/000_init.md` only as historical seed context

If documents conflict, follow the higher-priority document.

## Non-Negotiable Rules

- One ticket per branch.
- Do not broaden implementation scope without creating a new ticket.
- Do not hardcode creativity-specific fields into the core engine.
- Qwen/Ollama proposes candidate JSON only; Python validates and writes.
- Golden tests must support mock LLM mode and must not require Ollama to be running.
- No model output may write directly to accepted DB tables.
- No public write routes.
- No public source ingestion routes.
- No public agent execution routes.
- No raw prompts, local paths, secrets, private notes, or raw source text in public exports.
- Every implementation run must end with an agent report in `agent_reports/`.
- Never claim success unless required commands were run, or failures are explicitly documented.

## Operator Loop (human default)

Before coordinating the next ticket manually, run the bounded operator loop:

```bash
python -m rge.modules.operator_loop --mode plan
python -m rge.modules.operator_loop --mode execute-safe
python -m rge.modules.operator_autocycle --mode plan --max-cycles 10
```

Plan mode is read-only and recommends the next action with gate classification
(`safe_autonomous`, `review_gated`, `blocked`). Execute-safe runs mock-only
golden tests, pytest, safety audit, and public-site build when the working
tree is clean. It never merges, pushes, promotes tickets, or edits the queue.
See `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` for the full workflow.

**Live probe scratch evidence workflow** (local Ollama opt-in; operator-only
persist): after live probe sessions, follow the numbered checklist in
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` (**Scratch evidence workflow
checklist**). Plan mode surfaces `scratch_evidence_status` and may recommend
`run_scratch_evidence_review` when reviewed scratch rows exist. See also README
Operator Quickstart.

**Maturity tiers (honest framing):**

- **MVP-Engine:** mock/fixture-proven — golden tests, safety audit, fixture-mode run.
- **MVP-Research:** NM-1 live validated write proof (`extract-claims-live`) plus NM-4
  evidence DB operator spine (127–133) on gitignored `live_research_evidence.sqlite`;
  default graph synthnote path remains checksum-pinned mock — not arbitrary live extraction.
- **Arbitrary-source pipeline:** partial — Phase 3 staged mock spine fixture-proven through
  `--staged-spine` orchestration (operator network env required; tests patch I/O); opt-in
  operator live discover→fetch (ticket-167), discover→fetch→ingest-staged (ticket-168),
  and discover→fetch→ingest→mock extract (ticket-172), discover→fetch→ingest→extract→mock
  link (ticket-175), discover→fetch→ingest→extract→link→mock build (ticket-178),
  discover→fetch→ingest→extract→link→build→mock detect (ticket-181),
  discover→fetch→ingest→extract→link→build→detect→reconcile-scores (ticket-184),
  discover→fetch→ingest→extract→link→build→detect→reconcile→generate-run-report
  (ticket-187) and rank-2 discover→…→generate-run-report (ticket-190) and
  single-command orchestrator proof (ticket-193) via `pytest -m live_network` (not CI);
  per-step live Ollama extract on staged rank-1 ingest (ticket-204; operator opt-in;
  orchestrator still mock); evidence DB NM-4 proven; default graph
  synthnote checksum-mock; bare `research run --topic --domain` (no flags) remains
  `not_implemented`; full live MVP without golden fixtures remains out of scope.
- **Cloud providers:** deferred (ticket-059).

**Live staged network proofs** (operator opt-in; tickets 167–193): real OpenAlex HTTP
pytest proofs on temp DB paths. **Not** run in CI or default `pytest` (`live_network`
marker excluded in `pyproject.toml`). Default staged proofs use mock LLM after live
ingest; tickets 172/175/178/181 use explicit mock fixtures for `extract-claims`,
`link-concepts`, `build-relationships`, and `detect-contradictions` after live ingest;
tickets 184/187 add deterministic `reconcile-scores` and generate-run-report for rank-1;
ticket-190 adds rank-2 candidate discover through generate-run-report with
second-candidate mock fixtures; ticket-193 adds single-command
`research run --staged-spine` (or legacy `--fixture-mode --staged-spine`) via
`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` (orchestrator **always** forces mock LLM). Temp
DB/output only — no public export. Env gates: `RGE_ALLOW_SOURCE_NETWORK=1`,
`OPENALEX_MAILTO`, plus `RGE_ALLOW_LIVE_STAGED_FETCH=1` (discover→fetch),
`RGE_ALLOW_LIVE_STAGED_INGEST=1` (discover→fetch→ingest-staged),
`RGE_ALLOW_LIVE_STAGED_EXTRACT=1` (discover→fetch→ingest→mock extract),
`RGE_ALLOW_LIVE_STAGED_LINK=1` (discover→fetch→ingest→extract→mock link),
`RGE_ALLOW_LIVE_STAGED_BUILD=1` (discover→fetch→ingest→extract→link→mock build),
`RGE_ALLOW_LIVE_STAGED_DETECT=1` (discover→fetch→ingest→extract→link→build→mock
detect), `RGE_ALLOW_LIVE_STAGED_RECONCILE=1`
(discover→fetch→ingest→extract→link→build→detect→reconcile-scores),
`RGE_ALLOW_LIVE_STAGED_REPORT=1`
(discover→fetch→ingest→extract→link→build→detect→reconcile→generate-run-report),
`RGE_ALLOW_LIVE_STAGED_RANK2=1`
(rank-2 discover→fetch→ingest→second-candidate mock extract→…→generate-run-report), or
`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1`
(single-command discover→dual-candidate report via `research run --staged-spine`).
See README **Operator Quickstart** (**Live staged network proofs**) for per-step commands
and **One-time live orchestrator verification (operator checklist)** for the recommended
one-time orchestrator `pytest -m live_network` checklist (temp DB only; not CI-enforced).

**Live staged extract (live Ollama; ticket-204):** separate per-step operator proof —
not orchestrator-wide. Requires `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`,
`RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`, network gates above, temp `--db`, and
`extract-claims --live-staged-fallthrough` (or chained pytest in
`tests/unit/test_live_staged_extract_live_llm_spine.py` with `live_network` and
`live_smoke` markers). Link/build/detect on staged spine remain mock-only until
separate tickets.

**Manual synthnote operator spine** (mock LLM; tickets 088–099): for Level-1
`manual_text` research on the creativity synthnote source, follow the five-step
CLI sequence in README **Operator Quickstart** (**Manual synthnote operator spine**):
ingest → extract-claims → link-concepts → build-relationships →
detect-contradictions. Uses **checksum-pinned mock fixtures**
(`fixtures/manual_source_fixture_map.json`); no `--fixture` flags for `manual_text`.
Operator sources live under gitignored `data/sources/manual/creativity/`; committed
test copy at `fixtures/sources/manual_synthnote.txt`.

**Live validated extraction write** (NM-1): `extract-claims-live` with
`RGE_ALLOW_LIVE_LLM=1`, non-fixture-map source, explicit evidence DB only.
See README **Live validated extraction write**.

**Manual synthnote score reconciliation** (after the five-step spine): ingest a
follow-up `manual_text` source, extract claims, then run `reconcile-scores`.
See README **Operator Quickstart** (**Manual synthnote score reconciliation**)
for steps 6–8 (follow-up ingest → extract-claims → reconcile-scores; expected
1 `score_events` row and `may_reduce` confidence 0.5 → 0.62). Test copy:
`fixtures/sources/manual_synthnote_followup.txt`.

**Manual synthnote pipeline proof tests** (mock LLM; tickets 092–093, 105–106):
automated validation lives in `tests/unit/test_manual_source_pipeline_e2e.py`
(full spine through reconcile-scores) and
`tests/unit/test_manual_source_pipeline_idempotency.py` (spine and reconcile
re-run idempotency). Run with `RGE_LLM_MODE=mock`; no Ollama required.

**Creativity domain pack runtime loading (NM-5):** see README **Operator Quickstart**
(**Creativity domain pack runtime loading (NM-5; tickets 113–122)**) for the full
table of YAML overlays under `domain_packs/creativity/` and their runtime consumers.
Candidate claim `domain` labels must fall within the pack allowlist (`primary_domains`
and `overlap_domains` from `domain.yaml`); overlap labels such as `art` are accepted
when `extract-claims` validates against `domain_pack=creativity` via
`claim_validator` — out-of-scope labels are rejected as `unsupported_claim`.

## Expected Agent Workflow

1. Read the active ticket from `tickets/TICKET_QUEUE.md` or create the smallest next ticket in `tickets/`.
2. Confirm the phase and scope.
3. Identify expected files.
4. Implement only the ticket scope.
5. Run the required tests.
6. Run safety audit if relevant.
7. Write an agent report.
8. Recommend the next smallest ticket.
9. **Temporary merge checkpoint (until safety evaluator agent is live):** after a
   ticket is marked `done` and the agent report is written, merge the ticket
   branch into `main` and push `origin main`. Document the merge commit hash in
   the agent report. Do not force-push. If merge or push fails, leave the ticket
   `in_progress` or `blocked` and document the failure honestly.
   When the safety evaluator agent owns merge gating, remove this step and
   restore human/checkpoint merge per `docs/agents/04_CURSOR_BUILD_LOOP.md`.

## Default Verification Commands

Use the strongest available verification for the current phase.

**Preferred:** one mock-only suite (golden tests, full pytest, safety audit, optional site build):

```bash
export RGE_LLM_MODE=mock
python -m rge.cli verify
```

```powershell
# PowerShell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify
```

Add `--skip-site` when Node.js is unavailable or you only need Python checks:

```bash
python -m rge.cli verify --skip-site
```

On Windows, `research` may not be on PATH after `pip install -e ".[dev]"`. Use
`python -m rge.cli` for all CLI commands (including `verify`); do not treat a
missing `research` command as a verification failure when the module form works.

`operator_loop --mode execute-safe` resolves `npm` via `shutil.which` for the
public-site build step. If Node.js is not installed, use `verify --skip-site` or
rely on CI Golden Gate for the site build.

Individual checks (same gates, decomposed):

```bash
pytest
pytest tests/golden
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
research --help
research run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
research export-public --limit 100
```

If a command is not available yet, report that clearly instead of pretending it passed.

## Required Report Location

Write implementation reports to:

```txt
agent_reports/
```

Report filenames should use:

```txt
YYYY-MM-DD_phase-<n>_ticket-<id>_<slug>.md
```

Example:

```txt
agent_reports/2026-06-11_phase-0_ticket-001_repo-scaffold-model-runtime.md
```

## Ticket Queue Location

Read the active queue from:

```txt
tickets/TICKET_QUEUE.md
```

Save new ticket JSON files to:

```txt
tickets/
```
