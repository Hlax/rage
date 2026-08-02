# Phase 4 research-quality and RAG planning audit

## Outcome

Created a dependency-gated Phase 4 implementation program for the highest-priority
research-quality, graph-admission, retrieval, corroboration, and measured-improvement
gaps identified by the 2026-08-02 repository capability audit.

The program is defined in
`docs/agents/15_RESEARCH_QUALITY_RAG_IMPLEMENTATION_PLAN.md` and implemented as
ticket contracts 413 through 428. Ticket 413 is the only ready Phase 4 ticket. Tickets
414 through 428 are blocked by their immediate predecessor so scheduled automation
cannot jump ahead of claim-quality gates.

## Scheduling decision

`ticket-411` was the current in-progress ticket when this planning audit began. Its
required `origin/main` push checkpoint completed on 2026-08-02. Phase 4 work must not
begin on a new branch until the unrelated dirty worktree is preserved outside `main`.

`ticket-412` remains proposed. Ticket 413 is explicitly ready and has higher status
priority because research correctness is a higher product-risk concern than additional
launcher contract coverage. Ticket 412 is not rejected and can resume after Phase 4 or
through an explicit operator reprioritization.

## Program design

The sequence is:

1. deterministic research-quality corpus and baseline metrics;
2. source contamination gate and section-aware parsing;
3. structured claims, staged admission, semantic review, and human review;
4. cross-source corroboration and evidence-derived completeness;
5. reviewed open-access arbitrary-source proof;
6. lexical/graph retrieval, local embeddings, and citation-governed answers;
7. RAG benchmark and metric-driven improvement loop.

This ordering prevents retrieval or recursive-improvement features from amplifying the
known false-acceptance problem.

## Files added or changed

- `docs/agents/15_RESEARCH_QUALITY_RAG_IMPLEMENTATION_PLAN.md`
- `AGENTS.md`
- `tickets/ticket-413.json` through `tickets/ticket-428.json`
- `tickets/TICKET_QUEUE.md`
- this report

## Verification

Planning artifacts require structural verification rather than engine execution:

- parse all ticket JSON files;
- confirm ticket IDs, statuses, expected fields, and dependency chain;
- parse the queue and confirm ticket 411 remains active and ticket 413 becomes the
  first ready Phase 4 ticket after ticket 411 closes;
- run focused queue/operator tests if existing queue-selection assertions are affected;
- run the safety audit because the plan adds future accepted-graph and synthesis work,
  while making no runtime safety-policy changes in this planning pass.

No live network, live LLM, paid API, database migration, accepted graph write, public
export, merge, push, or publication was authorized or performed by this planning audit.

## Verification results

- PowerShell JSON parsing and required-field audit: pass for tickets 413–428.
- Repository `validate_builder_ticket`: pass for all 16 tickets with zero violations.
- Phase 4 status audit: exactly one ready ticket (`ticket-413`) and 15 blocked tickets.
- Queue simulation before the sync checkpoint selected `ticket-411`; after the completed
  ticket-411 row was removed in memory, it selected `ticket-413` with status `ready`.
- Focused operator, autocycle, and principal-audit tests: `59 passed in 67.99s`.
- Full safety audit: `pass`, with no blocked reasons.
- `git diff --check` surfaced a pre-existing trailing blank line warning in the unrelated
  dirty file `scripts/run_full_atlas_refresh_checklist.py`; no planning file produced a
  whitespace error.

The full golden and pytest suites were not rerun because this pass changed planning,
queue, and ticket artifacts only. Engine runtime code was not modified by this plan.
