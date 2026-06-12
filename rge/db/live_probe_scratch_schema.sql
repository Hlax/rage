-- Isolated scratch schema for operator-reviewed live probe reports only.
-- NOT applied via main schema_migrations; separate from creative_research.sqlite.

CREATE TABLE IF NOT EXISTS reviewed_live_probe_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_rel_path TEXT NOT NULL,
    report_created_at TEXT NOT NULL,
    command TEXT NOT NULL,
    run_mode TEXT NOT NULL,
    fixture_source TEXT,
    strict_chain INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    floors_met INTEGER NOT NULL DEFAULT 0,
    contradiction_input_mode TEXT,
    effective_llm_mode TEXT,
    provider TEXT,
    model TEXT,
    stage_claim_accepted INTEGER NOT NULL DEFAULT 0,
    stage_claim_rejected INTEGER NOT NULL DEFAULT 0,
    stage_link_accepted INTEGER NOT NULL DEFAULT 0,
    stage_link_rejected INTEGER NOT NULL DEFAULT 0,
    stage_relationship_accepted INTEGER NOT NULL DEFAULT 0,
    stage_relationship_rejected INTEGER NOT NULL DEFAULT 0,
    stage_contradiction_accepted INTEGER NOT NULL DEFAULT 0,
    stage_contradiction_rejected INTEGER NOT NULL DEFAULT 0,
    fixture_count INTEGER,
    fixtures_passed INTEGER,
    fixtures_failed INTEGER,
    rejection_diagnostics_json TEXT NOT NULL DEFAULT '[]',
    operator_reviewed_at TEXT NOT NULL,
    operator_note TEXT,
    ingested_at TEXT NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '0.1.0',
    UNIQUE (report_rel_path, report_created_at, command)
);

CREATE INDEX IF NOT EXISTS idx_reviewed_live_probe_reports_reviewed_at
    ON reviewed_live_probe_reports (operator_reviewed_at);
