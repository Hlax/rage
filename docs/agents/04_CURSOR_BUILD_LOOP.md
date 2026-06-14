# CURSOR_BUILD_LOOP.md

## 1. Purpose

The Cursor/build loop is the controlled implementation process for the Research Graph Engine. The research system can observe failures and propose improvements, but it must not directly rewrite itself. Builder agents implement one ticket at a time, with tests and safety audits before merge.

## 2. Core Loop

```txt
Research run
→ run report
→ research intelligence evaluator
→ theory / ontology / domain / prompt / scoring proposals
→ build evaluator
→ implementation ticket
→ Cursor/build agent branch
→ tests
→ safety audit
→ human/checkpoint merge
```

## 3. Non-Negotiable Rules

```txt
one ticket per branch
hard Git checkpoints after phases
no broad refactors without explicit ticket
acceptance criteria required
test plan required
expected files required
non-goals required
rollback plan required
builder agent must run tests before reporting success
safety audit must pass before merge
human can approve merge/checkpoint
research agent proposes tickets, builder agent implements tickets
```

## 4. Branch Naming

Recommended branch pattern:

```txt
phase-<n>/<ticket-id>-<short-slug>
```

Examples:

```txt
phase-0/ticket-001-repo-scaffold
phase-1/ticket-014-claim-quote-validation
phase-2/ticket-022-creativity-ontology-aliases
phase-3/ticket-037-fixture-run-contract
phase-4/ticket-044-public-card-export-safety
phase-5/ticket-052-improvement-ticket-generator
```

## 5. Ticket Schema

Every implementation ticket must include:

```json
{
  "title": "Improve claim extractor scope preservation",
  "problem": "High rejection rate caused by overgeneralized claims.",
  "evidence": ["run_report:run_...:overgeneralized_scope_count=7"],
  "affected_modules": ["claim_extractor", "claim_validator", "creativity_domain_pack"],
  "expected_files": [
    "rge/modules/claim_extractor.py",
    "rge/modules/claim_validator.py",
    "rge/prompts/claim_extraction.md",
    "tests/golden/test_02_claim_extraction.py"
  ],
  "acceptance_criteria": [
    "Overgeneralized fixture claim is rejected or rewritten with preserved scope.",
    "Claims without quote spans are rejected with missing_quote_span.",
    "pytest tests/golden/test_02_claim_extraction.py passes."
  ],
  "test_plan": [
    "pytest tests/golden/test_02_claim_extraction.py",
    "pytest tests/golden/test_03_claim_validation.py"
  ],
  "non_goals": [
    "Do not refactor the full LangGraph orchestration.",
    "Do not change public card schema."
  ],
  "risk_level": "medium",
  "rollback_plan": "Revert extractor prompt/schema changes and restore previous validator version."
}
```

## 6. Pre-Scaffold Ticket: Model Runtime Adapter

The first implementation ticket should be:

```txt
Add model runtime adapter spec and mock LLM mode
```

Ticket body:

```json
{
  "title": "Add model runtime adapter spec and mock LLM mode",
  "problem": "The architecture assigns small structured tasks to Qwen/Ollama, but scaffolding needs a formal adapter boundary, deterministic mock mode, and schema-versioned LLM outputs before implementation starts.",
  "evidence": [
    "Canonical context: Qwen/Ollama proposes small structured outputs while Python validates and writes.",
    "Golden tests must not depend on live model availability or non-deterministic phrasing."
  ],
  "affected_modules": [
    "rge/llm/base.py",
    "rge/llm/ollama_client.py",
    "rge/llm/mock_client.py",
    "rge/llm/schemas.py",
    "rge/llm/registry.py"
  ],
  "expected_files": [
    "MODEL_RUNTIME_SPEC.md",
    "rge/llm/__init__.py",
    "rge/llm/base.py",
    "rge/llm/ollama_client.py",
    "rge/llm/mock_client.py",
    "rge/llm/schemas.py",
    "rge/llm/registry.py",
    "fixtures/llm_outputs/*.json",
    ".env.example",
    "tests/golden/test_00_model_runtime.py"
  ],
  "acceptance_criteria": [
    "Model client interface exists.",
    "Ollama client uses configured localhost base URL.",
    "Mock client returns deterministic fixture outputs.",
    "LLM output schemas are versioned.",
    "Golden tests can force mock mode and run without Ollama.",
    "No model client can write directly to accepted DB tables."
  ],
  "test_plan": [
    "RGE_LLM_MODE=mock pytest tests/golden/test_00_model_runtime.py",
    "RGE_LLM_MODE=mock pytest tests/golden"
  ],
  "non_goals": [
    "Do not bundle model weights.",
    "Do not implement inference inside the repo.",
    "Do not add shell/Git/tool access for models.",
    "Do not add public model endpoints."
  ],
  "risk_level": "medium",
  "rollback_plan": "Disable ollama mode through config, keep mock mode for tests, and revert adapter files without touching DB schema or public export logic."
}
```

## 7. Builder Agent Instructions

For each ticket, the builder agent must:

1. Read the ticket.
2. Confirm affected files.
3. Avoid unrelated edits.
4. Create or use the ticket branch.
5. Implement only the requested scope.
6. Add or update tests listed in the ticket.
7. Run the ticket test plan.
8. Run relevant golden tests.
9. Run safety audit if touching exports, routes, prompts, model tool permissions, or public site.
10. Report changed files, tests run, pass/fail status, and remaining risks.

The builder agent must not:

- Claim success without tests.
- Make broad refactors outside ticket scope.
- Hide failing tests.
- Delete rejected-claim records to make counts look better.
- Loosen safety checks to pass tests.
- Add public write routes.
- Add model-controlled shell/Git access.

**Live probe scratch evidence workflow** (local Ollama opt-in; operator-only
persist): when coordinating live probe calibration outside mock golden tests,
follow the numbered checklist in
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` (**Scratch evidence workflow
checklist**). The bounded operator loop surfaces `scratch_evidence_status` and
may recommend `run_scratch_evidence_review`. See also `AGENTS.md` Operator Loop
and README Operator Quickstart.

**Manual synthnote operator spine** (mock LLM; tickets 088–099): for Level-1
`manual_text` research on the creativity synthnote source, follow the five-step
CLI sequence in README **Operator Quickstart** (**Manual synthnote operator spine**):
ingest → extract-claims → link-concepts → build-relationships →
detect-contradictions. Checksum fixtures resolve from
`fixtures/manual_source_fixture_map.json` (no `--fixture` flags for `manual_text`).
See also `AGENTS.md` Operator Loop and
`docs/agents/11_AGENT_OPERATING_PROTOCOL.md` Operator Loop.

**Manual synthnote score reconciliation** (after the five-step spine): ingest a
follow-up `manual_text` source, extract claims, then run `reconcile-scores`.
See README **Operator Quickstart** (**Manual synthnote score reconciliation**)
for steps 6–8 (follow-up ingest → extract-claims → reconcile-scores; expected
1 `score_events` row and `may_reduce` confidence 0.5 → 0.62). Test copy:
`fixtures/sources/manual_synthnote_followup.txt`. See also `AGENTS.md` Operator Loop
and `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` Operator Loop.

**Manual synthnote pipeline proof tests** (mock LLM; tickets 092–093, 105–106):
automated validation lives in `tests/unit/test_manual_source_pipeline_e2e.py`
(full spine through reconcile-scores) and
`tests/unit/test_manual_source_pipeline_idempotency.py` (spine and reconcile
re-run idempotency). Run with `RGE_LLM_MODE=mock`; no Ollama required. See also
`AGENTS.md` Operator Loop and
`docs/agents/11_AGENT_OPERATING_PROTOCOL.md` Operator Loop.

## 8. Build Phases

### Phase 0: Repo scaffold

Goal:

Create the project skeleton without implementing the full engine.
### Phase 0.5: Model runtime adapter and mock LLM mode

Goal:

Define how local Ollama/Qwen is called and ensure golden tests can run without a live model. This can be implemented as the first Phase 0 ticket or as an immediate checkpoint after the base scaffold.

Expected files:

```txt
MODEL_RUNTIME_SPEC.md
rge/llm/__init__.py
rge/llm/base.py
rge/llm/ollama_client.py
rge/llm/mock_client.py
rge/llm/schemas.py
rge/llm/registry.py
fixtures/llm_outputs/*.json
.env.example
tests/golden/test_00_model_runtime.py
```

Acceptance criteria:

- `rge/llm/base.py` defines the model client interface.
- `rge/llm/ollama_client.py` calls local Ollama through configured `OLLAMA_BASE_URL`.
- `rge/llm/mock_client.py` returns deterministic fixture outputs.
- `rge/llm/schemas.py` defines versioned output schemas.
- `.env.example` includes Ollama and mock-mode settings.
- Tests can force `RGE_LLM_MODE=mock`.
- `pytest tests/golden` can run without Ollama.
- No model client can write directly to accepted DB tables.
- Model-assisted node reports include model/provider/schema/prompt metadata.

Non-goals:

- Do not bundle model weights.
- Do not implement inference inside the repo.
- Do not add model-controlled shell tools.
- Do not add model-controlled Git access.
- Do not add public model endpoints.
- Do not add LangChain provider abstraction unless a later ticket requires it.

Hard checkpoint:

```bash
git tag checkpoint-phase-0-5-model-runtime
```


Expected files:

```txt
README.md
pyproject.toml
rge/__init__.py
rge/cli.py
rge/db/schema.sql
rge/llm/*.py stubs
rge/modules/*.py stubs
domain_packs/creativity/*.yaml stubs
fixtures/sources/*.txt
apps/public-site/package.json
apps/public-site/app/page.tsx
tests/golden/test_scaffold.py
```

Acceptance criteria:

- `research --help` works.
- `pytest` runs.
- Public site builds with placeholder JSON.
- No safety audit failures for scaffold.

Hard checkpoint:

```bash
git tag checkpoint-phase-0-scaffold
```

### Phase 1: General research graph engine

Goal:

Implement source/chunk/claim/concept/relationship/score foundations.

Expected files:

```txt
rge/db/schema.sql
rge/db/connection.py
rge/db/repositories.py
rge/modules/fetcher.py
rge/modules/parser.py
rge/modules/claim_validator.py
rge/modules/concept_linker.py
rge/modules/relationship_builder.py
rge/modules/score_reconciler.py
tests/golden/test_01_ingestion.py
tests/golden/test_02_claim_extraction.py
tests/golden/test_03_claim_validation.py
tests/golden/test_04_concept_linking.py
tests/golden/test_05_relationships.py
tests/golden/test_06_scores.py
```

Acceptance criteria:

- Source ingestion persists source and chunks.
- Scoped claims can be staged/accepted.
- Claims without quote spans are rejected.
- Overgeneralized claims are rejected or rewritten.
- Concepts link without duplicates.
- Relationships preserve support/contradiction/qualification.
- Score events preserve score history.

Hard checkpoint:

```bash
git tag checkpoint-phase-1-engine
```

### Phase 2: Creativity domain pack

Goal:

Implement the first domain pack while keeping core schema domain-general.

Expected files:

```txt
domain_packs/creativity/domain.yaml
domain_packs/creativity/ontology.yaml
domain_packs/creativity/aliases.yaml
domain_packs/creativity/source_preferences.yaml
domain_packs/creativity/evidence_types.yaml
domain_packs/creativity/scoring.yaml
domain_packs/creativity/claim_schema.yaml
domain_packs/creativity/card_templates.yaml
domain_packs/creativity/search_templates.yaml
domain_packs/creativity/safety_notes.yaml
rge/modules/concept_linker.py
rge/modules/candidate_ranker.py
tests/golden/test_04_concept_linking.py
tests/golden/test_07_queue.py
```

Acceptance criteria:

- Required creativity concepts exist.
- Aliases map correctly.
- Fixture claim maps to `AI assistance`, `brainstorming`, `semantic diversity`, `ideation`, and `creativity`.
- Domain metadata includes `creative_phase`, `measured_dimension`, and `track`.
- Creativity fields are in `domain_metadata`, not core-only columns.

Hard checkpoint:

```bash
git tag checkpoint-phase-2-creativity-pack
```

### Phase 3: Local research MVP

Goal:

Run the complete local fixture research flow.

Expected files:

```txt
rge/orchestration/langgraph_app.py
rge/orchestration/state.py
rge/orchestration/nodes.py
rge/modules/research_planner.py
rge/modules/source_discovery.py
rge/modules/research_queue.py
rge/modules/run_evaluator.py
rge/modules/cluster_reporter.py
rge/modules/theory_generator.py
rge/modules/ticket_writer.py
tests/golden/test_08_contract_drift.py
tests/golden/test_11_cluster_reports.py
tests/golden/test_12_theory_candidates.py
tests/golden/test_14_improvement_tickets.py
tests/golden/test_16_e2e_fixture_run.py
```

Acceptance criteria:

- `research run --fixture-mode` completes.
- Research contract is created.
- At least three sources are queued.
- At least two sources are ingested.
- Scoped claims are accepted.
- Bad claims are rejected with reasons.
- Relationships and score events are created.
- Run report is generated.
- Cluster report is generated.
- Candidate theory is generated.
- Improvement ticket is generated from actual failures.

Hard checkpoint:

```bash
git tag checkpoint-phase-3-local-mvp
```

### Phase 4: Public read-only card site/API

Goal:

Export public-safe cards and render them in static Next.js mode.

Expected files:

```txt
rge/modules/card_exporter.py
rge/modules/safety_auditor.py
apps/public-site/public/data/public_cards.json
apps/public-site/public/data/public_memos.json
apps/public-site/public/data/build_info.json
apps/public-site/app/page.tsx
apps/public-site/app/cards/[id]/page.tsx
apps/public-site/app/concepts/[id]/page.tsx
tests/golden/test_09_public_export.py
tests/golden/test_10_public_site_static.py
tests/golden/test_15_safety.py
```

Acceptance criteria:

- `research export-public --limit 100` writes expected JSON files.
- Export has only curated public fields.
- Export excludes private notes, local paths, API keys, full private source text, prompt text, hidden evaluator notes, unsafe HTML.
- Public site builds without local FastAPI or SQLite.
- Public site has no write/ingestion/agent routes.

Hard checkpoint:

```bash
git tag checkpoint-phase-4-public-site
```

### Phase 5: Self-improvement ticket loop

Goal:

Prove the system can generate useful tickets from its own reports and failures.

Expected files:

```txt
rge/modules/run_evaluator.py
rge/modules/ticket_writer.py
rge/modules/ontology_pressure.py
rge/modules/domain_proposer.py
rge/modules/safety_auditor.py
tickets/improvement_ticket_latest.json
tests/golden/test_13_domain_proposals.py
tests/golden/test_14_improvement_tickets.py
tests/golden/test_15_safety.py
```

Acceptance criteria:

- Rejection patterns generate actionable tickets.
- Tickets include all required fields.
- Tickets can be consumed by Cursor/build agents.
- Safety audit blocks dangerous changes.
- Golden tests pass after ticket implementation.

Hard checkpoint:

```bash
git tag checkpoint-phase-5-self-improvement
```

## 9. Required Test Commands Before Reporting Success

For any ticket:

```bash
pytest tests/golden/<relevant_test_file>.py
```

For phase checkpoint:

```bash
pytest tests/golden
research run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
research export-public --limit 100
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

A builder may report partial progress, but may not report completion unless required tests pass or failures are explicitly documented.

## 10. Safety Audit Before Merge

Safety audit is required before merge if the ticket touches:

- Public export.
- Public site.
- Routes/API.
- Prompt templates.
- Source ingestion.
- Model tool permissions.
- Shell/Git integration.
- Secrets/config.

Safety audit must fail on:

```txt
public write endpoints
public source ingestion endpoint
public agent execution endpoint
raw local file paths in public JSON
secrets in public export
shell execution from model output
unsafe raw HTML rendering
direct model access to Git push commands
```

## 11. Merge Checklist

Before human/checkpoint merge:

```txt
[ ] Ticket has one branch.
[ ] Scope matches ticket.
[ ] Acceptance criteria satisfied.
[ ] Test plan run.
[ ] Golden tests relevant to scope pass.
[ ] Full golden suite passes for phase checkpoints.
[ ] Safety audit passes if required.
[ ] Public site builds if public files touched.
[ ] Changed files are listed.
[ ] Remaining risks are listed.
[ ] Rollback plan is still valid.
```

## 12. Rollback Policy

Rollback plan must be ticket-specific.

Examples:

- Revert changed files.
- Restore previous prompt/schema version.
- Re-run migration rollback.
- Restore previous public export schema.
- Disable experimental domain pack.
- Mark proposal as rejected/superseded.

A ticket without rollback plan is not ready for builder implementation.

## 13. Anti-Patterns

Reject tickets or builder changes that:

- Ask to “make it better” without evidence.
- Combine unrelated refactors.
- Bypass validators to improve pass counts.
- Delete rejected claims instead of reporting them.
- Auto-activate new domains from model output.
- Move creativity-specific fields into core schema.
- Add public write routes.
- Add public source ingestion.
- Render raw HTML from public JSON.
- Depend on local FastAPI for static public site.
- Claim success without running tests.
