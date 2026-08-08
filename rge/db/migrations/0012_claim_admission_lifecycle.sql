-- Private, append-only claim admission history (ticket-417).
-- Existing claim rows retain their current status and are intentionally not backfilled
-- with invented actors, decisions, or timestamps.

CREATE TABLE IF NOT EXISTS claim_decisions (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    prior_status TEXT,
    new_status TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    validator_version TEXT,
    policy_version TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_claim_decisions_claim_created
    ON claim_decisions(claim_id, created_at, id);
CREATE INDEX IF NOT EXISTS idx_claim_decisions_new_status
    ON claim_decisions(new_status);
