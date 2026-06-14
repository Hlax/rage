---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-139
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-139 Source Provider Registry and OpenAlex Discovery Proof

## Verdict: **GO**

ticket-138 delivered the Phase 3 command surface only. ticket-139 may implement the
**first real API-first provider** under strict opt-in network, mocked tests, and
metadata-only output — no ingest, fetch, scraping, or DB writes in this ticket.

## Principal / cadence gate

| Field | Value |
|-------|-------|
| Latest checkpoint | post-ticket-136 (+ ticket-137) |
| ticket-138 | done — stub CLI only |
| Cadence after 138 merge | monitor (2 done since post-136 if counting 137+138) |
| Milestone triggers | network opt-in new surface — addressed below |
| Pre-ticket required | yes (medium risk) — **this report** |

## Audit questions

### What metadata fields are needed for a candidate source?

Minimum v1 candidate record (JSON only — **no schema/table in ticket-139**):

| Field | Purpose |
|-------|---------|
| `provider` | e.g. `openalex` |
| `provider_id` | OpenAlex work ID |
| `title` | display / queue ranking |
| `authors` | optional list of display names |
| `year` | recency prior |
| `doi` | stable identifier when present |
| `open_access_url` / `landing_page_url` | future fetcher entry (URL only, no fetch) |
| `abstract` | optional snippet for operator review (not stored in graph) |
| `domain_pack` | pack id passed through from CLI |
| `discovered_at` | ISO timestamp |

Later tickets add ingest/fetch; ticket-139 returns this list in CLI JSON only.

### Schema/table now or JSON output enough?

**JSON output is enough for ticket-139.** No migration, no `candidate_sources` table.
Staging table deferred until fetcher + operator review flow is specified (ticket-140+).

### Provider credentials checked safely?

- OpenAlex public API: unauthenticated with polite `mailto` query param (`OPENALEX_MAILTO` env).
- Optional `OPENALEX_API_KEY` only if future premium path needed — never log or print env values.
- Health check returns `{ "provider": "openalex", "configured": true/false, "mailto_set": bool }` without secret values.
- Safety audit: grep tests assert stdout/stderr exclude key patterns.

### Network opt-in?

- Require `RGE_ALLOW_SOURCE_NETWORK=1` (new env, parallel to `RGE_ALLOW_LIVE_LLM`).
- Without opt-in: structured JSON `{ "status": "blocked", "reason": "source_network_disabled", ... }`, exit **1** (distinct from stub exit **2**).
- CI/golden: never set opt-in; tests mock HTTP layer.

### Tests deterministic?

- Unit tests patch HTTP client (e.g. `urllib.request.urlopen` or dedicated thin `openalex_http.get_json`).
- Fixture: `fixtures/source_providers/openalex_works_sample.json`.
- No live network in pytest default collection.

### Connection to source_preferences, research_queue, NM-4?

| Consumer | ticket-139 | Later |
|----------|------------|-------|
| `source_preferences.yaml` | pass `domain_pack` into discover; ranking overlay in ticket-140+ | credibility priors applied when queue ranks candidates |
| `research_queue` | not wired | ticket-140 enqueue discovered candidates |
| NM-4 evidence DB ingest | **out of scope** | manual operator selects candidate → ingest manual_text or fetcher ticket |

### Out of scope (enforced)

- PDF/HTML fetch, Playwright, Scrapfly, browser automation
- Claim extraction, DB writes, public export/site
- Cloud LLM, automatic credibility decisions
- Public ingestion routes

## Hardened implementation scope

### In

1. `rge/modules/source_providers/` — protocol/registry + `OpenAlexProvider`.
2. Extend `discover-sources`:
   - default (no flags): keep ticket-138 stub **or** require `--provider` (audit decision: **require `--provider openalex` for real path**; bare `discover-sources` remains stub exit 2 until provider selected).
   - `--provider openalex --query "..." --limit N --domain creativity`
   - `--health` optional flag for provider readiness JSON.
3. `RGE_ALLOW_SOURCE_NETWORK=1` gate before HTTP.
4. Mocked unit tests + fixture JSON.
5. Manual live verification documented in agent report (optional, skipped in CI).

### Out

Everything listed in ticket-139 JSON non_goals.

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-139 | **GO** |
| Next after 139 | ticket-140 — wire candidates to research_queue + source_preferences ranking (product) |
| Docs/checkpoint/stub loop | **stop** — no ticket-140 docs-only |

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-139**.
