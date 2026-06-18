# Agent Report: ticket-324 — README staged-spine atlas preview refresh runbook

**Date:** 2026-06-18  
**Ticket:** ticket-324  
**Branch:** `phase-3/ticket-324-readme-staged-spine-atlas-preview-runbook`  
**Main tip before branch:** `f7aa16b`  
**Audit gate:** `agent_reports/2026-06-18_principal-audit-post-ticket-322.md` (GO; low risk docs)

## Summary

Updated README Operator Quickstart **Research Atlas public preview fixture refresh** to
document `scripts/refresh_atlas_preview_from_staged_spine.py` as the primary staged-spine
refresh path, `fixtures/atlas/atlas_snapshot_staged_spine_preview.json` offline
reference, and ticket-321 UI labeling. Retained ticket-312 fixture-mode MVP steps as legacy
alternate.

## Scope

**In:** README Operator Quickstart section + Public Site cross-link.

**Out:** CLI changes, public site code, script behavior, export-public.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Staged-spine primary runbook + legacy MVP subsection |
| `tickets/ticket-324.json` | Status `done` |
| `tickets/ticket-325.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Documents `scripts/refresh_atlas_preview_from_staged_spine.py` as primary path | **PASS** |
| Documents `fixtures/atlas/` offline reference + parity test | **PASS** |
| Retains fixture-mode MVP as legacy; cross-links 320–322 | **PASS** |
| Golden + full pytest pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 144 passed
python -m pytest -q                # 799 passed, 33 deselected
```

Safety audit not required — docs-only.

## Recommended next ticket

**ticket-325** — Extend refresh script to sync `fixtures/atlas/` reference (low risk), or
opt-in live layer-3 staged atlas proof (medium risk; pre-ticket audit if public JSON).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

_Placeholder — updated after merge._
