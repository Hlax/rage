ALTER TABLE claims ADD COLUMN claim_contract_version TEXT;
ALTER TABLE claims ADD COLUMN claim_kind TEXT;
ALTER TABLE claims ADD COLUMN study_design TEXT;
ALTER TABLE claims ADD COLUMN population_or_sample TEXT;
ALTER TABLE claims ADD COLUMN intervention_or_exposure TEXT;
ALTER TABLE claims ADD COLUMN comparator TEXT;
ALTER TABLE claims ADD COLUMN outcome TEXT;
ALTER TABLE claims ADD COLUMN effect_direction TEXT;
ALTER TABLE claims ADD COLUMN statistical_context TEXT;
ALTER TABLE claims ADD COLUMN section_provenance_json TEXT;

CREATE INDEX IF NOT EXISTS idx_claims_kind ON claims(claim_kind);
