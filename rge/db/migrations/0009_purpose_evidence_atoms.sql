-- Migration 0009: purpose metadata and operator-private evidence atoms.

ALTER TABLE research_contracts ADD COLUMN purpose_metadata_json TEXT;

CREATE TABLE IF NOT EXISTS evidence_atoms (
    id TEXT PRIMARY KEY,
    atom_type TEXT NOT NULL,
    canonical_text TEXT NOT NULL,
    source_claim_ids_json TEXT NOT NULL,
    source_quote_ids_json TEXT NOT NULL,
    concepts_json TEXT NOT NULL,
    stance_profile_json TEXT NOT NULL,
    support_count INTEGER NOT NULL DEFAULT 0,
    contradiction_count INTEGER NOT NULL DEFAULT 0,
    scope TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    asset_tags_json TEXT NOT NULL,
    evidence_maturity TEXT NOT NULL,
    training_suitability TEXT NOT NULL,
    confidence TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_atoms_maturity
    ON evidence_atoms(evidence_maturity, training_suitability);
