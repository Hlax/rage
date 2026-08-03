---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-08-02
phase: 4
ticket: ticket-415
---

# Pre-Ticket Audit: ticket-415 — Section-aware scientific segmentation v0

**Verdict: GO with scope constraints**

## Summary and recommendation

Ticket-415 may proceed on its own branch. The current parser is a deterministic
fixed-character splitter, the `chunks` table already has legacy `page` and `section`
columns, and the migration runner supports a bounded additive migration. Ticket-414's
source-artifact gate is complete and gives ticket-415 a fail-closed source boundary.

The work must remain a parser/provenance change. It must not add claim semantics,
domain-specific section labels, hosted parsing, destructive rewrites, live actions, or
public fields.

## Readiness evidence

| Field | Result |
|---|---|
| Working tree at audit start | Clean `main`, synchronized with `origin/main` |
| Current ticket | ticket-415 `ready`, risk `medium` |
| Predecessor | ticket-414 done, merged, pushed, full verify pass |
| Current parser | Deterministic fixed-size text chunks with stable IDs/checksums |
| Current schema | `chunks.page` and `chunks.section` exist; structural type/title and offsets do not |
| Migration runner | Ordered additive SQL migrations through `0009` |
| Network/model need | None; implementation and tests can be fully local/mock-only |

## Commands and results

| Command | Result |
|---|---|
| `python -m pytest tests/golden/test_01_ingestion.py tests/unit/test_document_parser.py tests/unit/test_text_quality_gate.py -q` | PASS — 23 passed |
| `python -m pytest tests/unit/test_manual_source_pipeline_e2e.py tests/unit/test_staged_artifact_ingest.py tests/unit/test_web_source_adapter.py -q` | PASS — 16 passed |
| Ticket-414 final `python -m rge.cli verify` | PASS — 165 golden; 1418 full pytest; 49 deselected; safety and site pass |

## Schema and compatibility findings

- Migration `0001_initial.sql` already stores `page TEXT` and `section TEXT` on chunks.
- `ChunkRecord` currently omits both legacy fields when reading and writes them as NULL.
- The smallest compatible migration is additive: normalized `section_type`, original
  `section_title`, exact `char_start`/`char_end`, and an extraction-eligibility flag or
  equivalent stable policy field.
- Existing rows must remain readable. New non-null policy fields require safe defaults;
  no table rebuild, deletion, backfill rewrite, or historical chunk mutation is allowed.
- The golden migration harness asserts the ordered migration list and must be updated for
  the new migration.

## Required implementation boundaries

1. Parse headings and structural spans deterministically from text already available to
   the local parser. No GROBID or network dependency may become mandatory.
2. Use a closed, domain-neutral section taxonomy covering metadata/title, abstract,
   introduction/background, methods, results, discussion, limitations, references,
   acknowledgements, and unknown.
3. Persist the original heading separately from the normalized type.
4. Define offsets against one documented source-text representation. `chunk_text` must
   reconstruct from `source_text[char_start:char_end]` under the documented whitespace
   rule; visual chunk boundaries must not replace exact provenance.
5. Mark references, acknowledgements, navigation, and boilerplate non-extractable by
   default. Unknown text must use an explicit conservative policy tied to the validated
   source/chunk quality boundary, not domain keywords.
6. Preserve checksum-pinned fixture, manual, staged, webpage, and existing-database
   behavior. Add compatibility coverage for pre-migration rows and idempotent migration.
7. Page provenance may be null when the parser lacks page boundaries, but must be stored
   when deterministic page spans are supplied by an available parser backend.
8. Activate only ticket-416 after all gates pass.

## Stop and re-audit conditions

Stop for a new audit if implementation requires any of the following:

- destructive migration or rewrite of existing chunk rows;
- claim-schema or accepted-graph admission changes beyond chunk eligibility filtering;
- hosted/GROBID/network requirement in default tests or runtime;
- public exposure of raw chunk text, local paths, or private provenance diagnostics;
- creativity-specific section names in core code or schema;
- offset semantics that cannot be reconstructed deterministically.

## Safety constraints

- Mock-only and network-free verification.
- No live LLM, cloud, credentials, publication, or public route work.
- Raw source/chunk text and detailed provenance remain private.
- Model output does not participate in parsing, classification, migration, or writes.
- No deletion or mutation of historical source/evidence data.

## Final recommendation

**GO** for ticket-415 within the constraints above. The smallest viable implementation is
an additive migration plus deterministic structural spans in `parser.py`, compatible
repository persistence, document-parser page-span support when available, extraction
eligibility enforcement, focused migration/parser tests, and full mock-only verification.
