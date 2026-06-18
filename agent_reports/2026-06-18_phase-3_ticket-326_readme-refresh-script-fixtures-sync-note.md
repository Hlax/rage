# Agent Report: ticket-326 — README refresh script auto-sync fixtures/atlas note

**Date:** 2026-06-18  
**Ticket:** ticket-326  
**Branch:** `phase-3/ticket-326-readme-refresh-script-fixtures-sync-note`  
**Main tip before branch:** `52365e7`  
**Audit gate:** `agent_reports/2026-06-18_principal-audit-post-ticket-325.md` (GO; low risk docs)

## Summary

Updated README Operator Quickstart staged-spine refresh section to document automatic
`fixtures/atlas/atlas_snapshot_staged_spine_preview.json` sync (ticket-325). Removed manual
copy/verify wording; added fixtures path to `git add` staging example; cross-linked tickets
320–325.

## Scope

**In:** README Operator Quickstart + Public Site cross-link.

**Out:** Script behavior, public site, live proofs.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Auto-sync note; staging includes fixtures/atlas |
| `tickets/ticket-326.json` | Status `done` |
| `tickets/ticket-327.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| README states script auto-writes fixtures/atlas reference | **PASS** |
| Manual copy instructions removed/updated | **PASS** |
| Golden + full pytest pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 144 passed
python -m pytest -q                # 800 passed
```

Safety audit not required — docs-only.

## Recommended next ticket

**ticket-327** — Principal audit post-ticket-326 (cadence due after 325–327 batch).

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

Merge commit: `b8df560`
