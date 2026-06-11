-- Migration 0003: candidate_sources and research_queue per docs/agents/05_DATA_MODEL.md 4.12–4.13.

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
