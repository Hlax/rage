# Agent Report: ticket-300 — Research Atlas read-only public preview v0

**Date:** 2026-06-17  
**Ticket:** ticket-300  
**Branch:** `phase-3/ticket-300-atlas-readonly-public-preview-v0`  
**Main tip before branch:** `f3e8ad4`  
**Audit gate:** `agent_reports/2026-06-17_pre-ticket-300_atlas-readonly-public-preview-audit.md` (GO)

## Summary

Shipped a text-first, read-only **Research Atlas preview** at `/atlas-preview` on the
public site. The page consumes committed fixture data only (`atlas_snapshot_preview.json`
copied from `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` plus derived
`atlas_coherence_preview.json`). No `export-public` changes, no API routes, no live LLM.

## Scope

**In:** `/atlas-preview` page, `lib/atlasPreview.ts`, committed preview JSON, home footer link.

**Out:** Graph visualization, operator DB wiring, auth, `export-public` changes, schema migrations.

## Changed files

| File | Change |
|------|--------|
| `apps/public-site/app/atlas-preview/page.tsx` | Text-first Atlas preview page |
| `apps/public-site/lib/atlasPreview.ts` | Types + static import helpers |
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Fixture snapshot copy (force-added; `data/` gitignore) |
| `apps/public-site/public/data/atlas_coherence_preview.json` | Coherence summary (force-added) |
| `apps/public-site/app/page.tsx` | Footer link to atlas preview |
| `agent_reports/2026-06-17_pre-ticket-300_atlas-readonly-public-preview-audit.md` | Pre-ticket GO audit |
| `tickets/ticket-300.json` | Status `done` |
| `tickets/ticket-301.json` | Seeded GT12 follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Page sections (text description)

Static export at `/atlas-preview.html` renders:

1. **Header** — primary research question, fixture-preview disclaimer, breadcrumb to public cards
2. **Coherence badge** — `pass` (green pill) with population counts (runs 1, cards 2, nodes 24, edges 2, etc.)
3. **Research run summary** — `run_golden_fixture_mvp`, fixture mode, completed status, topic
4. **Domains** — creativity (primary)
5. **Cards** — 2 cluster cards with confidence, summary, concepts; titles link to existing `/cards/[id]` when IDs match public export
6. **Nodes / edges summary** — 24 concept labels as inline text; 2 relationship edges with predicate + scope (no graph)
7. **Reports** — 1 run_report linked to run id
8. **Follow-up questions** — 3 queued questions + collapsible parked set (3 drift/legal adjacent)
9. **Lineage / research trail** — `research_question_id`, parent question, cluster label

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit before implementation | **PASS** |
| Read-only `/atlas-preview` with fixture data only | **PASS** |
| Text-first sections (runs, domains, cards, nodes/edges, reports, follow-ups, lineage, coherence) | **PASS** |
| No operator exports, write/ingest routes, live LLM | **PASS** |
| No `export-public` semantic changes | **PASS** |
| No graph viz or media assets | **PASS** |
| Public site build | **PASS** — `/atlas-preview` in static export |
| Safety audit | **PASS** |
| Golden + full pytest | **PASS** — 142 golden, 757 full |
| Product verdict in report | **PASS** — below |

## Product verdict

**Direction:** Yes — a text-first Atlas preview is the right v0. It answers the five
evaluation questions without backend coupling:

| Question | v0 answer |
|----------|-----------|
| What did the agent research? | Run summary + root question visible |
| What claims/cards exist? | Cards section with public-safe fields |
| How are things connected? | Edge list works; lacks visual graph |
| What follow-ups emerged? | Queued vs parked distinction is useful |
| Is the contract frontend-ready? | **Mostly** — shape is usable; reports are thin |

**Awkward / missing Atlas fields for frontend:**

- `reports[]` carry only `report_type` / `run_id` / `status` — no public summary body for UI
- `clusters[]` lack member node/claim lists — label only
- `nodes[]` have no degree/centrality hints for prioritization
- No stable `candidate_domain` section beyond `domains[]` (staged rank-2 not represented in fixture)
- Coherence verdict is a separate JSON file — consider optional `coherence_summary` block on snapshot for single-import pages

**Recommended next ticket:** **ticket-301** — extend GT12 to assert `/atlas-preview` static export exists and key sections render (prevents route regression). Product follow-on after that: report body projection into atlas snapshot for richer preview sections (separate pre-ticket audit if it touches export pipeline).

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q          # 142 passed
python -m pytest -q                       # 757 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full   # pass
cd apps/public-site && npm run build      # success; /atlas-preview exported
```

## Manual CLI verification

Not applicable — static fixture page only; no CLI surface changes.

## Spec deviations

None.

## Recommended next ticket

**ticket-301** — GT12 atlas-preview static export assertion.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: _(pending)_
