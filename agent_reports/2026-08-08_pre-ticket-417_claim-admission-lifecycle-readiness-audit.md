---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-08-08
phase: 4
ticket: ticket-417
---

# Pre-Ticket Audit: ticket-417 — Claim admission lifecycle and isolation v0

**Verdict: GO with terminal-state, migration, and accepted-only isolation constraints**

## Summary

Ticket-417 may proceed on its own branch. The current claim repository already preserves
accepted and rejected rows, graph builders explicitly request accepted claims, and the
public-card/evidence-atom projection paths filter accepted claims. The missing controls
are bounded: model candidates are persisted directly in their terminal state, lifecycle
decisions are not durable, and shared claim-concept/relationship-evidence readers do not
re-check claim status when reading historical links.

The implementation must remain a private, additive lifecycle change. Existing accepted
and rejected rows must retain their classifications. Model-derived candidates must be
created as proposed before deterministic Python admission, while deterministic internal
writers may retain a documented Python-only compatibility path that records genesis
decisions. No live model, network, cloud, public-write, or review-interface work is
required.

## Readiness evidence

| Field | Result |
|---|---|
| Working tree | Clean synchronized `main` at `dc6569f` before this audit |
| Queue | ticket-417 ready; no ticket in progress; 418–428 blocked |
| Predecessor | ticket-416 done, merged, pushed, full mock verify passed |
| Claim persistence | Additive migrations through `0011`; status already stored on every claim |
| Graph entry points | Link, relationship, contradiction, and score modules request accepted claims |
| Shared-reader gap | Claim-concept and relationship-evidence repository joins do not re-check accepted status |
| Public boundary | Claim-backed cards, atlas evidence-type projection, and evidence atoms filter accepted claims |
| Live dependency | None; implementation and verification can remain deterministic and mock-only |

## Audit commands

| Command | Result |
|---|---|
| Read-only `operator_loop --mode plan` | `complete_pre_ticket_audit`, review-gated |
| Claim/graph/report/atlas/synthesis focused pytest baseline | PASS — 42 passed |
| Ticket-416 full mock `verify` baseline | PASS — 165 golden; 1442 full; safety/site pass |

## Required lifecycle design

1. Add an append-only private decision table through migration `0012`. Every new
   transition records claim ID, prior state, new state, actor type, stable reason code,
   validator version, policy version, and timestamp.
2. Python must enforce the lifecycle. A model candidate has a single genesis state of
   `proposed`; allowed subsequent transitions are proposed to needs-review, rejected, or
   accepted, and needs-review to rejected or accepted. Accepted and rejected are terminal.
3. Model-backed extraction must insert proposed candidate data first, then call explicit
   deterministic Python admission. No model-facing API may request or write accepted
   status directly.
4. Direct accepted/rejected insertion remains permissible only for deterministic
   Python-owned compatibility writers, including fixture and quality-gate paths. Such
   creation must record a Python genesis decision and must not be reachable from raw
   model output without the proposed step.
5. Admission to accepted must atomically update the candidate fields, persist structured
   fields, add the primary quote, and append the decision. Rejection must atomically
   persist the rejection reason and decision.
6. Repeating an already-completed deterministic extraction or transition must not append
   duplicate decisions, erase history, or alter terminal outcomes.
7. Existing accepted/rejected rows must not be backfilled with invented actors or
   timestamps. They remain readable and terminal even if they predate decision history.
8. Shared graph readers must require `claims.status = 'accepted'`, including claim-concept
   and relationship-evidence joins. Synthesis throughput must count accepted claims and
   accepted-backed links only. Private repository inspection may still return all states.
9. Tests must inject stale link/evidence rows for proposed, needs-review, and rejected
   claims and prove they do not reach graph, scoring, reporting, synthesis, atlas, or
   public projection paths.

## Scope boundaries

- Do not add a human review UI, public review/write route, or automatic review decision.
- Do not implement semantic entailment, citation verification, uncertainty scoring, or
  local-model review; ticket-418 owns that contract.
- Do not delete or reclassify historical claims or decisions.
- Do not add creativity-specific lifecycle fields to core tables.
- Do not require Ollama, OpenAI, source network, or cloud access.
- Do not broaden accepted-only filtering into private diagnostics that intentionally
  report rejected or review-state counts.

## Stop and re-audit conditions

Stop for a new ticket or audit if implementation requires destructive claim-table
replacement, historical reclassification, a public schema change, semantic model review,
live action, a human-choice workflow, or a compatibility break that forces unrelated
deterministic internal claim writers into model-style review.

## Recommended implementation sequence

1. Add the lifecycle decision migration and typed repository record.
2. Implement atomic proposed creation and Python-enforced transitions with idempotency.
3. Route model-backed extraction through proposed before accepted/rejected admission.
4. Add accepted-only guards to shared graph, synthesis, atlas, and public consumers.
5. Add lifecycle, migration, stale-link isolation, and compatibility tests.
6. Run full mock-only verification, report, queue transition, merge, and ordinary push.

## Final recommendation

**GO** for ticket-417 under the constraints above. On successful completion, activate
only ticket-418; no later Phase 4 ticket may move from blocked.
