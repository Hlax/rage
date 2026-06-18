# Agent Report: ticket-325 — Refresh script sync fixtures/atlas staged-spine reference

**Date:** 2026-06-18  
**Ticket:** ticket-325  
**Branch:** `phase-3/ticket-325-refresh-script-sync-fixtures-atlas`  
**Main tip before branch:** `16865c9`  
**Audit gate:** `agent_reports/2026-06-18_principal-audit-post-ticket-324.md` (GO; low risk)

## Summary

Extended `write_public_preview_fixtures` / `export_staged_spine_preview_to_paths` with optional
`fixtures_reference_path`. The refresh script now auto-writes
`fixtures/atlas/atlas_snapshot_staged_spine_preview.json` alongside public-site preview JSON,
closing the manual copy gap documented in ticket-324 README.

## Scope

**In:** `atlas_preview_curator.py`, refresh script, unit test.

**Out:** README, public-site routing, coherence sidecar in fixtures/, export-public.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/atlas_preview_curator.py` | Optional fixtures reference sync on write |
| `scripts/refresh_atlas_preview_from_staged_spine.py` | Pass fixtures/atlas path |
| `tests/unit/test_public_atlas_preview_fixture.py` | Sync behavior test (+1) |
| `tickets/ticket-325.json` | Status `done` |
| `tickets/ticket-326.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Script writes `fixtures/atlas/atlas_snapshot_staged_spine_preview.json` | **PASS** |
| Parity test remains green without manual copy | **PASS** |
| No export-public or public-site routing changes | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_public_atlas_preview_fixture.py -q   # 7 passed
python -m pytest -q                                                     # 800 passed
```

Safety audit not required — script/curator path only; no committed public JSON change in this run.

## Recommended next ticket

**ticket-326** — README note that refresh script auto-syncs fixtures/atlas reference (low risk docs).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

_Placeholder — updated after merge._
