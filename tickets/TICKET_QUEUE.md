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
| 32 | ticket-032 | done | Phase 1 builder golden gate completion checkpoint | `phase-1/ticket-032-builder-golden-gate-completion` | `agent_reports/2026-06-12_phase-1_ticket-032_builder-golden-gate-completion.md` |

## Phase 2 Queue

| Order | Ticket ID | Status | Title | Branch | Report |
|---:|---|---|---|---|---|
| 33 | ticket-033 | done | Pre-phase-2 principal audit checkpoint | | `agent_reports/2026-06-12_pre-phase-2_principal-audit.md` |
| 34 | ticket-034 | done | Make fixture-mode run repo-clean and export serialization deterministic | `phase-2/ticket-034-fixture-run-artifact-hygiene` | `agent_reports/2026-06-12_phase-2_ticket-034_fixture-run-artifact-hygiene.md` |
| 35 | ticket-035 | done | Refresh README for Phase 1 reality and operator quickstart | `phase-2/ticket-035-readme-operator-refresh` | `agent_reports/2026-06-12_phase-2_ticket-035_readme-operator-refresh.md` |
| 36 | ticket-036 | done | Public-site presentation polish and about page (no data surface changes) | `phase-2/ticket-036-public-site-polish` | `agent_reports/2026-06-12_phase-2_ticket-036_public-site-polish.md` |
| 37 | ticket-037 | done | Implement Ollama structured tasks behind explicit live-mode opt-in | `phase-2/ticket-037-ollama-live-structured-tasks` | `agent_reports/2026-06-12_phase-2_ticket-037_ollama-live-structured-tasks.md` |
| 38 | ticket-038 | done | Gate live smoke tests behind env opt-in and add model-health command | `phase-2/ticket-038-live-smoke-gating` | `agent_reports/2026-06-12_phase-2_ticket-038_live-smoke-gating.md` |
| 39 | ticket-039 | done | Validate improvement-ticket round-trip into the builder queue with review gate | `phase-2/ticket-039-improvement-ticket-round-trip` | `agent_reports/2026-06-12_phase-2_ticket-039_improvement-ticket-round-trip.md` |
| 40 | ticket-040 | done | Add CI golden gate workflow and rge-principal-audit command doc | `phase-2/ticket-040-ci-golden-gate` | `agent_reports/2026-06-12_phase-2_ticket-040_ci-golden-gate.md` |
| 41 | ticket-041 | done | Bounded RGE operator loop runner | `phase-2/ticket-041-operator-loop-runner` | `agent_reports/2026-06-12_phase-2_ticket-041_operator-loop-runner.md` |
| 42 | ticket-042 | done | Public-site deployment readiness: static hosting docs and pre-deploy checklist | `phase-2/ticket-042-public-site-deployment-readiness` | `agent_reports/2026-06-12_phase-2_ticket-042_public-site-deployment-readiness.md` |
| 43 | ticket-043 | done | Extend safety auditor to data/exports and tighten evidence checks | `phase-2/ticket-043-safety-auditor-exports` | `agent_reports/2026-06-12_phase-2_ticket-043_safety-auditor-exports.md` |
| 44 | ticket-044 | done | Fix principal audit gate false overdue cadence counting | `phase-2/ticket-044-principal-audit-gate-fix` | `agent_reports/2026-06-12_phase-2_ticket-044_principal-audit-gate-fix.md` |
| 45 | ticket-045 | done | Promote improvement draft with explicit review gate | `phase-2/ticket-045-improvement-draft-promotion` | `agent_reports/2026-06-12_phase-2_ticket-045_improvement-draft-promotion.md` |
| 46 | ticket-046 | done | Fix operator loop done-without-commit false positive | `phase-2/ticket-046-operator-loop-drift-fix` | `agent_reports/2026-06-12_phase-2_ticket-046_operator-loop-drift-fix.md` |
| 47 | ticket-047 | done | Stop plain export-public from rewriting committed public-site JSON | `phase-2/ticket-047-export-public-publish-only` | `agent_reports/2026-06-12_phase-2_ticket-047_export-public-publish-only.md` |
| 48 | ticket-048 | rejected | Improve claim quote span validation | | `agent_reports/2026-06-12_pre-ticket-048_claim-quote-span-readiness-audit.md` |
| 49 | ticket-049 | done | Skip improvement tickets for golden-covered rejection modes | `phase-2/ticket-049-improvement-generator-filter` | `agent_reports/2026-06-12_phase-2_ticket-049_improvement-generator-filter.md` |
| 50 | ticket-050 | done | CI Golden Gate: opt into Node 24 for GitHub Actions | `phase-2/ticket-050-ci-node24-actions` | `agent_reports/2026-06-12_phase-2_ticket-050_ci-node24-actions.md` |
| 51 | ticket-051 | done | Implement research verify mock-only verification suite | `phase-2/ticket-051-research-verify` | `agent_reports/2026-06-12_phase-2_ticket-051_research-verify.md` |
| 52 | ticket-052 | done | Persist char_start and char_end for accepted claim quote spans | `phase-2/ticket-052-quote-span-offsets` | `agent_reports/2026-06-12_phase-2_ticket-052_quote-span-offsets.md` |
| 53 | ticket-053 | done | Loop rehearsal — stale draft hygiene and actionable improvement draft drill | `phase-2/ticket-053-loop-rehearsal` | `agent_reports/2026-06-12_phase-2_ticket-053_loop-rehearsal.md` |
| 54 | ticket-054 | done | Operator verify docs and Windows local verify reliability | `phase-2/ticket-054-operator-verify-docs` | `agent_reports/2026-06-12_phase-2_ticket-054_operator-verify-docs.md` |
| 55 | ticket-055 | done | Export snapshot manifest and scratch history for operator review | `phase-2/ticket-055-export-snapshot-history` | `agent_reports/2026-06-12_phase-2_ticket-055_export-snapshot-history.md` |
| 56 | ticket-056 | done | Windows-safe npm subprocess for operator execute-safe | `phase-2/ticket-056-windows-npm-subprocess` | `agent_reports/2026-06-12_phase-2_ticket-056_windows-npm-subprocess.md` |
| 57 | ticket-057 | done | Windows subprocess UTF-8 decode for operator/verify npm capture | `phase-2/ticket-057-windows-subprocess-utf8-decode` | `agent_reports/2026-06-12_phase-2_ticket-057_windows-subprocess-utf8-decode.md` |
| 58 | ticket-058 | done | Local-first model runtime readiness and escalation policy | `phase-2/ticket-058-local-first-model-runtime` | `agent_reports/2026-06-12_phase-2_ticket-058_local-first-model-runtime.md` |
| 59 | ticket-059 | proposed | OpenAI opt-in cloud adapter (placeholder — not implemented) | | |
| 60 | ticket-060 | done | Safe local live claim-extraction probe CLI | `phase-2/ticket-060-safe-local-live-claim-probe` | `agent_reports/2026-06-12_phase-2_ticket-060_safe-local-live-claim-probe.md` |
| 61 | ticket-061 | done | Live claim extraction calibration for local Qwen | `phase-2/ticket-061-live-claim-calibration` | `agent_reports/2026-06-12_phase-2_ticket-061_live-claim-calibration.md` |
| 62 | ticket-062 | done | Safe local live concept-linking probe CLI | `phase-2/ticket-062-safe-local-live-concept-linking-probe` | `agent_reports/2026-06-12_phase-2_ticket-062_safe-local-live-concept-linking-probe.md` |
| 63 | ticket-063 | done | Safe local live relationship-drafting probe CLI | `phase-2/ticket-063-safe-local-live-relationship-probe` | `agent_reports/2026-06-12_phase-2_ticket-063_safe-local-live-relationship-probe.md` |
| 64 | ticket-064 | done | Safe local live contradiction-detection probe CLI | `phase-2/ticket-064-safe-local-live-contradiction-probe` | `agent_reports/2026-06-12_phase-2_ticket-064_safe-local-live-contradiction-probe.md` |
| 65 | ticket-065 | done | Report-only local live mini-run chain | `phase-2/ticket-065-local-live-mini-run-chain` | `agent_reports/2026-06-12_phase-2_ticket-065_local-live-mini-run-chain.md` |
| 66 | ticket-066 | done | Multi-fixture local live mini-run repeatability | `phase-2/ticket-066-multi-fixture-mini-run-repeatability` | `agent_reports/2026-06-12_phase-2_ticket-066_multi-fixture-mini-run-repeatability.md` |
| 67 | ticket-067 | done | Multi-fixture prompt calibration for local live mini-run suite | `phase-2/ticket-067-multi-fixture-prompt-calibration` | `agent_reports/2026-06-12_phase-2_ticket-067_multi-fixture-prompt-calibration.md` |
| 68 | ticket-068 | done | Scratch DB persistence for reviewed live mini-run reports | `phase-2/ticket-068-scratch-db-reviewed-live-probe-persistence` | `agent_reports/2026-06-12_phase-2_ticket-068_scratch-db-reviewed-live-probe-persistence.md` |
| 69 | ticket-069 | done | Followup contradiction calibration | `phase-2/ticket-069-followup-contradiction-calibration` | `agent_reports/2026-06-12_phase-2_ticket-069_followup-contradiction-calibration.md` |
| 70 | ticket-070 | done | Scratch DB run summary | `phase-2/ticket-070-scratch-db-run-summary` | `agent_reports/2026-06-12_phase-2_ticket-070_scratch-db-run-summary.md` |
| 71 | ticket-071 | done | Deterministic scratch evidence review report | `phase-2/ticket-071-deterministic-evidence-review-report` | `agent_reports/2026-06-13_phase-2_ticket-071_deterministic-evidence-review-report.md` |
| 72 | ticket-072 | done | Operator loop scratch evidence status hook | `phase-2/ticket-072-operator-loop-scratch-evidence-status` | `agent_reports/2026-06-13_phase-2_ticket-072_operator-loop-scratch-evidence-status.md` |
| 73 | ticket-073 | done | Operator loop evidence review readiness action hint | `phase-2/ticket-073-operator-loop-evidence-review-action` | `agent_reports/2026-06-13_phase-2_ticket-073_operator-loop-evidence-review-action.md` |
| 74 | ticket-074 | done | Windows-safe UTF-8 stdout for probe-scratch-evidence-review | `phase-2/ticket-074-windows-evidence-review-utf8-stdout` | `agent_reports/2026-06-13_phase-2_ticket-074_windows-evidence-review-utf8-stdout.md` |
| 75 | ticket-075 | done | Live probe runbook Windows console encoding note | `phase-2/ticket-075-runbook-windows-encoding-note` | `agent_reports/2026-06-13_phase-2_ticket-075_runbook-windows-encoding-note.md` |
| 76 | ticket-076 | done | Runbook scratch evidence workflow checklist | `phase-2/ticket-076-runbook-scratch-workflow-checklist` | `agent_reports/2026-06-13_phase-2_ticket-076_runbook-scratch-workflow-checklist.md` |
| 77 | ticket-077 | done | README operator quickstart scratch evidence workflow pointer | `phase-2/ticket-077-readme-scratch-workflow-pointer` | `agent_reports/2026-06-13_phase-2_ticket-077_readme-scratch-workflow-pointer.md` |
| 78 | ticket-078 | done | AGENTS.md operator quickstart scratch evidence workflow cross-link | `phase-2/ticket-078-agents-scratch-workflow-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-078_agents-scratch-workflow-crosslink.md` |
| 79 | ticket-079 | done | Operating protocol scratch evidence workflow cross-link | `phase-2/ticket-079-operating-protocol-scratch-workflow-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-079_operating-protocol-scratch-workflow-crosslink.md` |
| 80 | ticket-080 | proposed | Post-ticket-079 principal audit checkpoint | | |

## Queue Notes (2026-06-13, ticket-080 seed)

- Principal audit required: 3 done tickets (077–079) since post-ticket-076 checkpoint.

## Queue Notes (2026-06-13, ticket-079 agent)

- 11_AGENT_OPERATING_PROTOCOL.md Operator Loop links runbook scratch evidence checklist.

## Queue Notes (2026-06-13, ticket-078 agent)

- AGENTS.md Operator Loop section links runbook scratch evidence checklist.

## Queue Notes (2026-06-13, ticket-077 agent)

- README Operator Quickstart + Key operator docs link to runbook checklist.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-077 seed)

- README link to runbook scratch evidence workflow checklist (docs-only).

## Queue Notes (2026-06-13, ticket-076 agent)

- Numbered 5-step checklist: probe → persist → summary → evidence review → operator loop plan.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-076 seed)

- Docs-only numbered checklist linking persist → summary → evidence review → operator loop plan.

## Queue Notes (2026-06-13, ticket-075 agent)

- Runbook documents ASCII-safe default markdown on Windows cp1252 post ticket-074.
- JSON/`--out` listed as optional conveniences, not encoding workarounds.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-075 seed)

- Docs-only follow-on from ticket-074: runbook Windows cp1252 guidance update.

## Queue Notes (2026-06-13, ticket-074 agent)

- Evidence review markdown uses ASCII `->` review window separator for cp1252 stdout.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-074 seed)

- Follow-on from operator probe: Windows cp1252 UnicodeEncodeError on markdown arrow.
- Narrow CLI/formatter fix only.

## Queue Notes (2026-06-13, ticket-073 agent)

- Plan mode recommends `run_scratch_evidence_review` when scratch rows exist and no blockers.
- Open queue tickets and improvement drafts still take precedence.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-073 seed)

- Proposed follow-on from ticket-072: review_gated plan action when scratch evidence is ready.
- No auto evidence review generation or queue mutation.

## Queue Notes (2026-06-13, ticket-072 agent)

- Plan mode adds `scratch_evidence_status` (path, exists, row count, readiness).
- Missing/invalid scratch DB fail gracefully; plan never crashes on scratch inspect.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-072 seed)

- Proposed follow-on from ticket-071: read-only scratch evidence status in operator loop plan mode.
- No LLM, no auto-persist, no queue mutation.

## Queue Notes (2026-06-13, ticket-071 agent)

- Adds `probe-scratch-evidence-review` reusing read-only scratch summary aggregation.
- Markdown default; no automated ticket recommendations; private `--out` only.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-13, ticket-071 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-13_pre-ticket-071_deterministic-evidence-review-report.md`.
- Adds formatted evidence review CLI reusing read-only `probe-scratch-summary` aggregation.
- No LLM, no graph/export writes, no automated ticket recommendations.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-13, principal audit post-ticket-070)

- Cadence satisfied: `agent_reports/2026-06-13_principal-audit-post-ticket-070.md` at `64f4686`.
- Live suite 4/4; scratch persist + read-only summary operational.
- Recommended next: ticket-071 evidence review (deterministic) before OpenAI.

## Queue Notes (2026-06-12, ticket-070 agent)

- Adds `probe-scratch-summary` read-only aggregation over scratch SQLite.
- SQLite `mode=ro`; no schema bootstrap; private `--out` paths only.
- **Cadence:** 3 done tickets since post-ticket-067 checkpoint — run `/rge-principal-audit` before next medium-risk ticket.
- ticket-059 OpenAI deferred.

## Queue Notes (2026-06-12, ticket-070 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-070_scratch-db-run-summary.md`.
- Adds read-only `probe-scratch-summary` over scratch SQLite; deterministic counts only.
- No LLM, no graph/export writes; ticket-059 OpenAI deferred.
- After done: post-ticket-070 principal audit required (3rd ticket since checkpoint).

## Queue Notes (2026-06-12, ticket-069 agent)

- Opposing-only hybrid overlay handoff + contradiction prompt claim-id rules.
- Live suite: **4/4** floors (`probe_mini_run_suite_2026-06-12T231236Z.json`).
- Validators unchanged; still report-only; ticket-059 OpenAI deferred.

## Queue Notes (2026-06-12, ticket-069 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-069_followup-contradiction-calibration.md`.
- Fixes opposing-only hybrid overlay handoff + contradiction prompt claim-id guidance for followup fixture.
- Goal: suite 4/4 floors; still report-only; validators unchanged.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-068 agent)

- Adds `probe-persist-reviewed-report --confirm-review` → `data/db/live_probe_scratch.sqlite`.
- Sanitized metadata only; mini-run/suite remain report-only by default.
- Safety auditor `live_probe_scratch_policy` check added.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-068 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-068_scratch-db-reviewed-live-probe-persistence.md`.
- Adds explicit `probe-persist-reviewed-report --confirm-review` to isolated scratch SQLite.
- No default DB, no public export, no auto-persist on mini-run.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-067 agent)

- Calibrated Ollama claim/relationship prompts; mini-run multi-claim id handoff.
- Added diversity + contradiction calibration fixtures for suite.
- Live suite: 3/4 fixtures pass floors; followup contradiction stage still flaky.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-067 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-067_multi-fixture-prompt-calibration.md`.
- Calibrates Ollama claim/relationship prompts; mini-run multi-claim handoff; contradiction calibration fixture.
- Goal: at least two suite fixtures pass floors; still report-only.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-066 agent)

- Adds `probe-mini-run-suite` batch command; default four creativity sources.
- Live suite: 1/4 fixtures pass floors (calibration short only); exposes overfit.
- Suite summary + per-fixture floors in gitignored reports; no DB/export/cloud.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-066 seed)

- Human approved evidence review option A.
- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-066_multi-fixture-mini-run-repeatability.md`.
- Adds `probe-mini-run-suite` (report-only, no default DB); batches hybrid mini-run across four committed creativity sources.
- Qwen remains bounded worker only; ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-065 agent)

- Adds `probe-mini-run` report-only CLI; chains extract → link → relationship live;
  stage 4 hybrid overlay by default; `--strict-chain` skips contradiction when insufficient.
  Live default: status=ok, hybrid_overlay, all stages accepted>=1. Live strict: partial, skipped stage 4.
- Qwen bounded worker only; no ticket authoring authority.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-065 seed)

- Pre-ticket audit GO (narrowed hybrid): `agent_reports/2026-06-12_pre-ticket-065_local-live-mini-run-chain.md`.
- Adds `probe-mini-run` (report-only, no default DB); chains extract → link → relationship live;
  stage 4 hybrid overlay by default; `--strict-chain` optional.
- Qwen remains bounded worker only; no ticket authoring authority.
- ticket-059 OpenAI remains proposed/deferred.

## Queue Notes (2026-06-12, ticket-064 agent)

- Adds `probe-detect-contradictions` report-only CLI; default embedded GT07-shaped
  contradiction bundle; optional `--from-report` / `--chain-relationship`; calibrated
  Ollama contradiction prompt; `contradiction_rejection_diagnostic` on rejections.
  Live: accepted_count=1, db_writes=false. `live_smoke` covers full probe chain (5 tests).
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-064 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-064_local-live-contradiction-probe.md`.
- Adds `probe-detect-contradictions` (report-only, no default DB); default embedded GT07-shaped
  contradiction bundle; optional `--from-report` / `--chain-relationship`; Ollama prompt calibration
  + contradiction rejection diagnostics.
- Prep hygiene: `live_smoke` extended for `probe-link-concepts` and `probe-draft-relationships`.
- ticket-059 OpenAI remains proposed/deferred.

## Queue Notes (2026-06-12, ticket-063 agent)

- Adds `probe-draft-relationships` report-only CLI; default embedded bundle fixture;
  optional `--from-report` / `--chain-link`; calibrated Ollama relationship prompt;
  `relationship_rejection_diagnostic` on rejections. Live: accepted_count=1, db_writes=false.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-063 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-063_local-live-relationship-probe.md`.
- Adds `probe-draft-relationships` (report-only, no default DB); default embedded bundle fixture
  (claim + concept links + probe-local concepts); optional `--from-report` / `--chain-link`;
  Ollama prompt calibration + relationship rejection diagnostics.
- ticket-059 OpenAI remains proposed/deferred.

## Queue Notes (2026-06-12, ticket-062 agent)

- Adds `probe-link-concepts` report-only CLI; default embedded quality claim fixture;
  optional `--from-report` / `--chain-extract`; calibrated Ollama concept prompt;
  `link_rejection_diagnostic` on rejections. Live: accepted_count=3, db_writes=false.
- ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-12, ticket-062 seed)

- Pre-ticket audit GO: `agent_reports/2026-06-12_pre-ticket-062_local-live-concept-linking-probe.md`.
- Adds `probe-link-concepts` (report-only, no default DB); default embedded accepted claim fixture;
  optional `--from-report` / `--chain-extract`; Ollama prompt calibration + link rejection diagnostics.
- ticket-059 OpenAI remains proposed/deferred.

## Queue Notes (2026-06-12, ticket-061 agent)

- Root cause of 0 accepted: scope not embedded in claim_text + missing SPO fields; validator correct.
- Calibrated Ollama prompt (SPO, scope-in-claim rules, examples), calibration fixture default, validation_diagnostic on rejections.

## Queue Notes (2026-06-12, ticket-060 agent)

- Pre-ticket-059 audit GO: seed local live probe; ticket-059 stays OpenAI placeholder.
- ticket-060 adds `probe-extract-claims` (report-only, no default DB), `rge/modules/live_probe.py`, unit + live_smoke tests.

## Queue Notes (2026-06-12, ticket-058 agent)

- Pre-ticket-058 audit: PARTIAL — human completed `ollama pull qwen2.5:7b`; model-health now `model_available: true`.
- ticket-058 adds `13_MODEL_ESCALATION_POLICY.md`, runbook updates, model-health hints (`configured_model`, `available_models`, `action_hint`).
- OpenAI/OpenRouter deferred; ticket-059 seeded as proposed placeholder only.

## Queue Notes (2026-06-12, ticket-057 agent)

- Post-ticket-056 audit: execute-safe passed but background UnicodeDecodeError on Windows cp1252 vs UTF-8 npm output.
- ticket-057 adds `rge/subprocess_capture.run_captured` with UTF-8 `errors=replace` for operator/verify subprocess capture.

## Queue Notes (2026-06-12, ticket-056 agent)

- `resolve_npm_executable()` uses `shutil.which('npm')` for execute-safe/verify site build.
- Omits `public_site_build` when npm is missing; AGENTS.md notes Windows behavior.

## Queue Notes (2026-06-12, ticket-055 agent)

- Pre-ticket-055 audit GO: scratch snapshot manifest + `data/exports/history/` copies.
- Default mock export retains history; `--no-snapshot-history` opt-out; ticket-047 publish guards preserved.

## Queue Notes (2026-06-12, ticket-054 agent)

- AGENTS.md and README.md lead with `python -m rge.cli verify` (and `--skip-site`).
- Windows PATH fallback documented; module form is canonical when `research` is missing.
- Windows repair: `test_default_pytest_deselects_live_smoke` uses temp-file subprocess capture; `verify_runner` prints stderr progress per check.

## Queue Notes (2026-06-12, ticket-053 agent)

- Pre-ticket audit rejects overgeneralized_scope promotion as GT02 golden-covered duplicate.
- ticket-053 extends golden-covered filter to `overgeneralized_scope`; clears stale
  `improvement_ticket_latest.json` to `[]`.
- Loop drill confirms `weak_concept_mapping` still produces actionable drafts; no `--confirm` promotion in this ticket.

## Queue Notes (2026-06-12, ticket-052 agent)

- ticket-052 stores quote char_start/char_end on accepted claims when quote_span
  matches chunk text (exact or collapsed whitespace). GT02 +4 offset unit tests;
  187 pytest pass.

## Queue Notes (2026-06-12, ticket-051 agent)

- ticket-051 implements `research verify` (mock-only golden/pytest/safety/site build).
  `--skip-site` for Python-only checks; 3 unit tests pass.

## Queue Notes (2026-06-12, ticket-050 agent)

- ticket-050 sets `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` on Golden Gate job.
  +1 CI meta-test; addresses Actions Node 20 deprecation annotation.

## Queue Notes (2026-06-12, ticket-049 agent)

- ticket-049 filters `missing_quote_span` from improvement drafts (GT02 already covers).
- Operator loop ignores golden-covered stale drafts in `improvement_ticket_latest.json`.
- +2 GT20, +1 operator loop unit test; 181 pytest pass; safety audit pass.

## Queue Notes (2026-06-12, pre-ticket-048 audit)

- ticket-048 **rejected**: quote-span validation already implemented (GT02 pass);
  `missing_quote_span_count=1` is intentional fixture rejection, not a gap.
  Pre-ticket audit: `agent_reports/2026-06-12_pre-ticket-048_claim-quote-span-readiness-audit.md`.
- Golden Gate run 27425020457 green on GitHub at `c98726b` (release PASS).
- ticket-049 seeded: filter improvement drafts for golden-covered failure modes.

## Queue Notes (2026-06-12, ticket-045 agent)

- ticket-045 promoted improvement draft to `tickets/ticket-048.json` via
  `promote-improvement-ticket --confirm --from-json`. GT21 pass; no runtime
  changes. Pre-ticket audit written before promotion. ticket-048 is proposed
  for future implementation (medium risk; pre-ticket audit required).

## Queue Notes (2026-06-12, ticket-047 agent)

- ticket-047 limits default mock-mode `export-public` to `data/exports/` only.
  Public-site committed JSON updates require `--publish` or fixture-mode.
  +1 export publish gate unit test; GT11 unchanged; 135 golden pass.

## Queue Notes (2026-06-12, ticket-046 agent)

- ticket-046 extends `ticket_has_implementation_commit` to accept `tickets/{id}.json`
  in git history on main when commit messages omit the ticket id (ticket-043/cc1c17c).
  +2 operator loop unit tests; 19 operator loop tests pass; 177 total pytest pass.

## Queue Notes (2026-06-12, ticket-044 agent)

- ticket-044 fixes `principal_audit_gate` to parse `post-ticket-NNN` and
  `pre-phase-N_principal-audit` checkpoints; counts only done tickets after the
  referenced ticket. Premature post-ticket reports ignored. Operator loop cadence
  now satisfied after post-ticket-042 audit. 7 gate unit tests + 17 operator loop
  tests; 174 total pytest pass.

## Queue Notes (2026-06-12, ticket-043 agent)

- ticket-043 added `_audit_data_exports()` to scan `data/exports/*.json` when present.
- GT23 +3 tests (135 golden total); safety audit pass; improvement promotion deferred.

## Queue Notes (2026-06-12, ticket-043 seed)

- Principal audit checkpoint written after tickets 040–042:
  `agent_reports/2026-06-12_principal-audit-post-ticket-042.md`.
- ticket-043 extends `safety_auditor` to validate `data/exports/*.json` when present
  using existing `validate_public_export_bundle` and `FORBIDDEN_VALUE_PATTERNS`.
- Improvement draft promotion deferred until after ticket-043.

## Queue Notes (2026-06-12, ticket-042 agent)

- ticket-042 added `docs/deployment/public-site-static-hosting.md` (build, pre-deploy
  checklist, snapshot refresh, static host guidance) and `preview:static` npm script.
  Docs-only; no export schema or route changes. 132 golden pass; safety audit pass;
  public site builds 12 static pages.

## Queue Notes (2026-06-12, ticket-042 seed)

- ticket-042 seeded from Phase 2 roadmap (deployment readiness). Docs-only;
  pre-deploy checklist requires safety audit + snapshot review. No pre-ticket
  audit required at low risk if scope stays documentation-only.

## Queue Notes (2026-06-12, ticket-041 agent)

- ticket-041 adds `python -m rge.modules.operator_loop` with `--mode plan`
  (read-only JSON status) and `--mode execute-safe` (mock-only golden/pytest/
  safety audit/public-site build when clean). Classifies next action as
  safe-autonomous, review-gated, or blocked. Detects documentation-ahead-of-git
  drift. Never merges, pushes, promotes, or edits the queue.

## Queue Notes (2026-06-12, ticket-040 agent)

- ticket-040 added `.github/workflows/golden-gate.yml` (mock-only golden +
  pytest + safety audit + public-site build), `/rge-principal-audit` command doc,
  `principal_audit_gate` checkpoint helper, and safety audit CI evidence check.
  132 golden + 150 total pytest pass; 1 live_smoke deselected; safety audit passes;
  public site builds 12 pages. Ready to merge; GitHub Actions first run pending push.

## Queue Notes (2026-06-12, ticket-039 agent)

- ticket-039 added `promote-improvement-ticket` with mandatory `--confirm` review
  gate, queue JSON mapping in `ticket_writer.py`, GT21 round-trip tests (+3),
  and promotion workflow docs. No auto `TICKET_QUEUE.md` mutation. 132 golden +
  143 total pytest pass; safety audit passes.
- ticket-040 (CI golden gate + principal-audit command) seeded as next proposed.

## Queue Notes (2026-06-12, ticket-038 agent)

- ticket-038 added `live_smoke` pytest marker excluded from default runs,
  `research model-health` CLI, live-mode `export-public --publish` guard, and
  safety audit `live_smoke_policy` evidence. 129 golden + 140 total pytest pass;
  1 smoke test deselected. Safety audit passes.
- ticket-039 (improvement-ticket promotion round-trip) seeded as next proposed.

## Queue Notes (2026-06-12, ticket-037 agent)

- ticket-037 implemented Ollama structured tasks behind `RGE_ALLOW_LIVE_LLM=1`
  opt-in: effective-mode resolver, four pipeline Ollama tasks, 8 canned unit
  tests, safety audit live-LLM evidence check. Golden/fixture runs stay
  mock-only. 137 tests pass; safety audit passes. Live Ollama extract-claims
  manual smoke not run in agent environment (documented in report).
- ticket-038 (live smoke gating + model-health CLI) seeded as next proposed.

## Queue Notes (2026-06-12, ticket-037 seed)

- ticket-037 seeded after focused pre-ticket-037 live-Ollama readiness audit
  (`agent_reports/2026-06-12_pre-ticket-037_ollama-live-structured-tasks-readiness-audit.md`).
  Recommendation: proceed with explicit `RGE_ALLOW_LIVE_LLM=1` opt-in, shared
  effective-mode resolver, Ollama structured tasks for four pipeline modules,
  canned unit tests with mocked HTTP, golden/fixture runs staying mock-only.
  ticket-038+ intentionally not seeded in this pass.

## Queue Notes (2026-06-12, ticket-036 agent)

- ticket-036 delivered presentation-only public-site polish: humanized enum
  labels, deterministic human-readable timestamps, static `/about` page,
  custom 404, and zero-card empty state. No export schema changes; no new
  public data fields. All 127 golden tests pass; safety audit passes; site
  builds 12 static pages.
- ticket-037 (live Ollama structured tasks) is next per Phase 2 roadmap and
  **requires its own pre-ticket audit** before seeding. ticket-040 (CI golden
  gate) is an independent low-risk alternative that may be pulled earlier.

## Queue Notes (2026-06-12, ticket-036 seed)

- ticket-036 seeded from the Phase 2 roadmap after a focused pre-ticket-036
  public-site readiness audit
  (`agent_reports/2026-06-12_pre-ticket-036_public-site-polish-readiness-audit.md`).
  Recommendation: proceed presentation-only; no export schema changes, no new
  public data fields. ticket-037+ intentionally not seeded in this pass.

## Queue Notes (2026-06-12, ticket-035 agent)

- ticket-035 refreshed README, `.env.example`, and `12_RUNTIME_CONFIG.md` for Phase 1
  MVP operator reality. All 123 golden tests pass; safety audit passes; public site
  builds 11 static pages. No runtime changes.
- ticket-036 (public-site presentation polish) is next per Phase 2 roadmap; seed
  JSON before implementation.

## Queue Notes (2026-06-12, ticket-035 seed)

- ticket-035 seeds Phase 2 operator docs refresh from the principal audit roadmap.
  Scope: README, `.env.example`, `docs/agents/12_RUNTIME_CONFIG.md` only.

## Queue Notes (2026-06-12, ticket-034 agent)

- ticket-034 made fixture-mode runs repo-clean: canonical export serialization,
  stable fixture timestamps, `source_count: 3` snapshot reconciliation, default
  improvement-ticket output under gitignored `data/tickets/`, and `data/` gitignore.
  All 123 golden tests pass; safety audit passes; repeated fixture runs leave
  git clean.
- ticket-035 (README/operator refresh) is next per Phase 2 roadmap; seed JSON
  before implementation.

## Queue Notes (2026-06-12, ticket-033 principal audit)

- ticket-033 completed pre-Phase-2 principal audit and Phase 2 roadmap
  (`agent_reports/2026-06-12_pre-phase-2_principal-audit.md`,
  `agent_reports/2026-06-12_phase-2_ticket-roadmap.md`). Phase 2 is GO.
  First must-fix: ticket-034 fixture-run artifact hygiene.
- All 119 golden tests pass; safety audit passes; fixture-mode MVP run completes
  all 12 steps but dirties the repo (non-deterministic export, timestamp churn,
  source_count drift, generated artifacts in `data/` and `tickets/`).

## Queue Notes (2026-06-12, ticket-032 agent)

- ticket-032 completed Phase 1 builder golden gate inventory: added
  `contradiction_detection` (GT07), `research_queue` (GT09), and
  `public_site_static_render` (GT12) to `REQUIRED_GOLDEN_AREAS`; documented
  nine optional golden modules in `INTENTIONALLY_OPTIONAL_GOLDEN_TESTS`.
  All 119 golden tests pass.
- Phase 1 MVP golden gate is complete. ticket-033 proposes a read-only
  pre-phase-2 principal audit before live Ollama or Phase 2 implementation.

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
ticket-080 (proposed) — Post-ticket-079 principal audit checkpoint
(ticket-059 OpenAI placeholder remains deferred)
```

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
- **Temporary:** after a ticket is `done`, merge its branch to `main` and push per `AGENTS.md` step 9 until the safety evaluator agent is live.
