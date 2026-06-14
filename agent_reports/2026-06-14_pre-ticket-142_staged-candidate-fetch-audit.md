---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-142
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-142 Fetch Staged Candidate Source from Queue URL

## Verdict: **GO**

ticket-141 persists staged `candidate_sources` rows with URLs. ticket-142 may fetch URL
bytes into **gitignored** `data/sources/staged/` behind `RGE_ALLOW_SOURCE_NETWORK=1` — JSON
report only; **no ingest, no accepted-table writes, no browser automation**.

## Principal / cadence gate

| Field | Value |
|-------|-------|
| Main tip verified | `75e8f16` (post ticket-141 merge) |
| Done since checkpoint | ticket-137–141 (**5**) |
| Milestone triggers (142) | none — filesystem staging + network opt-in only |
| Pre-ticket required | yes (medium risk) — **this report** |
| Cadence | overdue (informational); product continuation of Phase 3 spine |

## Hardened implementation scope

### In

1. **`fetch-candidate` CLI** — `--candidate <id> --db <path> [--out dir]`
2. **`fetcher.py`** — `fetch_staged_candidate_url()`, `default_staged_fetch_dir()`
3. **`CandidateSourceRepository.get_by_id()`** — load staging row
4. Network gate: `RGE_ALLOW_SOURCE_NETWORK=1` (reuse `source_network_enabled`)
5. Output: `data/sources/staged/{candidate_id}{ext}` (gitignored via `data/`)
6. JSON: `status`, `checksum`, `content_type`, `artifact_path`, `byte_count`
7. Idempotent: same checksum at path → `already_fetched`
8. Mocked `urllib` unit tests

### Out

- Playwright/Scrapfly, ingest, claim extraction, schema, public site
- Writes to `sources` / `claims`
- `research_queue` status updates (defer; file artifact only)

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-142 | **GO** |
| Next after 142 | ticket-143 — ingest from staged fetch artifact |
