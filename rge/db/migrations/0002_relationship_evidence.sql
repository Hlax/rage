-- Migration 0002: relationship_evidence table per docs/agents/05_DATA_MODEL.md 4.9.

CREATE TABLE IF NOT EXISTS relationship_evidence (
    id TEXT PRIMARY KEY,
    relationship_id TEXT NOT NULL REFERENCES relationships(id),
    claim_id TEXT NOT NULL REFERENCES claims(id),
    stance TEXT NOT NULL,
    relevance_score REAL,
    created_at TEXT NOT NULL,
    UNIQUE (relationship_id, claim_id, stance)
);

CREATE INDEX IF NOT EXISTS idx_relationship_evidence_relationship
    ON relationship_evidence(relationship_id);
CREATE INDEX IF NOT EXISTS idx_relationship_evidence_claim
    ON relationship_evidence(claim_id);
