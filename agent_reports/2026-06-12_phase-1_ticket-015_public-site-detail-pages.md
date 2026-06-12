---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-015 / public-site-detail-pages

## 1. Summary

Implemented public site card and concept detail pages for Golden Test 12. Added static routes `/cards/[id]` and `/concepts/[id]` (concept param is a URL slug derived from label strings), updated the list page with links and build-info footer, refreshed committed golden export JSON, and added Golden Test 12 (6 tests). All 65 golden tests pass without Ollama; public site static build emits 11 prerendered pages.

## 2. Ticket

- Ticket ID: ticket-015
- Ticket title: Add public site card and concept detail pages (Golden Test 12)
- Branch: `phase-1/ticket-015-public-site-detail-pages`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-12

## 3. Scope

### In Scope

- Card detail page with `generateStaticParams`, related-card links, escaped text fields.
- Concept detail page keyed by slugified concept labels (not `cpt_*` IDs).
- List page links to card/concept routes; build-info last updated footer retained.
- Representative golden export JSON in `apps/public-site/public/data/`.
- Shared `lib/publicCards.ts` helpers.
- Golden Test 12 (`tests/golden/test_12_public_site_static_render.py`).
- Pre-ticket-015 audit report and runner audit-gate patch (from prior audit session).

### Out of Scope / Non-Goals

- API routes, forms, fetches, SQLite/FastAPI at runtime, Ollama, memo pages, safety auditor module.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `apps/public-site/app/cards/[id]/page.tsx` | New: static card detail route. |
| `apps/public-site/app/concepts/[id]/page.tsx` | New: static concept detail route (slug param). |
| `apps/public-site/app/page.tsx` | Links to card/concept pages; uses shared card data. |
| `apps/public-site/lib/publicCards.ts` | New: types, slug helpers, card lookups. |
| `apps/public-site/public/data/public_cards.json` | Golden export sample (2 cards). |
| `apps/public-site/public/data/build_info.json` | Updated build metadata. |
| `tests/golden/test_12_public_site_static_render.py` | New: Golden Test 12 (6 tests). |
| `agent_reports/2026-06-12_pre-ticket-015_public-site-readiness-audit.md` | Pre-ticket audit (included from audit checkpoint). |
| `.cursor/commands/rge-run-next-ticket.md` | Audit gate §3.5 (included from audit checkpoint). |
| `tickets/TICKET_QUEUE.md` | ticket-015 done; ticket-016 proposed. |
| `tickets/ticket-015.json` | Status `done`. |
| `tickets/ticket-016.json` | Proposed cluster report ticket. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-015_public-site-readiness-audit.md`.
- Concept routes use slugified labels (`AI assistance` → `ai-assistance`) per audit hardened scope.
- Next.js static export writes flat HTML (`cards/<id>.html`); GT12 test checks that layout.
- GT12 HTML output test requires prior `npm run build` (same pattern as GT00 deferring npm to test_plan).

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Site builds with list, card detail, concept detail routes (static JSON) | PASS | 11 static pages. |
| Build info / last updated on list page | PASS | Footer renders `generated_at`. |
| No write, ingestion, or agent routes | PASS | GT12 + GT00 source scans. |
| `pytest tests/golden/test_12_public_site_static_render.py` | PASS | 6/6. |
| Existing golden tests still pass | PASS | 65/65. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_12_public_site_static_render.py` | PASS | 6 passed (after npm build). |
| `python -m pytest tests/golden` | PASS | 65 passed in 8.20s. |
| `python -m pytest` | PASS | 65 passed in 8.23s. |
| `cd apps/public-site && npm run build` | PASS | 11 prerendered routes. |

## 8. Test Results

### Passing

- `tests/golden/test_12_public_site_static_render.py` — 6/6.
- All prior golden tests — 59/59 unchanged behavior plus 6 new tests.

### Failing

- None.

## 9. Manual CLI Verification

Not required (public-site-only ticket). Static build verified via npm and GT12 HTML assertions.

## 10. Safety Audit Status

- Required: partial (public site routes touched).
- `python -m rge.modules.safety_auditor --audit full` — NOT AVAILABLE (Phase 0 stub).
- Mitigation: GT12 source scans forbid write/API/unsafe HTML patterns; static JSON-only data flow unchanged.

## 11. Spec Deviations

1. **Concept route param name.** Folder is `concepts/[id]` per ticket JSON, but the dynamic segment value is a concept **slug**, not a `cpt_*` database ID (export JSON has label strings only).

## 12. Known Failures

- None.

## 13. Rollback Plan

Revert branch `phase-1/ticket-015-public-site-detail-pages`. Restore placeholder `public_cards.json` if needed.

## 14. Merge to Main

- Instruction source: `AGENTS.md` step 9 (temporary).
- Pre-merge `main` tip: `c8042a1570ecd858296e2dfc88bdb82fba101db4`
- Branch: `phase-1/ticket-015-public-site-detail-pages`
- Merge result: pending (record hash below after merge/push).

## 15. Recommended Next Ticket

**ticket-016: Add cluster report threshold trigger (Golden Test 13)**

See `tickets/ticket-016.json`.

## 16. Can the Loop Continue?

**Yes.** Public static rendering for cards and concepts is in place. ticket-016 (cluster report) is the smallest intelligence-layer follow-on.

## 17. Suggested Next Prompt

Run `/rge-run-next-ticket` to implement ticket-016 on branch `phase-1/ticket-016-cluster-report`.
