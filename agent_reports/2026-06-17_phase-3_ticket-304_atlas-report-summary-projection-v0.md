# Agent Report: ticket-304 — Atlas snapshot public report summary projection v0

**Date:** 2026-06-17  
**Ticket:** ticket-304  
**Branch:** `phase-3/ticket-304-atlas-report-summary-projection-v0`  
**Main tip before branch:** `fa40414`  
**Audit gate:** Satisfied — `agent_reports/2026-06-17_pre-ticket-304_atlas-report-summary-projection-audit.md` (GO, 2026-06-17)

## Summary

Added `public_summary` to atlas `reports[]` entries, derived from whitelisted `run_report`
metric fields only. Regenerated the creativity fixture and public preview JSON; `/atlas-preview`
now renders the summary under each report row. No `export-public` changes.

## Scope

**In:**

- `_project_public_report_summary()` + `_build_report_summaries()` in `atlas_snapshot_builder.py`
- Regenerated `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`
- Synced `apps/public-site/public/data/atlas_snapshot_preview.json`
- `/atlas-preview` reports section + `lib/atlasPreview.ts` type
- Unit tests + GT12 public_summary assertion

**Out:**

- `export-public` / card exporter semantic changes
- Schema migrations
- Full run report body export
- Live operator-only paths without existing `run_reports` projection

## Changed files

| File | Change |
|------|--------|
| `rge/modules/atlas_snapshot_builder.py` | `public_summary` projection from whitelisted metrics |
| `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` | Regenerated with `public_summary` |
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Synced from fixture |
| `apps/public-site/app/atlas-preview/page.tsx` | Render `public_summary` |
| `apps/public-site/lib/atlasPreview.ts` | `public_summary?: string` on report type |
| `tests/unit/test_atlas_snapshot_report_summary.py` | 6 unit tests (new) |
| `tests/golden/test_12_public_site_static_render.py` | Assert summary in static HTML |
| `agent_reports/2026-06-17_pre-ticket-304_atlas-report-summary-projection-audit.md` | Pre-ticket audit (GO) |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit written before implementation | **PASS** |
| Fixture-mode `reports[]` include `public_summary` from whitelisted metrics | **PASS** |
| Committed fixture + preview JSON updated | **PASS** |
| `/atlas-preview` shows summary text | **PASS** |
| No `export-public` semantic changes | **PASS** |
| Golden + full pytest + safety audit + site build | **PASS** |

## Example `public_summary`

```txt
15 claims accepted from 3 ingested sources; 1 rejected; 2 relationships; 1 score event; 2 public cards; 1 cluster report.
```

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_snapshot_report_summary.py -q   # 6 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 769 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                     # pass
cd apps/public-site && npm run build                                    # pass
```

## Manual CLI verification

Regenerated creativity atlas fixture via fixture-mode `execute_fixture_mode_run` +
`export_atlas_snapshot_to_path`; confirmed `reports[0].public_summary` present and
`assert_no_private_fields` clean.

## Spec deviations

None.

## Recommended next ticket

**ticket-305** — Atlas cluster member projection v0 (cluster cards list member concept
labels in snapshot + `/atlas-preview` clusters section; per ticket-300 product verdict).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `22f4ae0`
