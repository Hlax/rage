-- Migration 0004: cluster intelligence reports (Golden Test 13).
-- Spec: docs/agents/05_DATA_MODEL.md section 4.18.

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

CREATE INDEX IF NOT EXISTS idx_cluster_reports_label ON cluster_reports(cluster_label);
CREATE INDEX IF NOT EXISTS idx_cluster_reports_created ON cluster_reports(created_at);
