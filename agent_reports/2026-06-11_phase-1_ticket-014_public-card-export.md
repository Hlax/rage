---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-014 / public-card-export

## 1. Summary

Implemented deterministic public card export for Golden Test 11 via `research export-public --limit N`. Added fail-closed safety validation in `public_export_policy`, golden card seeding from accepted claims, `PublicCardRepository`, and JSON writes to `data/exports/` and `apps/public-site/public/data/`. Golden Test 11 passes (4 tests); all 59 golden tests pass without Ollama; public site static build succeeds.

## 2. Ticket

- Ticket ID: ticket-014
- Ticket title: Add public card export with safety filtering (Golden Test 11)
- Branch: `phase-1/ticket-014-public-card-export`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-11

## 3. Scope

### In Scope

- `card_exporter`: golden card seeding, curated export, file writes.
- `public_export_policy`: allowed/required fields, forbidden key/value checks, fail-closed bundle validation.
- `PublicCardRepository`, `public_card_record_to_export_dict`.
- `research export-public` CLI with `--limit`, `--db`, `--output-dir`.
- Golden Test 11 (`tests/golden/test_11_public_card_export.py`).
- Scaffold import update for `card_exporter`.

### Out of Scope / Non-Goals

- Ollama, LangGraph, public write routes, live safety auditor module, memo export content.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/safety/public_export_policy.py` | Validation helpers and curated field filtering. |
| `rge/modules/card_exporter.py` | Golden seeding, export orchestration, JSON writes. |
| `rge/db/repositories.py` | `PublicCardRepository`, export dict mapper. |
| `rge/cli.py` | Working `export-public` subcommand. |
| `tests/golden/test_11_public_card_export.py` | New: Golden Test 11 (4 tests). |
| `tests/golden/test_00_scaffold.py` | Import `card_exporter`. |
| `tickets/TICKET_QUEUE.md` | ticket-014 done; ticket-015 proposed. |
| `tickets/ticket-014.json` | Status `done`. |
| `tickets/ticket-015.json` | Proposed public site detail pages ticket. |
| `agent_reports/2026-06-11_phase-1_ticket-013_research-contract-drift.md` | Record merge hash `69befe6`. |

## 5. Implementation Notes

- Golden cards seed on first export when accepted claims exist and no public-safe cards are stored.
- Optional card extras (`public_caveats`, `public_source_metadata`, `related_cards`) live in exporter constants keyed by card ID to avoid schema migration.
- Private evaluator notes, paths, prompts, and raw excerpts are stored in `private_fields_json` and never mapped to export JSON.
- Export fails closed when any card value matches forbidden patterns (e.g. `<script>`).
- `--output-dir` writes to a single directory for isolated golden tests.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| `research export-public --limit N` writes public-safe JSON without Ollama | PASS | CLI + module. |
| Export excludes private fields; includes whitelisted card fields | PASS | Golden Test 11 asserts. |
| `pytest tests/golden/test_11_public_card_export.py` | PASS | 4/4. |
| Existing golden tests still pass | PASS | 59/59. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_11_public_card_export.py` | PASS | 4 passed in 1.20s. |
| `python -m pytest tests/golden` | PASS | 59 passed in 8.40s. |
| `python -m pytest` | PASS | 59 passed in 8.29s. |
| `cd apps/public-site && npm run build` | PASS | Next.js static export succeeded. |

## 8. Test Results

### Passing

- `tests/golden/test_11_public_card_export.py` — 4/4.
- All prior golden tests — 55/55 unchanged behavior plus 4 new tests.

### Failing

- None.

## 9. Manual CLI Verification

Covered by golden tests: full spine ingest → extract → link → build-relationships → export-public on fresh `--db` with `--output-dir`.

## 10. Safety Audit Status

- Required: partial (public export boundaries touched).
- Full safety auditor module still Phase 0 stub; export uses deterministic `public_export_policy` validation instead.
- `python -m rge.modules.safety_auditor --audit full` not run (module not implemented).

## 11. Spec Deviations

1. **Optional public card fields.** `public_caveats`, `public_source_metadata`, and `related_cards` are supplied from exporter constants keyed by card ID rather than new DB columns.

## 12. Known Failures

- None.

## 13. Rollback Plan

Revert branch `phase-1/ticket-014-public-card-export`. Restore placeholder JSON under `apps/public-site/public/data/` if needed.

## 14. Merge to Main

- Instruction source: `AGENTS.md` step 9 (temporary).
- Pre-merge `main` tip: `69befe6304412ed33442f8a65a17d91ad6a69bad`
- Branch: `phase-1/ticket-014-public-card-export`
- Merge result: pending (record hash below after merge/push).

## 15. Recommended Next Ticket

**ticket-015: Add public site card and concept detail pages (Golden Test 12)**

See `tickets/ticket-015.json`.

## 16. Can the Loop Continue?

**Yes.** Public export with safety filtering is in place. ticket-015 (public site detail pages for Golden Test 12) is the smallest next step.

## 17. Suggested Next Prompt

Run `/rge-run-next-ticket` to implement ticket-015 on branch `phase-1/ticket-015-public-site-detail-pages`.
