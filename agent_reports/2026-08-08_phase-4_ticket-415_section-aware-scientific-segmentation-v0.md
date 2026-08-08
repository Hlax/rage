---
template_id: implementation_report
template_version: 1.0.0
status: complete
date: 2026-08-08
phase: 4
ticket: ticket-415
---

# Ticket 415 — Section-aware scientific segmentation and provenance v0

## Outcome

Implemented deterministic structural segmentation with exact private provenance and a
fail-closed extraction policy. Ticket-415 is complete locally and ticket-416 is the only
newly activated Phase 4 ticket.

## Changes

- Replaced fixed-only splitting with domain-neutral structural spans for title/metadata,
  abstract, introduction/background, methods, results, discussion, limitations,
  references, acknowledgements, navigation, boilerplate, and unknown sections.
- Preserved exact half-open source offsets: every stored `chunk_text` reconstructs from
  `source_text[char_start:char_end]`; only surrounding whitespace/delimiters may be
  excluded from a chunk span.
- Added additive migration `0010_structural_chunk_provenance` and repository support for
  `section_type`, `section_title`, `char_start`, `char_end`, legacy `section`, `page`, and
  `extraction_eligible`.
- Added deterministic PDF page-span propagation where local parser backends expose page
  boundaries. HTML, Markdown, PDF-derived text, and plain text remain network-free and do
  not require GROBID.
- Made title/metadata, references, acknowledgements, navigation, and boilerplate
  non-extractable by default. Unknown sections inherit the explicit source-level
  eligibility decision.
- Filtered claim extraction to eligible chunks. A source with no eligible structural
  chunks returns `blocked_by_section_gate` and cannot produce accepted claims.
- Preserved checksum-pinned manual fixture compatibility: a source-scoped fixture is
  evaluated once, candidates are assigned to the exact chunk containing their quote,
  and legacy source-wide scope validation is retained without duplicate candidate replay.
- Added scientific-section, exact-offset, page-persistence, migration, reference-only,
  HTML/Markdown/plain fallback, document-parser, and ingestion-schema regression coverage.
- Documented structural chunk fields and offset/page/eligibility semantics in the data
  model specification.

## Safety and scope

- Mock-only and network-free implementation/verification.
- No live LLM, network, cloud, publication, promotion, credential, or public-write action.
- No model participates in section classification or provenance writes.
- No creativity-specific section taxonomy or public export widening.
- Existing database rows remain readable through additive nullable/defaulted columns.

## Verification

| Command | Result |
|---|---|
| Focused structural/document/ingestion suite | PASS — 32 passed |
| Structural + manual fixture compatibility suite | PASS — 20 passed |
| Focused + staged/web/manual adjacent regressions | PASS — 65 passed |
| `python -m rge.cli verify` with mock-only env | PASS |
| Golden tests within verify | PASS — 165 passed |
| Full pytest within verify | PASS — 1427 passed, 49 deselected |
| Full safety audit within verify | PASS |
| Public-site build within verify | PASS |
| `git diff --check` | PASS |

The initially expanded adjacent suite found five deterministic manual-fixture failures
caused by replaying one source fixture across each new section. After routing candidates
once by quote-bearing chunk, three remaining scope-validation failures exposed context
split across sections. Source-wide validation was restored only for checksum-pinned
legacy fixtures; all focused and full gates then passed.

## Queue transition

- ticket-415: `done`
- ticket-416: `ready`
- tickets 417–428: unchanged and blocked

## Merge checkpoint

- Ticket branch: `phase-4/ticket-415-section-aware-scientific-segmentation-v0`
- Implementation commit: `c88c3ec`
- Merge commit on `main`: `4acbfb7`
- Ordinary non-force push to `origin/main`: pending

## Next smallest ticket

Ticket-416, domain-neutral structured research claim schema v0. Its medium-risk focused
pre-ticket audit remains the next action; no ticket-416 implementation was started in
this lifecycle.
