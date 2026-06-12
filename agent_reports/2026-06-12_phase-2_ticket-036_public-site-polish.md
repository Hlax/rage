---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 2 / ticket-036 / public-site-polish

## 1. Summary

Presentation-only public-site polish: humanized enum labels and deterministic human-readable timestamps via display helpers in `lib/publicCards.ts`, a new static `/about` page (engine overview, fixture provenance, confidence semantics, read-only safety boundary, public/private data split), a custom styled 404 page, and an explicit zero-card empty state on the home page. No export schema changes, no new public data fields, no runtime changes. All 127 golden tests pass; safety audit passes; the site builds 12 static pages.

## 2. Ticket

- Ticket ID: ticket-036
- Ticket title: Public-site presentation polish and about page (no data surface changes)
- Branch: `phase-2/ticket-036-public-site-polish`
- Phase: 2
- Agent/model: Cursor builder agent
- Date: 2026-06-12
- Main tip before branch: `44a2f29`
- Audit gate satisfied by: `agent_reports/2026-06-12_pre-ticket-036_public-site-polish-readiness-audit.md` (2026-06-12, committed `44a2f29`)

## 3. Scope

### In Scope

- Display helpers (`humanizeLabel`, `formatPublicTimestamp`, `formatSourceCount`) in `lib/publicCards.ts`; presentation-only, deterministic, no locale dependence.
- Humanized enum/timestamp rendering on home, card detail, and concept detail pages.
- New static `app/about/page.tsx` and `app/not-found.tsx`.
- Zero-card empty state on the home page.
- GT12/GT25 updates for presentation/page coverage only (no weakened assertions).

### Out of Scope / Non-goals

- Export schema, public data fields, runtime pipeline, live providers, write routes, deployment docs, ticket-037+.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `apps/public-site/lib/publicCards.ts` | Added `humanizeLabel`, `formatPublicTimestamp` (deterministic UTC formatting with raw fallback), `formatSourceCount`. |
| `apps/public-site/app/page.tsx` | Humanized card meta line, formatted footer timestamp (keeps `Last updated:` + `buildInfo.generated_at`), zero-card empty state, About links. |
| `apps/public-site/app/cards/[id]/page.tsx` | Humanized meta line and debug values; formatted timestamps. GT25 literals (`Research debug details`, `Evidence type`, `Public run timestamp`, `evidence_type`, `public_run_timestamp`) preserved. |
| `apps/public-site/app/concepts/[id]/page.tsx` | Humanized card meta line via shared helpers; removed unused import. |
| `apps/public-site/app/about/page.tsx` | New static about page: methodology, fixture provenance, confidence semantics, read-only boundary, public/private split. Hand-written copy + already-public build info only. |
| `apps/public-site/app/not-found.tsx` | New custom 404 in site visual language with link home. |
| `tests/golden/test_12_public_site_static_render.py` | +3 tests (about page static/presentation-only, custom 404, empty state); about/404 static HTML assertions in build check; `/about` link assertion. |
| `tests/golden/test_25_public_site_debug_details.py` | +1 test: about/404 pages reference no private fields and no raw HTML rendering. |
| `tickets/ticket-036.json` | Status `in_progress` → `done`. |
| `tickets/TICKET_QUEUE.md` | ticket-036 marked done; queue notes updated. |
| `agent_reports/2026-06-12_phase-2_ticket-036_public-site-polish.md` | This report. |

## 5. Implementation Notes

- `GET /about` was already in `ALLOWED_PUBLIC_ROUTES` (`rge/safety/route_audit.py`); no policy change needed or made.
- About-page copy deliberately avoids the route-audit forbidden literals (no `/ingest`-style path strings, no localhost references) and all GT25 private field names.
- `formatPublicTimestamp` is regex-based (no `Date`/locale APIs) so output is deterministic across environments and falls back to the raw value for unexpected shapes — safe public values are preserved.
- The concept detail page is not in the ticket `expected_files`, but it rendered the same raw enums; it was updated with the same shared helpers to satisfy the acceptance criterion "raw enum values are humanized in public UI". Documented here as the only deviation; no data surface change.
- Favicon/OG-image assets were not added (binary assets; the problem statement mentions them but the acceptance criteria do not require them). Layout metadata was already present.
- New pages are automatically covered by the safety auditor's recursive `app/` scan and GT12's forbidden-pattern glob.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Raw enum values humanized without export schema change | PASS | `humanizeLabel` on home/card/concept pages; JSON untouched. |
| Public timestamps human-formatted, safe values preserved | PASS | `formatPublicTimestamp`, deterministic, raw fallback. |
| `/about` explains engine, fixtures, confidence, boundary, data split | PASS | All five sections present. |
| Custom 404 + zero-card empty state in site visual language | PASS | `not-found.tsx`; empty-state block on home. |
| No new public export fields | PASS | `public/data/*.json` and `rge/` untouched (git diff). |
| No private/internal data rendered | PASS | GT25 page checks extended to about/404; safety audit pass. |
| Site remains static and read-only | PASS | `output: 'export'` unchanged; no fetches/forms/API routes. |
| GT12 and GT25 pass with presentation-only test updates | PASS | 14/14; no assertions weakened. |
| Public-site build passes | PASS | 12/12 static pages. |
| Full golden tests and safety audit pass | PASS | 127/127; audit `pass`. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `cd apps/public-site && npm run build` | PASS | 12 static pages incl. `/about`; exit 0. |
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_12_public_site_static_render.py tests/golden/test_25_public_site_debug_details.py` | PASS | 14 passed. |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS | 127 passed (123 prior + 4 new). |
| `RGE_LLM_MODE=mock python -m pytest` | PASS | 127 passed. |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS | `status: pass`, exit 0. |

## 8. Manual CLI Verification

Not required: no CLI or pipeline changes. Static export output verified via GT12 build assertions (`out/about.html`, `out/404.html`, card/concept pages).

## 9. Safety Audit

Full safety audit passes on the ticket branch. The auditor's route/raw-html scans cover the new `about/page.tsx` and `not-found.tsx` automatically; the public export bundle is byte-identical to main.

## 10. Merge to Main

- Merge commit: `2547632`
- Branch: `phase-2/ticket-036-public-site-polish` merged to `main`; full pytest re-run on merged main: 127 passed.

## 11. Recommended Next Ticket

**ticket-037**: Ollama live structured-task adapter behind explicit opt-in (Phase 2 roadmap). **Requires its own pre-ticket audit** (live Ollama rule in the audit-gate table) before seeding/implementation. Alternatively, ticket-040 (CI golden gate + principal-audit command) is independent, low-risk, and may be pulled earlier.

## 12. Suggested Next Prompt

```txt
Perform a focused pre-ticket-037 live-Ollama readiness audit (do not implement), then seed tickets/ticket-037.json from the Phase 2 roadmap if the audit recommends proceeding.
```
