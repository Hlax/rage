-- Migration 0001: initial Research Graph Engine schema (Phase 1).
-- Reconciles claim lifecycle with docs/agents/05_DATA_MODEL.md:
--   single `claims` table with status column + `claim_quotes` for provenance.

-- Source library -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    title TEXT,
    authors_json TEXT DEFAULT '[]',
    year INTEGER,
    source_type TEXT,
    domain TEXT,
    domain_metadata_json TEXT DEFAULT '{}',
    url TEXT,
    local_path TEXT,
    publisher TEXT,
    abstract TEXT,
    raw_text_checksum TEXT,
    quality_score REAL,
    credibility_notes TEXT,
    status TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sources_domain_status ON sources(domain, status);
CREATE INDEX IF NOT EXISTS idx_sources_checksum ON sources(raw_text_checksum);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT,
    page TEXT,
    section TEXT,
    token_count INTEGER,
    embedding_id TEXT,
    embedding_model TEXT,
    text_checksum TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_checksum ON chunks(text_checksum);

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

-- Claim lifecycle (reconciled) -----------------------------------------------

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
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
    status TEXT,
    rejection_reason TEXT,
    rejection_details_json TEXT,
    extractor_model TEXT,
    extractor_provider TEXT,
    llm_schema_version TEXT,
    prompt_template_version TEXT,
    validator_version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_claims_status_domain ON claims(status, domain);
CREATE INDEX IF NOT EXISTS idx_claims_source ON claims(source_id);
CREATE INDEX IF NOT EXISTS idx_claims_chunk ON claims(chunk_id);
CREATE INDEX IF NOT EXISTS idx_claims_statement_type ON claims(statement_type);

CREATE TABLE IF NOT EXISTS claim_quotes (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    chunk_id TEXT NOT NULL REFERENCES chunks(id),
    quote_text TEXT,
    char_start INTEGER,
    char_end INTEGER,
    page TEXT,
    is_primary INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- Concept graph --------------------------------------------------------------

CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    label TEXT,
    definition TEXT,
    domain TEXT,
    domain_metadata_json TEXT,
    status TEXT,
    parent_concept_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_concepts_domain_status ON concepts(domain, status);

CREATE TABLE IF NOT EXISTS claim_concepts (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    role TEXT,
    confidence REAL,
    domain_metadata_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (claim_id, concept_id, role)
);

-- Evidence graph -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS idx_relationships_subject ON relationships(subject_concept_id);
CREATE INDEX IF NOT EXISTS idx_relationships_object ON relationships(object_concept_id);
CREATE INDEX IF NOT EXISTS idx_relationships_domain ON relationships(domain);

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
    created_at TEXT NOT NULL
);

-- Runs and reports -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,
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
    id TEXT PRIMARY KEY,
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

-- Public surface and improvement loop ----------------------------------------

CREATE TABLE IF NOT EXISTS public_cards (
    id TEXT PRIMARY KEY,
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
    id TEXT PRIMARY KEY,
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
