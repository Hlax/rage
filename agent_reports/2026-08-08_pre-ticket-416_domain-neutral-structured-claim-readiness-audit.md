---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-08-08
phase: 4
ticket: ticket-416
---

# Pre-Ticket Audit: ticket-416 — Domain-neutral structured claim schema v0

**Verdict: GO with compatibility and privacy constraints**

## Summary

Ticket-416 may proceed on its own branch. Ticket-415 now supplies exact, typed chunk
provenance; the claim database and repository support additive migrations; existing
candidate fixtures are explicitly versioned at envelope version `0.1.0`; and public-safe
evidence previews project a fixed allowlist rather than serializing claim rows wholesale.

The implementation must remain a private claim-contract and deterministic-validation
change. It must not introduce semantic model review, lifecycle promotion, graph-consumer
gating, creativity-specific core fields, or public structured metadata.

## Readiness evidence

| Field | Result |
|---|---|
| Working tree | Clean synchronized `main` at `be4165b` |
| Queue | ticket-416 ready; no ticket in progress; 417–428 blocked |
| Predecessor | ticket-415 done, merged, pushed, full mock verify passed |
| Candidate contract | `CandidateClaim_v0_1`; versioned `0.1.0` envelope |
| Claim persistence | Additive columns through migration `0010`; JSON metadata already supported |
| Section provenance | Chunk type/title/page/exact offsets persisted and repository-readable |
| Public boundary | Atlas-safe evidence previews use an explicit allowlist and private-field scan |
| Live dependency | None; implementation and verification can remain local/mock-only |

## Audit commands

| Command | Result |
|---|---|
| Read-only `operator_loop --mode plan` | `complete_pre_ticket_audit`, review-gated |
| Claim/migration/section/public-export focused pytest baseline | PASS — 30 passed |
| Ticket-415 full mock `verify` baseline | PASS — 165 golden; 1427 full; safety/site pass |

## Required contract design

1. Add a typed, domain-neutral structured-claim object nested under the existing
   candidate envelope. The nested object has its own explicit contract version; legacy
   `0.1.0` fixtures may omit it and remain on a documented legacy path.
2. Structured candidates must provide every contract key explicitly. Optional or unknown
   values are represented as `null` or an explicit typed value, never populated by
   defaults inferred from claim text, domain, evidence type, or section.
3. Closed enums must cover claim kind, study design, effect direction, and normalized
   section type. Invalid values fail Pydantic parsing or deterministic validation.
4. Empirical-result claims require an outcome and exact section provenance. Conditional
   rules reject contradictory combinations such as effect direction without outcome,
   statistical context on an incompatible claim kind, or comparator without an
   intervention/exposure.
5. Section provenance must be checked against the persisted source chunk supplied by the
   extractor. A structured candidate cannot pass when its chunk type, title, page, or
   offsets disagree with that chunk; missing verifier context fails closed.
6. Persist structured fields through an additive migration and repository serialization.
   Existing rows remain readable with NULL structured fields; no rewrite or invented
   backfill is allowed.
7. Existing accepted/rejected fixture behavior must remain unchanged when the nested
   structured object is absent. The legacy path must be observable through a null/legacy
   contract version, not silently upgraded.
8. Public cards, atlas previews, and public exports must ignore the new private fields.
   Tests must prove fixed public payload keys remain unchanged and private field names do
   not appear.

## Scope boundaries

- Core code may not contain creativity ontology fields such as creative phase, track, or
  measured dimension; those remain in domain-pack metadata.
- Ticket-416 defines representation and deterministic structural consistency only. It
  does not decide author entailment, citation status, or scientific truth; ticket-418
  owns semantic admission.
- Ticket-416 does not introduce proposed/needs-review lifecycle states or prevent graph
  consumers from reading accepted claims; ticket-417 owns lifecycle isolation.
- Do not change public schemas, public card content, or public route behavior.
- Do not make GROBID, Ollama, cloud, or network access mandatory.

## Stop and re-audit conditions

Stop for a new ticket or audit if implementation requires a destructive migration,
historical claim rewrite, creativity-specific core field, public schema expansion,
semantic/model-based entailment decision, graph-consumer lifecycle refactor, live action,
or global model-envelope version change that forces unrelated task fixtures to migrate.

## Recommended implementation sequence

1. Typed nested structured-claim and section-provenance models with closed enums.
2. Deterministic conditional and chunk-provenance validation with stable rejection
   diagnostics.
3. Additive private persistence and backward-readable repository serialization.
4. Focused compatibility, migration, public-boundary, and fixture tests.
5. Full mock-only verification, report, queue transition, merge, and ordinary push.

## Final recommendation

**GO** for ticket-416 under the constraints above. On successful completion, activate
only ticket-417; no later Phase 4 ticket may move from blocked.
