---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-006 / sqlite-migration-source-ingestion

## 1. Summary

Implemented the SQLite migration harness, reconciled the claims lifecycle schema with `docs/agents/05_DATA_MODEL.md` (single `claims` table with status + `claim_quotes`), and added local text-file source ingestion via `research ingest`. The pipeline reads a fixture file, chunks it deterministically, persists `sources` and `chunks` rows with stable prefixed IDs, SHA-256 checksums, ISO-8601 timestamps, and status `ingested`. Golden Test 1 passes; all 29 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-006
- Ticket title: Add SQLite migration harness and source ingestion
- Branch: `phase-1/ticket-006-sqlite-migration-source-ingestion`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-11

## 3. Scope

### In Scope

- Versioned migration harness (`schema_migrations` + `0001_initial.sql`).
- Reconciled `schema.sql` (claims lifecycle per 05_DATA_MODEL.md).
- Local plain-text fetcher and deterministic parser/chunker.
- Repository persistence for sources and chunks.
- `research ingest <path> --domain <domain>` CLI subcommand.
- Golden Test 1 (`tests/golden/test_01_ingestion.py`).
- Updated scaffold golden test for reconciled table names and `ingest` help.

### Out of Scope / Non-Goals

- Claim extraction, validation, concept linking, relationships, scoring.
- URL/PDF fetching, Ollama calls, public export changes, public write routes.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/db/migrations/0001_initial.sql` | New: authoritative initial migration with reconciled claims + claim_quotes and Phase 1 table set. |
| `rge/db/connection.py` | Migration harness: `apply_migrations`, `ensure_database`, `schema_migrations` tracking. |
| `rge/db/schema.sql` | Reconciled reference schema; claims_staged/accepted/rejections replaced by claims + claim_quotes. |
| `rge/db/repositories.py` | Source/chunk repositories, stable ID helpers, `ingest_local_source` orchestration. |
| `rge/modules/fetcher.py` | `fetch_local_text_file` for UTF-8 plain-text sources. |
| `rge/modules/parser.py` | Deterministic text chunking with checksums and token counts. |
| `rge/cli.py` | New `ingest` subcommand with optional `--db` for tests. |
| `tests/golden/test_01_ingestion.py` | New: Golden Test 1 (migration, persist, restart, idempotency, JSON output). |
| `tests/golden/test_00_scaffold.py` | Updated expected schema tables and CLI help for `ingest`. |
| `pyproject.toml` | Package data includes `migrations/*.sql`. |
| `tickets/TICKET_QUEUE.md` | ticket-006 marked done; ticket-003 superseded; ticket-007 proposed. |
| `tickets/ticket-006.json` | Status updated to `done`. |
| `tickets/ticket-007.json` | New: proposed next ticket (claim extraction, Golden Test 2). |

## 5. Implementation Notes

- **Claims lifecycle reconciliation.** Phase 0 placeholder tables (`claims_staged`, `claims_accepted`, `claim_rejections`) are replaced by a single `claims` table with `status` (`draft`, `staged`, `accepted`, `rejected`) plus `rejection_reason` / `rejection_details_json`, and a `claim_quotes` table for provenance. Rejected rows are never discarded.
- **Stable IDs.** Source IDs derive from `src_<checksum_prefix>`; chunk IDs from source suffix + index + chunk checksum prefix. Re-ingesting identical content is idempotent (checksum lookup).
- **Migration authority.** `schema.sql` is documentation/reference; `migrations/0001_initial.sql` is what the harness applies.
- **Windows CLI note.** `research.exe` installs to a Scripts directory not on PATH; use `python -m rge.cli` (documented below).

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Migration harness creates DB from versioned migrations | PASS | `apply_migrations` applies `0001_initial`. |
| Schema reconciles claims lifecycle with 05_DATA_MODEL.md | PASS | `claims` + `claim_quotes`; old triple-table placeholders removed. |
| `research ingest` persists source + chunks with stable IDs, checksum, status `ingested` | PASS | Manual CLI verified; golden tests assert fields. |
| Source re-readable after process restart | PASS | `test_source_survives_process_restart`. |
| `pytest tests/golden/test_01_ingestion.py` passes without Ollama | PASS | 5/5. |
| Existing golden scaffold tests still pass | PASS | 29/29 total golden tests. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pip install -e ".[dev]"` | PASS | Editable install OK; `research.exe` not on PATH (Windows). |
| `python -m pytest tests/golden/test_01_ingestion.py` | PASS | 5 passed in 0.73s. |
| `python -m pytest tests/golden` | PASS | 29 passed in 0.78s. |
| `python -m pytest` | PASS | 29 passed in 0.78s. |
| `python -m rge.cli ingest fixtures/sources/creativity_ai_diversity_short.txt --domain creativity` | PASS | Persisted `src_fac29b647fa3cc77` + 1 chunk to `data/db/creative_research.sqlite`. |

**Windows PATH note:** `research.exe` is at `C:\Users\guestt\AppData\Local\Python\pythoncore-3.14-64\Scripts\research.exe`, which is not on PATH. Use `python -m rge.cli ingest ...` until PATH is updated.

## 8. Test Results

### Passing

- `tests/golden/test_01_ingestion.py` — 5/5.
- `tests/golden/test_00_scaffold.py` — 11/11.
- `tests/golden/test_00_model_runtime.py` — 7/7.
- `tests/golden/test_00_public_site_static.py` — 6/6.

### Failing

- None.

## 9. Safety Audit Status

- Required: no (no public routes, export, or model-assisted writes in this ticket).
- Status: not run.
- Notes: Ingestion stores private `local_path` and `chunk_text` in SQLite only; CLI JSON output excludes raw chunk text.

## 10. Spec Deviations

1. **Schema breadth.** Migration includes Phase 1 placeholder tables beyond ingestion needs (contracts, concepts, relationships, reports, cards, tickets, audits) but omits later-phase tables from 05_DATA_MODEL.md (e.g. `candidate_sources`, `model_invocations`, `domain_packs`). Intentional incremental scope.
2. **`public_cards` vs `cards`.** Retained `public_cards` name from Phase 0 placeholder rather than renaming to `cards` per full data model.
3. **`claim_concepts` rename.** Renamed `claim_concept_links` to `claim_concepts` per 05_DATA_MODEL.md during schema reconciliation.

## 11. Known Risks / Gaps

- Default DB path `data/db/creative_research.sqlite` is gitignored; manual ingest creates local state outside tests.
- Parser uses simple character-boundary chunking; PDF/HTML/URL ingestion deferred.
- No `RGE_DB_PATH` env config yet; tests use `--db` override.

## 12. Rollback Plan

Revert branch `phase-1/ticket-006-sqlite-migration-source-ingestion`. Delete locally created `data/db/*.sqlite` if present. Schema changes live only in migration files on the branch.

## 13. Recommended Next Ticket

**ticket-007: Add mock claim extraction (Golden Test 2)**

- Implement `research extract-claims --source <source_id>` using the mock LLM client.
- Stage candidate claims in `claims` with status `staged`/`accepted`/`rejected` per validators.
- Require quote spans via `claim_quotes` for accepted claims.
- Add `tests/golden/test_02_claim_extraction.py`.
- Non-goals: live Ollama, concept linking, relationships, public export.

See `tickets/ticket-007.json`.

## 14. Suggested Next Prompt

```txt
You are continuing the Research Graph Engine build.

Read AGENTS.md, tickets/TICKET_QUEUE.md, tickets/ticket-007.json,
docs/agents/00_GOLDEN_TESTS.md (Test 2), and
agent_reports/2026-06-11_phase-1_ticket-006_sqlite-migration-source-ingestion.md.

Implement ticket-007 only on branch phase-1/ticket-007-mock-claim-extraction:
- Add research extract-claims command.
- Use mock LLM fixtures for deterministic claim extraction.
- Persist staged/accepted/rejected claims with quote provenance.
- Add tests/golden/test_02_claim_extraction.py.

Do not call Ollama, implement concept linking, or touch public export.
Run pytest tests/golden, write an agent report, update TICKET_QUEUE.md.
```
