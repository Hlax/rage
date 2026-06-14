---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-127
---

# ticket-127: Arbitrary Manual Text Live Extraction Fall-Through (NM-4 Recenter)

## Summary

Completed NM-4 product-risk proof: calibrated Ollama claim extraction for arbitrary
`manual_text` sources absent from the checksum fixture map. Live operator run on
a fresh source persisted **1 accepted** and **1 rejected** claim to the gitignored
evidence DB. ticket-112 fall-through plumbing retained; changes are prompt
calibration and contract wiring only.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-127 |
| Branch | `phase-2/ticket-127-arbitrary-manual-live-fallthrough` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-127_arbitrary-manual-live-fallthrough-audit.md` (GO) |
| Principal audit gate | satisfied (post-ticket-125 checkpoint; pre-ticket audit on file) |
| Main tip before branch | `aa2ae06` |

## Scope

### In

- Ollama prompt calibration for `manual_text_arbitrary_live` contract mode
- Pass `manual_text_arbitrary_live` contract when `--live-manual-fallthrough` runs
- Committed calibration source `fixtures/sources/ticket127_arbitrary_manual_live.txt`
- Extended unit tests (fixture-map exclusion, contract hint)
- Live operator proof on gitignored evidence DB

### Out

- Fall-through re-plumbing (ticket-112)
- Validator weakening
- Public export/site changes
- Cloud/source discovery
- Concept linking live fall-through (deferred ticket-128)

## Changed files

| File | Change |
|------|--------|
| `rge/llm/ollama_client.py` | Prompt v0.1.1; manual_text arbitrary live calibration block |
| `rge/modules/claim_extractor.py` | `live_manual_fallthrough` contract hint |
| `fixtures/sources/ticket127_arbitrary_manual_live.txt` | Calibration source (not in fixture map) |
| `tests/unit/test_ollama_claim_prompt.py` | Manual-text calibration prompt test |
| `tests/unit/test_manual_live_fallthrough.py` | +2 unit tests |
| `tickets/ticket-127.json` | status done |
| `tickets/ticket-128.json` | seeded next NM-4 pipeline step |
| `tickets/TICKET_QUEUE.md` | ticket-127 done |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Fresh arbitrary source not in fixture map ingestible | **PASS** |
| 2 | Explicit live mode falls through to Ollama | **PASS** |
| 3 | ≥1 validated accepted claim in gitignored DB | **PASS** (live: 1 accepted) |
| 4 | Rejections preserved | **PASS** (live: 1 rejected `unsupported_claim`) |
| 5 | Synthnote tests deterministic | **PASS** |
| 6 | Golden mock-only pass | **PASS** (142) |
| 7 | Safety audit pass | **PASS** |
| 8 | Public export/site untouched | **PASS** |
| 9 | Evidence report committed | **PASS** (this file) |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_manual_live_fallthrough.py -q   # 8 passed
python -m pytest tests/unit/test_manual_source_pipeline_e2e.py -q # 3 passed
python -m pytest tests/unit/test_live_extraction_write.py -q      # 5 passed
python -m pytest tests/golden -q                                  # 142 passed
python -m pytest -q                                               # 460 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                 # pass
```

## Manual CLI verification (live)

```powershell
$env:RGE_LLM_MODE = "ollama"; $env:RGE_ALLOW_LIVE_LLM = "1"

python -m rge.cli ingest fixtures/sources/ticket127_arbitrary_manual_live.txt `
  --domain creativity --source-type manual_text `
  --source-title "Ticket-127 NM-4 live proof" `
  --db data/db/live_research_evidence.sqlite

python -m rge.cli extract-claims --source src_1b8354e5f2203f82 `
  --db data/db/live_research_evidence.sqlite --live-manual-fallthrough
```

| Field | Value |
|-------|-------|
| Checksum | `1b8354e5f2203f8236de918c8422f1c825af483c98abbfaa5e680db27f2d1aa5` |
| In fixture map | **No** |
| `accepted_count` | **1** |
| `rejected_count` | **1** |
| Accepted scope | `this songwriting workshop` |
| Rejection | `unsupported_claim` (quote/SPO mismatch on second candidate) |
| `db_writes` | true |
| Model | `qwen2.5:7b` via Ollama |

## Spec deviations

None. Prompt template version bumped to `0.1.1` for calibration traceability.

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

**ticket-128** — Arbitrary manual live concept linking fall-through (NM-4 pipeline
continuation). Requires pre-ticket audit (medium risk, live Ollama).

## Suggested next prompt

```text
/rge-principal-audit
```

(Cadence: 2 done tickets since post-ticket-125 audit after this merge; audit due
before ticket-128 if a third ticket lands first.)
