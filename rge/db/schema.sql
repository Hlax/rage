-- Research Graph Engine: SQLite schema reference (Phase 1).
--
-- Authoritative DDL is applied through versioned migrations in
-- ``rge/db/migrations/``. This file documents the intended shape from
-- ``docs/agents/05_DATA_MODEL.md`` for reviewers and golden tests.
--
-- Claim lifecycle is reconciled: a single ``claims`` table with a ``status``
-- column (draft, staged, accepted, rejected) plus ``claim_quotes`` for
-- provenance. Rejection reasons live on ``claims.rejection_reason`` and
-- ``claims.rejection_details_json``; rejected rows are never discarded.

-- Source library -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,                -- src_...
    title TEXT,
    authors_json TEXT,
    year INTEGER,
    source_type TEXT,                   -- paper, webpage, fixture, manual_note, ...
    domain TEXT,
    domain_metadata_json TEXT,
    url TEXT,
    local_path TEXT,                    -- PRIVATE: never public-exported
    publisher TEXT,
    abstract TEXT,
    raw_text_checksum TEXT,
    quality_score REAL,
    credibility_notes TEXT,
    status TEXT,                        -- candidate, ingested, parsed, failed, archived
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,                -- chk_...
    source_id TEXT REFERENCES sources(id),
    chunk_index INTEGER,
    chunk_text TEXT,                    -- PRIVATE raw chunk text
    page TEXT,
    section TEXT,
    token_count INTEGER,
    embedding_id TEXT,
    embedding_model TEXT,
    text_checksum TEXT,
    created_at TEXT
);

-- Research scoping -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_contracts (
    id TEXT PRIMARY KEY,
    root_topic TEXT,
    primary_question TEXT,
    domain_pack TEXT,
    allowed_concepts_json TEXT,
    adjacent_concepts_json TEXT,
    out_of_scope_concepts_json TEXT,
    source_budget INTEGER,
    search_budget INTEGER,
    follow_up_depth INTEGER,
    drift_threshold REAL,
    success_criteria_json TEXT,
    source_strategy_json TEXT,
    evidence_requirements_json TEXT,
    queue_priority_formula TEXT,
    topic_drift_formula TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Claim lifecycle (reconciled with 05_DATA_MODEL.md) -------------------------

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,                -- clm_...
    source_id TEXT REFERENCES sources(id),
    chunk_id TEXT REFERENCES chunks(id),
    claim_text TEXT,
    statement_type TEXT,
    subject TEXT,
    predicate TEXT,
    object TEXT,
    scope TEXT,
    evidence_type TEXT,
    confidence REAL,
    limitations_json TEXT,
    domain TEXT,
    domain_metadata_json TEXT,
    status TEXT,                        -- draft, staged, accepted, rejected
    rejection_reason TEXT,              -- required when status = rejected
    rejection_details_json TEXT,
    extractor_model TEXT,
    extractor_provider TEXT,
    llm_schema_version TEXT,
    prompt_template_version TEXT,
    validator_version TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS claim_quotes (
    id TEXT PRIMARY KEY,
    claim_id TEXT REFERENCES claims(id),
    source_id TEXT REFERENCES sources(id),
    chunk_id TEXT REFERENCES chunks(id),
    quote_text TEXT,
    char_start INTEGER,
    char_end INTEGER,
    page TEXT,
    is_primary INTEGER,
    created_at TEXT
);

-- Concept graph --------------------------------------------------------------

CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,                -- cpt_...
    label TEXT,
    definition TEXT,
    domain TEXT,
    domain_metadata_json TEXT,
    status TEXT,
    parent_concept_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS claim_concepts (
    id TEXT PRIMARY KEY,
    claim_id TEXT REFERENCES claims(id),
    concept_id TEXT REFERENCES concepts(id),
    role TEXT,
    confidence REAL,
    domain_metadata_json TEXT,
    created_at TEXT
);

-- Evidence graph -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,                -- rel_...
    subject_concept_id TEXT REFERENCES concepts(id),
    predicate TEXT,
    object_concept_id TEXT REFERENCES concepts(id),
    scope TEXT,
    confidence REAL,
    evidence_strength REAL,
    domain TEXT,
    domain_metadata_json TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS relationship_evidence (
    id TEXT PRIMARY KEY,
    relationship_id TEXT REFERENCES relationships(id),
    claim_id TEXT REFERENCES claims(id),
    stance TEXT,
    relevance_score REAL,
    created_at TEXT,
    UNIQUE (relationship_id, claim_id, stance)
);

CREATE TABLE IF NOT EXISTS score_events (
    id TEXT PRIMARY KEY,
    entity_type TEXT,
    entity_id TEXT,
    old_score REAL,
    new_score REAL,
    triggering_claim_id TEXT,
    triggering_source_id TEXT,
    reason TEXT,
    formula_version TEXT,
    created_at TEXT
);

-- Candidate discovery and queue ----------------------------------------------

CREATE TABLE IF NOT EXISTS candidate_sources (
    id TEXT PRIMARY KEY,
    research_question_id TEXT NOT NULL,
    contract_id TEXT,
    title TEXT NOT NULL,
    url TEXT,
    source_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    relevance_score REAL NOT NULL,
    credibility_prior REAL NOT NULL,
    gap_fill_score REAL NOT NULL,
    recency_score REAL NOT NULL DEFAULT 0.5,
    source_diversity_score REAL NOT NULL DEFAULT 0.5,
    novelty_score REAL NOT NULL DEFAULT 0.5,
    drift_risk REAL NOT NULL DEFAULT 0.1,
    priority_score REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidate_sources_question
    ON candidate_sources(research_question_id);

CREATE TABLE IF NOT EXISTS research_queue (
    id TEXT PRIMARY KEY,
    candidate_source_id TEXT REFERENCES candidate_sources(id),
    research_question_id TEXT NOT NULL,
    contract_id TEXT,
    item_type TEXT NOT NULL DEFAULT 'source',
    priority_score REAL NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_queue_question
    ON research_queue(research_question_id);

CREATE INDEX IF NOT EXISTS idx_research_queue_priority
    ON research_queue(priority_score DESC);

-- Runs and reports -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,                -- run_...
    contract_id TEXT REFERENCES research_contracts(id),
    topic TEXT,
    domain_pack TEXT,
    mode TEXT,
    status TEXT,
    started_at TEXT,
    finished_at TEXT,
    summary_json TEXT
);

CREATE TABLE IF NOT EXISTS node_reports (
    id TEXT PRIMARY KEY,                -- rep_...
    run_id TEXT REFERENCES research_runs(id),
    node_name TEXT,
    status TEXT,
    input_ids_json TEXT,
    output_ids_json TEXT,
    metrics_json TEXT,
    model_runtime_json TEXT,
    errors_json TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS run_reports (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES research_runs(id),
    topic TEXT,
    domain_pack TEXT,
    report_json TEXT,
    prose_summary TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS cluster_reports (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES research_runs(id),
    cluster_label TEXT NOT NULL,
    included_concepts_json TEXT NOT NULL,
    evidence_packet_json TEXT NOT NULL,
    report_json TEXT NOT NULL,
    prose_summary TEXT,
    created_at TEXT NOT NULL
);

-- Public surface and improvement loop ----------------------------------------

CREATE TABLE IF NOT EXISTS public_cards (
    id TEXT PRIMARY KEY,                -- card_...
    type TEXT,
    title TEXT,
    summary TEXT,
    confidence TEXT,
    concepts_json TEXT,
    source_count INTEGER,
    claim_ids_json TEXT,
    public_detail_level TEXT,
    is_public_safe INTEGER,
    private_fields_json TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS improvement_tickets (
    id TEXT PRIMARY KEY,                -- ticket_...
    run_id TEXT,
    priority TEXT,
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
    status TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS safety_audits (
    id TEXT PRIMARY KEY,
    run_id TEXT,
    audit_type TEXT,
    status TEXT,
    blocked_reasons_json TEXT,
    checked_routes_json TEXT,
    checked_exports_json TEXT,
    checked_secrets_json TEXT,
    report_json TEXT,
    created_at TEXT
);
