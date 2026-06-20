# Agent report — Live network source health → Atlas visibility (GO)

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Commits:** `1ae4aaf` (graph summary panel), prior `cc534c9` (atlas preview bundle)

## What we tested (not “great insights” yet)

```
real source discovery
→ source health persistence
→ purpose-fit counts
→ blocked/extractable status
→ Atlas preview visibility
```

**GO bar:** real source acquisition is visible and debuggable in Atlas.  
**PARTIAL is fine:** OpenAlex/arXiv finds sources but abstract/evidence yield is thin.  
**NO-GO:** live discovery or source-health persistence unreliable.

## Verdict: **GO** (source-health layer)

Live network smoke **passed**. Source discovery, health persistence, purpose-fit counts, and extractable/blocked posture are **reliable and Atlas-visible**.

Evidence acceptance is **PARTIAL** (0 accepted abstract claims on mock LLM) — expected at this phase and **not** a source-health NO-GO.

## Live commands

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"

python -m pytest tests/unit/test_live_network_source_health_smoke.py -m live_network -q
# 2 passed

# Operator export + public preview refresh
python -c "..."  # run_live_network_source_health_smoke → data/exports/live_network_source_health_smoke/
python scripts/refresh_atlas_source_health_preview.py `
  --input data/exports/live_network_source_health_smoke/atlas_source_health_run_latest.json
cd apps/public-site; npm run build
```

## Live run summary (2026-06-20)

| Signal | Result |
| --- | --- |
| Sources resolved | 5 (OpenAlex 1 + arXiv 4) |
| `sources_with_metadata` | 5 |
| Source status | 5 × `oa_pdf_available` |
| Quality gate | 5 × `extractable` |
| Purpose fit | 5 × `match` |
| Purpose gate | 5 × `accepted` |
| Failure reasons | none |
| Accepted claims | 0 (mock fixture `unsupported_claim` on real abstracts) |
| Rejected claims | 5 |
| Atlas artifact | public-safe (`assert_no_private_fields` = []) |

## Atlas preview after live refresh

`/atlas-preview` panels now reflect **live-network run artifact** (5 extractable sources, no blocked counts, purpose-fit tiles populated). Graph/readiness/gaps panels show thin-evidence posture (weak atoms, clustering packet recommendation).

## Public / private boundary

- Live export DB: `data/exports/live_network_source_health_smoke/` (operator-private; gitignored path pattern)
- Public commit surface: aggregated `atlas_source_health_run_latest.json` only — no `source_id`, quotes, paths, or prompts in published artifact
- Safety audit: **pass** after live artifact refresh + site build

## Top blockers (evidence layer — next packet scope)

1. Mock abstract extractor emits checksum-pinned fixture claim → `unsupported_claim` on all 5 live abstracts.
2. No live quote-backed abstract claim acceptance path wired to evidence atoms yet.
3. Graph summary remains thin (0 relationships / weak atoms) because claims never accepted.
4. Atlas trace preview still fixture-backed below the six run-artifact panels.

## Next recommended packet

### **Live Abstract Evidence → Atom Trace**

**Goal:** bridge from “Atlas shows source health” to “Atlas shows what the agent learned from real sources.”

```
live OpenAlex/arXiv abstract
→ quote-backed abstract claim
→ purpose-gated acceptance
→ evidence atom
→ relationship/cluster if possible
→ Atlas trace preview
```

**Acceptance hints:**

- ≥1 accepted abstract claim from live source on temp DB (mock or live LLM gate explicit)
- Purpose gate decision visible in run artifact / trace preview
- Public Atlas trace panel prefers live run artifact (no raw quotes / private IDs)
- Opt-in `live_network` pytest; default CI remains mock
