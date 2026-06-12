---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-017 Audit: Theory Generator Readiness

- Audit type: pre-implementation readiness audit (no ticket-017 code changes)
- Date: 2026-06-12
- Agent/model: Cursor principal audit agent (Auto)
- Scope: Git/main state after ticket-016, executable spine through cluster report generation, cluster report safety/format, theory-generator prerequisites for Golden Test 15, runner audit-gate review

## 1. Summary

The repo is **ready for ticket-017 (mock theory generator / Golden Test 15)** with hardening requirements folded into the ticket itself. Main is clean and aligned with `origin/main` at `6918345`. ticket-016 is merged and pushed (`a72ea7b`). All **69** golden tests pass without Ollama; public site static build succeeds (11 prerendered routes).

The full spine through **ingest → extract-claims → link-concepts → build-relationships → detect-contradictions → reconcile-scores → generate-cluster-report → export-public** runs successfully on a fresh temp DB. Cluster reports are deterministic, persisted to `cluster_reports`, and written to `cluster_report_latest.json` with balanced supporting and qualifying claim IDs. Report artifacts contain no raw source text, prompts, secrets, or private paths.

What ticket-017 still lacks (expected — not yet implemented) is the theory module, CLI command, `theory_candidates` migration/repository, mock theory fixture, validation layer, and Golden Test 15. `theory_generator.py` remains a Phase 0 stub raising `NotImplementedError`.

**Contract decisions ticket-017 must make explicit:**

1. Add migration `0005_theory_candidates.sql` per `05_DATA_MODEL.md` §4.22 (table absent from current migrations and `schema.sql`).
2. Input contract: load latest cluster report for domain (or `--cluster-report-id`), pass `evidence_packet` + linked claim IDs to mock inference; Python validates all referenced claim IDs exist in the packet before persistence.
3. Golden Test 15’s example graph path (`variation volume`, `selection burden`, `taste`) is **not** present in the current creativity fixture cluster. Use a deterministic mock fixture (`fixtures/llm_outputs/theory_generation_creativity_diversity.json`) referencing **actual** claim IDs from the golden cluster evidence packet; do not invent unsupported claims at validation time.
4. Persist theories with `status: candidate` only; never write to accepted graph tables or public card export in this ticket.
5. Required output fields per `08_REPORTING_SPEC.md` §13: `report_type`, `type`, `graph_pattern`, `theory_text`, `confidence`, supporting/contradicting-or-qualifying claim IDs, `boundary_conditions`, `weakening_evidence` (or explicit none-found rationale tied to packet), `next_questions`, `status`.
6. Optional internal artifact: `data/reports/theory_candidate_latest.json` (not public export).

Recommendation: **proceed with ticket-017 as the next smallest safe ticket**, hardened per above. No separate pre-hardening ticket required.

Runner command patched to add an explicit audit-gate row for theory/inference generation milestones.

## 2. Git / Main Status

| Check | Result | Evidence |
|---|---|---|
| Current branch | `main` | `git branch --show-current` |
| Working tree clean | PASS | `nothing to commit, working tree clean` |
| `main` up to date with `origin/main` | PASS | both at `691834535b02d71bfa5bccea937dbfc3dd7d7494` |
| ticket-016 merged to `main` | PASS | merge commit `a72ea7b55fa97a6a84db038e0caa9c60b5f07722` |
| ticket-016 implementation reachable | PASS | `f36e2b3` contained in `main` |
| ticket-016 doc follow-up on remote | PASS | `6918345` on `origin/main` |
| Force-push / branch drift signs | NONE OBSERVED | linear merge history; no diverged remote |

Recent linear history:

```txt
6918345 docs: record main merge hash for ticket-016
a72ea7b Merge branch 'phase-1/ticket-016-cluster-report'
f36e2b3 Implement ticket-016 cluster report threshold trigger for Golden Test 13.
4e3ab50 docs: record main merge hash for ticket-015
5125d27 Merge branch 'phase-1/ticket-015-public-site-detail-pages'
```

Local branch `phase-1/ticket-016-cluster-report` still exists but is fully contained in `main` (not unmerged work).

## 3. Ticket / Report Consistency

| Ticket | Queue Status | JSON Status | Report Present |
|---|---|---|---|
| ticket-011 | done | done | `agent_reports/2026-06-11_phase-1_ticket-011_mock-contradiction-detection.md` |
| ticket-012 | done | done | `agent_reports/2026-06-11_phase-1_ticket-012_mock-research-queue.md` |
| ticket-013 | done | done | `agent_reports/2026-06-11_phase-1_ticket-013_research-contract-drift.md` |
| ticket-014 | done | done | `agent_reports/2026-06-11_phase-1_ticket-014_public-card-export.md` |
| ticket-015 | done | done | `agent_reports/2026-06-12_phase-1_ticket-015_public-site-detail-pages.md` |
| ticket-016 | done | done | `agent_reports/2026-06-12_phase-1_ticket-016_cluster-report.md` |
| ticket-017 | proposed | proposed | *(none — expected)* |

- **Next proposed ticket:** ticket-017 is correct (lowest-order `proposed` in queue).
- **Golden Test 14 gap:** Queue skips from GT13 → GT15. GT14 (balanced evidence packet) is partially exercised inside GT13 evidence-packet assertions; acceptable deferral — not a blocker for ticket-017.
- **ticket-016 audit gate:** Satisfied via `agent_reports/2026-06-12_pre-ticket-016_cluster-report-readiness-audit.md` (medium-risk ticket + schema migration).

## 4. Runner Behavior Findings

| Finding | Status |
|---|---|
| One ticket per invocation | PASS — §13 explicitly stops after merge/push |
| Audit gate for medium/high risk | PASS — §3.5 requires pre-ticket audit |
| Audit gate for theory generation | **PATCHED** — added explicit milestone row for theory/inference generation |
| ticket-017 would have been blocked without this audit | YES — `risk_level: medium` and no prior `pre-ticket-017` report |

Patch applied: `.cursor/commands/rge-run-next-ticket.md` §3.5 — new row **Theory / inference generation**.

## 5. Tests / Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden` | PASS | 69 passed in 11.01s |
| `python -m pytest` | PASS | 69 passed in 11.08s |
| `cd apps/public-site && npm run build` | PASS | 11 static routes |
| Ollama required | NO | `RGE_LLM_MODE=mock` throughout |

Golden test coverage for intelligence layer:

| Stage | Golden test file | Tests |
|---|---|---|
| contradiction detection | `test_07_contradiction_detection.py` | 3 |
| score reconciliation | `test_08_score_reconciliation.py` | 4 |
| cluster report | `test_13_cluster_report.py` | 4 |
| theory generator | *(none yet)* | ticket-017 scope |

## 6. Fresh DB Spine Verification

Manual audit spine run on fresh temp SQLite (`RGE_LLM_MODE=mock`):

| Step | Command | Result |
|---|---|---|
| 1 | `ingest` base fixture | PASS |
| 2 | `extract-claims` | PASS (2 accepted) |
| 3 | `link-concepts` | PASS |
| 4 | `build-relationships` | PASS (1 relationship, supports edge) |
| 5 | `ingest` + pipeline contradiction source | PASS |
| 6 | `detect-contradictions` with fixture | PASS (qualifies edge preserved) |
| 7 | `ingest` + `extract-claims` follow-up fixture | PASS |
| 8 | `reconcile-scores` | PASS (1 score event, confidence 0.5 → 0.62) |
| 9 | `generate-cluster-report` | PASS (15 claims, 3 sources, thresholds met, 1 cluster report row) |
| 10 | `export-public` | PASS (2 public-safe cards) |

Post-spine counts:

```txt
accepted_claims: 15 (11 golden padding + 4 fixture spine)
independent_sources: 3
cluster_reports: 1
score_events: 1
export cards: 2
```

Fixture flags used (same as golden tests 7/8/13):

```txt
claim_extraction_creativity_diversity_contradiction.json
concept_linking_creativity_diversity_contradiction.json
relationship_drafting_creativity_diversity_contradiction.json
contradiction_detection_creativity_diversity.json
claim_extraction_creativity_diversity_followup.json
```

## 7. Cluster Report Findings

| Check | Result | Notes |
|---|---|---|
| Threshold logic deterministic | PASS | Fixed constants in `cluster_reporter.py`; padding uses deterministic claim text rotation |
| `cluster_reports` persistence | PASS | Migration `0004`; `ClusterReportRepository.insert` |
| Report JSON written | PASS | `cluster_report_latest.json` via `--output-dir` |
| Format vs `08_REPORTING_SPEC.md` §9 | PASS | `report_type`, concepts, supporting/qualifying claims, relationships, gaps, next questions, nested `evidence_packet` |
| Evidence packet balanced | PASS (GT13) | Supporting + qualifying claims present; not support-only |
| Raw source text in report JSON | PASS | Claim IDs only; no chunk text |
| Private paths in report JSON | PASS | No `C:\` or `/home/` in report body |
| Prompts/secrets in report JSON | PASS | No prompt templates or API keys |
| Public export unchanged by cluster report | PASS | Separate command; cluster report not auto-exported |

**Observation (non-blocking):** Golden padding claims (`golden_padding: true`) inflate claim count to 15. Theory generator must treat padding claims as valid linked IDs if referenced, but should prefer spine-derived supporting/qualifying claims in mock fixture design for meaningful GT15 assertions.

**Observation (non-blocking):** CLI stdout includes `output_path` with temp directory — acceptable machine-readable CLI output; not part of persisted report JSON.

## 8. Theory-Generator Readiness

| Prerequisite | Status | Notes |
|---|---|---|
| Input contract from cluster reports | READY | `evidence_packet` + `linked_claim_ids` in cluster report JSON; DB row in `cluster_reports` |
| Fields to propose theories without inventing claims | READY WITH HARDENING | Packet has supporting/qualifying IDs, gaps, next questions; validation must reject IDs not in packet |
| Storage target | **MISSING (expected)** | `theory_candidates` in data model §4.22; no migration yet — ticket-017 must add `0005` |
| Mock fixture support | **MISSING (expected)** | No `fixtures/llm_outputs/theory_*.json` yet |
| Validation rules | **MISSING (expected)** | Stub only; follow contradiction/relationship validator patterns |
| Rejection reasons | **MISSING (expected)** | Required for invalid candidates (missing support, no caveats, IDs not in packet) |
| Public/private boundary | READY | Theories are internal candidates; ticket-017 non-goals exclude public write routes |
| Live Ollama | NOT REQUIRED | Mock mode sufficient |

**Golden Test 15 alignment gap:** Spec example uses graph path concepts (`variation volume`, `selection burden`, `taste`) absent from current creativity fixture graph. ticket-017 should **not** attempt to build that exact ontology path in this ticket. Instead:

- Use `graph_pattern: "contradiction_by_metric"` or `"boundary_condition"` grounded in existing AI assistance ↔ diversity edges.
- Mock fixture theory text may paraphrase GT15 example but **must** reference real claim IDs from the cluster evidence packet.
- `weakening_evidence` should map to qualifying/contradicting claim IDs or cite packet open gaps.

## 9. Safety Findings

| Risk | Status |
|---|---|
| Unsupported speculation stored as fact | MITIGATED BY DESIGN — `theory_candidates.status` must remain `candidate`; no accepted-graph writes |
| Model output writes directly to DB | NOT PRESENT — stub raises; ticket-017 must preserve validate-then-repository pattern |
| Raw source text leakage | PASS on cluster artifacts; ticket-017 must keep claim IDs only in theory JSON |
| Raw prompt leakage | PASS on current exports/reports |
| Local path leakage | PASS on report/export artifacts |
| Unreviewed theories as public cards | NOT PRESENT — no theory export path; ticket-017 must not add theory cards to `export-public` |
| Public export schema change | OUT OF SCOPE for ticket-017 |

## 10. Blocking Issues

**None.** Missing migration, fixture, module, and golden test are expected ticket-017 deliverables, not pre-implementation blockers.

## 11. Recommended Next Action

Proceed with **ticket-017** implementation after reading this audit. Run `/rge-run-next-ticket` or implement on branch `phase-1/ticket-017-theory-generator`.

## 12. Hardened Ticket-017 Scope

Implement only:

1. **Migration** `rge/db/migrations/0005_theory_candidates.sql` + `schema.sql` reference update.
2. **`TheoryCandidateRepository`** in `repositories.py` with insert/list/get; status always `candidate`.
3. **`theory_generator.py`**: load cluster report → mock fixture propose → Python validate → persist.
4. **CLI** `generate-theory-candidates` (or `generate-theories`): `--domain`, `--db`, optional `--cluster-report-id`, `--fixture`, `--output-dir`.
5. **Mock fixture** `fixtures/llm_outputs/theory_generation_creativity_diversity.json` referencing real golden cluster claim IDs.
6. **Validation rules** (minimum):
   - `type == candidate_theory`
   - non-empty `theory_text`
   - ≥1 supporting claim ID present in evidence packet
   - ≥1 contradicting/qualifying claim ID OR explicit boundary/weakening fields
   - all claim ID references ⊆ packet claim IDs
   - `status == candidate`
   - reject with machine-readable reasons
7. **Golden Test 15** in `tests/golden/test_15_theory_generator.py` — runs spine through cluster report, then theory generation; asserts candidate storage and caveat fields.
8. **Idempotent** re-run behavior (return existing candidate if already generated for cluster report).

Non-goals (reaffirm):

- No Ollama
- No public export / public site changes
- No theory cards in `export-public`
- No LangGraph
- No auto-promotion to facts

## 13. Runner Command Patch

Applied to `.cursor/commands/rge-run-next-ticket.md` §3.5:

```txt
| **Theory / inference generation** | First or changed theory_generator, candidate-theory CLI, theory_candidates persistence, theory report artifacts | Higher-level semantic synthesis must not present speculation as fact or bypass validation |
```

This ensures future theory/inference tickets require a pre-ticket audit even when `risk_level` is later lowered.
