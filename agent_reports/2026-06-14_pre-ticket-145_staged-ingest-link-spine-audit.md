---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-145
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-145 Link Concepts on Staged-Ingested Source

## Verdict: **GO**

ticket-144 proves extract-claims on staged sources. ticket-145 may add
**link-concepts** with `staged_fetch_link_concepts.json` and extend the e2e unit
test — mock LLM only.

## Hardened scope

### In

1. `fixtures/llm_outputs/staged_fetch_link_concepts.json`
2. `concept_linker.py` — staged source title heuristic + claim id resolution for spine text
3. `tests/unit/test_staged_ingest_link_spine.py` — discover→fetch→ingest→extract→link

### Out

- Live Ollama, build-relationships/detect spine, schema, public site

## Recommendation

**GO** — implement ticket-145; next ticket-146 build-relationships on staged source.
