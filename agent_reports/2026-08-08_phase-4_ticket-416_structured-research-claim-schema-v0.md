---
template_id: implementation_report
template_version: 1.0.0
status: complete
date: 2026-08-08
phase: 4
ticket: ticket-416
---

# Ticket 416 — Domain-neutral structured research claim schema v0

## Outcome

Implemented a private, explicitly versioned structured research claim contract with
deterministic conditional validation, exact chunk-provenance checks, additive persistence,
an observable legacy-fixture path, and fixed public projections. Ticket-416 is complete
locally and ticket-417 is the only newly activated Phase 4 ticket.

## Changes

- Added domain-neutral typed enums for claim kind, study design, effect direction, and
  normalized scientific section type.
- Added `StructuredResearchClaim_v0_1` nested under the existing candidate envelope.
  Every nested key is required even where `null` is allowed, preventing silent invention
  of unknown values. Existing `0.1.0` fixtures may omit the nested contract and remain
  explicitly legacy.
- Represented claim kind, study design, population/sample, intervention/exposure,
  comparator, outcome, effect direction, statistical context, limitations, and exact
  section provenance without creativity-specific core fields.
- Added deterministic structured validation with stable `invalid_structured_claim`
  rejection diagnostics. Empirical results require outcome and section provenance;
  contradictory combinations fail closed; non-empirical claims retain explicitly null
  empirical fields.
- Compared candidate chunk ID, normalized section type, original section title, page,
  and exact document offsets to persisted chunk metadata before acceptance.
- Passed structured chunk metadata through the model-candidate→Python-validator path.
  Model output remains candidate data only; Python validation still gates database writes.
- Added migration `0011_structured_research_claim` with nullable private claim columns and
  `idx_claims_kind`. Existing rows are preserved with NULL structured fields and are not
  rewritten or reclassified.
- Updated repository reads/writes and validator version `0.2.0` to serialize structured
  accepted/rejected candidates while leaving legacy inserts unchanged.
- Proved fixed public claim views, evidence cards, and atlas-safe previews do not expose
  the new private fields.
- Documented the private structured fields, explicit-null semantics, legacy behavior,
  deterministic rules, rejection code, and index in the canonical data model.

## Safety and scope

- Mock-only and network-free implementation/verification.
- No live LLM, cloud, source-network, publication, promotion, credential, or public-write
  action.
- No creativity-specific structured fields in the core contract.
- No semantic author-entailment decision, human review UI, lifecycle transition change,
  or graph-consumer isolation; those remain tickets 417–419.
- No public schema or route widening and no historical claim rewrite.

## Verification

| Command | Result |
|---|---|
| Pre-ticket claim/migration/section/public baseline | PASS — 30 passed |
| Focused structured/migration/legacy/public suite | PASS — 35 passed |
| Focused suite plus migration-order compatibility retry | PASS — 36 passed |
| Adjacent legacy/manual/staged/evidence/atlas regressions | PASS — 80 passed, 2 deselected |
| First full `verify` | Expected test-maintenance failure — 1 failed, 1441 passed, 49 deselected; golden/safety/site passed |
| Final `python -m rge.cli verify` with mock-only env | PASS |
| Golden tests within final verify | PASS — 165 passed |
| Full pytest within final verify | PASS — 1442 passed, 49 deselected |
| Full safety audit within final verify | PASS |
| Public-site build within final verify | PASS |
| `git diff --check` | PASS |

The first full gate found one historical ticket-415 test that asserted migration `0010`
was always the final migration. The test was corrected to prove ordered additive
application of `0010` followed by `0011`; the focused retry and complete final gate passed.

## Queue transition

- ticket-416: `done`
- ticket-417: `ready`
- tickets 418–428: unchanged and blocked

## Merge checkpoint

- Ticket branch: `phase-4/ticket-416-structured-research-claim-schema-v0`
- Implementation commit: `567248d`
- Merge commit on `main`: `86dd30d`
- Ordinary non-force push to `origin/main`: completed (`355db74` included)

## Next smallest ticket

Ticket-417, candidate claim lifecycle, quarantine, and graph-consumer isolation v0. It is
high risk and requires its focused pre-ticket audit before implementation; no ticket-417
implementation was started in this lifecycle.
