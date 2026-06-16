---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-284
category: Phase 3 / Research Atlas / follow_up_questions projection
---

# Pre-Ticket Audit: ticket-284 Atlas Snapshot follow_up_questions[] v0

## Verdict: **GO**

Projects queued follow-up questions from `research_queue` into atlas snapshot as
`follow_up_questions[]`. Read-only DB projection; no public export or site changes.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | Atlas export remains operator-private CLI |
| Public site | **No** | None |
| Schema migrations | **No** | Reuse existing `research_queue` rows |
| Theory / inference | **No** | Question text only (planner output), not theory synthesis |
| Live Ollama | **No** | Fixture MVP DB tests only |

## Hardened scope

### In scope

1. `follow_up_questions[]` on atlas snapshot dict (optional; empty when no queue rows)
2. Source: `ResearchQueueRepository.list_followups_for_contract()` or equivalent SQL for golden contract
3. Per-item fields: `id`, `research_question_id`, `reason`, `status`, `question_text`, `priority_score`
4. `AtlasSnapshot_v0_1` pydantic optional field + constant for documented keys
5. Regenerate `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`
6. Builder tests + `assert_no_private_fields` pass

### Out of scope

- `research_questions` table migration
- Public atlas export route
- Public-site UI
- `review_batch` persistence
- Exposing `last_error` key name (map to `question_text` only)

## Safety

- `question_text` is scoped research question prose from planner (ticket-013 pattern), not raw source text
- Fail-closed private-field scan before export unchanged
- No new public write routes

## Recommendation

**GO** — implement follow_up_questions projection and regenerate fixture.
