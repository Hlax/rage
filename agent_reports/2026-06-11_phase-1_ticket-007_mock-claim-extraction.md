---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-007 / mock-claim-extraction

## 1. Summary

Implemented mock LLM claim extraction for ingested sources via `research extract-claims --source <source_id>`. The mock client proposes candidate claims from deterministic fixtures; Python validates quote spans, scope, and required fields; accepted claims persist to `claims` with primary `claim_quotes` rows, and rejected claims persist with machine-readable reasons. Golden Tests 2–4 patterns pass in `tests/golden/test_02_claim_extraction.py`; all 33 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-007
- Ticket title: Add mock claim extraction (Golden Test 2)
- Branch: `phase-1/ticket-007-mock-claim-extraction`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-11

## 3. Scope

### In Scope

- `claim_extractor`: mock client integration, chunk-level extraction, source orchestration.
- `claim_validator`: deterministic acceptance/rejection with stored reasons.
- `ClaimRepository`: persist accepted claims + primary quotes; persist rejected claims.
- `research extract-claims` CLI subcommand with optional `--fixture` and `--db`.
- Golden Test 2 (`tests/golden/test_02_claim_extraction.py`) including quote-span and overgeneralized rejection patterns.
- Supporting creativity-scoped mock fixture for two accepted Golden Test 2 claims.

### Out of Scope / Non-Goals

- Live Ollama calls, concept linking, relationships, scoring, public export.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/claim_extractor.py` | Mock extraction, validation orchestration, `extract_claims_for_source`. |
| `rge/modules/claim_validator.py` | Deterministic validators for quote span, scope, overgeneralization, required fields. |
| `rge/db/repositories.py` | `ClaimRepository`, claim/quote ID helpers, public claim dict helper. |
| `rge/cli.py` | `extract-claims` subcommand. |
| `fixtures/llm_outputs/claim_extraction_creativity_scoped.json` | New: two scoped claims with quotes for Golden Test 2. |
| `fixtures/llm_outputs/claim_extraction_valid_and_missing_quote.json` | Scope aligned to pass validator scope-in-claim check. |
| `tests/golden/test_02_claim_extraction.py` | New: Golden Test 2 + rejection pattern tests. |
| `tests/golden/test_00_scaffold.py` | CLI help includes `extract-claims`. |
| `tickets/TICKET_QUEUE.md` | ticket-007 done; ticket-008 proposed. |
| `tickets/ticket-007.json` | Status `done`. |
| `tickets/ticket-008.json` | New: proposed concept linking ticket. |

## 5. Implementation Notes

- **Model proposes; Python validates.** `extract_claims` forces `RGE_LLM_MODE=mock` for this ticket; candidates never write directly to DB.
- **Fixture selection.** Creativity diversity chunk text selects `claim_extraction_creativity_scoped.json`; `--fixture` overrides for rejection tests.
- **Quote validation.** Quote spans are matched with whitespace normalization so multi-line source text still validates.
- **Idempotency.** Re-running `extract-claims` on a source with existing claims returns `already_extracted`.
- **Rejected claims retained.** `missing_quote_span` and `overgeneralized_scope` reasons stored on `claims.status = rejected`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| `research extract-claims` extracts scoped claims from ingested fixture | PASS | 2 accepted claims on creativity fixture. |
| Accepted claims include required fields + primary quote in `claim_quotes` | PASS | Asserted in golden tests. |
| Overgeneralized claims rejected with machine-readable reasons | PASS | `overgeneralized_scope` on "AI reduces creativity." |
| Claims without quote spans rejected (Golden Test 3) | PASS | `missing_quote_span` persisted. |
| `pytest tests/golden/test_02_claim_extraction.py` passes without Ollama | PASS | 4/4. |
| Existing golden tests still pass | PASS | 33/33. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pip install -e ".[dev]"` | PASS | Editable install OK. |
| `python -m pytest tests/golden/test_02_claim_extraction.py` | PASS | 4 passed in 0.68s. |
| `python -m pytest tests/golden` | PASS | 33 passed in 1.37s. |
| `python -m pytest` | PASS | 33 passed in 1.38s. |
| `python -m rge.cli extract-claims --source src_fac29b647fa3cc77` | PASS | 2 accepted, 0 rejected on previously ingested source. |

**Windows PATH note:** Use `python -m rge.cli` when `research.exe` is not on PATH.

## 8. Test Results

### Passing

- `tests/golden/test_02_claim_extraction.py` — 4/4.
- All prior golden tests — 29/29 unchanged.

### Failing

- None.

## 9. Safety Audit Status

- Required: no (no public routes or export changes; mock-only model path).
- Status: not run.
- Notes: CLI JSON output excludes raw chunk text and private quote storage details beyond accepted claim metadata.

## 10. Spec Deviations

1. **Accepted status vs staged.** Validated claims are written directly with `status = accepted` rather than a separate staging step. Simpler Phase 1 path; staging can be added when multi-step review is implemented.
2. **Creativity fixture added.** `claim_extraction_creativity_scoped.json` was added because existing fixtures could not satisfy Golden Test 2 (two accepted scoped claims) and Test 3 (one missing quote) simultaneously without override.
3. **Extractor forces mock mode.** `extract_claims_for_source` sets `RGE_LLM_MODE=mock` regardless of config, per ticket non-goal of no Ollama.

## 11. Known Risks / Gaps

- Scope validation requires scope text to appear in `claim_text` (case-insensitive); may reject valid paraphrases until rewriter logic exists.
- No `model_invocations` table writes yet; extractor metadata lives on claim rows only.
- Re-extraction with a different `--fixture` on an already-extracted source returns `already_extracted` without replacing claims.

## 12. Rollback Plan

Revert branch `phase-1/ticket-007-mock-claim-extraction`. Delete `claims` and `claim_quotes` rows from local `data/db/creative_research.sqlite` if created during manual testing.

## 13. Recommended Next Ticket

**ticket-008: Add mock concept linking (Golden Test 5)**

- Implement `research link-concepts --source <source_id>` using mock client.
- Map accepted claims to creativity domain concepts via `claim_concepts`.
- Add `tests/golden/test_05_concept_linking.py` (or next sequential golden test file per convention).
- Non-goals: relationships, scoring, Ollama, public export.

See `tickets/ticket-008.json`.

## 14. Suggested Next Prompt

```txt
You are the Research Graph Engine implementation agent.

Read AGENTS.md, tickets/TICKET_QUEUE.md, tickets/ticket-008.json,
docs/agents/00_GOLDEN_TESTS.md (Test 5), and
agent_reports/2026-06-11_phase-1_ticket-007_mock-claim-extraction.md.

Implement ticket-008 only on branch phase-1/ticket-008-mock-concept-linking:
- Add research link-concepts command.
- Link accepted claims to creativity domain concepts via claim_concepts.
- Use mock LLM mode only; no Ollama.
- Add golden test for concept linking.

Run pytest tests/golden, write an agent report, update TICKET_QUEUE.md, commit one ticket.
```
