---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-141
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-141 Enqueue Discovered Candidates to Staging Research Queue

## Verdict: **GO**

ticket-140 ranks discovered candidates in CLI JSON only. ticket-141 may persist ranked
candidates to **staging** tables (`candidate_sources`, `research_queue`) behind explicit
`--enqueue` with `--rank-only` — no fetch, ingest, or accepted-table writes.

## Principal / cadence gate

| Field | Value |
|-------|-------|
| Main tip verified | `03f68d9` (post ticket-140 merge) |
| Latest principal checkpoint | `agent_reports/2026-06-14_ticket-137_principal-audit-post-ticket-136.md` |
| Done since checkpoint | ticket-137, ticket-138, ticket-139, ticket-140 (**4**) |
| `principal_audit_gate --next-ticket ticket-141` | `cadence_status: overdue`; `implementation_gate: blocked_missing_pre_ticket_audit` |
| Milestone triggers (141) | none — staging DB only; no migrations, public export, theory, live-smoke |
| Pre-ticket required | yes (medium risk) — **this report** |
| Cadence note | Cadence overdue by counter. ticket-139–140 are product work. This audit satisfies the medium-risk gate for ticket-141. |

## Repo verification (2026-06-14)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_SOURCE_NETWORK = "0"

python -m pytest tests/golden -q          # 142 passed
python -m pytest -q                       # 511 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full   # pass
```

## Gap analysis

| Layer | ticket-140 | ticket-141 need |
|-------|------------|-----------------|
| `discover-sources --rank-only` | JSON `ranked_candidates[]` | Same + optional `--enqueue` |
| `candidate_sources` / `research_queue` | fixture path via `queue-sources` only | discovered candidate persist |
| Idempotency | fixture: whole-question `already_queued` | per `(research_question_id, provider_id)` |
| Candidate ID | fixture ids (`cand_*`) | stable `disc_{provider}_{provider_id}` |

## Hardened implementation scope

### In

1. **`discovered_candidate_source_id(provider, provider_id)`** — stable staging PK.
2. **`enqueue_discovered_candidates(conn, ranked, provider_id, research_question_id, contract_id)`**
   - Map ranked rows to `CandidateSourceRepository.insert` + `ResearchQueueRepository.insert`
   - URL from `landing_page_url` or `open_access_url`
   - Skip `research_queue` insert when `status == rejected`
   - Idempotency: if any `candidate_sources` row exists for question with id prefix
     `disc_{provider}_`, return `already_queued` (mirror fixture coarse guard)
   - Repository `ON CONFLICT DO NOTHING` prevents duplicate rows on re-run
3. **CLI:** `discover-sources --rank-only --enqueue --db <path> [--question <rq_id>]`
   - `--enqueue` requires `--rank-only` and `--db`
   - Default `--question` to `DEFAULT_RESEARCH_QUESTION_ID`
4. **`source_discovery.py`** — optional enqueue hook or keep DB in CLI (prefer CLI like `queue-sources`)
5. **Tests:** `test_discovered_source_queue_enqueue.py` — mocked discover + temp db + idempotency

### Out

- Fetch/ingest/extract, Playwright, schema migrations, public site
- Writes to `sources`, `claims`, or other accepted graph tables
- Automatic ingest or credibility finalization

## Contract sketch

```json
{
  "command": "discover-sources",
  "status": "completed",
  "enqueue_status": "completed",
  "research_question_id": "rq_creativity_ai_diversity",
  "provider": "openalex",
  "queue_count": 2,
  "queue_item_ids": ["..."],
  "ranked_candidates": [ "... scored rows ..." ]
}
```

Re-run: `enqueue_status: "already_queued"` when staging rows exist for question+provider.

## Safety

| Boundary | ticket-141 |
|----------|------------|
| Staging tables only | `candidate_sources`, `research_queue` |
| Accepted graph | no writes |
| Operator review | required before ingest (later tickets) |

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-141 | **GO** |
| Next after 141 | ticket-142 — fetch staged candidate URL (product) |

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-141**.
