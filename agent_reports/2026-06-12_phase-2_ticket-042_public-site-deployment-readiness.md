---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 2 / ticket-042 / public-site-deployment-readiness

## Summary

Added operator-facing deployment documentation for the static public site: build
steps, mandatory pre-deploy checklist (safety audit + snapshot diff review), snapshot
refresh workflow, static host guidance, and local preview via `npm run preview:static`.
Docs-only; no export schema, route, or runtime changes.

## Ticket metadata

- Ticket ID: ticket-042
- Branch: `phase-2/ticket-042-public-site-deployment-readiness`
- Base: `main` at `6a288d4` (ticket-042 seed)
- Date: 2026-06-12
- Risk level: low

## Changed files

| File | Change |
|---|---|
| `docs/deployment/public-site-static-hosting.md` | New deployment guide |
| `apps/public-site/package.json` | Added `preview:static` script |
| `README.md` | Link to deployment guide |
| `tickets/ticket-042.json` | Status done |
| `tickets/TICKET_QUEUE.md` | Row 42 done + queue notes |

## Commands run

| Command | Result |
|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden -q` | 132 passed |
| `python -m rge.modules.safety_auditor --audit full` | pass |
| `cd apps/public-site && npm run build` | PASS — 12 static pages |

## Acceptance criteria

| Criterion | Status |
|---|---|
| Operator can deploy from `out/` following docs | PASS (documented) |
| Pre-deploy checklist requires safety audit + snapshot review | PASS |
| No new public routes or server surface | PASS |
| Golden tests pass without Ollama | PASS |

## Git state

- **Committed on branch:** pending review
- **Merged to main:** no
- **Pushed:** no

## Recommended next ticket

**ticket-043** (optional per roadmap): extend safety auditor to `data/exports/`,
or review/promote the pending improvement-ticket draft (`missing_quote_span`) if
prioritizing self-improvement loop over safety expansion.
