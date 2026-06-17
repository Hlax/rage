# Agent Report: ticket-310 — Atlas preview card and cluster concept slug links

**Date:** 2026-06-17  
**Ticket:** ticket-310  
**Branch:** `phase-3/ticket-310-atlas-preview-card-cluster-concept-links`  
**Main tip before branch:** `951d5ce`  
**Audit gate:** `agent_reports/2026-06-17_pre-ticket-310_atlas-preview-card-cluster-concept-links-audit.md` (GO)

## Summary

Extended ticket-309 fail-closed concept linking to **card Concepts lines** and **cluster
member_concepts lines** via shared `renderConceptLabelList` helper (comma separators).
Unknown labels remain plain text. GT12 asserts helper in page source and elevated
`/concepts/` link count in static export.

## Scope

**In:**

- `renderConceptLabelList` helper in `atlas-preview/page.tsx`
- Card and cluster Concepts lines use conditional `Link` to `/concepts/[slug]`
- GT12 source + static HTML assertions

**Out:**

- Nodes section changes (ticket-309)
- `export-public` changes
- New routes or graph visualization

## Changed files

| File | Change |
|------|--------|
| `apps/public-site/app/atlas-preview/page.tsx` | Card/cluster concept label links |
| `tests/golden/test_12_public_site_static_render.py` | GT12 helper + link-count assertions |
| `tickets/ticket-310.json` | Status `done` |
| `tickets/ticket-311.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit before implementation | **PASS** |
| Card Concepts lines link when slug exists | **PASS** |
| Cluster member_concepts lines link when slug exists | **PASS** |
| Unknown labels plain text; separators preserved | **PASS** |
| Golden + full pytest + public-site build pass | **PASS** — 144 golden, 789 full |
| No `export-public` semantic changes | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
cd apps/public-site && npm run build
python -m pytest tests/golden/test_12_public_site_static_render.py -q   # 11 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 789 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                     # pass
```

## Manual CLI verification

Not applicable — static fixture page only; no CLI surface changes.

## Spec deviations

None.

## Recommended next ticket

**ticket-311** — Principal audit post-ticket-310 checkpoint (cadence advisory after
309–310 public-site navigation work; read-only).

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

Merge commit: _(pending)_
