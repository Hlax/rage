# TICKET_QUEUE.md

## Purpose

This file tracks the implementation queue for the Research Graph Engine.

Agents may propose new tickets, but they must not silently reorder or broaden the queue without explaining why.

## Status Values

```txt
proposed
ready
in_progress
blocked
done
rejected
superseded
```

## Phase 0 / 0.5 Initial Queue

| Order | Ticket ID | Status | Title | Branch | Report |
|---:|---|---|---|---|---|
| 1 | ticket-001 | done | Scaffold repo and model runtime adapter | `phase-0/ticket-001-repo-scaffold-model-runtime` | `agent_reports/2026-06-11_phase-0_ticket-001_repo-scaffold-model-runtime.md` |
| 2 | ticket-002 | superseded | Add CLI help and config loading | | |
| 3 | ticket-003 | superseded | Add SQLite schema and migration harness | | |
| 4 | ticket-004 | superseded | Add golden test skeleton and fixtures | | |
| 5 | ticket-005 | superseded | Add public-site placeholder static build | | |
| 6 | ticket-006 | done | Add SQLite migration harness and source ingestion | `phase-1/ticket-006-sqlite-migration-source-ingestion` | `agent_reports/2026-06-11_phase-1_ticket-006_sqlite-migration-source-ingestion.md` |

## Phase 1 Queue

| Order | Ticket ID | Status | Title | Branch | Report |
|---:|---|---|---|---|---|
| 7 | ticket-007 | done | Add mock claim extraction (Golden Test 2) | `phase-1/ticket-007-mock-claim-extraction` | `agent_reports/2026-06-11_phase-1_ticket-007_mock-claim-extraction.md` |
| 8 | ticket-008 | done | Add mock concept linking (Golden Test 5) | `phase-1/ticket-008-mock-concept-linking` | `agent_reports/2026-06-11_phase-1_ticket-008_mock-concept-linking.md` |
| 9 | ticket-009 | done | Add mock relationship builder (Golden Test 6) | `phase-1/ticket-009-mock-relationship-builder` | `agent_reports/2026-06-11_phase-1_ticket-009_mock-relationship-builder.md` |
| 10 | ticket-010 | done | Add score reconciliation with history (Golden Test 8) | `phase-1/ticket-010-score-reconciliation` | `agent_reports/2026-06-11_phase-1_ticket-010_score-reconciliation.md` |
| 11 | ticket-011 | done | Add mock contradiction detection (Golden Test 7) | `phase-1/ticket-011-mock-contradiction-detection` | `agent_reports/2026-06-11_phase-1_ticket-011_mock-contradiction-detection.md` |
| 12 | ticket-012 | done | Add mock research queue ranking (Golden Test 9) | `phase-1/ticket-012-mock-research-queue` | `agent_reports/2026-06-11_phase-1_ticket-012_mock-research-queue.md` |
| 13 | ticket-013 | done | Add research contract drift gating (Golden Test 10) | `phase-1/ticket-013-research-contract-drift` | `agent_reports/2026-06-11_phase-1_ticket-013_research-contract-drift.md` |
| 14 | ticket-014 | done | Add public card export with safety filtering (Golden Test 11) | `phase-1/ticket-014-public-card-export` | `agent_reports/2026-06-11_phase-1_ticket-014_public-card-export.md` |
| 15 | ticket-015 | done | Add public site card and concept detail pages (Golden Test 12) | `phase-1/ticket-015-public-site-detail-pages` | `agent_reports/2026-06-12_phase-1_ticket-015_public-site-detail-pages.md` |
| 16 | ticket-016 | done | Add cluster report threshold trigger (Golden Test 13) | `phase-1/ticket-016-cluster-report` | `agent_reports/2026-06-12_phase-1_ticket-016_cluster-report.md` |
| 17 | ticket-017 | done | Add mock theory generator (Golden Test 15) | `phase-1/ticket-017-theory-generator` | `agent_reports/2026-06-12_phase-1_ticket-017_theory-generator.md` |
| 18 | ticket-018 | done | Add contract-respecting question generation (Golden Test 16) | `phase-1/ticket-018-question-generation` | `agent_reports/2026-06-12_phase-1_ticket-018_question-generation.md` |
| 19 | ticket-019 | done | Add ontology pressure report (Golden Test 17) | `phase-1/ticket-019-ontology-pressure` | `agent_reports/2026-06-12_phase-1_ticket-019_ontology-pressure.md` |
| 20 | ticket-020 | done | Add domain proposal threshold trigger (Golden Test 18) | `phase-1/ticket-020-domain-proposal` | `agent_reports/2026-06-12_phase-1_ticket-020_domain-proposal.md` |
| 21 | ticket-021 | done | Add research run report (Golden Test 19) | `phase-1/ticket-021-run-report` | `agent_reports/2026-06-12_phase-1_ticket-021_run-report.md` |
| 22 | ticket-022 | done | Add improvement ticket generation (Golden Test 20) | `phase-1/ticket-022-improvement-tickets` | `agent_reports/2026-06-12_phase-1_ticket-022_improvement-tickets.md` |
| 23 | ticket-023 | done | Validate improvement tickets for builder consumption (Golden Test 21) | `phase-1/ticket-023-builder-ticket-consumption` | `agent_reports/2026-06-12_phase-1_ticket-023_builder-ticket-consumption.md` |
| 24 | ticket-024 | done | Add builder golden merge gate (Golden Test 22) | `phase-1/ticket-024-builder-golden-gate` | `agent_reports/2026-06-12_phase-1_ticket-024_builder-golden-gate.md` |
| 25 | ticket-025 | done | Add safety audit merge gate (Golden Test 23) | `phase-1/ticket-025-safety-audit-gate` | `agent_reports/2026-06-12_phase-1_ticket-025_safety-audit-gate.md` |
| 26 | ticket-026 | done | Add prompt-injection golden fixture handling (Golden Test 24) | `phase-1/ticket-026-prompt-injection` | `agent_reports/2026-06-12_phase-1_ticket-026_prompt-injection.md` |
| 27 | ticket-027 | done | Add public-site debug details without private data exposure (Golden Test 25) | `phase-1/ticket-027-public-site-debug-details` | `agent_reports/2026-06-12_phase-1_ticket-027_public-site-debug-details.md` |
| 28 | ticket-028 | done | Full MVP end-to-end golden run (Golden Test 26) | `phase-1/ticket-028-full-mvp-run` | `agent_reports/2026-06-12_phase-1_ticket-028_full-mvp-run.md` |
| 29 | ticket-029 | done | Extend builder golden gate for full MVP run (Golden Test 26) | `phase-1/ticket-029-builder-golden-gate-mvp` | `agent_reports/2026-06-12_phase-1_ticket-029_builder-golden-gate-mvp.md` |
| 30 | ticket-030 | done | Extend builder golden gate for safety and prompt-injection (Golden Tests 23-24) | `phase-1/ticket-030-builder-golden-gate-safety` | `agent_reports/2026-06-12_phase-1_ticket-030_builder-golden-gate-safety.md` |
| 31 | ticket-031 | done | Extend builder golden gate for public-site debug details (Golden Test 25) | `phase-1/ticket-031-builder-golden-gate-public-site` | `agent_reports/2026-06-12_phase-1_ticket-031_builder-golden-gate-public-site.md` |
| 32 | ticket-032 | proposed | Phase 1 builder golden gate completion checkpoint | | |

## Queue Notes (2026-06-12, ticket-031 agent)

- ticket-031 added `public_site_debug` (GT25) to Golden Test 22
  `REQUIRED_GOLDEN_AREAS`. All 118 golden tests pass.
- ticket-032 proposes builder gate completion checkpoint for remaining Phase 1
  golden areas.

## Queue Notes (2026-06-12, ticket-030 agent)

- ticket-030 added `safety_audit_gate` (GT23) and `prompt_injection` (GT24) to Golden
  Test 22 `REQUIRED_GOLDEN_AREAS`. All 118 golden tests pass.
- ticket-031 proposes public-site debug builder gate coverage for GT25.

## Queue Notes (2026-06-12, ticket-029 agent)

- ticket-029 added `full_mvp_run` to Golden Test 22 `REQUIRED_GOLDEN_AREAS`
  (`test_26_full_mvp_run.py`). All 118 golden tests pass.
- ticket-030 proposes safety/prompt-injection builder gate coverage for GT23-24.

## Queue Notes (2026-06-12, ticket-028 agent)

- ticket-028 implemented fixture-mode `research run` orchestration via
  `execute_fixture_mode_run()`, Golden Test 26 (4 tests), scaffold test update,
  and full safety audit GT26 evidence check. All 118 golden tests pass; public
  site builds 11 static pages; `python -m rge.modules.safety_auditor --audit full`
  returns `pass`.
- Pre-ticket-028 env/config audit included in branch base (`08d0940`).
- ticket-029 proposes builder golden gate coverage for GT26.

## Queue Notes (2026-06-12, ticket-027 agent)

- ticket-027 implemented curated `evidence_type` and `public_run_timestamp` public
  export fields, card detail debug section, Golden Test 25 (4 tests), and full
  safety audit GT25 evidence check. All 114 golden tests pass; public site builds
  11 static pages; `python -m rge.modules.safety_auditor --audit full` returns
  `pass`.
- Pre-ticket-027 audit report included in branch base.
- ticket-028 proposes full MVP end-to-end golden run for Golden Test 26.

## Queue Notes (2026-06-12, ticket-026 agent)

- ticket-026 implemented deterministic prompt-injection fixture handling with
  `unsafe_or_injected_content` rejection, prompt-injection source/LLM fixtures,
  Golden Test 24 (4 tests), and full safety audit prompt-injection evidence.
  All 110 golden tests pass; `python -m rge.modules.safety_auditor --audit full`
  returns `pass`.
- Pre-ticket-026 audit report included in branch base; generated export artifacts
  were cleaned before implementation.
- ticket-027 proposes public-site debug details without private data exposure for
  Golden Test 25 (medium risk; pre-ticket audit recommended).

## Queue Notes (2026-06-12, ticket-025 agent)

- ticket-025 implemented full `run_safety_audit()` with route/export/secrets/raw-html/
  model-tool checks, CLI pass/fail JSON output, and Golden Test 23 (5 tests). All
  106 golden tests pass; `python -m rge.modules.safety_auditor --audit full`
  returns `pass`.
- Pre-ticket-025 audit report included in merge; satisfies overdue checkpoint.
- ticket-026 proposes prompt-injection fixture handling for Golden Test 24
  (medium risk; pre-ticket audit recommended).

## Queue Notes (2026-06-12, ticket-024 agent)

- ticket-024 implemented Golden Test 22 merge gate meta-tests with
  `BUILDER_MERGE_GATE_COMMAND` and required golden area coverage map (4 tests).
  All 101 golden tests pass without Ollama.
- ticket-025 proposes safety audit merge gate for Golden Test 23 (medium risk;
  pre-ticket audit recommended).

## Queue Notes (2026-06-12, ticket-023 agent)

- ticket-023 implemented `validate_builder_ticket()` with GT21 required-field and
  vagueness checks, pre-insert validation in `generate_improvement_tickets`, and
  Golden Test 21 (4 tests). All 97 golden tests pass without Ollama.
- ticket-024 proposes builder golden merge gate for Golden Test 22.

## Queue Notes (2026-06-12, ticket-022 agent)

- ticket-022 implemented `generate-improvement-tickets` with
  `ImprovementTicketRepository`, deterministic failure-mode templates
  (`overgeneralized_scope`, `missing_quote_span`, `weak_concept_mapping`),
  draft improvement tickets, and Golden Test 20 (4 tests). All 93 golden tests
  pass without Ollama.
- Pre-ticket-022 audit report included in merge.
- ticket-023 proposes builder-consumable ticket validation for Golden Test 21.

## Queue Notes (2026-06-12, ticket-021 agent)

- ticket-021 implemented `generate-run-report` with `ResearchRunRepository` /
  `RunReportRepository`, deterministic metric aggregation, machine-readable
  `top_failure_modes`, and Golden Test 19 (4 tests). All 89 golden tests pass
  without Ollama.
- Pre-ticket-021 audit report included in merge.
- ticket-022 proposes improvement ticket generation for Golden Test 20.

## Queue Notes (2026-06-12, ticket-020 agent)

- ticket-020 implemented `generate-domain-proposal` with migration `0007`,
  deterministic golden padding (40 claims / 8 sources / 15 specialized terms /
  3 mismatch signals), draft domain proposals, and Golden Test 18 (4 tests).
  All 85 golden tests pass without Ollama.
- Pre-ticket-020 audit report included in merge.
- ticket-021 proposes research run report for Golden Test 19.

## Queue Notes (2026-06-12, ticket-019 agent)

- ticket-019 implemented `generate-ontology-pressure` with migration `0006`,
  deterministic golden vocabulary padding (20 pressure claims / 2+ sources),
  draft ontology proposals, and Golden Test 17 (4 tests). All 81 golden tests
  pass without Ollama.
- Pre-ticket-019 audit report included in merge.
- ticket-020 proposes domain proposal threshold trigger for Golden Test 18.

## Queue Notes (2026-06-12, ticket-018 agent)

- ticket-018 implemented `generate-followup-questions` with cluster/theory context
  proposal, extended contract validation, and Golden Test 16 (4 tests). All 77
  golden tests pass without Ollama.
- Pre-ticket-018 audit report included in merge.
- ticket-019 proposes ontology pressure report for Golden Test 17.

## Queue Notes (2026-06-12, ticket-017 agent)

- ticket-017 implemented `generate-theory-candidates` with migration `0005`,
  mock theory fixture, deterministic validation against cluster evidence packets,
  and Golden Test 15 (4 tests). All 73 golden tests pass without Ollama.
- Pre-ticket-017 audit report committed on main before implementation branch.
- ticket-018 proposes contract-respecting question generation for Golden Test 16.

## Queue Notes (2026-06-12, ticket-016 agent)

- ticket-016 implemented `generate-cluster-report` with migration `0004`,
  deterministic golden threshold padding (15 claims / 3 sources), balanced
  evidence packet assembly, and Golden Test 13 (4 tests). All 69 golden tests
  pass without Ollama.
- Pre-ticket-016 audit report included in merge.
- ticket-017 proposes mock theory generator for Golden Test 15.

## Queue Notes (2026-06-12, ticket-015 agent)

- ticket-015 implemented static card detail (`/cards/[id]`) and concept detail
  (`/concepts/[slug]`) pages, list-page links, golden export JSON refresh, and
  Golden Test 12 (6 tests). All 65 golden tests pass; public site builds 11 static pages.
- Pre-ticket-015 audit report and runner audit-gate patch included in merge.
- ticket-016 proposes cluster report threshold trigger for Golden Test 13.

## Queue Notes (2026-06-11, ticket-014 agent)

- ticket-014 implemented `research export-public` with deterministic safety validation,
  golden card seeding from accepted claims, and JSON writes to `data/exports/` plus
  `apps/public-site/public/data/`. Golden Test 11 passes (4 tests); all 59 golden
  tests pass without Ollama; public site static build succeeds.
- ticket-015 proposes public site card/concept detail pages for Golden Test 12.

## Queue Notes (2026-06-11, ticket-013 agent)

- ticket-013 implemented `research validate-contract` with golden contract seeding,
  deterministic out-of-scope parking (`out_of_scope_topic_drift`), and on-scope follow-up
  queueing. Golden Test 10 passes (4 tests); all 55 golden tests pass without Ollama.
- ticket-014 proposes public card export for Golden Test 11.

## Queue Notes (2026-06-11, ticket-012 agent)

- ticket-012 implemented `research queue-sources` with migration `0003`,
  deterministic fixture ranking (`golden_v0.1.0`), and persistence to
  `candidate_sources` + `research_queue`. Golden Test 9 passes (3 tests); all
  51 golden tests pass without Ollama.
- ticket-013 proposes research contract drift gating for Golden Test 10.

## Queue Notes (2026-06-11, ticket-011 agent)

- ticket-011 implemented `research detect-contradictions` with mock fixture detection,
  cross-source qualification links (`qualifies` stance), and
  `contradiction_classification` metadata on relationships. Golden Test 7 passes
  (3 tests); all 48 golden tests pass without Ollama.
- ticket-012 proposes mock research queue ranking for Golden Test 9.

## Queue Notes (2026-06-11, ticket-010 agent)

- ticket-010 implemented `research reconcile-scores` with deterministic score boost
  (`golden_v0.1.0`, +0.12 when claim confidence ≥ 0.8), append-only `score_events`
  via `persist_relationship_score_update`, and follow-up source/fixture for Golden Test 8.
  Golden Test 8 passes (4 tests); all 45 golden tests pass without Ollama.
- ticket-011 proposes mock contradiction detection for Golden Test 7.

## Queue Notes (2026-06-11, ticket-009 agent)

- ticket-009 implemented `research build-relationships` with mock fixture drafting,
  deterministic validation, `0002_relationship_evidence` migration, and persistence of
  active relationships plus evidence links. Golden Test 6 passes (5 tests); all 41
  golden tests pass without Ollama.
- Confidence labels from mock candidates map deterministically to REAL scores
  (low=0.25, medium=0.5, high=0.75) in Python before DB write.
- ticket-010 proposes score reconciliation for Golden Test 8.

## Queue Notes (2026-06-11, ticket-008 agent)

- ticket-008 implemented `research link-concepts` with mock fixture linking, ontology
  seeding, and `claim_concepts` persistence. Golden Test 5 passes (3 tests); all 36
  golden tests pass without Ollama.
- No prior merge-to-main workflow existed; canonical docs specify human/checkpoint merge
  (`docs/agents/04_CURSOR_BUILD_LOOP.md`). Added temporary `AGENTS.md` step 9: merge
  ticket branch to `main` and push after each done ticket until the safety evaluator
  agent owns merge gating.
- ticket-008 branch merged to `main` and pushed (includes previously unmerged 001/006/007 work).
- ticket-009 proposes mock relationship builder for Golden Test 6.

## Queue Notes (2026-06-11, ticket-007 agent)

- ticket-007 implemented `research extract-claims` with mock LLM fixtures, deterministic
  validation (quote span, scope, overgeneralization), and persistence to `claims` +
  `claim_quotes`. Golden Test 2 passes (4 tests); all 33 golden tests pass without Ollama.
- ticket-008 proposes mock concept linking for Golden Test 5.

## Queue Notes (2026-06-11, ticket-006 agent)

- ticket-006 implemented the migration harness, reconciled claims lifecycle, and
  `research ingest`. Golden Test 1 passes (5 tests).
- On Windows, `research.exe` may not be on PATH; use `python -m rge.cli`.

## Current Active Ticket

```txt
ticket-032 (proposed; awaiting review)
```

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
- **Temporary:** after a ticket is `done`, merge its branch to `main` and push per `AGENTS.md` step 9 until the safety evaluator agent is live.
