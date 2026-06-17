# Agent Report: ticket-309 — Atlas preview nodes concept slug links

**Date:** 2026-06-17  
**Ticket:** ticket-309  
**Branch:** `phase-3/ticket-309-atlas-preview-node-concept-links`  
**Main tip before branch:** `c9e7f77`  
**Audit gate:** `agent_reports/2026-06-17_pre-ticket-309_atlas-preview-node-concept-links-audit.md` (GO)

## Summary

Linked atlas preview **concept node labels** to existing `/concepts/[slug]` pages when
`conceptToSlug` + `findConceptBySlug` resolve against the public card export. Unknown
labels (e.g. `agency`) remain plain text. GT12 asserts helper imports and
`/concepts/ai-assistance` in static `atlas-preview.html`.

## Scope

**In:**

- Nodes section conditional `Link` in `atlas-preview/page.tsx`
- GT12 source + static HTML assertions in `test_12_public_site_static_render.py`

**Out:**

- Card/cluster concept link changes (nodes section only)
- `export-public` changes
- New routes or graph visualization

## Changed files

| File | Change |
|------|--------|
| `apps/public-site/app/atlas-preview/page.tsx` | Node labels link to `/concepts/[slug]` when slug exists |
| `tests/golden/test_12_public_site_static_render.py` | GT12 asserts helpers + concept link in static export |
| `tickets/ticket-309.json` | Status `done` |
| `tickets/ticket-310.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit before implementation | **PASS** |
| Nodes link to `/concepts/[slug]` when slug exists | **PASS** |
| Unknown labels remain plain text | **PASS** |
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

**ticket-310** — Atlas preview card and cluster concept slug links (same fail-closed slug
resolution for `card.concepts` and `cluster.member_concepts`; pre-ticket audit required).

## Suggested next prompt

```txt
Write pre-ticket-310 audit, then /rge-run-next-ticket
```

## Merge to main

Merge commit: _(pending)_
