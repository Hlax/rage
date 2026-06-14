---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-112
---

# Pre-Ticket Audit: ticket-112 Arbitrary Manual Live Fall-Through

## Verdict: **GO**

NM-1 established the validated live write boundary. The remaining gap is wiring
the standard manual `extract-claims` path to use live Ollama when a `manual_text`
checksum is absent from the fixture map, with explicit opt-in and mock/golden
determinism preserved for pinned sources.

## Where does the current manual checksum fixture path live?

- `fixtures/manual_source_fixture_map.json` — checksum → fixture filenames
- `rge/modules/manual_source_fixtures.py` — `extract_fixture_for_manual_source(source)`
- `rge/modules/claim_extractor.py`:
  - `_default_fixture_for_source_chunk()` calls `extract_fixture_for_manual_source`
  - When `MockModelClient`, fixture_name is passed to `extract_claims()`
  - Checksum-pinned synthnote sources resolve to hand-authored JSON in mock mode

## Where does NM-1 validated live writing live?

- `rge/modules/live_extraction_write.py` — gates, fixture-map exclusion, provenance payload
- `rge/cli.py` — `extract-claims-live` command
- Reuses `extract_claims_for_source()` → validator → `ClaimRepository` persistence
- Default evidence DB: `data/db/live_research_evidence.sqlite` (gitignored)
- Refuses default `creative_research.sqlite` and checksum-pinned sources

## What should call what?

```
ingest (manual_text, arbitrary checksum)
  → extract-claims [--live-manual-fallthrough] [--db evidence.sqlite]
      → claim_extractor: if manual_text + no fixture map + live enabled + explicit flag
          → Ollama client (no fixture_name)
      → else if mock mode + checksum map hit
          → MockModelClient + pinned fixture
      → else if mock mode + manual_text + no map
          → raise clear error (do not silently use generic golden fixtures)
      → validate_candidate_claims (unchanged)
      → ClaimRepository insert_accepted/rejected (unchanged)
```

`extract-claims-live` remains as the narrow NM-1 operator command; ticket-112
adds the fall-through flag on `extract-claims` for pipeline ergonomics while
reusing `live_extraction_write` gate helpers.

## Smallest safe integration path

1. Add `manual_text_requires_live_or_fixture_map(source)` helper in
   `manual_source_fixtures.py` or `claim_extractor.py`.
2. In `_default_fixture_for_source_chunk`: when `manual_text` + no map entry,
   return `None` and let caller decide (mock → error; live+flag → Ollama).
3. Add `--live-manual-fallthrough` flag to `extract-claims` that:
   - Requires `RGE_LLM_MODE=ollama` + `RGE_ALLOW_LIVE_LLM=1`
   - Requires non-default DB or reuses evidence DB default when flag set
   - Delegates gate checks to `live_extraction_write.assert_*` helpers
4. Unit tests with mocked Ollama client (no golden Ollama dependency).
5. Optional live proof in ticket report (operator machine), not in CI.

## Mock/golden determinism preservation

- Checksum-pinned synthnote paths unchanged: mock still resolves fixtures by map.
- Golden tests force `RGE_LLM_MODE=mock`; no `--live-manual-fallthrough` in golden spine.
- Unknown `manual_text` in mock without map: **fail closed with explicit error**
  instead of silently using `claim_extraction_valid_and_missing_quote.json` heuristics.
- Existing `test_manual_source_pipeline_e2e.py` / idempotency tests unchanged.

## Live mode explicit gating

Layers (all required for fall-through):

1. `RGE_LLM_MODE=ollama`
2. `RGE_ALLOW_LIVE_LLM=1`
3. CLI `--live-manual-fallthrough` on `extract-claims`
4. Non-default or explicit evidence `--db` path
5. `assert_ollama_health()` before inference

## Avoiding silent empty candidates

Today in mock mode, unknown manual_text without map uses generic chunk heuristics
(not empty, but **wrong canned content**). Ticket-112 changes this to an explicit
error in mock mode.

In live mode with flag, `OllamaModelClient.extract_claims()` always runs inference;
empty batch is surfaced in result JSON with `accepted_count: 0` and honest report.

## Proving source absent from fixture map

Reuse `resolve_manual_source_fixture(checksum, "extract_claims") is None` and
`assert_checksum_not_in_fixture_map()` from NM-1. Include checksum in CLI JSON output.

## Tests to add

`tests/unit/test_manual_live_fallthrough.py`:

- Checksum-pinned manual source in mock mode still uses fixture (no live call)
- Unknown manual_text in mock mode without flag raises clear error
- `--live-manual-fallthrough` blocked when `RGE_ALLOW_LIVE_LLM=0`
- `--live-manual-fallthrough` blocked on default graph DB
- With mocked Ollama client, unknown manual_text persists validated claims
- `assert_checksum_not_in_fixture_map` rejects synthnote checksums

## Expected files to change

- `rge/modules/claim_extractor.py`
- `rge/modules/live_extraction_write.py` (shared gate helpers)
- `rge/cli.py` (`extract-claims` flag + DB guard)
- `tests/unit/test_manual_live_fallthrough.py` (new)
- `agent_reports/2026-06-14_ticket-112_arbitrary-manual-live-fallthrough.md`

## Out of scope

- Cloud providers, public export/site, validator changes
- LangGraph/FastAPI/embeddings
- Replacing golden fixtures
- Source discovery / URL fetch
- Concept linking / relationship live fall-through (claim extraction only)
