# DATA_MODEL.md

## 1. Purpose

The data model defines the durable memory of the Research Graph Engine. The database must preserve sources, chunks, claims, quotes, concepts, relationships, reports, public exports, safety audits, and improvement tickets. The MVP uses SQLite first.

The schema must support:

- Atomic scoped claims with provenance.
- Staged and rejected claims, not only accepted claims.
- Concept graph and domain overlays.
- Evidence relationships with support, contradiction, and qualification.
- Score history through append-only score events.
- Research contracts and queue execution.
- JSON-first reports.
- Public-safe card exports.
- Improvement tickets that builder agents can consume.
- Versioned model outputs and runtime metadata for reproducible extraction tests.

## 2. SQLite Conventions

Recommended conventions:

- Use `TEXT` stable IDs with prefixes: `src_`, `chk_`, `clm_`, `cpt_`, `rel_`, `run_`, `rep_`, `card_`, `ticket_`.
- Use ISO-8601 UTC timestamps as `TEXT`.
- Use JSON columns as `TEXT` containing validated JSON.
- Use `REAL` for scores in `0.0–1.0`.
- Use lookup constraints for statuses and statement types where practical.
- Use migrations from the start.
- Never rely on prompt context as memory; write durable state to SQLite.

## 3. Entity Overview

```txt
sources
  → chunks
    → claims
      → claim_quotes
      → claim_concepts
        → concepts
          → concept_aliases
      → relationship_evidence
        → relationships
          → score_events

research_contracts
  → research_questions
  → candidate_sources
  → research_queue
  → research_runs
    → node_reports
    → run_reports
    → cluster_reports
    → theory_candidates
    → ontology_proposals
    → domain_proposals
    → improvement_tickets
    → safety_audits

cards
  → public_exports

memos
  → public_exports if public-safe
```

## 4. Tables

### 4.1 `sources`

Stores source-level metadata and ingestion state.

Required columns:

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable source ID |
| `title` | TEXT | Title or filename |
| `authors_json` | TEXT | JSON array |
| `year` | INTEGER | Nullable |
| `source_type` | TEXT | `paper`, `book`, `essay`, `interview`, `transcript`, `webpage`, `manual_note`, `fixture`, etc. |
| `domain` | TEXT | Primary domain ID |
| `domain_metadata_json` | TEXT | Domain overlay data |
| `url` | TEXT | Nullable |
| `local_path` | TEXT | Private; never public-export |
| `publisher` | TEXT | Nullable |
| `abstract` | TEXT | Nullable |
| `raw_text_checksum` | TEXT | Required after ingest |
| `quality_score` | REAL | Derived/source prior |
| `credibility_notes` | TEXT | Private/internal by default |
| `status` | TEXT | `candidate`, `ingested`, `parsed`, `failed`, `archived` |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

Indexes:

- `idx_sources_domain_status(domain, status)`
- `idx_sources_checksum(raw_text_checksum)`

### 4.2 `chunks`

Stores parsed source text chunks.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable chunk ID |
| `source_id` | TEXT FK | `sources.id` |
| `chunk_index` | INTEGER | Ordered within source |
| `chunk_text` | TEXT | Private raw chunk text |
| `page` | TEXT | PDF page or range |
| `section` | TEXT | Section label |
| `token_count` | INTEGER | Approximate |
| `embedding_id` | TEXT | Optional reference |
| `embedding_model` | TEXT | Nullable |
| `text_checksum` | TEXT | Deduplication |
| `created_at` | TEXT | Required |

Indexes:

- `idx_chunks_source(source_id)`
- `idx_chunks_checksum(text_checksum)`

### 4.3 `claims`

Stores atomic claims in draft, staged, accepted, or rejected state.

Required columns:

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable claim ID |
| `source_id` | TEXT FK | Required except allowed `user_note` edge cases |
| `chunk_id` | TEXT FK | Required for source-backed claims |
| `claim_text` | TEXT | Atomic scoped claim |
| `statement_type` | TEXT | `observation`, `source_claim`, `agent_inference`, `user_note`, `hypothesis` |
| `subject` | TEXT | Structured subject |
| `predicate` | TEXT | Structured predicate |
| `object` | TEXT | Structured object |
| `scope` | TEXT | Required for accepted source claims |
| `evidence_type` | TEXT | `empirical`, `meta_analysis`, `case_study`, `theory`, `interview`, `benchmark`, etc. |
| `confidence` | REAL | Derived/staged claim confidence |
| `limitations_json` | TEXT | JSON array |
| `domain` | TEXT | Primary domain |
| `domain_metadata_json` | TEXT | Domain overlay data |
| `status` | TEXT | `draft`, `staged`, `accepted`, `rejected` |
| `rejection_reason` | TEXT | Required when rejected |
| `rejection_details_json` | TEXT | Optional structured details |
| `extractor_model` | TEXT | Model/version that proposed it |
| `extractor_provider` | TEXT | `mock`, `ollama`, or later provider name |
| `llm_schema_version` | TEXT | Versioned output schema used for candidate extraction |
| `prompt_template_version` | TEXT | Prompt template version used for candidate extraction |
| `validator_version` | TEXT | Validator version |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

Statement types:

```txt
observation
source_claim
agent_inference
user_note
hypothesis
```

Claim statuses:

```txt
draft
staged
accepted
rejected
```

Common rejection reasons:

```txt
missing_quote_span
overgeneralized_scope
unsupported_claim
invalid_json
weak_concept_mapping
missing_source_id
unsafe_or_injected_content
```

Indexes:

- `idx_claims_status_domain(status, domain)`
- `idx_claims_source(source_id)`
- `idx_claims_chunk(chunk_id)`
- `idx_claims_statement_type(statement_type)`

### 4.4 `claim_quotes`

Stores quote spans/provenance for accepted or staged source-backed claims.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable quote ID |
| `claim_id` | TEXT FK | `claims.id` |
| `source_id` | TEXT FK | Redundant for query speed |
| `chunk_id` | TEXT FK | Redundant for query speed |
| `quote_text` | TEXT | Minimal quote span; not full source text |
| `char_start` | INTEGER | Nullable if parser lacks offsets |
| `char_end` | INTEGER | Nullable if parser lacks offsets |
| `page` | TEXT | Nullable |
| `is_primary` | INTEGER | 0/1 |
| `created_at` | TEXT | Required |

Validation rule: no source-backed claim may be accepted without at least one primary quote span.

### 4.5 `concepts`

Stores reusable concept nodes.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable concept ID |
| `label` | TEXT | Canonical label |
| `definition` | TEXT | Required for active concepts |
| `domain` | TEXT | Primary domain or `general` |
| `domain_metadata_json` | TEXT | Domain overlay data |
| `status` | TEXT | `candidate`, `draft`, `experimental`, `active`, `deprecated`, `merged` |
| `parent_concept_id` | TEXT | Optional graph/tree parent |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

Indexes:

- `idx_concepts_domain_status(domain, status)`
- Unique index on normalized label per domain where possible.

### 4.6 `concept_aliases`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable alias ID |
| `concept_id` | TEXT FK | `concepts.id` |
| `alias` | TEXT | Alias phrase |
| `source` | TEXT | `domain_pack`, `model_proposed`, `human_added` |
| `status` | TEXT | `active`, `draft`, `deprecated` |
| `created_at` | TEXT | Required |

### 4.7 `claim_concepts`

Many-to-many join between claims and concepts.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable link ID |
| `claim_id` | TEXT FK | `claims.id` |
| `concept_id` | TEXT FK | `concepts.id` |
| `role` | TEXT | `subject`, `object`, `context`, `method`, `metric`, `limitation`, `domain`, `bridge` |
| `confidence` | REAL | Link confidence |
| `domain_metadata_json` | TEXT | Domain overlay metadata |
| `created_at` | TEXT | Required |

Unique constraint:

- `(claim_id, concept_id, role)`

### 4.8 `relationships`

Stores graph edges between concepts or claim-derived entities.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable relationship ID |
| `subject_concept_id` | TEXT FK | Required |
| `predicate` | TEXT | `may_increase`, `may_reduce`, `supports`, `contradicts`, `depends_on`, etc. |
| `object_concept_id` | TEXT FK | Required |
| `scope` | TEXT | Relationship scope/boundary condition |
| `confidence` | REAL | Derived confidence |
| `evidence_strength` | REAL | Derived evidence score |
| `domain` | TEXT | Primary domain |
| `domain_metadata_json` | TEXT | Domain overlay data |
| `status` | TEXT | `draft`, `active`, `deprecated` |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

Indexes:

- `idx_relationships_subject(subject_concept_id)`
- `idx_relationships_object(object_concept_id)`
- `idx_relationships_domain(domain)`

### 4.9 `relationship_evidence`

Links relationships to claims with stance.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable evidence link ID |
| `relationship_id` | TEXT FK | `relationships.id` |
| `claim_id` | TEXT FK | `claims.id` |
| `stance` | TEXT | `supports`, `contradicts`, `qualifies` |
| `relevance_score` | REAL | Claim relevance to edge |
| `created_at` | TEXT | Required |

Unique constraint:

- `(relationship_id, claim_id, stance)`

### 4.10 `research_questions`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable question ID |
| `question_text` | TEXT | Required |
| `root_topic` | TEXT | Required |
| `domain` | TEXT | Primary domain |
| `status` | TEXT | `active`, `parked`, `answered`, `deprecated` |
| `priority` | REAL | Queue priority |
| `topic_fit` | REAL | Contract fit |
| `evidence_fit` | REAL | Evidence fit |
| `drift_risk` | REAL | Drift risk |
| `reason` | TEXT | Active/parked reason |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.11 `research_contracts`

Stores run-scoping contracts.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable contract ID |
| `root_topic` | TEXT | Required |
| `primary_question` | TEXT | Required |
| `domain_pack` | TEXT | Required |
| `allowed_concepts_json` | TEXT | JSON array |
| `adjacent_concepts_json` | TEXT | JSON array |
| `out_of_scope_concepts_json` | TEXT | JSON array |
| `source_budget` | INTEGER | Required |
| `search_budget` | INTEGER | Required |
| `follow_up_depth` | INTEGER | Required |
| `drift_threshold` | REAL | Default `0.35` |
| `success_criteria_json` | TEXT | JSON array |
| `source_strategy_json` | TEXT | JSON object |
| `evidence_requirements_json` | TEXT | JSON object |
| `queue_priority_formula` | TEXT | Formula version/name |
| `topic_drift_formula` | TEXT | Formula version/name |
| `status` | TEXT | `draft`, `active`, `completed`, `failed` |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.12 `candidate_sources`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable candidate ID |
| `research_question_id` | TEXT FK | Required |
| `contract_id` | TEXT FK | Required |
| `title` | TEXT | Required |
| `url` | TEXT | Nullable for fixtures/manual |
| `source_type` | TEXT | Required |
| `reason` | TEXT | Required |
| `relevance_score` | REAL | Required |
| `credibility_prior` | REAL | Required |
| `gap_fill_score` | REAL | Required |
| `recency_score` | REAL | Required |
| `source_diversity_score` | REAL | Required |
| `novelty_score` | REAL | Required |
| `drift_risk` | REAL | Required |
| `priority_score` | REAL | Required |
| `status` | TEXT | `candidate`, `queued`, `rejected`, `parked`, `ingested` |
| `created_at` | TEXT | Required |

### 4.13 `research_queue`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable queue item ID |
| `candidate_source_id` | TEXT FK | Nullable for follow-up questions |
| `research_question_id` | TEXT FK | Required |
| `contract_id` | TEXT FK | Required |
| `item_type` | TEXT | `source`, `question`, `cluster_review`, `manual_review` |
| `priority_score` | REAL | Required |
| `reason` | TEXT | Required |
| `status` | TEXT | Required queue status |
| `attempt_count` | INTEGER | Default `0` |
| `last_error` | TEXT | Nullable |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

Queue statuses:

```txt
queued
fetching
fetched
parsing
extracting
staged
accepted
rejected
failed
needs_manual_review
parked
```

### 4.14 `search_runs`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable search run ID |
| `contract_id` | TEXT FK | Required |
| `query` | TEXT | Required |
| `provider` | TEXT | `fixture`, `manual`, `brave`, `semantic_scholar`, etc. |
| `result_count` | INTEGER | Required |
| `candidate_source_ids_json` | TEXT | JSON array |
| `status` | TEXT | `completed`, `failed` |
| `error` | TEXT | Nullable |
| `created_at` | TEXT | Required |

### 4.15 `research_runs`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable run ID |
| `contract_id` | TEXT FK | Required |
| `topic` | TEXT | Required |
| `domain_pack` | TEXT | Required |
| `mode` | TEXT | `fixture`, `manual`, `live` |
| `status` | TEXT | `running`, `completed`, `completed_with_failures`, `failed` |
| `started_at` | TEXT | Required |
| `finished_at` | TEXT | Nullable |
| `summary_json` | TEXT | Machine-readable summary |

### 4.16 `node_reports`

JSON-first report emitted by each workflow node.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable node report ID |
| `run_id` | TEXT FK | Required |
| `node_name` | TEXT | Required |
| `status` | TEXT | `pass`, `fail`, `partial`, `skipped` |
| `input_ids_json` | TEXT | JSON object |
| `output_ids_json` | TEXT | JSON object |
| `metrics_json` | TEXT | JSON object |
| `model_runtime_json` | TEXT | JSON object with provider/model/schema/prompt metadata for model-assisted nodes |
| `errors_json` | TEXT | JSON array |
| `created_at` | TEXT | Required |

### 4.17 `run_reports`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable run report ID |
| `run_id` | TEXT FK | Required |
| `topic` | TEXT | Required |
| `domain_pack` | TEXT | Required |
| `report_json` | TEXT | Canonical JSON report |
| `prose_summary` | TEXT | Optional human-readable summary |
| `created_at` | TEXT | Required |

Minimum report fields:

```json
{
  "run_id": "...",
  "topic": "...",
  "domain_pack": "...",
  "sources_discovered": 0,
  "sources_ingested": 0,
  "claims_extracted": 0,
  "claims_accepted": 0,
  "claims_rejected": 0,
  "relationships_updated": 0,
  "score_events_created": 0,
  "cards_exported": 0,
  "top_failure_modes": [],
  "tickets_generated": 0
}
```

### 4.18 `cluster_reports`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable cluster report ID |
| `run_id` | TEXT FK | Nullable if periodic report |
| `cluster_label` | TEXT | Required |
| `included_concepts_json` | TEXT | JSON array |
| `evidence_packet_json` | TEXT | Required |
| `report_json` | TEXT | Required |
| `prose_summary` | TEXT | Optional |
| `created_at` | TEXT | Required |

Evidence packet fields:

```json
{
  "top_supporting_claims": [],
  "top_contradicting_claims": [],
  "top_qualifying_claims": [],
  "highest_quality_sources": [],
  "newest_claims": [],
  "highest_score_change_events": [],
  "bridge_concepts": [],
  "open_gaps": []
}
```

### 4.19 `score_events`

Append-only score change history.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable score event ID |
| `entity_type` | TEXT | `claim`, `relationship`, `source`, `theory_candidate`, etc. |
| `entity_id` | TEXT | Required |
| `old_score` | REAL | Required |
| `new_score` | REAL | Required |
| `triggering_claim_id` | TEXT | Nullable |
| `triggering_source_id` | TEXT | Nullable |
| `reason` | TEXT | Required |
| `formula_version` | TEXT | Required |
| `created_at` | TEXT | Required |

Rules:

- Scores may not change without score events.
- Old score must be preserved.
- Reason must be machine-readable enough for reports.

### 4.20 `cards`

Internal card records before public export.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable card ID |
| `type` | TEXT | `claim_card`, `concept_card`, `cluster_card`, `theory_card`, `memo_card` |
| `title` | TEXT | Required |
| `summary` | TEXT | Required |
| `confidence` | TEXT | Public-friendly confidence label |
| `concepts_json` | TEXT | JSON array |
| `source_count` | INTEGER | Required |
| `claim_ids_json` | TEXT | JSON array |
| `public_detail_level` | TEXT | `summary`, `standard`, `detailed` |
| `is_public_safe` | INTEGER | 0/1 |
| `private_fields_json` | TEXT | Internal only, never export |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.21 `memos`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable memo ID |
| `run_id` | TEXT FK | Nullable |
| `title` | TEXT | Required |
| `memo_type` | TEXT | `run_memo`, `cluster_memo`, `public_memo`, `private_note` |
| `body_markdown` | TEXT | Required |
| `claim_ids_json` | TEXT | JSON array |
| `source_ids_json` | TEXT | JSON array |
| `is_public_safe` | INTEGER | 0/1 |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.22 `theory_candidates`

Theories are candidates, not facts.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable theory ID |
| `run_id` | TEXT FK | Nullable |
| `cluster_report_id` | TEXT FK | Nullable |
| `theory_text` | TEXT | Required |
| `confidence` | TEXT | `low`, `medium`, `high` |
| `supporting_claims_json` | TEXT | JSON array |
| `contradicting_or_qualifying_claims_json` | TEXT | JSON array |
| `boundary_conditions_json` | TEXT | JSON array |
| `weakening_evidence_json` | TEXT | JSON array |
| `next_questions_json` | TEXT | JSON array |
| `status` | TEXT | `candidate`, `under_review`, `rejected`, `superseded` |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.23 `ontology_proposals`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable proposal ID |
| `proposal_type` | TEXT | `promote_concept`, `merge_aliases`, `deprecate_concept`, `add_relationship` |
| `candidate_concept` | TEXT | Nullable |
| `status` | TEXT | `draft`, `accepted`, `rejected`, `implemented` |
| `evidence_claims_json` | TEXT | JSON array |
| `reason` | TEXT | Required |
| `proposal_json` | TEXT | Required |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.24 `domain_proposals`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable proposal ID |
| `domain_id` | TEXT | Proposed domain ID |
| `status` | TEXT | `candidate`, `draft`, `experimental`, `active`, `deprecated`, `merged` |
| `parent_domains_json` | TEXT | JSON array |
| `overlap_domains_json` | TEXT | JSON array |
| `specialized_terms_json` | TEXT | JSON array |
| `scoring_overlay_proposals_json` | TEXT | JSON array |
| `evidence_claims_json` | TEXT | JSON array |
| `threshold_report_json` | TEXT | Must prove threshold status |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

Domain proposal thresholds:

```txt
40 accepted claims
8 independent sources
15 recurring specialized terms
3 repeated extraction/scoring mismatch signals
clear reason parent domain is underspecified
```

### 4.25 `improvement_tickets`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable ticket ID |
| `run_id` | TEXT FK | Nullable |
| `priority` | TEXT | `low`, `medium`, `high`, `critical` |
| `title` | TEXT | Required |
| `problem` | TEXT | Required |
| `evidence_json` | TEXT | Required |
| `affected_modules_json` | TEXT | Required |
| `expected_files_json` | TEXT | Required |
| `acceptance_criteria_json` | TEXT | Required |
| `test_plan_json` | TEXT | Required |
| `non_goals_json` | TEXT | Required |
| `risk_level` | TEXT | Required |
| `rollback_plan` | TEXT | Required |
| `status` | TEXT | `draft`, `ready`, `in_progress`, `implemented`, `rejected` |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.26 `public_exports`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable export ID |
| `export_type` | TEXT | `cards`, `memos`, `build_info`, `full_public_snapshot` |
| `file_path` | TEXT | Private local path to export artifact |
| `record_count` | INTEGER | Required |
| `schema_version` | TEXT | Required |
| `safety_audit_id` | TEXT FK | Required before success |
| `status` | TEXT | `created`, `validated`, `failed`, `published` |
| `checksum` | TEXT | Required |
| `created_at` | TEXT | Required |

### 4.27 `domain_packs`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | `creativity`, etc. |
| `name` | TEXT | Required |
| `version` | TEXT | Required |
| `status` | TEXT | `draft`, `active`, `deprecated` |
| `root_path` | TEXT | Local path |
| `config_json` | TEXT | Loaded/validated domain config snapshot |
| `created_at` | TEXT | Required |
| `updated_at` | TEXT | Required |

### 4.28 `model_invocations`

Stores private runtime metadata for model-assisted tasks. This table is local/private and must never be public-exported.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable invocation ID |
| `run_id` | TEXT FK | Nullable |
| `node_report_id` | TEXT FK | Nullable |
| `task_name` | TEXT | `claim_extraction`, `concept_linking`, `relationship_drafting`, etc. |
| `llm_mode` | TEXT | `mock`, `ollama`, later provider modes |
| `provider` | TEXT | `mock`, `ollama`, etc. |
| `model_name` | TEXT | `qwen2.5:7b`, `mock`, etc. |
| `base_url` | TEXT | Private local URL when applicable |
| `schema_version` | TEXT | Versioned output schema |
| `prompt_template_version` | TEXT | Versioned prompt template |
| `request_checksum` | TEXT | Hash of private prompt/request payload |
| `response_checksum` | TEXT | Hash of private model response payload |
| `status` | TEXT | `completed`, `failed`, `invalid_json`, `schema_invalid` |
| `error` | TEXT | Nullable |
| `created_at` | TEXT | Required |

Rules:

- Store checksums/metadata by default, not raw prompts or full raw responses.
- Raw responses may be stored only in private diagnostics if explicitly enabled.
- Public export must exclude this table entirely.
- Golden tests should use `llm_mode = mock`.

### 4.29 `safety_audits`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Stable audit ID |
| `run_id` | TEXT FK | Nullable |
| `audit_type` | TEXT | `public_export`, `route_permissions`, `prompt_injection`, `secrets`, `full` |
| `status` | TEXT | `pass`, `fail` |
| `blocked_reasons_json` | TEXT | JSON array |
| `checked_routes_json` | TEXT | JSON array |
| `checked_exports_json` | TEXT | JSON array |
| `checked_secrets_json` | TEXT | JSON array |
| `report_json` | TEXT | Required |
| `created_at` | TEXT | Required |

## 5. Public Export Schema

Public cards may include only curated public fields:

```json
{
  "id": "card_...",
  "type": "cluster_card",
  "title": "AI assistance and semantic diversity",
  "summary": "Evidence suggests AI-assisted brainstorming may improve average idea quality while reducing semantic diversity in some short-form writing tasks.",
  "confidence": "medium",
  "concepts": ["AI assistance", "semantic diversity", "ideation"],
  "source_count": 3,
  "public_caveats": ["Most evidence is from short-form writing tasks."],
  "public_source_metadata": [
    {"title": "...", "year": 2026, "source_type": "fixture"}
  ],
  "related_cards": [],
  "public_detail_level": "standard",
  "updated_at": "2026-06-11T00:00:00Z"
}
```

Public cards must not include:

```txt
raw private notes
local file paths
API keys
full private source text
prompt text
hidden evaluator notes
unsafe raw HTML/script content
unreviewed draft claims unless marked public-safe
```

## 6. Core Validation Rules

### Claims

A source-backed claim can be accepted only if:

- It has `source_id`.
- It has `chunk_id`.
- It has at least one primary `claim_quotes` row.
- It is atomic enough to map to subject/predicate/object.
- It preserves scope.
- It has evidence type.
- It has limitations, even if `[]`.
- It has a primary domain.
- It passes injection sanitation.

### Relationships

A relationship can be active only if:

- It has subject and object concept IDs.
- It has at least one evidence link.
- Each evidence link has stance.
- It has confidence and scope.

### Scores

A score can change only if:

- A score event is written.
- The old score is preserved.
- The triggering claim/source is recorded when available.
- The formula version is recorded.

### Model outputs

A model output can influence staged records only if:

- It was produced through `rge/llm` adapter layer.
- It declares `task_name` and `schema_version`.
- Its schema version matches the parser/validator expected version.
- Its prompt template version is recorded.
- Its provider/model/mode metadata is recorded in node reports or `model_invocations`.
- It passes JSON parsing and Pydantic validation.
- It is then checked by deterministic domain, quote-span, scope, and safety validators.

### Public export

A public export can be validated only if:

- All records match public schema.
- No forbidden fields are present.
- No raw HTML/script content is emitted.
- No local paths or secrets are present.
- Safety audit status is `pass`.
