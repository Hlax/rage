---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-152
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-152 Second Staged Candidate Fetch and Ingest

## Verdict: **GO**

OpenAlex fixture already returns **two** works; ticket-141 enqueue persists both to
`candidate_sources` and `research_queue`. ticket-142/143 prove fetch + ingest-staged for
rank #1 (`disc_openalex_W2741809807`). ticket-152 may add **unit tests only** for rank #2
(`disc_openalex_W1234567890`) with mocked network — no production changes expected.

## 1. Rank #2 candidate contract

| Field | Value |
|-------|-------|
| provider_id | `W1234567890` |
| candidate_sources id | `disc_openalex_W1234567890` |
| title | Constraint management in AI-assisted creative teams |
| landing_page_url | `https://example.org/landing/constraint-management` |
| rank | #2 (lower `priority_score` than W2741809807) |

## 2. Existing idempotent surfaces (reuse)

| Step | Re-run status |
|------|---------------|
| discover enqueue | `already_queued` when prefix rows exist |
| fetch-candidate | `already_fetched` |
| ingest-staged | `already_ingested` |

## 3. Minimal test design

File: `tests/unit/test_staged_second_candidate_spine.py`

1. `discover-sources --rank-only --enqueue` (mock OpenAlex) → 2 candidates, 2 queue rows
2. Optional: fetch rank #1 artifact (establishes two-artifact baseline)
3. `fetch-candidate --candidate disc_openalex_W1234567890` with mock HTML → `completed`
4. Assert staging dir has **one artifact per fetched candidate** (no duplicate filenames)
5. `ingest-staged --candidate disc_openalex_W1234567890` → `ingested`; `sources` count stable on re-run
6. CLI JSON asserts `status`, `checksum` / `artifact_checksum`

Mock HTML for rank #2 (distinct from rank #1 co-creativity text):

```html
<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>
```

## 4. Out of scope (ticket non_goals)

- extract/link/build for second source → ticket-153 follow-on
- Live OpenAlex, schema, public export/site

## 5. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_spine.py -q
python -m pytest tests/unit/test_staged_ingest_idempotency.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Audit gates

| Gate | Status |
|------|--------|
| Principal cadence | satisfied (post ticket-150) |
| Pre-ticket audit (medium) | **this report — GO** |
