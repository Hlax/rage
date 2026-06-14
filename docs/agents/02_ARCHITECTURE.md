# ARCHITECTURE.md

## 1. Purpose

The Research Graph Engine (RGE) is a local-first research infrastructure system. It is not a generic chat app, simple RAG wrapper, or summarizer. Its job is to transform sources into a durable, queryable, evidence-backed claim graph that can support research, public cards, memos, dashboards, candidate theories, and improvement tickets.

The core pipeline is:

```txt
source library
→ extracted claims
→ concept graph
→ evidence graph
→ inference engine
→ reports / dashboards / memos / public cards
→ improvement tickets
→ builder loop
```

The first domain pack is `creativity`, focused on human creativity, AI creativity, and human-AI co-creativity. The core engine must remain domain-general. Creativity-specific fields must live in domain pack overlays, `domain_metadata`, templates, scoring overlays, and ontology files, not in hardcoded core tables or core module logic.

## 2. Architectural Principles

1. Use a General Research Graph Engine as the core.
2. Use domain packs for topic-specific ontology, search, scoring, extraction overlays, aliases, and card templates.
3. Start with the `creativity` domain pack.
4. Use Python for the research engine.
5. Use LangGraph as workflow orchestration, not as the intelligence itself. **Status: planned, not implemented** — Phase 1–2 orchestration is CLI step chaining in `rge/cli.py`.
6. Use SQLite first for local durable memory.
7. Treat the database as memory; prompts are not memory.
8. Use a private local FastAPI app for control and inspection. **Status: planned, not implemented.**
9. Use Next.js/Vercel for the public read-only site. **Status: static Next.js export implemented** (no live API).
10. Export static JSON snapshots from the local DB to the public site.
11. Never connect the public site directly to the private local agent.
12. Qwen/Ollama proposes small structured outputs; Python validates and writes.
13. Bigger models through Cursor/API handle hard synthesis and architecture review.
14. Deterministic safety checks decide pass/fail.
15. Research agents propose improvements; builder agents implement them through tickets.

## 3. Local-First System Boundary

### Local private system

The local private system owns:

- Source ingestion.
- Raw source text and chunks.
- Private notes.
- Research contracts.
- Research queues.
- Claims, quote spans, relationships, score events.
- Reports.
- Safety audits.
- Improvement tickets.
- Public export generation.
- Local dashboard and API.

### Public read-only system

The public system owns:

- Static public JSON snapshots.
- Public research cards.
- Public memos if explicitly exported.
- Public concept pages.
- Build metadata.

The public system must not own:

- Source ingestion.
- Agent execution.
- Write routes.
- Private notes.
- Raw prompts.
- Raw source text.
- Local file paths.
- Secrets.
- Unreviewed draft claims unless explicitly marked public-safe.

## 4. Recommended Repo Structure

```txt
research-graph-engine/
  README.md
  pyproject.toml
  .env.example
  .gitignore

  data/
    db/
      creative_research.sqlite
    sources/
      manual/
      fixtures/
    reports/
    exports/
    backups/

  domain_packs/
    creativity/
      domain.yaml
      ontology.yaml
      aliases.yaml
      source_preferences.yaml
      evidence_types.yaml
      scoring.yaml
      claim_schema.yaml
      card_templates.yaml
      search_templates.yaml
      safety_notes.yaml

  rge/
    __init__.py
    cli.py
    config.py
    db/
      connection.py
      migrations/
      schema.sql
      repositories.py
    llm/
      __init__.py
      base.py
      ollama_client.py
      mock_client.py
      schemas.py
      registry.py
    graph/
      graph_analysis.py
      cluster_detection.py
      relationship_queries.py
    models/
      ids.py
      schemas.py
      contracts.py
      reports.py
    orchestration/
      langgraph_app.py
      state.py
      nodes.py
    modules/
      research_planner.py
      source_discovery.py
      candidate_ranker.py
      research_queue.py
      fetcher.py
      parser.py
      claim_extractor.py
      claim_validator.py
      concept_linker.py
      relationship_builder.py
      score_reconciler.py
      card_exporter.py
      run_evaluator.py
      cluster_reporter.py
      theory_generator.py
      ontology_pressure.py
      domain_proposer.py
      ticket_writer.py
      safety_auditor.py
    prompts/
      claim_extraction.md
      concept_linking.md
      cluster_report.md
      theory_candidate.md
      ticket_writer.md
    safety/
      public_export_policy.py
      prompt_injection.py
      route_audit.py
      secrets_audit.py

  apps/
    local-dashboard/
      README.md
    public-site/
      package.json
      next.config.js
      public/
        data/
          public_cards.json
          public_memos.json
          build_info.json
      app/
        page.tsx
        cards/[id]/page.tsx
        concepts/[id]/page.tsx

  fixtures/
    sources/
      creativity_ai_diversity_short.txt
      creativity_ai_diversity_contradiction.txt
      prompt_injection_source.txt
    llm_outputs/
      claim_extraction_valid_and_missing_quote.json
      claim_extraction_overgeneralized.json
    candidate_sources/
      source_ranking_fixture.json

  tests/
    golden/
      test_01_ingestion.py
      test_02_claim_extraction.py
      test_03_claim_validation.py
      test_04_concept_linking.py
      test_05_relationships.py
      test_06_scores.py
      test_07_queue.py
      test_08_contract_drift.py
      test_09_public_export.py
      test_10_public_site_static.py
      test_11_cluster_reports.py
      test_12_theory_candidates.py
      test_13_domain_proposals.py
      test_14_improvement_tickets.py
      test_15_safety.py
      test_16_e2e_fixture_run.py
    unit/
    integration/

  tickets/
    improvement_ticket_latest.json
    archive/
```

## 5. Required Core Modules

The MVP must include these modules as implementation boundaries. A module can start small, but it must have a clear contract, inputs, outputs, and reports.

| Module | Responsibility | Deterministic? | Model use allowed? |
|---|---|---:|---:|
| `research_planner.py` | Create research contracts and run plans | Mixed | Yes |
| `source_discovery.py` | Find candidate sources from manual fixtures/search APIs | Mixed | Yes |
| `candidate_ranker.py` | Rank sources by relevance, quality, gap value, drift risk | Mostly yes | Optional |
| `research_queue.py` | Queue candidate sources and follow-ups | Yes | No |
| `fetcher.py` | Fetch local files, URLs, PDFs, metadata | Yes | No |
| `parser.py` | Parse text/PDF/HTML into chunks | Yes | No |
| `claim_extractor.py` | Produce structured candidate claims from chunks | No | Yes |
| `claim_validator.py` | Validate claim fields, quote spans, scope, injection safety | Yes | No |
| `concept_linker.py` | Link claims to concepts and domain metadata | Mixed | Yes, validated |
| `relationship_builder.py` | Build support/contradict/qualify edges | Mixed | Yes, validated |
| `score_reconciler.py` | Update confidence and write score events | Yes | No |
| `card_exporter.py` | Create public-safe card JSON | Yes | No |
| `run_evaluator.py` | Build run reports and failure summaries | Mostly yes | Optional |
| `cluster_reporter.py` | Build evidence packets and cluster reports | Mixed | Yes |
| `theory_generator.py` | Generate candidate theories from evidence packets | Mixed | Yes |
| `ontology_pressure.py` | Detect concept/domain pressure | Mixed | Yes, validated |
| `domain_proposer.py` | Draft domain proposals when thresholds are met | Mixed | Yes, validated |
| `ticket_writer.py` | Create implementation tickets from actual failures | Mixed | Yes, validated |
| `safety_auditor.py` | Run deterministic safety checks | Yes | No |

## 6. LangGraph Node Layout

> **Implementation status (2026-06-14):** LangGraph is **not present in the repo**.
> MVP orchestration is `execute_fixture_mode_run()` and discrete CLI commands in
> `rge/cli.py`. The layout below is the target design, not current code.

LangGraph is the workflow/state machine. It should route state through deterministic and model-assisted nodes.

### MVP graph

```txt
Start
→ CreateResearchContract
→ DiscoverCandidateSources
→ RankCandidateSources
→ QueueSources
→ FetchNextSource
→ ParseSource
→ ExtractCandidateClaims
→ ValidateClaims
→ LinkConcepts
→ BuildRelationships
→ ReconcileScores
→ EvaluateRun
→ MaybeClusterReport
→ MaybeTheoryCandidate
→ ExportPublicCards
→ SafetyAudit
→ GenerateImprovementTickets
→ End
```

### Node rules

- Every node must emit a `node_report`.
- Every node must record input IDs and output IDs.
- Model-assisted nodes must stage outputs before acceptance.
- Deterministic validators must run before DB writes to accepted graph tables.
- Node failure must produce structured failure records, not just logs.
- A run can complete with partial success if failures are recorded and ticketed.

### State object minimum

```json
{
  "run_id": "run_...",
  "contract_id": "contract_...",
  "domain_pack": "creativity",
  "active_question_id": "rq_...",
  "candidate_source_ids": [],
  "queue_item_ids": [],
  "source_ids": [],
  "chunk_ids": [],
  "candidate_claim_ids": [],
  "accepted_claim_ids": [],
  "rejected_claim_ids": [],
  "relationship_ids": [],
  "score_event_ids": [],
  "report_ids": [],
  "public_export_id": null,
  "ticket_ids": [],
  "safety_audit_id": null,
  "errors": []
}
```

## 7. Local Model Runtime: Ollama/Qwen

The MVP must include a formal local model runtime boundary. Qwen should not be custom-built inside the repository. The repository must not contain model weights or implement inference itself. Ollama runs Qwen as a separate local model service, and the Python research engine calls that service through a thin adapter layer.

Runtime shape:

```txt
Ollama/Qwen = local model runtime
Python repo = research engine
LangGraph = workflow orchestration
SQLite = durable memory
```

Default MVP configuration:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
RGE_LOCAL_LLM=qwen2.5:7b
RGE_LLM_MODE=ollama
RGE_TEST_LLM_MODE=mock
RGE_LLM_TIMEOUT_SECONDS=60
RGE_LLM_TEMPERATURE=0
RGE_LLM_SCHEMA_VERSION=0.1.0
```

Formal adapter package:

```txt
rge/
  llm/
    __init__.py
    base.py
    ollama_client.py
    mock_client.py
    schemas.py
    registry.py
```

Adapter responsibilities:

- `base.py` defines the model-client interface and shared request/response envelopes.
- `ollama_client.py` calls local Ollama, sends prompt + JSON schema, parses JSON, and returns typed candidate objects.
- `mock_client.py` returns deterministic fixture outputs for golden tests.
- `schemas.py` defines versioned Pydantic schemas for model outputs.
- `registry.py` chooses `mock` or `ollama` mode from config.

LangGraph node behavior:

```txt
ExtractCandidateClaims node
→ rge.modules.claim_extractor.extract_candidate_claims(...)
→ rge.llm.registry.get_model_client(...)
→ OllamaModelClient or MockModelClient
→ CandidateClaimBatch schema validation
→ claim_validator.py validates quote spans / scope / source IDs
→ Python writes staged / accepted / rejected claims
→ node_report emitted
```

Qwen/Ollama may power early candidate-generation tasks:

```txt
research_planner.py        query drafts / contract draft suggestions
claim_extractor.py         candidate claim JSON
concept_linker.py          proposed concept links
relationship_builder.py    proposed relationship drafts
run_evaluator.py           small run summary draft
ticket_writer.py           first-pass ticket wording
```

Qwen/Ollama must not directly handle:

```txt
DB writes
source fetching
browser actions
file deletes
Git commands
public export approval
safety pass/fail
domain activation
score changes without score_events
accepted graph mutation
shell commands
route creation
secret handling
```

Golden tests must run without a live model. `RGE_LLM_MODE=mock` must force deterministic fixture responses so `pytest tests/golden` does not depend on Ollama availability, model phrasing, or model-version drift.

Every model output schema must be versioned. Model-assisted node reports must include provider, model name, LLM mode, task name, schema version, and prompt template version. Raw model responses must never be public-exported.

See `MODEL_RUNTIME_SPEC.md` for the full adapter contract.

## 8. Model and Tool Responsibilities

### Qwen/Ollama local

Use for:

- Query drafts.
- Chunk summaries.
- Claim extraction.
- Concept tagging.
- Limitation extraction.
- Card drafts.
- Small run summaries.
- First-pass ticket drafting.

Rules:

- Qwen/Ollama output is never trusted until parsed and validated.
- Qwen/Ollama must not call shell tools directly.
- Qwen/Ollama must not write accepted records directly.

### Python deterministic code

Use for:

- Fetching and parsing.
- Queue management.
- Scoring formulas.
- Schema validation.
- Deduplication.
- Drift scoring.
- DB writes.
- Public export filtering.
- Graph analysis.
- Report packet construction.
- Safety checks.

Rules:

- Python is the only layer allowed to write to accepted graph tables.
- Python validators decide pass/fail.
- Python creates durable reports.

### Embedding model

Use for:

- Similarity.
- Drift detection.
- Duplicate detection.
- Cluster membership.
- Evidence retrieval.
- Claim/source similarity.

Rules:

- Embedding similarity is a signal, not a final decision.
- Store model name/version for reproducibility.

### Bigger model via Cursor/API

Use for:

- Cluster report synthesis.
- Candidate theory generation.
- Ontology pressure review.
- Domain proposal review.
- Build-ticket refinement.
- Architecture review.
- Weekly/monthly synthesis.

Rules:

- Bigger model outputs are stored as reports, proposals, candidates, or tickets.
- Bigger model cannot activate domains or merge code.
- Bigger model cannot bypass safety audit.

## 9. Local App vs Public Site

### Local FastAPI app

> **Implementation status (2026-06-14):** No FastAPI app exists. Use `python -m rge.cli`
> and operator modules instead.

MVP local routes may include:

```txt
POST /local/runs
POST /local/sources
POST /local/queue/advance
GET  /local/runs/{id}
GET  /local/reports/{id}
GET  /local/claims?status=staged
POST /local/claims/{id}/accept
POST /local/claims/{id}/reject
POST /local/exports/public
GET  /local/safety-audits/{id}
```

Requirements:

- Local-only bind by default: `127.0.0.1`.
- No public exposure by default.
- Optional auth later.
- All write routes are private/local only.

### Public Next.js site

MVP pages:

```txt
/                         public card list
/cards/[id]                card detail
/concepts/[id]             public concept page
/about                     explanation + last updated
```

MVP data files:

```txt
apps/public-site/public/data/public_cards.json
apps/public-site/public/data/public_memos.json
apps/public-site/public/data/build_info.json
```

Requirements:

- Must build without local FastAPI.
- Must build without local SQLite.
- Must render only static JSON.
- Must not include public write routes.

## 10. Static JSON Export Flow

```txt
Local SQLite
→ card_exporter selects accepted/public-safe records
→ safety_auditor checks export payload
→ writes data/exports/*.json
→ copies files into apps/public-site/public/data/*.json
→ public site static build reads JSON
→ GitHub/Vercel deploys read-only site
```

Export must fail closed. If any unsafe field is detected, no public export should be marked successful.

## 11. Build Phases

### Phase 0: Repo scaffold

Scope:

- Repo structure.
- Python package.
- SQLite schema stub.
- CLI stub.
- Fixture directories.
- Public site stub.
- Golden test placeholders.

Exit criteria:

- `pytest` runs.
- `research --help` runs.
- `cd apps/public-site && npm run build` runs with fixture JSON.

### Phase 1: General research graph engine

Scope:

- SQLite schema.
- Source ingestion.
- Chunking.
- Claim staging/validation.
- Concept and relationship tables.
- Score events.

Exit criteria:

- Golden tests for ingestion, claim validation, concept linking, relationship building, score history pass.

### Phase 2: Creativity domain pack

Scope:

- Creativity ontology.
- Aliases.
- Source preferences.
- Scoring overlays.
- Card templates.
- Search templates.
- Domain metadata mapping.

Exit criteria:

- Creativity-specific concept linking and metadata tests pass.

### Phase 3: Local research MVP

Scope:

- LangGraph run.
- Research contract.
- Queue.
- Fixture-mode run.
- Reports.
- Cluster report.
- Candidate theory.
- Improvement ticket generation.

Exit criteria:

- `research run --fixture-mode` completes.
- Run report, cluster report, candidate theory, and ticket exist.

### Phase 4: Public read-only card site/API

Scope:

- Public card export.
- Static site rendering.
- Public JSON validation.
- Optional read-only API route if safe.

Exit criteria:

- `research export-public --limit 100` validates.
- `npm run build` works without local API/DB.

### Phase 5: Self-improvement ticket loop

Scope:

- Run evaluator.
- Failure pattern detection.
- Ticket writer.
- Cursor build loop docs.
- Safety audit before merge.

Exit criteria:

- At least one useful improvement ticket generated from real run reports.
- Golden tests still pass after implementing a ticket.

## 12. MVP Scope

In scope:

- Manual/fixture source ingestion.
- Local file text parsing.
- Basic URL/PDF support if easy, but fixtures are enough for MVP proof.
- Atomic scoped claim extraction.
- Claim validation with rejection reasons.
- Concept linking through creativity domain pack.
- Support/contradict/qualify relationships.
- Score reconciliation with score event history.
- Research contracts and drift controls.
- Research queue with priority scoring.
- JSON-first node/run/cluster/safety reports.
- Candidate theories stored as candidates, not facts.
- Public-safe card export.
- Static Next.js public site.
- Improvement tickets from actual failures.
- Deterministic safety audit.

Out of scope for MVP:

- Fully autonomous web crawler.
- Public source ingestion.
- Public agent execution.
- Public write API.
- Model-controlled shell access.
- Model-controlled Git push.
- Automatic domain activation.
- Broad dashboard polish.
- Full graph visualization.
- Multi-user auth.
- Cloud DB migration.
- Large-scale scraping.
- Agentic code self-modification.

## 13. Recommended Defaults and Later Alternatives

| Decision | MVP default | Later alternative |
|---|---|---|
| DB | SQLite | Postgres/Supabase/Cloud SQL |
| Graph | Relational edge tables + NetworkX | Kùzu/Neo4j |
| Public site | Static Next.js JSON | Read-only public API |
| Source discovery | Fixture/manual + simple APIs | Browser fallback/crawler |
| Extraction model | Qwen through Ollama adapter | API provider adapter for difficult chunks |
| Synthesis | Cursor/API bigger model | Local larger model if hardware allows |
| Deployment | Local + Vercel static | Cloud worker fleet |
