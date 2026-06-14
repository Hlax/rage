---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-144
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-144 Staged Ingest Extract Mock Spine

## Verdict: **GO**

ticket-143 ingests staged artifacts into sources/chunks. ticket-144 may prove
**extract-claims** on that source with mock fixtures and an e2e unit test covering
discover → enqueue → fetch → ingest-staged → extract — **no live LLM**.

## Principal / cadence gate

| Field | Value |
|-------|-------|
| Main tip | `494dc6c` (post ticket-143) |
| Pre-ticket required | yes — **this report** |
| Milestone triggers | none — mock extract only; no public export/migrations |

## Hardened scope

### In

1. `fixtures/llm_outputs/staged_fetch_extract_claims.json` — quotes match staged HTML text
2. `claim_extractor.py` — auto-select staged fixture when chunk text matches spine pattern
3. `tests/unit/test_staged_ingest_extract_spine.py` — full mocked Phase 3 path + extract-claims
4. No CLI changes required (`extract-claims --fixture` already exists)

### Out

- Live Ollama, link-concepts/relationship spine (ticket-145+), schema, public site

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-144 | **GO** |
| Next | ticket-145 — link-concepts on staged-ingested source |
