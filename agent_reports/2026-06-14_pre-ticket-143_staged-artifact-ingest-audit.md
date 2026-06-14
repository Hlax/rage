---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-143
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-143 Ingest from Staged Fetch Artifact

## Verdict: **GO**

ticket-142 writes gitignored fetch artifacts. ticket-143 may ingest those bytes into
`sources` + `chunks` via explicit **`ingest-staged`** CLI with checksum verification —
**no automatic claim extraction**.

## Principal / cadence gate

| Field | Value |
|-------|-------|
| Main tip | `51c6634` (post ticket-142) |
| Pre-ticket required | yes (medium) — **this report** |
| Milestone triggers | none — uses existing ingest path; no migrations/public export |

## Hardened scope

### In

1. **`ingest-staged` CLI** — `--domain` required; `--candidate` or `--artifact`; optional `--checksum`, `--db`
2. Resolve artifact from `data/sources/staged/{candidate_id}.*` or explicit path
3. Verify `sha256` when `--checksum` provided
4. HTML → minimal text extraction; reuse `ingest_local_source` (idempotent by checksum)
5. Pull title/source_type from `candidate_sources` when `--candidate` + row exists
6. Mocked/fixture unit tests; scaffold help update

### Out

- extract-claims, live LLM, Playwright, schema, public site
- Automatic pipeline after ingest

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-143 | **GO** |
| Next | ticket-144 — operator extract-claims on staged-ingested source |
