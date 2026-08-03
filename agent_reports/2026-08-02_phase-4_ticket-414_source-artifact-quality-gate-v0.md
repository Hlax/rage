---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 4 / ticket-414 / source-artifact quality gate v0

## 1. Summary

Implemented a deterministic, domain-neutral source eligibility gate before extraction.
The gate classifies source text as `eligible`, `quarantined`, or `needs_review`, persists
private versioned diagnostics in source metadata, prevents quarantined content from
creating extraction-eligible chunks, and blocks quarantined sources even when a pinned
mock claim fixture is supplied.

The research-quality benchmark now contains explicit source-artifact annotations for
access challenges, navigation and redirect shells, error pages, empty content, and
insufficient content. It reports source false admissions separately from claim-level
false acceptance. The committed corpus records zero false admissions across six blocked
source artifacts.

## 2. Ticket

- Ticket ID: ticket-414
- Ticket title: Source-artifact contamination and extraction eligibility gate v0
- Branch: `phase-4/ticket-414-source-artifact-quality-gate-v0`
- Phase: 4
- Agent/model: Codex (GPT-5)
- Date: 2026-08-02
- Main tip before branch: `9172b37`

## 3. Scope

### In Scope

- Deterministic source-level eligibility statuses, reason codes, and gate version.
- Private persistence through `sources.domain_metadata_json` without a migration.
- Parser, local/staged ingest, and claim-extraction enforcement.
- Source-only benchmark slices and separate false-admission metrics.
- Mock-only tests for contamination, short legitimate content, persistence, and accepted
  claim isolation.
- Ticket-415 activation after complete verification.

### Out of Scope / Non-Goals

- Semantic claim entailment or structured scientific claim fields.
- Section-aware segmentation, which remains ticket-415.
- Destructive cleanup of historical source, chunk, or claim rows.
- Live LLM, network, cloud, publication, or public-route changes.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/source_quality_gate.py` | Versioned domain-neutral source eligibility classifier and metadata loader |
| `rge/modules/document_parser.py` | Parser results expose eligibility status, reasons, version, and extraction readiness |
| `rge/db/repositories.py` | Local ingest persists private eligibility diagnostics and omits chunks for quarantined sources |
| `rge/modules/fetcher.py` | Staged ingest supplies a validated-artifact metadata signal after existing checksum/usability checks |
| `rge/modules/text_quality_gate.py` | Extraction gate enforces persisted or recomputed source eligibility |
| `rge/modules/claim_extractor.py` | Quarantined sources fail closed under mock/live paths; review-only text remains blocked outside deterministic mock fixtures |
| `rge/modules/research_quality_benchmark.py` | Source-artifact contract validation and separate false-admission metrics |
| `fixtures/research_quality/manifest.json` | Benchmark v1.1 source-artifact annotations and required slices |
| `fixtures/research_quality/documents/{error_page,empty_content,insufficient_content}.txt` | Additional synthetic source-only contamination fixtures |
| `tests/unit/test_source_quality_gate.py` | Classification, precedence, persistence, zero-chunk, and zero-accepted-claim coverage |
| `tests/unit/test_document_parser.py` | Parser quarantine and short-content review coverage |
| `tests/unit/test_research_quality_benchmark.py` | Manifest v1.1 and source false-admission metric coverage |
| `tickets/ticket-414.json` | Status `done` |
| `tickets/ticket-415.json` | Status `ready` after verification |
| `tickets/TICKET_QUEUE.md` | Strict dependency-chain transition and completion evidence |

## 5. Implementation Notes

- Gate version: `source_eligibility_v0.1.0`.
- Stable blocking reasons: `access_challenge`, `redirect_shell`, `error_page`,
  `navigation_shell`, `empty_content`, and `insufficient_content`.
- Decisions store bounded counts only; source text, paths, prompts, and secrets are not
  copied into the eligibility payload.
- Strong contamination checks run before any validated-artifact or source-type signal,
  so metadata cannot override an access challenge or shell.
- Legitimate short content is distinguishable as `needs_review`. Existing checksum-pinned
  mock staged fixtures retain deterministic behavior, while non-mock needs-review sources
  remain blocked.
- No database migration was needed because source diagnostics are private, versioned
  metadata in the existing `domain_metadata_json` field.
- The ticket named a prospective `source_ingestor.py`; the repository's actual local
  ingest implementation is `ingest_local_source` in `rge/db/repositories.py`, so the gate
  was integrated there instead of adding a duplicate ingestion module.

## 6. Acceptance Criteria Status

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| Three deterministic statuses plus stable reasons/version | PASS | Classifier constants, frozen decision object, metadata round-trip tests |
| Challenge/redirect/navigation/error/empty/insufficient sources yield zero eligible chunks and accepted claims | PASS | Six fixture classes tested through ingest and pinned mock extraction |
| Domain-neutral signals; legitimate short abstracts distinguished | PASS | Generic text/HTTP/navigation metadata only; `needs_review` short-abstract test |
| Quarantine diagnostics remain private | PASS | Existing private source metadata only; safety audit and public build pass |
| Fixture/manual ingest remains deterministic | PASS | Adjacent manual, staged, webpage, and full golden suites pass |
| Benchmark separates source false admission from claim false acceptance | PASS | `source_artifact_admission`; 0/6 false admissions |
| Activate only ticket-415 | PASS | Ticket-415 ready; tickets 416–428 blocked |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `.venv-ci-test\Scripts\python.exe -m pytest tests/unit/test_source_quality_gate.py tests/unit/test_document_parser.py tests/unit/test_research_quality_benchmark.py -q` | PASS | Initial focused run: 42 passed |
| Adjacent manual/staged/web extraction suite | PASS | 78 passed after short scholarly-source refinement |
| Reproduced golden plus staged-cluster suite | PASS | 47 passed after needs-review mock-fixture correction |
| Final rank-2/staged/focused suite | PASS | 58 passed after validated-artifact metadata integration |
| `.venv-ci-test\Scripts\python.exe -m rge.cli verify` | PASS | Final complete mock-only verification |
| Golden tests within verify | PASS | 165 passed |
| Full pytest within verify | PASS | 1418 passed, 49 deselected |
| Full safety audit within verify | PASS | No blocked reasons |
| Public-site build within verify | PASS | Static build completed |

## 8. Verification History

Two deterministic local regressions were found and corrected before completion:

1. The first full run failed 64 tests because short checksum-pinned staged fixtures were
   classified too conservatively. Quarantined content remains hard-blocked; review-only
   content now retains stored chunks and may proceed only in deterministic mock-fixture
   mode.
2. The second full run passed golden, safety, and site gates but failed one mocked rank-2
   fallthrough test. Staged ingest now supplies a bounded `artifact_validated` signal
   only after its existing checksum/usability checks. Tests prove this signal cannot
   override contamination.

The final full run passed all required gates.

## 9. Safety Audit Status

- Required: yes, through full `verify`.
- Status: pass.
- Model/network mode: mock-only; no live LLM, network, or cloud action was run.
- Public surface: unchanged. Eligibility diagnostics remain in private source metadata.
- Accepted-graph boundary: quarantined sources cannot create accepted claims.
- Destructive behavior: none; historical rows and files are preserved.

## 10. Spec Deviations

None. The repository does not contain the prospective `source_ingestor.py` named by the
ticket, so integration used the existing repository-layer ingestion function without
creating a competing module.

## 11. Known Risks / Gaps

- Heuristics are intentionally conservative and synthetic-fixture proven; arbitrary-live
  performance remains a later reviewed milestone.
- `needs_review` is a private stop state outside checksum-pinned deterministic mock
  fixtures; no review UI is added here.
- Section-level references, acknowledgements, and boilerplate are ticket-415 scope.
- Historical sources are re-evaluated when extraction is attempted, but historical
  chunks are not deleted.

## 12. Rollback Plan

Revert the source gate, parser/repository/extractor integration, benchmark v1.1 fields,
and tests. Existing `domain_metadata_json` remains readable; no schema or data migration
rollback is required. Preserve historical rows and fixture evidence.

## 13. Recommended Next Ticket

```json
{
  "id": "ticket-415",
  "title": "Section-aware scientific document segmentation and provenance v0",
  "status": "ready",
  "risk_level": "medium"
}
```

## 14. Suggested Next Prompt

```txt
Run the focused pre-ticket-415 audit, then implement section-aware scientific document
segmentation and exact provenance on its own branch if the audit is GO. Activate only
ticket-416 after full mock-only verification.
```

## Merge to Main

Merge commit: pending.

Push status: pending.
