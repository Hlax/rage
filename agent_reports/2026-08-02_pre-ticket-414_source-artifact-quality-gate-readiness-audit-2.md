---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-08-02
phase: 4
ticket: ticket-414
---

# Pre-Ticket Audit Recheck: ticket-414 — Source-artifact contamination and extraction eligibility gate v0

**Verdict: GO with scope constraints**

## Summary and recommendation

Ticket-414 may proceed on its own branch. Corrective ticket-429 made the ticket-413
benchmark checksum contract invariant across LF, CRLF, and bare-CR checkout policies,
while retaining fail-closed detection of substantive content changes. The focused suite
and complete mock-only verification now pass on the Windows CRLF checkout.

This GO applies only to the ticket-414 source-artifact eligibility scope. It does not
authorize semantic claim entailment, destructive quarantine cleanup, live source/model
actions, public diagnostics, or broad ingestion refactors.

## Checkpoint status

| Field | Result |
|---|---|
| Previous audit | `2026-08-02_pre-ticket-414_source-artifact-quality-gate-readiness-audit-1.md` — NO-GO |
| Corrective ticket | ticket-429 — completed |
| Ticket risk | `medium` |
| Corrective branch | `phase-4/ticket-429-research-quality-checksum-portability-v0` |
| Recheck verdict | **GO with scope constraints** |
| Ticket-414 queue status | `ready` |

## Verification evidence

| Command | Result | Evidence |
|---|---|---|
| `.venv-ci-test\Scripts\python.exe -m pytest tests/unit/test_research_quality_benchmark.py -q` | PASS | 12 passed, including LF/CRLF/CR equivalence and substantive-change rejection |
| `.venv-ci-test\Scripts\python.exe -m rge.cli verify` | PASS | All four verify gates passed in mock mode |
| Golden tests | PASS | 165 passed |
| Full pytest | PASS | 1393 passed, 49 deselected |
| Full safety audit | PASS | No blocked reasons |
| Public-site build | PASS | Static build completed |

## Corrective evidence

- Manifest declares checksum contract `sha256_utf8_lf_v1`.
- Fixture text is decoded as UTF-8 and CRLF/bare CR are normalized to LF before hashing.
- Excerpt bounds and quote checks use the same canonical text representation.
- The unchanged manifest validates all three newline styles.
- A one-word substantive change still raises `BenchmarkContractError` for checksum
  mismatch.

## Hardened ticket-414 scope

- Add a deterministic pre-extraction gate returning `eligible`, `quarantined`, or
  `needs_review`, with stable reason codes and a gate version.
- Use domain-neutral content and metadata signals. Do not encode creativity-specific
  keywords.
- Ensure known challenge, redirect, navigation, error, empty, and insufficient-content
  documents produce zero extraction-eligible chunks and zero accepted claims.
- Preserve legitimate short abstracts and existing deterministic fixture/manual-source
  behavior.
- Persist private eligibility diagnostics without deleting existing source or evidence
  history.
- Extend benchmark output with source-artifact false-admission counts separate from
  claim-level false acceptance.
- Activate only ticket-415 after all ticket-414 checks pass.

## Safety constraints

- Mock-only tests and operator verification.
- No live LLM, network, cloud, or paid provider use.
- No public ingestion, review, agent-execution, or write routes.
- No quarantined content or diagnostics in public exports.
- No direct model writes to accepted graph tables.
- No deletion of historical source files or database rows.

## Final recommendation

**GO** for ticket-414 within the hardened scope above. Stop and re-audit if the
implementation requires a schema migration beyond stable private eligibility fields,
changes accepted-graph admission semantics outside source eligibility, or introduces a
new public or live execution surface.
