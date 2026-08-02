---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 4 / ticket-413 / research-quality benchmark baseline v0

## 1. Summary

Added a versioned, domain-neutral research-quality benchmark that measures whether
candidate claims are legitimate scoped findings instead of merely quote-bearing text.
The committed corpus contains 40 annotated decisions across 10 checksum-pinned,
synthetic multidisciplinary documents. A deterministic quote-presence baseline emits
raw metric counts, per-slice counts, reason-code confusion, and an honest `PARTIAL`
verdict without using a model, network, database write, or public export.

## 2. Ticket

- Ticket ID: ticket-413
- Ticket title: Research-quality benchmark contract and baseline evaluator v0
- Branch: `phase-4/ticket-413-research-quality-benchmark-baseline-v0`
- Phase: 4
- Agent/model: Codex (GPT-5)
- Date: 2026-08-02
- Main tip before branch: `296c6e3`

## 3. Scope

### In Scope

- Versioned benchmark manifest and provenance validation.
- Ten synthetic, checksum-pinned document fixtures.
- Forty annotated positive and negative candidate decisions.
- Deterministic binary and reason-code evaluation.
- Honest quote-presence baseline artifact output.
- Focused tests, golden tests, safety audit, report, and successor activation.

### Out of Scope / Non-Goals

- Claim acceptance behavior changes.
- Source contamination gating or section parsing.
- Live LLM, source network, or cloud-provider calls.
- Database migrations or accepted-graph writes.
- Retrieval, answer generation, or public export changes.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/research_quality_benchmark.py` | Read-only manifest validation, quote-presence baseline, raw metrics, per-slice counts, reason confusion, thresholds, and CLI JSON artifact |
| `fixtures/research_quality/manifest.json` | Versioned 10-document / 40-decision benchmark contract and annotations |
| `fixtures/research_quality/documents/*.txt` | Ten synthetic multidisciplinary positive and negative fixture documents |
| `tests/unit/test_research_quality_benchmark.py` | Contract, metric, failure-reproduction, provenance, read-only, predictor, and CLI tests |
| `tickets/ticket-413.json` | Status `done` |
| `tickets/ticket-414.json` | Immediate successor promoted from `blocked` to `ready` |
| `tickets/TICKET_QUEUE.md` | Ticket 413 completion, ticket 414 activation, and queue evidence |
| `agent_reports/2026-08-02_phase-4_ticket-413_research-quality-benchmark-baseline-v0.md` | This report |

## 5. Implementation Notes

- The manifest is domain-neutral: fixture topics span clinical, education, ecology,
  materials, attention, and river-model research, with no domain-pack-specific fields.
- Every document is synthetic, carries a synthetic identifier and license marker, and
  is protected by SHA-256 plus exact character boundaries. The loader also requires
  license and canonical source metadata for any future non-synthetic fixture.
- Required negative slices cover bibliography/reference text, navigation, access
  challenges, redirect shells, methods presented as findings, cited background,
  unsupported generalization, and quote/claim mismatch.
- Each metric reports `value`, `numerator`, and `denominator`. Per-slice output preserves
  the complete confusion counts, and reason-code confusion is deterministic.
- The baseline accepts any well-formed candidate with a present quote. This deliberately
  reproduces the current weakness instead of encoding expected labels into predictions.
- The evaluator reads fixture files only. It imports no model, network, database,
  repository, or public-export writer.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| At least 40 annotated decisions across at least 10 documents | PASS | Exactly 40 decisions across 10 synthetic fixtures; all raw counts reported |
| Positive findings plus all required negative slices | PASS | 12 valid findings and 28 negatives across all eight required failure slices |
| Synthetic or redistribution-compatible provenance | PASS | All fixtures synthetic; every document has identifier, license marker, checksum, and boundaries; non-synthetic validation is fail-closed |
| Precision, recall, F1, false-acceptance, slices, and reason confusion | PASS | Deterministic JSON artifact reports every requested metric and confusion view |
| Honest failing baseline | PASS | `PARTIAL`; precision 0.30, recall 1.00, F1 0.461538, false-acceptance rate 1.00 |
| No production graph or public-export writes | PASS | Read-only API/CLI; tests prohibit `Path` writes and runtime evidence reports zero model/network/DB/export calls |
| Activate only ticket-414 | PASS | Ticket 414 is `ready`; tickets 415–428 remain `blocked` |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m rge.modules.research_quality_benchmark --compact` | PASS | Completed deterministic baseline artifact; intentionally `PARTIAL` |
| `python -m py_compile rge/modules/research_quality_benchmark.py tests/unit/test_research_quality_benchmark.py` | PASS | Syntax validation |
| `.venv-ci-test\Scripts\python.exe -m pytest tests/unit/test_research_quality_benchmark.py -q` | PASS | 8 passed |
| `.venv-ci-test\Scripts\python.exe -m pytest tests/golden -q` | PASS | 165 passed |
| `python -m rge.modules.safety_auditor --audit full` | PASS | No blocked reasons |
| `git diff --check` | PASS | No whitespace errors |

## 8. Test Results

### Passing

- Focused benchmark suite: 8 passed.
- Golden suite: 165 passed.
- Full safety audit: pass.
- Baseline corpus contract: 10 documents, 40 candidates, 9 slices.
- Baseline counts: 12 true positives, 28 false positives, 0 false negatives,
  0 true negatives.

### Intentionally Failing Quality Metrics

- Precision: 0.30 (12/40), below 0.90 target.
- False-acceptance rate: 1.00 (28/28), above 0.05 target.
- Overall benchmark verdict: `PARTIAL`; this is expected evidence, not a test failure.

### Failing Commands

- None. The initially selected bundled Python did not include pytest; verification used
  the repository's existing `.venv-ci-test` environment without installing packages.

### Not Run

- Full pytest/`verify`: not required because this ticket adds a read-only benchmark and
  touches no migration, accepted graph write, synthesis behavior, or public export.
- Public-site build: not relevant to this private read-only benchmark.

## 9. Safety Audit Status

- Required: yes.
- Status: pass.
- Notes: No public write, ingestion, agent-execution, export, route, secret, model, or
  network surface was added. Candidate text never reaches production tables.

## 10. Spec Deviations

None.

## 11. Known Risks / Gaps

- The compact synthetic corpus is a repository regression benchmark, not an estimate of
  arbitrary-domain or live scientific performance.
- The quote-presence baseline intentionally has no source-artifact or semantic awareness.
- Ticket 414 adds the first contamination/eligibility gate; later tickets add structured
  provenance, semantic entailment, review lifecycle, and corroboration.

## 12. Rollback Plan

Remove the benchmark module, fixtures, and focused tests; restore ticket 413 to `ready`
and ticket 414 to `blocked`. No data migration or production record rollback is needed.

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
Implement ticket-414 on its own branch. Use the ticket-413 benchmark to add a
deterministic pre-extraction source-artifact gate, keep all tests mock-only, and activate
only ticket-415 after verification.
```

## Merge to Main

Merge commit: pending.

Push status: pending.
