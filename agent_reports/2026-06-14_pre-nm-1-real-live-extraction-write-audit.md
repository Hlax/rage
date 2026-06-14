---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
scope: NM-1 live validated extraction write to gitignored DB
---

# Pre-Ticket Audit: NM-1 Real Live Extraction Write

## Verdict: **GO**

Live Ollama is reachable and the configured model is available. The existing
validator + `extract_claims_for_source` persistence path can be wrapped with
explicit live opt-in gates without weakening safety boundaries.

## Is a live Ollama model available?

**Yes.** `python -m rge.cli model-health` with `RGE_ALLOW_LIVE_LLM=1`:

- `reachable`: true
- `model_available`: true
- `configured_model`: `qwen2.5:7b`
- `available_models`: includes `qwen2.5:7b`

## What model is configured?

- Default: `qwen2.5:7b` via `RGE_LOCAL_LLM` / `rge/config.py`
- Provider: `ollama` at `http://127.0.0.1:11434`
- Live calls require `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`

## Where is the model adapter boundary?

- `rge/llm/ollama_client.py` — HTTP structured JSON calls; returns typed
  `CandidateClaimBatch_v0_1` only; never writes to DB
- `rge/llm/registry.get_model_client()` — selects mock vs ollama
- `rge/llm/mode.effective_llm_mode()` — fail-closed: mock unless both ollama
  mode and live opt-in are set
- `rge/modules/claim_extractor.extract_candidate_claims()` — calls client;
  fixture lookup applies only to `MockModelClient`

## Where are accepted/rejected claims written today?

- `rge/modules/claim_extractor.extract_claims_for_source()` →
  `ClaimRepository.insert_accepted()` / `insert_rejected()` in
  `rge/db/repositories.py`
- Quote provenance: `claim_quotes` table via `insert_accepted`
- Existing `research extract-claims` CLI uses this path but has no explicit
  live-write gate or fixture-map exclusion check

## What command path currently supports live extraction?

| Path | DB writes | Live inference |
|------|-----------|----------------|
| `probe-extract-claims` | **No** (`db_writes: false`) | Yes (opt-in) |
| `research extract-claims` | Yes (default DB) | Yes if env set, but no explicit operator gate |
| Manual synthnote spine | Yes | **No** — checksum-keyed mock fixtures only |

## What prevents live output from writing to the graph today?

1. `effective_llm_mode()` defaults to mock without `RGE_ALLOW_LIVE_LLM=1`
2. Live probes are architecturally report-only (`live_probe.py`)
3. Manual pipeline uses `manual_source_fixture_map.json` for mock candidates
4. No operator command combines: live gate + non-fixture checksum proof +
   dedicated gitignored evidence DB

## Minimal safe implementation path

1. Add `rge/modules/live_extraction_write.py`:
   - Reuse `assert_live_probe_env` / `assert_ollama_health` gates
   - Assert source checksum **not** in `fixtures/manual_source_fixture_map.json`
   - Force Ollama client; call existing `extract_claims_for_source`
   - Default DB: `data/db/live_research_evidence.sqlite` (gitignored)
2. Add CLI `extract-claims-live` with required `--source` and optional `--db`
3. Proof flow:
   - Create gitignored source under `data/sources/manual/creativity/`
   - `research ingest` → gitignored evidence DB
   - `research extract-claims-live` → validated accepted/rejected rows
4. Unit tests: gate failures (mock mode, fixture-map match) with mocked health
5. Evidence report with counts, claim text, quote span, checksum proof

## Expected files to change

- `rge/modules/live_extraction_write.py` (new)
- `rge/cli.py` (new subcommand)
- `tests/unit/test_live_extraction_write.py` (new)
- `agent_reports/2026-06-14_nm-1-real-live-extraction-write-proof.md` (after run)

## Explicitly out of scope

- Public export / site mutation
- Validator weakening
- Cloud/OpenAI providers
- General arbitrary-source pipeline (NM-4)
- Checksum fixture map changes
- Golden test live Ollama dependency
- ticket-111 README cross-link as primary work
