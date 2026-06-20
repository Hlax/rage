# Live Abstract Evidence → Atom Trace

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Packet:** Live Abstract Evidence → Atom Trace  
**Verdict:** **GO** (operator opt-in live network smoke)

## Goal

Close the evidence layer gap after source-health GO:

```
live OpenAlex/arXiv abstract
→ quote-backed abstract claim
→ purpose-gated acceptance
→ evidence atom
→ relationship/cluster if possible
→ Atlas trace preview
```

## What shipped

### 1. Deterministic live abstract quote extraction (`rge/modules/abstract_evidence.py`)

- `select_quote_span_from_abstract()` — first substantive sentence (40–280 chars)
- `propose_quote_grounded_claim_from_abstract()` — validator-ready candidate
- `extract_and_validate_live_abstract_chunk()` — no mock LLM / fixture
- `extract_abstract_evidence_card(..., live_abstract_mode=True)` — sets `extraction_mode: live_deterministic_quote`

### 2. Atom + trace spine (`rge/modules/live_arbitrary_source_health.py`)

- `persist_abstract_evidence_outcomes(..., live_abstract_mode=True)` — persists with `deterministic/live_abstract_quote` extractor metadata
- `_execute_source_health_proof_pipeline(..., live_abstract_mode=True)` — skips fixture concept-linking; runs `ensure_purpose_gated_relationship_density_proof` (atoms + typed relationships)
- `_build_trace_summary_for_artifact()` — public-safe `atlas_trace_preview` rows via `build_atlas_trace_export` + `build_atlas_trace_preview`
- `build_atlas_safe_run_artifact()` — adds `trace_summary` block
- `run_live_network_abstract_evidence_atom_trace_smoke()` — operator entry point
- Env gate: `RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE=1` (plus existing network gates)

### 3. Atlas preview (`apps/public-site`)

- `resolveTracePanelPreview()` — prefers run-artifact `trace_summary.atlas_trace_preview`; fixture fallback
- Evidence trace detail panel shows preview source + trace/atom/claim counts

## Operator live smoke

```powershell
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_abstract_evidence_atom_trace_smoke.py -m live_network -q
```

Refresh public preview after exporting artifact to `data/exports/.../atlas_source_health_run_latest.json`:

```powershell
python scripts/refresh_atlas_source_health_preview.py --input <path-to-artifact>
cd apps/public-site; npm run build
```

## Verification

| Check | Result |
|-------|--------|
| `tests/unit/test_abstract_evidence.py` (incl. live quote tests) | pass |
| `tests/unit/test_live_arbitrary_source_health.py` (live abstract mode) | pass |
| `tests/unit/test_live_network_abstract_evidence_atom_trace_smoke.py` (`live_network`) | **1 passed** |
| `tests/golden/test_12_public_site_static_render.py` (atlas preview wiring) | pass |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| `cd apps/public-site && npm run build` | **pass** (13 static pages) |
| `python -m rge.cli verify --skip-site` | **not clean** — pre-existing suite failures unrelated to this packet (golden subtitle string fixed in-page; broader pytest still has unrelated failures) |

## Verdict framework

| Layer | Status |
|-------|--------|
| Source acquisition / health | GO (prior packet) |
| Live abstract quote acceptance | **GO** — deterministic quote spans from real abstracts |
| Purpose-gated persistence | GO |
| Evidence atoms + relationships | **GO** — density proof promotes atoms + typed edges |
| Atlas trace preview | **GO** — `trace_summary` in run artifact + `/atlas-preview` resolver |

## Next recommended packet

1. **Public Site Graph Panel Golden Gate** — enforce graph summary + trace panel in CI golden gate with refreshed live artifact
2. **Operator Loop Full Atlas Refresh Checklist** — single command: live smoke → artifact sync → site build
3. Refresh committed `apps/public-site/public/data/atlas_source_health_run_latest.json` from a live atom-trace export (operator choice; not required for mock CI)
