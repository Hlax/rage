---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-08-08
phase: 4
ticket: ticket-418
---

# Pre-Ticket Audit: ticket-418 — Semantic claim admission validator v0

**Verdict: GO with fail-closed policy, bounded-context, and private-provenance constraints**

## Summary

Ticket-418 may proceed on its own branch. Ticket-413 supplies a checksum-pinned,
domain-neutral benchmark with 40 labeled claim decisions across valid findings and eight
negative slices. Tickets 414–416 supply source eligibility, section provenance, and a
structured research-claim contract. Ticket-417 now guarantees proposed-first model data,
Python-owned lifecycle transitions, append-only decisions, and accepted-only consumers.

The implementation must remain a private second-pass admission gate. A semantic reviewer
may propose a typed decision over an exact quote plus bounded same-section context, but
Python must validate the proposal, combine it with existing deterministic gates, and
apply the lifecycle transition. Invalid, inconsistent, or uncertain reviewer output goes
to `needs_review`; it never fails open to accepted.

## Readiness evidence

| Field | Result |
|---|---|
| Working tree | Clean synchronized `main` at `4012f60` |
| Queue | ticket-418 ready; no ticket in progress; 419–428 blocked |
| Predecessor | ticket-417 done, merged, pushed, all final component gates passed |
| Benchmark | 40 labeled claims across valid plus eight required negative slices |
| Source boundary | Eligibility and section-aware extraction gates already persist stable reason codes |
| Claim boundary | Exact quote, scope, domain, injection, structured schema, and provenance checks already fail closed |
| Lifecycle | Model candidate → proposed; Python-only accepted/rejected/needs-review transitions |
| Model modes | Deterministic mock is default; Ollama requires explicit live opt-in |
| Live dependency | None for implementation, CI, golden tests, or completion |

## Audit commands

| Command | Result |
|---|---|
| Read-only `operator_loop --mode plan` | `complete_pre_ticket_audit`, review-gated |
| Benchmark/lifecycle/validator/structured/extraction baseline | PASS — 41 passed |
| Ticket-417 final component gates | PASS — 165 golden; 1448 full; safety/site pass |

## Required semantic-review design

1. Define a versioned, domain-neutral review proposal with closed fields for decision
   (`accepted`, `rejected`, `needs_review`), entailment, source-author role, reason code,
   and bounded private rationale/evidence. The model cannot emit a database status or
   invoke repository writers.
2. Review only the exact validated quote plus a deterministic bounded window from the
   same persisted chunk/section. Do not send a full document, unrelated section, local
   path, secret, private note, or public-export payload.
3. Python validates schema and combination rules. Accepted requires structural admission,
   entailed content, source-author finding classification, an accepted-compatible reason,
   exact provenance, and no deterministic source/section/content veto.
4. Bibliography/reference text, navigation, access challenge, redirect shell,
   methods-as-findings, cited background, unsupported generalization, and quote/claim
   mismatch must produce their stable rejection reason or `needs_review`; none may be
   accepted in the committed benchmark.
5. Hypothesis, speculation, title-only, non-content, ambiguous attribution, ambiguous
   entailment, invalid reviewer JSON, unknown enum, or inconsistent field combinations
   route to `needs_review` with stable Python policy reasons unless a deterministic
   rejection rule is conclusive.
6. Record reviewer provider/model identity, prompt-contract version, bounded-context
   checksum, proposed decision, and Python policy outcome privately. Use an additive
   migration if the ticket-417 decision record cannot represent this provenance without
   overloading actor/reason fields. Existing decisions remain unchanged.
7. Default mock review must be deterministic, fixture-backed, and network-free. Golden
   extraction behavior remains reproducible without Ollama.
8. Optional local Ollama review must require `RGE_LLM_MODE=ollama`,
   `RGE_ALLOW_LIVE_LLM=1`, and a semantic-review-specific opt-in. Missing gates select or
   retain mock review and never make a live call. This ticket does not run the live path.
9. Reruns must not duplicate lifecycle decisions or erase the original reviewer/policy
   provenance. Terminal accepted/rejected claims remain terminal.
10. Evaluate the committed benchmark through the actual semantic policy and report
    precision, recall, false acceptance, per-slice decisions, and reason-code behavior.

## Scope boundaries

- Do not use the model reviewer as sole authority; existing deterministic gates remain
  mandatory and cannot be weakened or bypassed.
- Do not implement ticket-419's human review CLI or any public review/write route.
- Do not bulk-promote `needs_review` claims or historical candidates.
- Do not add retrieval, answer generation, cross-source corroboration, or graph-completion
  logic; those belong to later tickets.
- Do not require live Ollama, network, cloud, credentials, or paid providers.
- Do not expose reviewer rationale, context, model identity, or lifecycle history publicly.

## Stop and re-audit conditions

Stop for a new ticket or audit if implementation requires full-document model context,
destructive migration, historical reclassification, public schema expansion, live action,
cloud review, a human-choice workflow, or acceptance based solely on a reviewer label
without deterministic Python policy checks.

## Recommended implementation sequence

1. Versioned review proposal and bounded-context contract.
2. Deterministic Python semantic policy with stable decisions/reasons.
3. Fixture-backed mock reviewer and separately gated optional Ollama adapter.
4. Proposed-claim integration and private review/decision provenance.
5. Benchmark, contract, invalid-output, lifecycle, and no-live-call tests.
6. Full mock-only verification, report, queue transition, merge, and ordinary push.

## Final recommendation

**GO** for ticket-418 under the constraints above. On successful completion, activate
only ticket-419; no later Phase 4 ticket may move from blocked.
