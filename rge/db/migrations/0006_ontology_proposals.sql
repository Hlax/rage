-- Migration 0006: ontology pressure proposals (Golden Test 17).
-- Spec: docs/agents/05_DATA_MODEL.md section 4.23.

CREATE TABLE IF NOT EXISTS ontology_proposals (
    id TEXT PRIMARY KEY,
    proposal_type TEXT NOT NULL,
    candidate_concept TEXT,
    status TEXT NOT NULL,
    evidence_claims_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    proposal_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ontology_proposals_candidate ON ontology_proposals(candidate_concept);
CREATE INDEX IF NOT EXISTS idx_ontology_proposals_status ON ontology_proposals(status);
