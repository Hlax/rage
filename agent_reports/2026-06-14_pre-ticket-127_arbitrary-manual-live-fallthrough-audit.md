---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-127
category: product-risk reduction / NM-4
---

# Pre-Ticket Audit: ticket-127 Arbitrary Manual Live Fall-Through (NM-4 Recenter)

## Verdict: **GO** (hardened scope)

ticket-112 already landed the fall-through **plumbing** (`--live-manual-fallthrough`,
mock fail-closed, unit tests, gitignored DB writes). ticket-127 must **complete
NM-4 product-risk proof**: live Ollama on arbitrary real text with **≥1 validated
accepted claim** in a gitignored DB. Do **not** re-implement the fall-through path
or seed another docs/operator chain.

## Recenter context

| Span | Nature |
|------|--------|
| ticket-120–122 | NM-5 runtime/test work (real) |
| ticket-123–125 | NM-5 docs cross-links only |
| ticket-126 | Bounded operator visibility bridge (done) |
| **ticket-127** | **NM-4 product-risk reduction (this audit)** |

## Where does the current checksum fixture path live?

| Location | Role |
|----------|------|
| `fixtures/manual_source_fixture_map.json` | Checksum → fixture filenames for synthnote spine |
| `rge/modules/manual_source_fixtures.py` | `extract_fixture_for_manual_source()`, `manual_text_lacks_extract_fixture()` |
| `rge/modules/claim_extractor.py` | `_default_fixture_for_source_chunk()` resolves pinned fixtures; mock fail-closed when absent |

Checksum-pinned synthnote sources (`fixtures/sources/manual_synthnote*.txt`) remain
deterministic in mock mode.

## Where does NM-1 live validated writing live?

| Location | Role |
|----------|------|
| `rge/modules/live_extraction_write.py` | Gate helpers, `extract_claims_manual_live_fallthrough()`, provenance payload |
| `rge/cli.py` | `extract-claims-live` (NM-1) and `extract-claims --live-manual-fallthrough` (ticket-112) |
| Default evidence DB | `data/db/live_research_evidence.sqlite` (gitignored) |
| Persistence | `ClaimRepository` insert accepted/rejected after `validate_candidate_claims` |

No model output writes directly to accepted tables; Python validates first.

## What command path should fall through to live extraction?

```
ingest <arbitrary.txt> --domain creativity --source-type manual_text --db data/db/live_research_evidence.sqlite

extract-claims --source <source_id> --db data/db/live_research_evidence.sqlite --live-manual-fallthrough
  (requires RGE_LLM_MODE=ollama, RGE_ALLOW_LIVE_LLM=1)
```

`extract-claims-live` remains the narrow NM-1 operator command; `--live-manual-fallthrough`
is the pipeline ergonomics path from ticket-112.

## How will mock/golden determinism be preserved?

- Golden tests force `RGE_LLM_MODE=mock`; no `--live-manual-fallthrough` in golden spine.
- Checksum-pinned synthnote paths unchanged (`test_manual_source_pipeline_e2e.py`, idempotency tests).
- Unknown `manual_text` in mock without map: explicit error (fail-closed since ticket-112).
- ticket-127 changes must not alter golden fixtures or weaken validators.

## How will live mode be explicitly gated?

All layers required (unchanged from ticket-112):

1. `RGE_LLM_MODE=ollama`
2. `RGE_ALLOW_LIVE_LLM=1`
3. `--live-manual-fallthrough` on `extract-claims`
4. Explicit gitignored `--db` (evidence DB default when flag set)
5. `assert_ollama_health()` before inference

## How will the system avoid silently returning empty candidates for arbitrary real text?

| Mode | Behavior |
|------|----------|
| Mock, no fixture map | Raises clear error (no generic golden fallback) |
| Live + flag | Runs Ollama inference; JSON reports `accepted_count` / `rejected_count` |
| Live, no flag | Does not fall through; mock fail-closed or pinned fixture only |

ticket-112 live proof confirmed fall-through runs inference but got **0 accepted /
2 rejected** (`overgeneralized_scope`). ticket-127 must improve live acceptance
via **prompt/source calibration** (not validator weakening) and document results
honestly.

## How will the system prove the source is absent from the fixture map?

Reuse existing helpers:

- `manual_text_lacks_extract_fixture(source)` in `manual_source_fixtures.py`
- `assert_checksum_not_in_fixture_map()` in `live_extraction_write.py`
- Include source checksum in CLI JSON output (already in ticket-112 payload)

## What tests need to be added?

| Test | Purpose |
|------|---------|
| Extend `tests/unit/test_manual_live_fallthrough.py` | Regression for gates and mock fail-closed |
| Live operator evidence (report only, not CI) | Arbitrary `.txt` ingest + extract with ≥1 accepted row |
| Optional calibration unit test | Stub Ollama client returning validator-passing SPO claims |

Do **not** add Ollama to golden tests or default pytest collection.

## What files are expected to change?

| File | Likely change |
|------|---------------|
| `rge/llm/ollama_client.py` or claim prompt templates | Live prompt calibration for scoped manual_text claims |
| `rge/modules/claim_extractor.py` | Minor prompt/context wiring if needed |
| `data/sources/manual/creativity/` (gitignored) | Operator arbitrary source for live proof |
| `tests/unit/test_manual_live_fallthrough.py` | Extended regression |
| `agent_reports/2026-06-14_ticket-127_arbitrary-manual-live-fallthrough.md` | Evidence report with live DB row counts |

**Out of scope for file changes:** public site, export policy, schema migrations,
source discovery/fetcher, cloud providers.

## What is out of scope?

Cloud/OpenAI/OpenRouter, public export/site, source discovery/fetcher,
Playwright/Scrapfly, internet crawling, validator weakening, golden fixture
replacement, LangGraph/FastAPI/embedding architecture, NM-5 docs chain.

## Ollama / Qwen environment

| Check | Result |
|-------|--------|
| Ollama installed | **Yes** — `C:\Users\guestt\AppData\Local\Programs\Ollama\ollama.exe` |
| Version | **0.21.0** |
| Qwen model found | **Yes** — `qwen2.5:7b` (4.7 GB, modified 2 days ago) |
| Download performed | **No** — model already present |
| `model-health` | **ok** — `model_available: true`, `configured_model: qwen2.5:7b`, `live_llm_enabled: true` |

## Hardened scope for ticket-127 implementation

### In

1. Re-verify ticket-112 fall-through on a **fresh** arbitrary source not in fixture map.
2. Calibrate live claim prompt and/or operator source text so **≥1 claim passes**
   Python validation (scope, SPO, quote span) in gitignored evidence DB.
3. Preserve rejections in DB when produced; report honestly if none.
4. Keep mock/golden/synthnote spine deterministic.

### Out

- Re-plumbing `--live-manual-fallthrough` (already done).
- Validator rule weakening.
- Docs cross-link chain.
- Cloud/source discovery.

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-127 | **GO** |
| Broaden to source discovery / cloud | **NO-GO** |
| Seed another NM-5 docs ticket | **NO-GO** |

## Next command

```text
/rge-run-next-ticket
```

(Targets **ticket-127 / NM-4** — live accepted-claim proof on arbitrary real text.)
