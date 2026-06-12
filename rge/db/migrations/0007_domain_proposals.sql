-- Migration 0007: domain proposal drafts (Golden Test 18).
-- Spec: docs/agents/05_DATA_MODEL.md section 4.24.

CREATE TABLE IF NOT EXISTS domain_proposals (
    id TEXT PRIMARY KEY,
    domain_id TEXT NOT NULL,
    status TEXT NOT NULL,
    parent_domains_json TEXT NOT NULL,
    overlap_domains_json TEXT NOT NULL,
    specialized_terms_json TEXT NOT NULL,
    scoring_overlay_proposals_json TEXT NOT NULL,
    evidence_claims_json TEXT NOT NULL,
    threshold_report_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_domain_proposals_domain_id ON domain_proposals(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_proposals_status ON domain_proposals(status);
