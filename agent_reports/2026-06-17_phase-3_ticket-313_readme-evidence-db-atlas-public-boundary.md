# Agent Report: ticket-313 — README evidence DB atlas vs public preview boundary

**Date:** 2026-06-17  
**Ticket:** ticket-313  
**Branch:** `phase-3/ticket-313-readme-evidence-db-atlas-public-boundary`  
**Main tip before branch:** `de74e52`  
**Audit gate:** `agent_reports/2026-06-17_principal-audit-post-ticket-310.md` (cadence satisfied; low risk docs).

## Summary

Added explicit **Public boundary** paragraph to the Evidence DB atlas section: non-fixture
exports stay operator-private under `data/` and do not publish to `/atlas-preview` or
`export-public`. Cross-linked fixture-mode refresh runbook (ticket-312). Deduplicated
transition text before the fixture refresh section.

## Scope

**In:**

- Evidence DB atlas **Public boundary** paragraph + cross-link
- Fixture refresh section back-reference to boundary

**Out:**

- CLI changes, public site code, live evidence-DB → public pipeline

## Changed files

| File | Change |
|------|--------|
| `README.md` | Evidence DB vs public preview boundary |
| `tickets/ticket-313.json` | Status `done` |
| `tickets/ticket-314.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Evidence DB section cross-links fixture refresh runbook | **PASS** |
| Explicit operator-private vs public `/atlas-preview` boundary | **PASS** |
| No CLI or export semantic changes | **PASS** |
| Golden + full pytest pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 144 passed
python -m pytest -q                # 789 passed, 33 deselected
```

Safety audit not required — README-only.

## Manual CLI verification

Not applicable — docs-only ticket.

## Spec deviations

None.

## Recommended next ticket

**ticket-314** — Principal audit post-ticket-313 checkpoint (cadence: 3 done tickets since
principal audit 311; read-only).

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

Merge commit: `a29ac73`
