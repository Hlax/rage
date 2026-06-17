# Agent Report: ticket-305 — Atlas cluster member projection v0

**Date:** 2026-06-17  
**Ticket:** ticket-305  
**Branch:** `phase-3/ticket-305-atlas-cluster-member-projection-v0`  
**Main tip before branch:** `7bbedf7`  
**Audit gate:** Satisfied — `agent_reports/2026-06-17_pre-ticket-305_atlas-cluster-member-projection-audit.md` (GO, 2026-06-17)

## Summary

Added `member_concepts` to atlas `clusters[]` entries, parsed from
`cluster_reports.included_concepts_json` (deduplicated string labels only).
Regenerated creativity fixture and public preview JSON; `/atlas-preview` clusters
section lists concept labels under each cluster. No `export-public` changes.

## Scope

**In:**

- `_project_cluster_member_concepts()` + `_build_cluster_summaries()` in `atlas_snapshot_builder.py`
- Regenerated `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`
- Synced `apps/public-site/public/data/atlas_snapshot_preview.json`
- `/atlas-preview` clusters UI + `lib/atlasPreview.ts` type
- Unit tests + GT12 member-concept assertions

**Out:**

- `export-public` changes
- Full cluster report / evidence_packet export
- Schema migrations
- Claim IDs or raw claim text in snapshot

## Changed files

| File | Change |
|------|--------|
| `rge/modules/atlas_snapshot_builder.py` | `member_concepts` projection |
| `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` | Regenerated |
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Synced |
| `apps/public-site/app/atlas-preview/page.tsx` | Render member concepts |
| `apps/public-site/lib/atlasPreview.ts` | Type update |
| `tests/unit/test_atlas_snapshot_cluster_members.py` | 7 unit tests (new) |
| `tests/golden/test_12_public_site_static_render.py` | Cluster member assertions |
| `agent_reports/2026-06-17_pre-ticket-305_atlas-cluster-member-projection-audit.md` | Pre-ticket audit |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit written | **PASS** |
| Fixture-mode `clusters[]` include `member_concepts` | **PASS** |
| Committed fixture + preview JSON updated | **PASS** |
| `/atlas-preview` lists member labels | **PASS** |
| No `export-public` semantic changes | **PASS** |
| Golden + full pytest + safety audit + site build | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_snapshot_cluster_members.py -q   # 7 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 776 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                     # pass
cd apps/public-site && npm run build                                    # pass
```

## Manual CLI verification

Fixture-mode export confirmed `member_concepts` =
`["AI assistance", "semantic diversity", "originality", "ideation"]`;
`assert_no_private_fields` clean.

## Spec deviations

GT12 asserts each member label individually (not exact `Concepts: a, b, c` line) because
Next static HTML injects `<!-- -->` between label prefix and concept list.

## Recommended next ticket

**ticket-306** — GT12 atlas-preview cluster member regression hardening (optional) or
atlas snapshot `coherence_summary` inline block (ticket-300 product follow-on; pre-ticket audit).

## Suggested next prompt

```txt
/rge-principal-audit
```

(two done tickets since ticket-303 checkpoint — cadence advisory before more public-site work)

## Merge to main

Merge commit: `9b4b694`
