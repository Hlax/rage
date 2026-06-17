# Agent Report: ticket-306 — Atlas snapshot inline coherence summary v0

**Date:** 2026-06-17  
**Ticket:** ticket-306  
**Branch:** `phase-3/ticket-306-atlas-coherence-summary-inline-v0`  
**Main tip before branch:** `f1a0bb7`  
**Audit gate:** Satisfied — `agent_reports/2026-06-17_pre-ticket-306_atlas-coherence-summary-inline-audit.md` (GO, 2026-06-17)

## Summary

Added optional `coherence_summary` on atlas snapshots with `overall_coherence_verdict`
and `preview_label` only (verdict from `build_atlas_coherence_report`). Regenerated
creativity fixture and preview JSON. `/atlas-preview` uses
`resolveAtlasCoherencePreview()` (inline first, separate JSON fallback for population).
No `export-public` changes.

## Scope

**In:**

- `_project_coherence_summary()` in `atlas_snapshot_builder.py`
- Regenerated fixture + `atlas_snapshot_preview.json`
- `resolveAtlasCoherencePreview()` in `lib/atlasPreview.ts`
- `/atlas-preview` page uses resolver
- Unit tests + GT12 updates

**Out:**

- Full coherence report body in snapshot
- Removing `atlas_coherence_preview.json`
- `export-public` changes
- Schema migrations

## Changed files

| File | Change |
|------|--------|
| `rge/modules/atlas_snapshot_builder.py` | `coherence_summary` projection |
| `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` | Regenerated |
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Synced |
| `apps/public-site/lib/atlasPreview.ts` | Types + resolver |
| `apps/public-site/app/atlas-preview/page.tsx` | Use resolver |
| `tests/unit/test_atlas_snapshot_coherence_summary.py` | 6 unit tests (new) |
| `tests/golden/test_12_public_site_static_render.py` | Static fixture + preview_label assertions |
| `agent_reports/2026-06-17_pre-ticket-306_atlas-coherence-summary-inline-audit.md` | Pre-ticket audit |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit written | **PASS** |
| Fixture-mode snapshot includes `coherence_summary` | **PASS** |
| Committed fixture + preview JSON updated | **PASS** |
| `/atlas-preview` reads inline coherence with file fallback | **PASS** |
| No `export-public` semantic changes | **PASS** |
| Golden + full pytest + safety audit + site build | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_snapshot_coherence_summary.py -q   # 6 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 782 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                     # pass
cd apps/public-site && npm run build                                    # pass
```

## Manual CLI verification

Fixture export: `coherence_summary` =
`{overall_coherence_verdict: pass, preview_label: Fixture-mode creativity atlas (mock-safe)}`;
`assert_no_private_fields` clean.

## Spec deviations

GT12 `test_atlas_preview_page_is_static_fixture_only` now asserts
`resolveAtlasCoherencePreview` on the page and `coherence_summary` in `atlasPreview.ts`
(instead of direct `atlasCoherence` import on the page).

## Recommended next ticket

**ticket-307** — Sync `atlas_coherence_preview.json` population + verdict from snapshot
export pipeline (reduces dual-file drift; keeps separate file for safety auditor scan).

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

Merge commit: `26f7939`
