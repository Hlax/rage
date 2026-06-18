# Agent Report: ticket-312 — README operator atlas preview fixture refresh runbook

**Date:** 2026-06-17  
**Ticket:** ticket-312  
**Branch:** `phase-3/ticket-312-readme-atlas-preview-fixture-refresh-runbook`  
**Main tip before branch:** `f4ed019`  
**Audit gate:** `agent_reports/2026-06-17_principal-audit-post-ticket-310.md` (cadence satisfied; low risk docs).

## Summary

Documented operator workflow to refresh committed `/atlas-preview` JSON from fixture-mode
`export-atlas-snapshot` with `--coherence-preview-out` (ticket-308). Replaced stale
“public atlas deferred” README text; cross-linked tickets 300/308/312 and Public Site
section.

## Scope

**In:**

- Operator Quickstart **Research Atlas public preview fixture refresh** section
- Public Site cross-link to runbook and `/atlas-preview`

**Out:**

- CLI changes, public site code, automated script, export-public changes

## Changed files

| File | Change |
|------|--------|
| `README.md` | Fixture refresh runbook + Public Site cross-link |
| `tickets/ticket-312.json` | Status `done` |
| `tickets/ticket-313.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Operator Quickstart documents fixture-mode export to preview paths | **PASS** |
| Documents `--coherence-preview-out` sidecar | **PASS** |
| Notes `git add -f` when paths not staged | **PASS** |
| Cross-links ticket-300/308 and `/atlas-preview` | **PASS** |
| Golden + full pytest pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 144 passed
python -m pytest -q                # 789 passed, 33 deselected
```

Safety audit not required — README-only; no export or site surface changes.

## Manual CLI verification

Not run — docs-only ticket; runbook commands match `test_atlas_coherence_preview_sync.py`
fixture-mode CLI pattern.

## Spec deviations

None.

## Recommended next ticket

**ticket-313** — README evidence DB atlas vs public preview boundary note (clarify
non-fixture exports stay operator-private; public preview refresh is fixture-mode only).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `0f8ac38`
