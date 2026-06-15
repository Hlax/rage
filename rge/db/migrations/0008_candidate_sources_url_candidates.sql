-- Migration 0008: persist ordered OpenAlex fetch URL candidates (ticket-233).

ALTER TABLE candidate_sources ADD COLUMN url_candidates_json TEXT;
