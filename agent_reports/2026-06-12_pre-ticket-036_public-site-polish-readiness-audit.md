---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-036 Public-Site Polish Readiness Audit

- Audit type: focused pre-ticket audit — public-site presentation polish and `/about` page readiness
- Date: 2026-06-12
- Agent/model: Cursor audit agent
- Scope: read-only audit of the public-site surface, export policy, safety auditor, and golden tests before seeding ticket-036. No runtime, schema, frontend, or export changes were made.

## Summary

Ticket-036 (public-site presentation polish and `/about` page) is **safe to begin as a presentation-only ticket**. The public-site surface is small (4 source files, all static, zero client fetches), the export schema needs **no changes**, no new public data fields are required, `GET /about` is already in `ALLOWED_PUBLIC_ROUTES`, and a custom `not-found.tsx` is a framework file rather than a new route. All 123 golden tests pass, the full safety audit passes, and the site builds 11 static pages with the working tree remaining clean. This report satisfies the audit-gate requirement for ticket-036 provided implementation stays presentation-only.

## Repo / Main Status

| Check | Result |
|---|---|
| Branch | `main`, aligned with `origin/main` (`## main...origin/main`) |
| Working tree | clean before and after verification commands (build artifacts gitignored since ticket-034) |
| Main tip | `6b3021f` (docs: record main merge hash for ticket-035) |
| ticket-034 merge commit | `2e1dd9d` — present in `git log` |
| ticket-035 merge commit | `27fdae7` — present in `git log` |
| Unmerged branches | `git branch --all --no-merged main` → none |

## Ticket / Queue Status

| Ticket | Status | Verified |
|---|---|---|
| ticket-033 (principal audit) | done | report exists; JSON `status: done` |
| ticket-034 (artifact hygiene) | done | merged `2e1dd9d`; JSON `status: done` |
| ticket-035 (README refresh) | done | merged `27fdae7`; JSON `status: done` |
| ticket-036 | **not yet seeded** | `tickets/ticket-036.json` does not exist; queue lists it as the current active proposed item |

No later roadmap item (037+) should jump ahead: 037/038 (live Ollama) require their own pre-ticket audit, 039 depends on loop semantics review, and 040/041 are independent but lower priority than making the existing public surface presentable.

## Principal-Audit / Roadmap Alignment

- The principal audit (`2026-06-12_pre-phase-2_principal-audit.md`) recommends sequence 034 → 035 → 036; 034 and 035 are done, so ticket-036 is the correct next item.
- The principal audit's "Public-Facing UI / Product Assessment" section is **still applicable**: no public-site source file has changed since the audit (only `public_cards.json` `source_count` reconciliation in ticket-034, which the audit itself called for).
- The roadmap's ticket-036 entry explicitly bounds scope: "**No export schema changes; no new data fields.**"
- The principal audit states the audit gate for ticket-036 can be satisfied by its UI section if scope stays presentation-only; this focused report re-verifies that at the current main tip and serves as the gate record.

## Current Public-Site Findings

Surface inventory: `app/layout.tsx`, `app/page.tsx`, `app/cards/[id]/page.tsx`, `app/concepts/[id]/page.tsx`, `lib/publicCards.ts`. No API routes, no forms, no fetches, no `dangerouslySetInnerHTML`, all data from static JSON imports.

UI issues ticket-036 should address (all confirmed present in source):

| Issue | Location | Fix shape |
|---|---|---|
| Raw enum strings rendered: `cluster_card`, `empirical`, `standard`, confidence values | `page.tsx` lines 52–53, card detail lines 51–53, 126; concept page line 62 | Display-helper functions in `lib/publicCards.ts` mapping known enum values to human labels (presentation-only; JSON unchanged) |
| Raw ISO timestamps (`2026-06-12T00:00:00Z`) | home footer (`buildInfo.generated_at`), card detail footer + debug `public_run_timestamp`/`updated_at` | Deterministic UTC date formatter; keep underlying values intact |
| No `/about` page | `GET /about` allowed in `route_audit.py` but unimplemented | New `app/about/page.tsx` static page: engine overview, fixture provenance, confidence semantics, read-only safety boundary, public/private data split |
| Default unstyled Next 404 | no `app/not-found.tsx` | Custom `not-found.tsx` in site visual language |
| No empty state for zero cards | `page.tsx` renders "Public cards (0)" with nothing else | Conditional empty-state copy |
| Minimal metadata | `layout.tsx` title/description only | Optional metadata polish within existing layout; no new data |
| Inline-style debt | all pages | May consolidate shared style constants; cosmetic only, not required |

## Safety / Public-Data Boundary Findings

- **Export policy (`rge/safety/public_export_policy.py`):** 14 allowed card fields, 9 required, forbidden key substrings and value patterns. Every field ticket-036 needs to display (`type`, `confidence`, `evidence_type`, `public_detail_level`, timestamps, `source_count`) is already exported. **No schema change needed; none permitted.**
- **Route audit (`rge/safety/route_audit.py`):** `GET /about` is already in `ALLOWED_PUBLIC_ROUTES` — an `/about` page is policy-compatible with zero policy edits. `not-found.tsx` is not a route addition; the safety auditor scans source content (write handlers, forbidden paths, raw HTML), not filenames, so a custom 404 is compatible with the current route audit.
- **Safety auditor (`rge/modules/safety_auditor.py`):** scans all `.ts/.tsx/.js/.jsx` under `app/` and `lib/` recursively, so new `about/page.tsx` and `not-found.tsx` are automatically covered by the route/raw-html checks. No auditor change required.
- **Trap to respect:** `_FORBIDDEN_ROUTE_SOURCE_PATTERNS` rejects the literal strings `/ingest`, `/agent`, `/local/runs`, `/local/sources`, `/local/queue`, `127.0.0.1:<port>` in public-site sources. `/about` copy describing the safety model must avoid those literal path strings (e.g. write "no source ingestion routes" not "`/ingest`").
- **GT12 (`test_12_public_site_static_render.py`):** list page must keep `Last updated:` text and a `buildInfo.generated_at` reference; forbidden patterns include `<form` and POST literals. Humanized date formatting must keep the `Last updated:` label and still reference `buildInfo.generated_at`. Built HTML must contain card titles/summaries (unaffected by label formatting).
- **GT25 (`test_25_public_site_debug_details.py`):** card detail page must keep the literal strings `Research debug details`, `Evidence type`, `Public run timestamp`, `evidence_type`, `public_run_timestamp` and reference no private field names. Humanizing the *values* (e.g. `empirical` → `Empirical`) is compatible; the headings and field references must remain.
- **What ticket-036 must not expose:** raw source text, prompts, secrets, local paths, private notes, hidden reasoning, injected-instruction markers, unreviewed draft internals, internal IDs (`claim_id`, `source_id`, `chunk_id`). The `/about` page must be hand-written static copy only — no data beyond the already-public build info.

## Audit Question Answers

| Question | Answer |
|---|---|
| Is ticket-036 safe to begin? | **Yes** |
| Can it stay presentation-only? | **Yes** — all needed data is already exported |
| Export schema changes needed? | **No** |
| New public data fields needed? | **No** |
| `GET /about` + custom 404 compatible with route audit? | **Yes** — `/about` already allowed; `not-found.tsx` is not a route audit concern |
| New pre-ticket audit required for ticket-036? | This report satisfies the gate if scope stays presentation-only |

## Allowed Ticket-036 Scope

- Humanize enum display values via display helpers in `lib/publicCards.ts`.
- Deterministic human-readable date formatting for public timestamps.
- New static `app/about/page.tsx` (methodology, fixture provenance, confidence semantics, safety boundary, public/private split).
- New `app/not-found.tsx` styled 404.
- Zero-card empty state on the home page.
- Optional shared style constants / layout metadata polish.
- Update GT12/GT25 only for presentation/page coverage (e.g. `/about` static export check); do not weaken existing assertions.

## Blocked / Out-of-Scope Changes

- Any change to `rge/safety/public_export_policy.py`, `rge/modules/card_exporter.py`, or export JSON shape.
- Any new field read from or added to `public_cards.json` / `build_info.json` / `public_memos.json`.
- Any API route, form, fetch, client-side data loading, or `dangerouslySetInnerHTML`.
- Any change to `route_audit.py` or the safety auditor.
- Deployment docs (ticket-041), live providers (ticket-037+), CI (ticket-040).

## Tests Run (exact results)

| Command | Result |
|---|---|
| `git status --short --branch` | `## main...origin/main` — clean |
| `git log --oneline --decorate -30` | tip `6b3021f`; merges `27fdae7` (035), `2e1dd9d` (034) present |
| `git branch --all --no-merged main` | empty |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | **123 passed** in 35.72s |
| `RGE_LLM_MODE=mock python -m pytest` | **123 passed** in 35.74s |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | `status: pass`, `blocked_reasons: []`, exit 0 |
| `cd apps/public-site && npm run build` | pass — 11/11 static pages, exit 0 |
| `git status --short` (after build) | clean |

## Recommendation

Recommendation: proceed with ticket-036 as a presentation-only public-site polish ticket.
