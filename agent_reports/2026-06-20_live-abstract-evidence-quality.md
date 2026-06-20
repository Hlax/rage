# Live Abstract Evidence Quality

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Packet:** Live Abstract Evidence Quality  
**Verdict:** **GO**

## Goal

Prove live OpenAlex/arXiv abstract sources produce useful quote-backed evidence — not just source health — for:

> How does AI affect human creativity?

Mock LLM only (`RGE_LLM_MODE=mock`); deterministic live abstract quote extraction. Explicit live-network opt-in; no paid API; no PDF downloads.

## What shipped

### Quality summary + verdict (`rge/modules/live_arbitrary_source_health.py`)

- `build_live_abstract_evidence_quality_summary()` — aggregates required operator metrics
- `classify_live_abstract_evidence_quality_verdict()` — GO / PARTIAL / NO-GO
- `run_live_network_abstract_evidence_quality_smoke()` — gated operator entry point
- Env gate: `RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE=1` (requires atom-trace + source-health gates)

### Tests

- `tests/unit/test_live_abstract_evidence_quality.py` — summary/verdict unit tests (network-free)
- `tests/unit/test_live_network_abstract_evidence_quality_smoke.py` — opt-in `live_network` smoke

## Operator commands

```powershell
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE = "1"
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"

python -m pytest tests/unit/test_live_network_abstract_evidence_quality_smoke.py -m live_network -q

# Export Atlas-safe artifact (operator-private path)
python -c "..."  # see agent_reports/2026-06-20_live-abstract-evidence-quality-latest.json

# Public preview already wired via committed run artifact (golden gate)
cd apps/public-site; npm run build
```

## Live run summary (2026-06-20)

| Signal | Result |
| --- | --- |
| Live source count | 5 |
| Abstract availability count | 5 |
| Claims accepted | 5 |
| Claims rejected | 0 |
| Rejection reasons | none |
| Purpose-fit (`match`) | 5 |
| Purpose gate (`accepted`) | 5 |
| Quote-backed accepted | 5 |
| Evidence atoms | 5 |
| Relationships | 5 |
| Trace summary rows | 5 |
| Atlas artifact public-safe | yes |

## Atlas preview proof

Committed public artifact `apps/public-site/public/data/atlas_source_health_run_latest.json` (refreshed in golden gate) supplies run-artifact data for:

- source health
- graph summary
- readiness
- trace summary

`npm run build` — **pass** (13 static pages). Panel wiring covered by `tests/unit/test_atlas_source_health_run_preview.py`.

## Verification

| Check | Result |
| --- | --- |
| `tests/unit/test_live_abstract_evidence_quality.py` | 4 passed |
| `tests/unit/test_live_network_abstract_evidence_quality_smoke.py` (`live_network`) | 1 passed |
| `python -m rge.cli verify --skip-site` | **pass** (1060 pytest) |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| `cd apps/public-site && npm run build` | **pass** |

## Public / private boundary

- Operator export: `data/exports/live_abstract_evidence_quality/` (gitignored pattern)
- Public surface: aggregated run artifact fields only — no `source_id`, quotes, paths, or prompts
- Machine-readable summary: `agent_reports/2026-06-20_live-abstract-evidence-quality-latest.json`

## Next recommended packet

**Operator Loop Full Atlas Refresh Checklist** — single operator command chaining live quality smoke → artifact sync → site build.
