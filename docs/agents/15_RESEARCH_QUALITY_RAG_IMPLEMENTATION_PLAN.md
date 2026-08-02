# Research Quality and RAG Implementation Plan

## Purpose

This plan converts the post-MVP capability audit into bounded Phase 4 tickets. The
objective is not to relabel the existing graph pipeline as RAG. The objective is to
make research claims trustworthy enough for retrieval, then add a measurable
retrieve-to-evidence-to-answer path, and finally make improvement tickets depend on
observed quality deltas.

This document is subordinate to the canonical context, golden tests, architecture,
data model, safety model, operating protocol, runtime configuration, and model
escalation policy. Existing non-negotiable rules remain in force:

- models propose candidate JSON only;
- Python validates and writes;
- no model output writes directly to accepted graph tables;
- mock mode remains the default for tests and operator automation;
- live network, live local models, and paid providers remain explicit opt-ins;
- no public ingestion, agent execution, or write routes;
- no raw source text, prompts, local paths, secrets, or private review notes enter
  public exports.

## Honest Starting Point

The current repo is a mock-proven research graph pipeline with experimental live
claim extraction. It is not yet a production RAG system. Live evidence proves that
source text can be chunked and sent to a model, but it also contains accepted
bibliography titles, challenge-page text, and redirect-page text. Quote presence is
therefore necessary but not sufficient for graph admission.

The order in this plan is intentional:

1. measure the failure modes;
2. reject contaminated documents and preserve scientific structure;
3. stage, semantically validate, and review candidate claims;
4. require independent evidence and honest graph metrics;
5. prove the arbitrary-source path on reviewed open-access material;
6. add retrieval and cited answering;
7. drive improvement tickets from benchmark regressions and measured gains.

Retrieval work must not start before claim-admission and graph-integrity gates are in
place. Efficient retrieval over unreliable claims would make the product faster, not
more correct.

## Execution Rules for Scheduled Agents

- Resolve the existing `ticket-411` push checkpoint before opening a Phase 4 branch.
- Execute only the first `ready` Phase 4 ticket. Later tickets are `blocked` by their
  immediate predecessor. The ticket-414 readiness audit inserted corrective ticket-429
  between tickets 413 and 414 after Windows CRLF checkout exposed a checksum-portability
  regression; ticket-414 stays blocked until ticket-429 records a follow-up GO audit.
- Create one branch per ticket, using `phase-4/ticket-<id>-<slug>`.
- A completed ticket must update its immediate successor from `blocked` to `ready` in
  both the ticket JSON and queue. Do not activate multiple successors.
- Medium- and high-risk tickets require the pre-ticket audit required by the existing
  principal-audit gate.
- Every ticket ends with its scoped tests, mock-only golden tests, relevant safety
  audit, and an agent report. Full `verify` is required when migrations, accepted graph
  writes, synthesis, or public-export behavior are touched.
- Live proof artifacts are gitignored and review-gated. A scheduled agent may build
  the harness in mock mode, but must not claim a live quality gate passed without the
  required reviewed artifact.
- `ticket-412` remains proposed. Phase 4 ticket 413 is marked `ready` because research
  correctness is a higher product-risk priority than additional launcher coverage.
  This is an explicit queue reprioritization, not a silent reorder.

## Program Gates and Tickets

### Gate A: Measurable claim quality

#### ticket-413 — Research-quality benchmark contract and baseline evaluator

Create a domain-neutral, deterministic benchmark with positive research claims and
negative examples covering references, navigation, access challenges, redirects,
methods presented as findings, background citations, unsupported generalizations,
and quote/claim mismatches. Record precision, recall, F1, false-acceptance rate, and
reason-code confusion counts. This ticket measures the baseline; it does not weaken
tests to make the baseline look good.

#### ticket-429 — Research-quality fixture checksum newline portability

Normalize fixture text newlines before checksum, boundary, and quote validation so the
ticket-413 benchmark is identical under LF, CRLF, and CR checkout policies. Preserve
fail-closed detection of substantive content changes. A second focused pre-ticket-414
audit must be GO before ticket-414 is reactivated.

#### ticket-414 — Source-artifact contamination and eligibility gate

Quarantine bot challenges, redirects, error pages, navigation shells, and insufficient
content before claim extraction. Persist deterministic eligibility reason codes.

#### ticket-415 — Section-aware scientific document segmentation

Preserve section title/type, page when available, and exact source offsets. Reference,
acknowledgement, navigation, and boilerplate chunks are not extraction-eligible by
default. Abstract, methods, results, discussion, and limitations remain distinguishable.

#### ticket-416 — Domain-neutral structured research claim schema

Represent claim kind, study design, population/sample, intervention or exposure,
outcome, direction, statistical context, limitations, and section provenance without
hardcoding creativity fields. Requiredness is conditional on claim/evidence type.

### Gate B: Safe graph admission

#### ticket-417 — Candidate claim lifecycle and quarantine state

Introduce explicit proposed, needs-review, rejected, and accepted transitions with an
append-only decision record. Only accepted claims can feed concept, relationship,
score, report, synthesis, retrieval, or public-export consumers.

#### ticket-418 — Semantic entailment and scientific-claim validator

Add a second-pass validator that checks whether the structured claim is entailed by
the quote plus bounded context and whether it is the source authors' finding rather
than a citation, title, method, or speculation. Default tests use deterministic mocks;
live local review remains opt-in. Uncertainty routes to `needs_review`, never accepted.

#### ticket-419 — Private human claim-review CLI and audit history

Give operators a private CLI to inspect context and explicitly accept or reject staged
claims with reason codes. There are no public review or write routes.

#### ticket-420 — Cross-source deduplication and corroboration

Normalize equivalent propositions, distinguish independent source families, and
prevent duplicate pages or versions of one study from inflating support. Relationship
and score consumers use accepted, independent evidence only.

#### ticket-421 — Evidence-derived graph completeness and product verdict

Remove hard-coded canonical relationship completion from product-quality metrics.
Separate fixture completeness from research completeness. A research `GO` requires
accepted claims, independent evidence, traceable relationships, and no unresolved
critical review queue.

### Gate C: Arbitrary-source research proof

#### ticket-422 — Reviewed open-access arbitrary-source quality proof

Run the quality-gated pipeline on a small, licensed open-access corpus using temp or
gitignored storage. Produce a human-reviewed artifact that reports document eligibility,
claim precision/recall, false acceptances, review decisions, corroboration, and graph
counts. This is review-gated and cannot be replaced by mock fixtures.

Gate C exits only when all of the following hold on the reviewed proof corpus:

- contaminated-source false admission count: `0`;
- accepted-claim precision: at least `0.90`;
- accepted-claim recall: at least `0.75`;
- false-acceptance rate: at most `0.05`;
- every accepted claim has source, section, quote, offsets, and decision provenance;
- bibliography, challenge, redirect, and navigation examples produce zero accepted
  claims;
- the artifact records corpus licenses, checksums, model/runtime identity, and reviewer
  decision counts.

The artifact must report `PARTIAL` or `NO-GO` when thresholds are missed. Small-corpus
metrics must include raw numerators and denominators; they must not be presented as a
general scientific performance claim.

### Gate D: Operational RAG

#### ticket-423 — Query-to-evidence packet contract with lexical and graph retrieval

Add a private query path that searches accepted claims and graph evidence, filters by
research contract/domain/scope, and returns a bounded evidence packet with stable
citations. SQLite FTS5 or an equivalent local lexical index is the deterministic base.

#### ticket-424 — Local embedding index and hybrid retrieval ranker

Add a pluggable local-first embedding adapter, versioned embedding records, incremental
reindexing, and deterministic hybrid fusion across lexical, semantic, and graph signals.
Tests use a deterministic mock embedding provider; no external model download is part
of default verification.

#### ticket-425 — Citation-required answer generation and grounding governor

Generate candidate answers only from retrieved packets. Every factual sentence must
resolve to packet claim/evidence identifiers; unsupported sentences fail closed. Model
output remains a candidate artifact and never writes accepted graph data.

#### ticket-426 — RAG retrieval and answer-quality benchmark

Create a question set and evaluator for recall@k, MRR or nDCG, citation precision,
source diversity, unsupported-sentence rate, and abstention. Gate D targets are:

- evidence recall@5: at least `0.85` on the committed benchmark;
- citation precision: at least `0.95`;
- unsupported factual sentence rate: `0`;
- required abstentions taken for unanswerable questions: `100%`;
- no rejected or needs-review claim appears in any evidence packet.

These are repository benchmark gates, not claims of performance on arbitrary domains.

### Gate E: Measured improvement loop

#### ticket-427 — Research quality evaluator v2

Replace count-based success signals with benchmark metrics, reviewed live-proof status,
corroboration, unresolved-review counts, and RAG-quality metrics. Keep legacy diagnostic
counts but prevent them from independently producing `GO`.

#### ticket-428 — Benchmark-delta improvement ticket and builder gate

Require generated improvement tickets to name a failing metric, baseline, target,
reproduction command, affected slice, and safety constraints. Builder completion must
record before/after results and may not promote a change that regresses a protected
quality or safety metric. Ticket promotion, push, merge, and publication remain governed
and are never triggered directly by model output.

Gate E exits when a deterministic seeded regression produces a correctly scoped ticket,
the bounded fix improves the targeted metric, all protected metrics remain within their
floors, and the full audit trail links run → metric failure → ticket → branch/report →
before/after result.

## Dependency Chain

```text
ticket-413 → 429 → 414 → 415 → 416 → 417 → 418 → 419 → 420 → 421 → 422
                                                                  ↓
ticket-428 ← 427 ← 426 ← 425 ← 424 ← 423 ←────────────────────────┘
```

No ticket may be skipped merely because its successor can be demonstrated with a mock
fixture. If a dependency proves unnecessary after implementation evidence, create a
small principal-audit report and explicitly supersede or rewrite the affected ticket.

## Program Definition of Done

Phase 4 is complete only when:

1. scientific documents are structurally parsed and contaminated artifacts fail closed;
2. accepted claims pass quote, structure, semantic, lifecycle, and provenance gates;
3. uncertain claims remain private review candidates and cannot reach graph consumers;
4. graph confidence reflects independent corroboration rather than duplicate documents
   or hard-coded completion;
5. a reviewed arbitrary-source artifact meets or honestly fails the stated thresholds;
6. a user question retrieves accepted evidence and produces a citation-governed answer;
7. RAG metrics pass on a committed deterministic benchmark;
8. improvement tickets are caused by measured failures and closed only with recorded
   before/after gains;
9. golden tests, full pytest, safety audit, and relevant public-site build pass in mock
   mode;
10. README and canonical maturity wording calls the system operational RAG only after
    Gates C and D pass.
