-- Ticket 415: additive structural chunk provenance and eligibility.

ALTER TABLE chunks ADD COLUMN section_type TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE chunks ADD COLUMN section_title TEXT;
ALTER TABLE chunks ADD COLUMN char_start INTEGER;
ALTER TABLE chunks ADD COLUMN char_end INTEGER;
ALTER TABLE chunks ADD COLUMN extraction_eligible INTEGER NOT NULL DEFAULT 1;
