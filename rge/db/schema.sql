-- Research Graph Engine: SQLite schema PLACEHOLDER (Phase 0).
--
-- This file sketches the durable data model from docs/agents/05_DATA_MODEL.md
-- so the scaffold reflects the future shape. It is NOT applied by any code in
-- Phase 0 and intentionally omits the full column set, indexes, and the
-- migration harness (later tickets).
--
-- Conventions (05_DATA_MODEL.md section 2):
--   TEXT stable IDs with prefixes (src_, chk_, clm_, cpt_, rel_, run_, rep_,
--   card_, ticket_), ISO-8601 UTC TEXT timestamps, JSON-as-TEXT columns,
--   REAL scores in 0.0-1.0.
--
-- Note: 05_DATA_MODEL.md models claim lifecycle as a single `claims` table
-- with a status column. Phase 0 stages the lifecycle as explicit placeholder
-- tables (claims_staged / claims_accepted / claim_rejections) per ticket-001;
-- the Phase 1 schema ticket reconciles the two representations.

-- Source library -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,                -- src_...
    title TEXT,
    source_type TEXT,                   -- paper, webpage, fixture, manual_note, ...
    domain TEXT,
    domain_metadata_json TEXT,
    url TEXT,
    local_path TEXT,                    -- PRIVATE: never public-exported
    raw_text_checksum TEXT,
    quality_score REAL,
    status TEXT,                        -- candidate, ingested, parsed, failed, archived
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,                -- chk_...
    source_id TEXT REFERENCES sources(id),
    chunk_index INTEGER,
    chunk_text TEXT,                    -- PRIVATE raw chunk text
    text_checksum TEXT,
    created_at TEXT
);

-- Research scoping -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_contracts (
    id TEXT PRIMARY KEY,                -- contract_...
    root_topic TEXT,
    primary_question TEXT,
    domain_pack TEXT,
    allowed_concepts_json TEXT,
    out_of_scope_concepts_json TEXT,
    drift_threshold REAL,
    status TEXT,                        -- draft, active, completed, failed
    created_at TEXT,
    updated_at TEXT
);

-- Claim lifecycle ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS claims_staged (
    id TEXT PRIMARY KEY,                -- clm_...
    source_id TEXT REFERENCES sources(id),
    chunk_id TEXT REFERENCES chunks(id),
    claim_text TEXT,
    statement_type TEXT,                -- observation, source_claim, agent_inference, user_note, hypothesis
    subject TEXT,
    predicate TEXT,
    object TEXT,
    scope TEXT,
    evidence_type TEXT,
    confidence REAL,
    limitations_json TEXT,
    domain TEXT,
    domain_metadata_json TEXT,
    extractor_model TEXT,
    extractor_provider TEXT,            -- mock, ollama
    llm_schema_version TEXT,
    prompt_template_version TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS claims_accepted (
    id TEXT PRIMARY KEY,                -- clm_...
    source_id TEXT REFERENCES sources(id),
    chunk_id TEXT REFERENCES chunks(id),
    claim_text TEXT,
    statement_type TEXT,
    subject TEXT,
    predicate TEXT,
    object TEXT,
    scope TEXT,                         -- required: accepted claims preserve scope
    evidence_type TEXT,
    confidence REAL,
    limitations_json TEXT,
    domain TEXT,
    domain_metadata_json TEXT,
    quote_span_json TEXT,               -- required: no acceptance without quote provenance
    validator_version TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS claim_rejections (
    id TEXT PRIMARY KEY,                -- clm_... (rejected claims are kept, never discarded)
    source_id TEXT,
    chunk_id TEXT,
    claim_text TEXT,
    rejection_reason TEXT,              -- missing_quote_span, overgeneralized_scope, unsupported_claim,
                                        -- invalid_json, weak_concept_mapping, missing_source_id,
                                        -- unsafe_or_injected_content
    rejection_details_json TEXT,
    created_at TEXT
);

-- Concept graph --------------------------------------------------------------

CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,                -- cpt_...
    label TEXT,
    definition TEXT,
    domain TEXT,                        -- primary domain or 'general'
    domain_metadata_json TEXT,
    status TEXT,                        -- candidate, draft, experimental, active, deprecated, merged
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS claim_concept_links (
    id TEXT PRIMARY KEY,
    claim_id TEXT,
    concept_id TEXT REFERENCES concepts(id),
    role TEXT,                          -- subject, object, context, method, metric, limitation, domain, bridge
    confidence REAL,
    domain_metadata_json TEXT,
    created_at TEXT
);

-- Evidence graph -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,                -- rel_...
    subject_concept_id TEXT REFERENCES concepts(id),
    predicate TEXT,                     -- may_increase, may_reduce, supports, contradicts, depends_on, ...
    object_concept_id TEXT REFERENCES concepts(id),
    scope TEXT,
    confidence REAL,
    evidence_strength REAL,
    domain TEXT,
    domain_metadata_json TEXT,
    status TEXT,                        -- draft, active, deprecated
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS score_events (
    id TEXT PRIMARY KEY,                -- append-only: scores never change without an event
    entity_type TEXT,                   -- claim, relationship, source, theory_candidate
    entity_id TEXT,
    old_score REAL,
    new_score REAL,
    triggering_claim_id TEXT,
    triggering_source_id TEXT,
    reason TEXT,
    formula_version TEXT,
    created_at TEXT
);

-- Runs and reports -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,                -- run_...
    contract_id TEXT REFERENCES research_contracts(id),
    topic TEXT,
    domain_pack TEXT,
    mode TEXT,                          -- fixture, manual, live
    status TEXT,                        -- running, completed, completed_with_failures, failed
    started_at TEXT,
    finished_at TEXT,
    summary_json TEXT
);

CREATE TABLE IF NOT EXISTS node_reports (
    id TEXT PRIMARY KEY,                -- rep_...
    run_id TEXT REFERENCES research_runs(id),
    node_name TEXT,
    status TEXT,                        -- pass, fail, partial, skipped
    input_ids_json TEXT,
    output_ids_json TEXT,
    metrics_json TEXT,
    model_runtime_json TEXT,            -- provider/model/schema/prompt metadata for model-assisted nodes
    errors_json TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS run_reports (
    id TEXT PRIMARY KEY,                -- rep_...
    run_id TEXT REFERENCES research_runs(id),
    topic TEXT,
    domain_pack TEXT,
    report_json TEXT,                   -- JSON-first; prose second
    prose_summary TEXT,
    created_at TEXT
);

-- Public surface and improvement loop ----------------------------------------

CREATE TABLE IF NOT EXISTS public_cards (
    id TEXT PRIMARY KEY,                -- card_...
    type TEXT,                          -- claim_card, concept_card, cluster_card, theory_card, memo_card
    title TEXT,
    summary TEXT,
    confidence TEXT,
    concepts_json TEXT,
    source_count INTEGER,
    public_detail_level TEXT,           -- summary, standard, detailed
    is_public_safe INTEGER,             -- 0/1; export filters on this
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS improvement_tickets (
    id TEXT PRIMARY KEY,                -- ticket_...
    run_id TEXT,
    priority TEXT,                      -- low, medium, high, critical
    title TEXT,
    problem TEXT,
    evidence_json TEXT,
    affected_modules_json TEXT,
    expected_files_json TEXT,
    acceptance_criteria_json TEXT,
    test_plan_json TEXT,
    non_goals_json TEXT,
    risk_level TEXT,
    rollback_plan TEXT,
    status TEXT,                        -- draft, ready, in_progress, implemented, rejected
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS safety_audits (
    id TEXT PRIMARY KEY,
    run_id TEXT,
    audit_type TEXT,                    -- public_export, route_permissions, prompt_injection, secrets, full
    status TEXT,                        -- pass, fail
    blocked_reasons_json TEXT,
    checked_routes_json TEXT,
    checked_exports_json TEXT,
    checked_secrets_json TEXT,
    report_json TEXT,
    created_at TEXT
);
