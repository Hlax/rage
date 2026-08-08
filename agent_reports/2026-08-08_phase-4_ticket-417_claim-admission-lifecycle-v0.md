---
template_id: implementation_report
template_version: 1.0.0
status: current
date: 2026-08-08
phase: 4
ticket: ticket-417
---

# Ticket 417 — Claim admission lifecycle and graph-consumer isolation v0

## Outcome

Implemented a private, Python-enforced claim lifecycle with append-only decision history.
Model-backed candidates now enter as `proposed`; deterministic Python admission alone can
move them to `needs_review`, `rejected`, or `accepted`. Shared graph repositories reject
new non-accepted links and filter historical stale links, while reporting, synthesis, and
atlas projections count or expose only accepted-backed graph data.

Historical accepted and rejected claims retain their status and receive no invented
backfill decisions. Ticket-417 is complete locally, and ticket-418 is the only newly
activated Phase 4 ticket.

## Changes

- Added additive migration `0012_claim_admission_lifecycle` with private append-only
  `claim_decisions` rows containing claim, prior/new state, actor, reason, validator and
  policy versions, and timestamp. Existing claim rows are untouched.
- Added explicit `proposed`, `needs_review`, `rejected`, and `accepted` lifecycle states,
  allowed-transition enforcement, terminal accepted/rejected states, deterministic
  decision IDs, private decision inspection, and idempotent repeated transitions.
- Added model-candidate insertion that persists bounded candidate fields and private quote
  provenance only as `proposed`. Admission to accepted requires Python transition code and
  a primary quote; rejection requires a stable reason.
- Preserved deterministic Python fixture/quality-gate compatibility writers while making
  them record genesis actor/reason/version provenance.
- Routed normal claim extraction and arbitrary-source abstract evidence persistence
  through proposed before Python accepted/rejected decisions. Source and purpose gates
  remain explicit Python-only terminal writers.
- Added accepted-status enforcement to new claim-concept and relationship-evidence writes,
  and accepted-only filtering to their shared source/relationship readers.
- Filtered cluster readiness, run metrics, synthesis throughput, and atlas relationship
  edges to accepted claim evidence. Private rejected/review diagnostics remain available.
- Added lifecycle, migration-preservation, rerun-idempotency, model→proposed→Python
  terminal, stale-link isolation, evidence-atom, report, synthesis, atlas, and public-card
  tests.
- Updated the schema reference and canonical data-model documentation.

## Safety and scope

- Mock-only and network-free implementation and verification.
- No live LLM, cloud, source-network, publication, promotion, credential, public-write,
  force-push, or destructive action.
- No semantic entailment reviewer or automatic uncertain-claim acceptance; ticket-418
  owns that bounded second-pass contract.
- No human review UI and no public lifecycle or decision-history projection.
- No historical claim reclassification, decision backfill, or deletion.
- No creativity-specific lifecycle fields in the core schema.

## Verification

| Command | Result |
|---|---|
| Pre-ticket claim/graph/report/atlas/synthesis baseline | PASS — 42 passed |
| Focused lifecycle and consumer-isolation suite | PASS — 6 passed |
| Migration plus focused retry | PASS — 20 passed, then 9 passed after full-gate maintenance |
| Broad downstream regression suite | PASS — 71 passed before migration expectation maintenance |
| First full `verify --skip-site` | Expected test-maintenance failure — 164/165 golden and 1446 passed/2 failed full; safety passed |
| Second full `verify --skip-site` | Golden PASS — 165; safety PASS; full pytest 1447 passed/1 transient atlas fixture mismatch |
| Exact transient atlas test retry | PASS — 1 passed |
| Complete atlas snapshot builder file | PASS — 7 passed |
| Final full pytest confirmation | PASS — 1448 passed, 49 deselected |
| Public-site production build | PASS — 13 static pages generated; export passed |
| `git diff --check` | PASS |

The first full gate found two historical migration-order assertions that ended at `0011`;
they were updated to include additive migration `0012`, and their focused retry passed.
The second full gate reported one atlas fixture mismatch that did not reproduce either as
the exact test or as the complete atlas-builder file. A complete full-pytest confirmation
then passed all 1448 selected tests. Golden, safety, and site-build gates are therefore all
green on the final code state; the transient failure is retained here rather than hidden.

## Queue transition

- ticket-417: `done`
- ticket-418: `ready`
- tickets 419–428: unchanged and blocked

## Merge checkpoint

- Ticket branch: `phase-4/ticket-417-claim-admission-lifecycle-v0`
- Implementation commit: `cf5e8be`
- Merge commit on `main`: `c35a1ae`
- Ordinary non-force push to `origin/main`: completed (`c35a1ae` included)

## Next smallest ticket

Ticket-418, semantic entailment and scientific-claim admission validator v0. It is high
risk and requires its focused pre-ticket audit before implementation; no ticket-418
implementation was started in this lifecycle.
