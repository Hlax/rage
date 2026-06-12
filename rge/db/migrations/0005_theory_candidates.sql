-- Migration 0005: candidate theory records (Golden Test 15).
-- Spec: docs/agents/05_DATA_MODEL.md section 4.22.

CREATE TABLE IF NOT EXISTS theory_candidates (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES research_runs(id),
    cluster_report_id TEXT REFERENCES cluster_reports(id),
    theory_text TEXT NOT NULL,
    confidence TEXT NOT NULL,
    supporting_claims_json TEXT NOT NULL,
    contradicting_or_qualifying_claims_json TEXT NOT NULL,
    boundary_conditions_json TEXT NOT NULL,
    weakening_evidence_json TEXT NOT NULL,
    next_questions_json TEXT NOT NULL,
    status TEXT NOT NULL,
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_theory_candidates_cluster ON theory_candidates(cluster_report_id);
CREATE INDEX IF NOT EXISTS idx_theory_candidates_status ON theory_candidates(status);
