---
template_id: implementation_report
status: done
date: 2026-06-14
workstream: NM-1
risk_level: medium
---

# NM-1: Real Live Extraction Write Proof

## Verdict

**PASS** — first committed proof that a non-checksum-pinned source produced ≥1
validator-accepted claim via live Ollama inference, written to a gitignored local DB.

## Commands run

```powershell
# Pre-flight
python -m rge.cli model-health   # RGE_ALLOW_LIVE_LLM=1

# Proof source (gitignored)
# data/sources/manual/creativity/nm1_human_ai_creative_work.txt

$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"

python -m rge.cli ingest data/sources/manual/creativity/nm1_human_ai_creative_work.txt `
  --domain creativity --source-type manual_text `
  --source-title "NM-1 human-AI creative workshop note" `
  --db data/db/live_research_evidence.sqlite

python -m rge.cli extract-claims-live --source src_88432c967cec9995 `
  --db data/db/live_research_evidence.sqlite

# Mock verification (post-implementation)
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q          # 140 passed
python -m pytest -q                       # 390 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

## Model used

- Provider: `ollama`
- Model: `qwen2.5:7b`
- Schema version: `0.1.0`
- Base URL: `http://127.0.0.1:11434`

## DB path

`data/db/live_research_evidence.sqlite` — **gitignored** under `data/`. Not committed.

## Source

| Field | Value |
|-------|-------|
| Path | `data/sources/manual/creativity/nm1_human_ai_creative_work.txt` |
| Title | NM-1 human-AI creative workshop note |
| Source ID | `src_88432c967cec9995` |
| Checksum | `88432c967cec9995afd8cc5a6422c025bd27f4540ec1844cc87a120a06101dfd` |
| Chunk ID | `chk_88432c967cec9995_0_149085e8` |

## Fixture-map non-match proof

Checksum `88432c967cec9995…` is **not** present in
`fixtures/manual_source_fixture_map.json` (only `2c53bfdf…` and `c5d1add6…` are listed).
`extract-claims-live` enforced `fixture_map_match: false`.

## Results

| Metric | Value |
|--------|------:|
| Accepted count | 1 |
| Rejected count | 1 |
| DB writes | true |

### Accepted claim

- **Text:** AI-assisted pairs produced more revised lines per hour during the same two-hour session.
- **Scope:** two-hour session
- **Quote span:** Facilitators reported that human-AI pairs produced more revised lines per hour during the same two-hour session.
- **Char range:** 277–389

### Rejection

- **Text:** AI-assisted pairs reused similar rhyme schemes more often than unassisted pairs.
- **Reason:** `overgeneralized_scope` (validator correctly rejected — scope not embedded in claim)

## Implementation

- New module: `rge/modules/live_extraction_write.py`
- New CLI: `research extract-claims-live` (`python -m rge.cli extract-claims-live`)
- Unit tests: `tests/unit/test_live_extraction_write.py`

Safety boundaries preserved:

- Model proposes candidates only; Python validator unchanged
- Default graph DB write refused
- Public export/site untouched
- Golden/mock path unchanged

## Limitations and next risks

1. Single source, single chunk, single domain — not arbitrary-source pipeline (NM-4).
2. Live extraction quality varies; one run is not a calibration floor.
3. BOM in source file produced `\ufeff` in chunk preview — operator hygiene note.
4. No concept linking / relationships / public cards from this proof yet.
5. Re-running on same source is idempotent (`already_extracted`).

## Next move

**NM-4** — manual pipeline live fall-through for any `manual_text` without fixture-map entry.
