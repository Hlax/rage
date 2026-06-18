# Agent Report: ticket-329 — README live layer-3 vs public atlas preview boundary

**Date:** 2026-06-18  
**Ticket:** ticket-329  
**Branch:** `phase-3/ticket-329-readme-live-layer3-public-preview-boundary`  
**Main tip before branch:** `671b919`  
**Audit gate:** `agent_reports/2026-06-18_pre-ticket-328_live-layer-3-staged-atlas-coherence-audit.md` (GO; low risk docs)

## Summary

Added explicit README boundary callouts cross-linking live layer-3 private atlas coherence
proof (ticket-285) with mock staged-spine public preview refresh (tickets 320–326). Both
Operator Quickstart sections now state the other path does not write committed public
preview or `fixtures/atlas/` JSON.

## Scope

**In:** README Operator Quickstart boundary paragraphs (live layer-3 + public preview sections).

**Out:** Live network pytest, public site, export-public, marker changes.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Bidirectional boundary cross-links |
| `tickets/ticket-329.json` | Status `done` |
| `tickets/ticket-330.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| README states live layer-3 does not refresh public preview/fixtures | **PASS** |
| Cross-links mock staged-spine (320–326) vs ticket-285 live_network pytest | **PASS** |
| Golden + full pytest pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 144 passed
python -m pytest -q                # 800 passed
```

Safety audit not required — docs-only.

## Recommended next ticket

**ticket-330** — Orphan `agent_reports` hygiene (superseded ticket-308 file); or operator
opt-in live layer-3 pytest on a machine with suitable OpenAlex catalog.

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

_Placeholder — updated after merge._
