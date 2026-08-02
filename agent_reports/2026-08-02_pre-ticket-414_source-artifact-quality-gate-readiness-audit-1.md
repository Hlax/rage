---
template_id: pre_ticket_audit
template_version: 1.0.0
status: current
date: 2026-08-02
phase: 4
ticket: ticket-414
---

# Pre-Ticket Audit: ticket-414 — Source-artifact contamination and extraction eligibility gate v0

**Verdict: NO-GO**

## Summary and recommendation

Do not begin ticket-414. The repository was clean and synchronized at audit start, and
the ticket's source-quality scope is appropriate, but the required full verification
reproduced a cross-platform defect in its ticket-413 benchmark dependency. Six benchmark
tests fail after Git checks the fixture text out with CRLF on Windows because the manifest
contains canonical LF-text checksums while the loader hashes raw working-tree bytes.

Create and complete the smallest corrective ticket, ticket-429, then rerun this focused
readiness audit. Ticket-414 may become `ready` only after a second audit records GO.

## Checkpoint status

| Field | Result |
|---|---|
| Operator action at start | `complete_pre_ticket_audit` |
| Gate | `review_gated` |
| Ticket risk | `medium` |
| Repository state at start | Clean `main`, synchronized with `origin/main` |
| Audit verdict | **NO-GO** |
| Implementation started | No |
| Required corrective ticket | ticket-429 |

The pre-ticket gate was correctly honored. This report does not authorize ticket-414
implementation; the queue keeps 414 blocked until the corrective proof and audit recheck.

## Verification evidence

| Command | Result | Evidence |
|---|---|---|
| `python -m rge.modules.operator_loop --mode plan` | PASS | Recommended review-gated pre-ticket audit for medium-risk ticket-414 |
| `.venv-ci-test\Scripts\python.exe -m rge.cli verify` | **FAIL** | Golden 165 passed; full pytest 6 failed, 1383 passed, 49 deselected; safety pass; static site build pass |
| `.venv-ci-test\Scripts\python.exe -m pytest tests/unit/test_research_quality_benchmark.py -q -x -vv` | **FAIL** | First failure is `BenchmarkContractError` for raw-byte checksum mismatch on `clinical_trial.txt` |
| Canonical-text SHA-256 diagnostic | PASS | `read_text(encoding="utf-8")` normalized CRLF and reproduced manifest checksum `de7d32e...`; canonical length 401 |
| `.venv-ci-test\Scripts\python.exe -m pytest --collect-only -q` | PASS | 1389/1438 collected, 49 deselected; zero `tests/smoke` collection lines |

## Root cause

`research_quality_benchmark._sha256` uses `Path.read_bytes()`. The ticket-413 manifest
was generated from LF fixture bytes. On this Windows checkout, Git materialized equivalent
text with CRLF, producing a different raw-byte digest (`9867dbd3...`) even though Python's
canonical text read reproduces the intended LF digest (`de7d32e...`). Excerpt lengths and
quote checks already operate on normalized text, so checksum validation is inconsistent
with the rest of the corpus contract.

## Hardened corrective scope

- Add an explicit canonical-text function: UTF-8 decode and normalize `CRLF` and bare
  `CR` to `LF` before hashing, boundary validation, and quote lookup.
- Document the canonical checksum representation in the manifest.
- Test equivalent LF, CRLF, and CR fixtures against one checksum.
- Preserve failure on any substantive character change.
- Rerun focused benchmark tests and full mock-only `verify`.
- Write a second `pre-ticket-414` audit with GO evidence before reactivating ticket-414.

## Ticket-414 scope after correction

- Deterministic pre-extraction classification: `eligible`, `quarantined`, or
  `needs_review` with stable reason codes and a gate version.
- Persist private eligibility diagnostics without deleting historical source records.
- Ensure challenge, redirect, navigation, error, empty, and insufficient-content slices
  produce no extraction-eligible chunks or accepted claims.
- Keep valid short abstracts and existing fixture/manual ingestion deterministic.
- Report source-artifact false admissions separately from claim-level false acceptance.

## Safety boundaries

| Boundary | Assessment |
|---|---|
| Live model/network/cloud | Not authorized and not used |
| Database migration | Not part of corrective ticket-429; ticket-414 must audit any persistence change explicitly |
| Accepted graph writes | No benchmark candidate may write accepted tables |
| Public surface | No public ingestion, review, agent, or write route; diagnostics remain private |
| Destructive cleanup | Prohibited; quarantined/historical records are preserved |
| Mock defaults | Required for all automated verification |

## Queue action

- ticket-414: `ready` → `blocked`.
- ticket-429: created as the sole `ready` corrective ticket.
- tickets 415–428: remain `blocked`.
- ticket authorization budget: unchanged because no ticket implementation was started.
