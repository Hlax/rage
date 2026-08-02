---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 4 / ticket-429 / research-quality checksum portability v0

## 1. Summary

Corrected the ticket-413 benchmark provenance gate so equivalent UTF-8 fixture text has
the same SHA-256 under LF, CRLF, and bare-CR checkout policies. Checksum, excerpt-boundary,
and quote validation now share one canonical LF-text representation. Regression tests
prove newline portability and retain fail-closed rejection of substantive changes.

## 2. Ticket

- Ticket ID: ticket-429
- Ticket title: Research-quality fixture checksum newline portability v0
- Branch: `phase-4/ticket-429-research-quality-checksum-portability-v0`
- Phase: 4
- Agent/model: Codex (GPT-5)
- Date: 2026-08-02
- Main tip before branch: `7db5bbe`
- Implementation commit: `d738855`

## 3. Scope

### In Scope

- Canonical UTF-8/LF fixture representation.
- Cross-platform SHA-256 contract declaration and validation.
- LF, CRLF, bare-CR, and substantive-change tests.
- Full mock-only verification and ticket-414 readiness re-audit.
- Queue/report bookkeeping and ticket-414 reactivation.

### Out of Scope / Non-Goals

- Ticket-414 source-artifact classification.
- Claim acceptance, database, retrieval, or public-export changes.
- Live LLM, network, or cloud actions.
- Weakening or removing checksum provenance checks.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/research_quality_benchmark.py` | Canonical newline normalization and UTF-8/LF SHA-256 helpers; one canonical validation representation |
| `fixtures/research_quality/manifest.json` | Explicit `sha256_utf8_lf_v1` checksum contract |
| `tests/unit/test_research_quality_benchmark.py` | LF/CRLF/CR equivalence and substantive-change regression coverage |
| `agent_reports/2026-08-02_pre-ticket-414_source-artifact-quality-gate-readiness-audit-2.md` | Required ticket-414 GO re-audit |
| `tickets/ticket-429.json` | Status `done` |
| `tickets/ticket-414.json` | Restored to `ready` after GO re-audit |
| `tickets/TICKET_QUEUE.md` | Corrective completion and strict-chain activation |
| `agent_reports/2026-08-02_phase-4_ticket-429_research-quality-checksum-portability-v0.md` | This report |

## 5. Implementation Notes

- `canonicalize_fixture_text` explicitly maps CRLF and bare CR to LF.
- `canonical_text_sha256` hashes the canonical string encoded as UTF-8.
- The loader reads canonical text once, then uses it for checksum, excerpt bounds, and
  quote validation, eliminating representation drift between gates.
- The manifest declares the checksum algorithm, encoding, newline rule, and versioned
  contract ID.
- Tests materialize the complete 10-document corpus under each newline style rather
  than testing only the helper in isolation.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Canonical UTF-8/LF checksum contract | PASS | Versioned manifest declaration plus shared canonical helpers |
| Equivalent LF, CRLF, and CR validate; substantive changes fail | PASS | Full-corpus parametrized tests and changed-word rejection |
| Bounds, checksum, and quote use one representation | PASS | `_validate_document` uses the canonical text for all three |
| Focused and full pytest pass after Windows checkout | PASS | 12 focused; 1393 full passed, 49 deselected |
| Follow-up ticket-414 audit is GO after all gates | PASS | Audit 2 records golden, full pytest, safety, and site pass |
| Activate only ticket-414 | PASS | Ticket 414 ready; tickets 415–428 blocked |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `.venv-ci-test\Scripts\python.exe -m pytest tests/unit/test_research_quality_benchmark.py -q` | PASS | 12 passed |
| `.venv-ci-test\Scripts\python.exe -m rge.cli verify` | PASS | Mock mode; all verification gates passed |
| Golden tests within verify | PASS | 165 passed |
| Full pytest within verify | PASS | 1393 passed, 49 deselected |
| Full safety audit within verify | PASS | No blocked reasons |
| Public-site build within verify | PASS | Static build completed |

## 8. Test Results

### Passing

- Focused benchmark tests: 12 passed.
- Golden tests: 165 passed.
- Full pytest: 1393 passed, 49 deselected.
- Safety audit: pass.
- Public-site build: pass.

### Failing

- None after the correction.

### Historical Failure Reproduced

- Pre-ticket-414 audit 1: raw-byte SHA-256 produced six benchmark failures after CRLF
  checkout. The focused diagnostic reproduced the mismatch before implementation.

## 9. Safety Audit Status

- Required: yes, through full `verify`.
- Status: pass.
- Notes: The change reads fixture text only and adds no model, network, database,
  accepted-graph, public-export, route, or secret surface.

## 10. Spec Deviations

None.

## 11. Known Risks / Gaps

- Unicode normalization is intentionally not performed; a Unicode code-point change is
  treated as substantive and changes the checksum.
- The benchmark remains synthetic and does not estimate arbitrary-domain performance.
- Ticket-414 still owns document contamination and extraction-eligibility behavior.

## 12. Rollback Plan

Revert canonical newline hashing and portability tests, return ticket-429 to `ready`,
return ticket-414 to `blocked`, and restore the NO-GO audit state. No migration or data
rollback is needed.

## 13. Recommended Next Ticket

```json
{
  "id": "ticket-414",
  "title": "Source-artifact contamination and extraction eligibility gate v0",
  "status": "ready",
  "risk_level": "medium"
}
```

## 14. Suggested Next Prompt

```txt
Implement ticket-414 on its own branch under the hardened GO audit scope. Integrate a
private deterministic pre-extraction source eligibility gate and activate only ticket-415
after full mock-only verification.
```

## Merge to Main

Merge commit: `f77f21991fc26c3d0053915a8a84581fe195de4a`.

Push status: completed to `origin/main` with a normal non-force push.
