---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-027 / public-site-debug-details

## 1. Summary

Implemented Golden Test 25 public-site debug details without private data exposure. Added curated `evidence_type` and `public_run_timestamp` fields to public export policy and card exporter, rendered a read-only "Research debug details" section on card detail pages, extended full safety audit with GT25 evidence checks, and added Golden Test 25 (4 tests). All 114 golden tests pass without Ollama; public site static build succeeds; full safety audit returns `pass`.

## 2. Ticket

- Ticket ID: ticket-027
- Ticket title: Add public-site debug details without private data exposure (Golden Test 25)
- Branch: `phase-1/ticket-027-public-site-debug-details`
- Phase: 1
- Agent/model: Cursor builder agent (GPT-5.5)
- Date: 2026-06-12
- Main tip before branch: `1b2929c` (includes pre-ticket-027 audit)

## 3. Scope

### In Scope

- Curated public export fields: `evidence_type`, `public_run_timestamp`
- Card exporter derivation from linked claims and golden extras
- Public-site card detail debug section
- Golden Test 25 (`tests/golden/test_25_public_site_debug_details.py`)
- Safety audit GT25 evidence check
- GT00/GT11 allowed-field list sync

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, prompt-injection changes, DB schema migration, or ticket beyond ticket-027.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/safety/public_export_policy.py` | Whitelisted `evidence_type` and `public_run_timestamp`. |
| `rge/modules/card_exporter.py` | Golden extras + claim-derived evidence type; public run timestamp from card creation. |
| `rge/db/repositories.py` | Export dict supports new debug extras. |
| `apps/public-site/lib/publicCards.ts` | TypeScript types for debug fields. |
| `apps/public-site/app/cards/[id]/page.tsx` | Research debug details section. |
| `apps/public-site/public/data/public_cards.json` | Golden cards include debug fields. |
| `rge/modules/safety_auditor.py` | Full audit GT25 evidence check. |
| `tests/golden/test_25_public_site_debug_details.py` | New: Golden Test 25 (4 tests). |
| `tests/golden/test_00_public_site_static.py` | Sync allowed field list. |
| `tests/golden/test_11_public_card_export.py` | Sync allowed field list. |
| `tickets/TICKET_QUEUE.md` | ticket-027 done; ticket-028 proposed. |
| `tickets/ticket-027.json` | Status `done`. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-027_public-site-debug-readiness-audit.md` (commit `1b2929c`).
- `GOLDEN_PRIVATE_FIELDS` remain in DB only; export uses `curated_public_card()` and GT25 asserts they never leak.
- `public_run_timestamp` defaults to card `created_at` when not overridden by golden extras.
- `evidence_type` defaults to dominant type among linked accepted claims.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Card detail shows public-safe debug details | PASS | evidence type, run timestamp, plus existing summary/concepts/confidence/sources/caveats/metadata/related |
| No private data in public debug UI | PASS | GT25 forbidden-key/value checks; no dangerouslySetInnerHTML |
| `pytest tests/golden/test_25_public_site_debug_details.py` | PASS | 4/4 |
| Existing golden tests still pass (110+) | PASS | 114/114 |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_25_public_site_debug_details.py` | PASS | 4 passed |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS | 114 passed |
| `RGE_LLM_MODE=mock python -m pytest` | PASS | 114 passed |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS | status `pass`, exit 0 |
| `cd apps/public-site && npm run build` | PASS | 11 static pages |

## 8. Safety Audit

Full safety audit passes and now includes GT25 evidence files in `checked_files`:

- `apps/public-site/app/cards/[id]/page.tsx`
- `apps/public-site/lib/publicCards.ts`
- `tests/golden/test_25_public_site_debug_details.py`

## 9. Spec Deviations

- Updated `test_00_public_site_static.py` allowed fields (required after policy expansion; not listed in ticket expected_files but necessary for green suite).
- Extended full safety audit with `public_site_debug` check beyond ticket minimum (mirrors GT24 pattern).

## 10. Merge to Main

- Merge commit: `32e0e04` (fast-forward from `1b2929c`)
- Branch: `phase-1/ticket-027-public-site-debug-details` merged to `main`.
- Post-merge pytest on `main`: 114 passed.
- Post-merge safety audit on `main`: `pass`.

## 11. Recommended Next Ticket

**ticket-028**: Full MVP end-to-end golden run (Golden Test 26).

## 12. Suggested Next Prompt

```txt
/rge-run-next-ticket
```
