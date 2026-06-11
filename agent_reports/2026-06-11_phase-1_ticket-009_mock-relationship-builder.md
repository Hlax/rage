---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-009 / mock-relationship-builder

## 1. Summary

Implemented mock relationship building for accepted, concept-linked claims via `research build-relationships --source <source_id>`. Added migration `0002_relationship_evidence.sql`, deterministic mock fixture drafting, Python validation with machine-readable rejection reasons, and persistence of active `relationships` plus `relationship_evidence` rows. Golden Test 6 passes (5 tests); all 41 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-009
- Ticket title: Add mock relationship builder (Golden Test 6)
- Branch: `phase-1/ticket-009-mock-relationship-builder`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-11

## 3. Scope

### In Scope

- `0002_relationship_evidence` migration and `schema.sql` mirror.
- `relationship_builder`: mock proposal, validation, orchestration.
- `RelationshipRepository` / `RelationshipEvidenceRepository`.
- `research build-relationships` CLI with optional `--fixture` and `--db`.
- Mock fixtures for valid Golden Test 6 edge and invalid unknown-concept candidate.
- Golden Test 6 (`tests/golden/test_06_relationship_builder.py`).
- Updated scaffold and ingestion golden tests for new schema table.

### Out of Scope / Non-Goals

- Ollama, scoring/score_events writes, contradiction detection, public export, LangGraph, theory generation.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/db/migrations/0002_relationship_evidence.sql` | New: `relationship_evidence` table per 05_DATA_MODEL.md 4.9. |
| `rge/db/schema.sql` | Added `relationship_evidence` reference DDL. |
| `rge/modules/relationship_builder.py` | Mock drafting, validation, `build_relationships_for_source`. |
| `rge/db/repositories.py` | `RelationshipRepository`, `RelationshipEvidenceRepository`, `ConceptRepository.list_for_domain`. |
| `rge/cli.py` | `build-relationships` subcommand. |
| `rge/llm/mock_client.py` | Fixture-backed `draft_relationships`. |
| `fixtures/llm_outputs/relationship_drafting_creativity_diversity.json` | Golden Test 6 mock edge. |
| `fixtures/llm_outputs/relationship_drafting_unknown_concept.json` | Rejection test fixture. |
| `tests/golden/test_06_relationship_builder.py` | New: Golden Test 6 (5 tests). |
| `tests/golden/test_00_scaffold.py` | `relationship_evidence` table + CLI help. |
| `tests/golden/test_01_ingestion.py` | Expect `0002` migration on fresh DB. |
| `tickets/TICKET_QUEUE.md` | ticket-009 done; ticket-010 proposed. |
| `tickets/ticket-009.json` | Status `done`. |
| `tickets/ticket-010.json` | Proposed score reconciliation ticket. |
| `agent_reports/2026-06-11_pre-ticket-009_relationship-builder-readiness-audit.md` | Pre-implementation audit (included in merge). |

## 5. Implementation Notes

- Model proposes; Python validates. `build_relationships_for_source` forces `RGE_LLM_MODE=mock`.
- Confidence labels (`low`/`medium`/`high`) map to REAL scores 0.25/0.5/0.75 before DB write.
- Fixture `supporting_claim_ids` placeholders resolve to the semantic-diversity accepted claim ID.
- Relationships written as `status = active` directly after validation (mirrors ticket-007 accepted-directly pattern).
- Idempotent: re-run returns `already_built`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| `research build-relationships` creates active relationship with evidence link | PASS | 1 relationship + 1 evidence row on creativity fixture. |
| Golden Test 6 edge: AI assistance → may_reduce → semantic diversity | PASS | Asserted in golden tests and manual CLI. |
| `relationship_evidence` rows include stance `supports` and claim_id | PASS | `rev_*` row links diversity claim. |
| `pytest tests/golden/test_06_relationship_builder.py` passes without Ollama | PASS | 5/5. |
| Existing golden tests still pass | PASS | 41/41. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_06_relationship_builder.py` | PASS | 5 passed in 1.27s. |
| `python -m pytest tests/golden` | PASS | 41 passed in 3.23s. |
| `python -m pytest` | PASS | 41 passed in 3.21s. |
| Manual CLI spine on fresh temp DB | PASS | ingest → extract-claims → link-concepts → build-relationships; 1 active edge with evidence. |

**Windows PATH note:** Use `python -m rge.cli` when `research.exe` is not on PATH.

## 8. Test Results

### Passing

- `tests/golden/test_06_relationship_builder.py` — 5/5.
- All prior golden tests — 36/36 unchanged behavior plus 1 ingestion assertion update for `0002`.

### Failing

- None.

## 9. Manual CLI Verification

Fresh DB at `%TEMP%\rge_ticket009_fresh.sqlite`:

1. `ingest` → `src_fac29b647fa3cc77`, status `ingested`.
2. `extract-claims` → 2 accepted claims.
3. `link-concepts` → 5 concept links on diversity claim.
4. `build-relationships` → 1 relationship (`AI assistance` → `may_reduce` → `semantic diversity`, confidence 0.5, scope preserved) and 1 evidence row (stance `supports`, claim `clm_b25c649cc0da33ea`).

## 10. Safety Audit Status

- Required: no (no public routes or export changes; mock-only model path).
- Status: not run.
- Notes: CLI JSON excludes raw chunk text and local paths.

## 11. Spec Deviations

1. **Active status directly.** Validated relationships are written with `status = active` rather than a separate staging step, mirroring ticket-007's accepted-directly pattern.
2. **Confidence label mapping.** Golden Test 6 expresses confidence as a label; Python maps labels to REAL before persistence. Label strings are not stored on `relationships`.
3. **Placeholder claim ID resolution.** Mock fixture claim IDs are resolved to the semantic-diversity accepted claim in Python, same pattern as concept linking retargeting.

## 12. Known Failures

- None.

## 13. Rollback Plan

Revert branch `phase-1/ticket-009-mock-relationship-builder` (or merge revert on `main`). Delete `relationships` and `relationship_evidence` rows from local SQLite if created during manual testing. Migration `0002` can remain applied harmlessly or DB can be recreated.

## 14. Merge to Main

- Instruction source: `AGENTS.md` step 9 (temporary).
- Pre-merge `main` tip: `f69e49b`
- Branch: `phase-1/ticket-009-mock-relationship-builder`
- Merge result: `--no-ff` merge commit `705ff64492f0fc11f7f2e8ac5e5157a0bd9aea1a`; pushed `origin/main`.

## 15. Recommended Next Ticket

**ticket-010: Add score reconciliation with history (Golden Test 8)**

See `tickets/ticket-010.json`.

## 16. Can the Loop Continue?

**Yes.** The executable spine now covers ingest → extract-claims → link-concepts → build-relationships with durable persistence, mock-only model paths, and 41 passing golden tests. ticket-010 (score reconciliation) is the smallest next step toward Golden Test 8 without broadening into contradiction detection or public export.

## 17. Suggested Next Prompt

```txt
You are the Research Graph Engine implementation agent.

Read AGENTS.md, tickets/TICKET_QUEUE.md, tickets/ticket-010.json,
docs/agents/00_GOLDEN_TESTS.md (Test 8), and
agent_reports/2026-06-11_phase-1_ticket-009_mock-relationship-builder.md.

Implement ticket-010 only on branch phase-1/ticket-010-score-reconciliation.
Run pytest tests/golden, write agent report, update TICKET_QUEUE.md,
merge to main and push per AGENTS.md step 9.
```
