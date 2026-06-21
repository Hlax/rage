# Multi-Question Live Abstract Runs (cycle restart)

**Date:** 2026-06-20  
**Packet:** Multi-Question Live Abstract Runs  
**Cycle:** Operator loop restart after **live** full-atlas close (second cycle — all 7 packets refreshed)  
**Verdict:** **GO**

## Goal

Prove live OpenAlex/arXiv abstract evidence across 5 question types with purpose gating — generic AI/diversity evidence must not pass unrelated agency/style questions.

Mock LLM only; explicit live-network opt-in; no paid APIs; no PDF downloads.

## Cycle restart changes

- Added `multi_question_verdict` / `multi_question_rationale` to the public Atlas bundle (classified before sync).
- Wired Atlas preview panel (`resolveMultiQuestionLiveAbstractPreview`) on `/atlas-preview`.
- Fixed full-atlas refresh registry: validates `multi_question_verdict` on the multi-question artifact.
- `NEXT_RECOMMENDED_PACKET` → **Live Source Expansion** (`live-source-expansion`).

## Question profiles

| ID | Question type | Gate |
| --- | --- | --- |
| `mq_ai_human_creativity` | AI + human creativity | open |
| `mq_ai_assistance_diversity` | AI assistance + idea quality/diversity | open |
| `mq_cocreation_agency` | Human-AI co-creation + agency | strict |
| `mq_artist_style_originality` | Artists/designers + originality/style | strict |
| `mq_ai_creativity_benchmark` | AI creativity evaluation/benchmarks | open |

## Purpose routing proof

Generic AI/diversity fixture text:

- **Rejected** on strict agency and style questions
- **Accepted** on open creativity/diversity/benchmark questions

Live agency question (`mq_cocreation_agency`) showed purpose differentiation:

- `purpose_fit_status_counts`: `{mismatch: 3, match: 2}`
- `claims_accepted`: 1 / `claims_rejected`: 4

## Live run summary (2026-06-20 — post live full-atlas close)

| Question | Sources | Accepted | Rejected | Purpose-fit |
| --- | ---: | ---: | ---: | --- |
| AI + creativity | 5 | 5 | 0 | match: 6 |
| AI assistance + diversity | 5 | 5 | 0 | match: 5 |
| Co-creation + agency | 5 | 1 | 4 | mismatch: 3, match: 2 |
| Artist style + originality | 5 | 3 | 2 | match: 5 |
| AI creativity benchmark | 5 | 5 | 0 | match: 5 |

**Aggregate:** 19 accepted claims · 5/5 questions with live sources · purpose routing valid

## Artifacts

- Public bundle: `apps/public-site/public/data/atlas_multi_question_live_abstract_latest.json`
- Operator export: `data/exports/multi_question_live_abstract/` (per-question DBs + artifacts)

## Operator command

```powershell
$env:RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE = "1"
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE = "1"
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python scripts/run_multi_question_live_abstract_smoke.py --sync-public
```

## Verification

| Command | Status |
| --- | --- |
| Live operator smoke `--sync-public` | **PASS** (GO, 5/5 questions) |
| `pytest tests/unit/test_live_network_multi_question_abstract_smoke.py tests/unit/test_full_atlas_refresh_checklist.py -q` | **PASS** (8 passed) |
| `python -m rge.modules.safety_auditor --audit full` | **PASS** |
| `cd apps/public-site && npm run build` | **PASS** |

## Next recommended packet

**Live Source Expansion** (`live-source-expansion`) — OpenAlex, arXiv, Unpaywall DOI/OA enrichment for better source diversity.
