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
| 80 | ticket-080 | done | Post-ticket-079 principal audit checkpoint | `phase-2/ticket-080-principal-audit-post-ticket-079` | `agent_reports/2026-06-13_principal-audit-post-ticket-079.md` |
| 81 | ticket-081 | done | Cursor build loop scratch evidence workflow cross-link | `phase-2/ticket-081-cursor-build-loop-scratch-workflow-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-081_cursor-build-loop-scratch-workflow-crosslink.md` |
| 82 | ticket-082 | done | Runtime config scratch evidence workflow cross-link | `phase-2/ticket-082-runtime-config-scratch-workflow-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-082_runtime-config-scratch-workflow-crosslink.md` |
| 83 | ticket-083 | done | Post-ticket-082 principal audit checkpoint | `phase-2/ticket-083-principal-audit-post-ticket-082` | `agent_reports/2026-06-13_principal-audit-post-ticket-082.md` |
| 84 | ticket-084 | done | Master repo alignment audit | `phase-2/ticket-084-master-alignment-audit` | `agent_reports/2026-06-13_master-alignment-audit-post-ticket-082.md` |
| 85 | ticket-085 | done | Domain-entry gate spec + Phase-3 ingestion readiness audit | `phase-2/ticket-085-domain-entry-gate-spec-and-ingestion-readiness` | `agent_reports/2026-06-13_phase-2_ticket-085_domain-entry-gate-spec-and-ingestion-readiness.md` |
| 86 | ticket-086 | done | Real manual source ingestion (Level-1) | phase-2/ticket-086-real-manual-source-ingestion | agent_reports/2026-06-13_phase-2_ticket-086_real-manual-source-ingestion.md |
| 87 | ticket-087 | done | Minimal domain pack loader: ontology + aliases | phase-2/ticket-087-minimal-domain-pack-loader | agent_reports/2026-06-13_phase-2_ticket-087_minimal-domain-pack-loader.md |
| 88 | ticket-088 | done | Real claim extraction proof from manual creativity source | phase-2/ticket-088-real-claim-extraction-manual-source | agent_reports/2026-06-13_phase-2_ticket-088_real-claim-extraction-manual-source.md |
| 89 | ticket-089 | done | Manual source concept linking proof (synthnote) | phase-2/ticket-089-manual-source-concept-linking | agent_reports/2026-06-13_phase-2_ticket-089_manual-source-concept-linking.md |
| 90 | ticket-090 | done | Manual source relationship proof (synthnote) | phase-2/ticket-090-manual-source-relationship-building | agent_reports/2026-06-13_phase-2_ticket-090_manual-source-relationship-building.md |
| 91 | ticket-091 | done | Manual source contradiction detection proof (synthnote) | phase-2/ticket-091-manual-source-contradiction-detection | agent_reports/2026-06-13_phase-2_ticket-091_manual-source-contradiction-detection.md |
| 92 | ticket-092 | done | Manual source end-to-end pipeline proof (synthnote) | phase-2/ticket-092-manual-source-pipeline-e2e | agent_reports/2026-06-13_phase-2_ticket-092_manual-source-pipeline-e2e.md |
| 93 | ticket-093 | done | Manual source pipeline idempotency proof (synthnote) | phase-2/ticket-093-manual-source-pipeline-idempotency | agent_reports/2026-06-13_phase-2_ticket-093_manual-source-pipeline-idempotency.md |
| 94 | ticket-094 | done | README manual synthnote operator spine quickstart | phase-2/ticket-094-readme-manual-synthnote-spine | agent_reports/2026-06-13_phase-2_ticket-094_readme-manual-synthnote-spine.md |
| 95 | ticket-095 | done | AGENTS.md manual synthnote spine cross-link | phase-2/ticket-095-agents-manual-synthnote-crosslink | agent_reports/2026-06-13_phase-2_ticket-095_agents-manual-synthnote-crosslink.md |
| 96 | ticket-096 | done | Operating protocol manual synthnote spine cross-link | phase-2/ticket-096-operating-protocol-manual-synthnote-crosslink | agent_reports/2026-06-13_phase-2_ticket-096_operating-protocol-manual-synthnote-crosslink.md |
| 97 | ticket-097 | done | Cursor build loop manual synthnote spine cross-link | phase-2/ticket-097-cursor-build-loop-manual-synthnote-crosslink | agent_reports/2026-06-13_phase-2_ticket-097_cursor-build-loop-manual-synthnote-crosslink.md |
| 98 | ticket-098 | done | Runtime config manual synthnote spine cross-link | phase-2/ticket-098-runtime-config-manual-synthnote-crosslink | agent_reports/2026-06-13_phase-2_ticket-098_runtime-config-manual-synthnote-crosslink.md |
| 99 | ticket-099 | done | Manual source score reconciliation proof (synthnote follow-up) | phase-2/ticket-099-manual-source-score-reconciliation | agent_reports/2026-06-13_phase-2_ticket-099_manual-source-score-reconciliation.md |
| 100 | ticket-100 | done | README manual synthnote reconcile-scores operator step | `phase-2/ticket-100-readme-manual-synthnote-reconcile-scores` | `agent_reports/2026-06-13_phase-2_ticket-100_readme-manual-synthnote-reconcile-scores.md` |
| 101 | ticket-101 | done | AGENTS.md manual synthnote reconcile-scores cross-link | `phase-2/ticket-101-agents-manual-synthnote-reconcile-scores-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-101_agents-manual-synthnote-reconcile-scores-crosslink.md` |
| 102 | ticket-102 | done | Operating protocol manual synthnote reconcile-scores cross-link | `phase-2/ticket-102-operating-protocol-manual-synthnote-reconcile-scores-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-102_operating-protocol-manual-synthnote-reconcile-scores-crosslink.md` |
| 103 | ticket-103 | done | Cursor build loop manual synthnote reconcile-scores cross-link | `phase-2/ticket-103-cursor-build-loop-manual-synthnote-reconcile-scores-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-103_cursor-build-loop-manual-synthnote-reconcile-scores-crosslink.md` |
| 104 | ticket-104 | done | Runtime config manual synthnote reconcile-scores cross-link | `phase-2/ticket-104-runtime-config-manual-synthnote-reconcile-scores-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-104_runtime-config-manual-synthnote-reconcile-scores-crosslink.md` |
| 105 | ticket-105 | done | Manual source pipeline e2e through reconcile-scores | `phase-2/ticket-105-manual-source-pipeline-e2e-reconcile-scores` | `agent_reports/2026-06-13_phase-2_ticket-105_manual-source-pipeline-e2e-reconcile-scores.md` |
| 106 | ticket-106 | done | Manual source pipeline idempotency through reconcile-scores | `phase-2/ticket-106-manual-source-pipeline-idempotency-reconcile-scores` | `agent_reports/2026-06-13_phase-2_ticket-106_manual-source-pipeline-idempotency-reconcile-scores.md` |
| 107 | ticket-107 | done | AGENTS.md manual synthnote pipeline proof test cross-link | `phase-2/ticket-107-agents-manual-synthnote-pipeline-proof-test-crosslink` | `agent_reports/2026-06-13_phase-2_ticket-107_agents-manual-synthnote-pipeline-proof-test-crosslink.md` |
| 108 | ticket-108 | done | Operating protocol manual synthnote pipeline proof test cross-link | `phase-2/ticket-108-operating-protocol-manual-synthnote-pipeline-proof-test-crosslink` | `agent_reports/2026-06-14_phase-2_ticket-108_operating-protocol-manual-synthnote-pipeline-proof-test-crosslink.md` |
| 109 | ticket-109 | done | Cursor build loop manual synthnote pipeline proof test cross-link | `phase-2/ticket-109-cursor-build-loop-manual-synthnote-pipeline-proof-test-crosslink` | `agent_reports/2026-06-14_phase-2_ticket-109_cursor-build-loop-manual-synthnote-pipeline-proof-test-crosslink.md` |
| 110 | ticket-110 | done | Runtime config manual synthnote pipeline proof test cross-link | `phase-2/ticket-110-runtime-config-manual-synthnote-pipeline-proof-test-crosslink` | `agent_reports/2026-06-14_phase-2_ticket-110_runtime-config-manual-synthnote-pipeline-proof-test-crosslink.md` |
| 111 | ticket-111 | superseded | README manual synthnote pipeline proof test cross-link | | (folded into NM-2 corrective doc pass) |
| 112 | ticket-112 | done | Arbitrary manual text live extraction fall-through | `phase-2/ticket-112-arbitrary-manual-live-fallthrough` | `agent_reports/2026-06-14_ticket-112_arbitrary-manual-live-fallthrough.md` |
| 113 | ticket-113 | done | Domain pack scoring.yaml loader proof (NM-5 preview) | `phase-2/ticket-113-domain-pack-scoring-loader` | `agent_reports/2026-06-14_ticket-113_domain-pack-scoring-loader.md` |
| 114 | ticket-114 | done | Domain pack evidence_types.yaml loader proof (NM-5 continuation) | `phase-2/ticket-114-domain-pack-evidence-types-loader` | `agent_reports/2026-06-14_ticket-114_domain-pack-evidence-types-loader.md` |
| 115 | ticket-115 | done | Domain pack claim_schema.yaml loader proof (NM-5 continuation) | `phase-2/ticket-115-domain-pack-claim-schema-loader` | `agent_reports/2026-06-14_ticket-115_domain-pack-claim-schema-loader.md` |
| 116 | ticket-116 | done | Domain pack source_preferences.yaml loader proof (NM-5 continuation) | `phase-2/ticket-116-domain-pack-source-preferences-loader` | `agent_reports/2026-06-14_ticket-116_domain-pack-source-preferences-loader.md` |
| 117 | ticket-117 | done | Domain pack card_templates.yaml loader proof (NM-5 continuation) | `phase-2/ticket-117-domain-pack-card-templates-loader` | `agent_reports/2026-06-14_ticket-117_domain-pack-card-templates-loader.md` |
| 118 | ticket-118 | done | Domain pack search_templates.yaml loader proof (NM-5 continuation) | `phase-2/ticket-118-domain-pack-search-templates-loader` | `agent_reports/2026-06-14_ticket-118_domain-pack-search-templates-loader.md` |
| 119 | ticket-119 | done | Domain pack safety_notes.yaml loader proof (NM-5 continuation) | `phase-2/ticket-119-domain-pack-safety-notes-loader` | `agent_reports/2026-06-14_ticket-119_domain-pack-safety-notes-loader.md` |
| 120 | ticket-120 | done | Domain pack domain.yaml loader proof (NM-5 completion) | `phase-2/ticket-120-domain-pack-domain-yaml-loader` | `agent_reports/2026-06-14_ticket-120_domain-pack-domain-yaml-loader.md` |
| 121 | ticket-121 | done | Wire claim_validator domain checks to pack domain.yaml | `phase-2/ticket-121-claim-validator-domain-pack` | `agent_reports/2026-06-14_ticket-121_claim-validator-domain-pack.md` |
| 122 | ticket-122 | done | Golden test overlap-domain claim label acceptance (mock) | `phase-2/ticket-122-golden-overlap-domain-claim` | `agent_reports/2026-06-14_ticket-122_golden-overlap-domain-claim.md` |
| 123 | ticket-123 | done | README operator quickstart NM-5 domain pack loading summary | `phase-2/ticket-123-readme-nm5-domain-pack-summary` | `agent_reports/2026-06-14_ticket-123_readme-nm5-domain-pack-summary.md` |
| 124 | ticket-124 | done | AGENTS.md cross-link README NM-5 domain pack section | `phase-2/ticket-124-agents-nm5-crosslink` | `agent_reports/2026-06-14_ticket-124_agents-nm5-crosslink.md` |
| 125 | ticket-125 | done | Domain pack spec cross-link README NM-5 runtime table | `phase-2/ticket-125-domain-pack-spec-nm5-crosslink` | `agent_reports/2026-06-14_ticket-125_domain-pack-spec-nm5-crosslink.md` |
| 126 | ticket-126 | done | Operator loop plan surfaces domain pack load health | `phase-2/ticket-126-operator-loop-domain-pack-health` | `agent_reports/2026-06-14_ticket-126_operator-loop-domain-pack-health.md` |
| 127 | ticket-127 | done | Arbitrary manual text live extraction fall-through (NM-4 recenter) | `phase-2/ticket-127-arbitrary-manual-live-fallthrough` | `agent_reports/2026-06-14_ticket-127_arbitrary-manual-live-fallthrough.md` |
| 128 | ticket-128 | done | Arbitrary manual live concept linking fall-through | `phase-2/ticket-128-arbitrary-manual-live-concept-linking` | `agent_reports/2026-06-14_ticket-128_arbitrary-manual-live-concept-linking.md` |
| 129 | ticket-129 | done | Arbitrary manual live relationship fall-through | `phase-2/ticket-129-arbitrary-manual-live-relationship-fallthrough` | `agent_reports/2026-06-14_ticket-129_arbitrary-manual-live-relationship-fallthrough.md` |
| 130 | ticket-130 | done | Arbitrary manual live contradiction fall-through | `phase-2/ticket-130-arbitrary-manual-live-contradiction-fallthrough` | `agent_reports/2026-06-14_ticket-130_arbitrary-manual-live-contradiction-fallthrough.md` |
| 131 | ticket-131 | done | NM-4 evidence DB score reconciliation operator proof | `phase-2/ticket-131-nm4-evidence-db-score-reconciliation` | `agent_reports/2026-06-14_ticket-131_nm-4-evidence-db-score-reconciliation.md` |
| 132 | ticket-132 | done | Operator loop NM-4 evidence DB spine status | `phase-2/ticket-132-operator-loop-nm4-evidence-spine-status` | `agent_reports/2026-06-14_ticket-132_operator-loop-nm4-evidence-spine-status.md` |
| 133 | ticket-133 | done | README NM-4 evidence DB operator quickstart | `phase-2/ticket-133-readme-nm4-evidence-operator-quickstart` | `agent_reports/2026-06-14_ticket-133_readme-nm4-evidence-operator-quickstart.md` |
| 134 | ticket-134 | done | Principal audit checkpoint post-ticket-133 | | `agent_reports/2026-06-14_principal-audit-post-ticket-133.md` |
| 135 | ticket-135 | done | README maturity table honest NM-4 relabel | `phase-2/ticket-135-readme-maturity-nm4-relabel` | `agent_reports/2026-06-14_ticket-135_readme-maturity-nm4-relabel.md` |
| 136 | ticket-136 | done | Canonical context maturity NM-4 alignment | `phase-2/ticket-136-canonical-context-maturity-nm4-alignment` | `agent_reports/2026-06-14_ticket-136_canonical-context-maturity-nm4-alignment.md` |
| 137 | ticket-137 | done | Principal audit checkpoint post-ticket-136 | | `agent_reports/2026-06-14_principal-audit-post-ticket-136.md` |
| 138 | ticket-138 | done | Source discovery stub CLI (Phase 3 entry) | `phase-2/ticket-138-source-discovery-stub-cli` | `agent_reports/2026-06-14_ticket-138_source-discovery-stub-cli.md` |
| 139 | ticket-139 | done | Source provider registry and OpenAlex discovery proof | `phase-2/ticket-139-source-provider-openalex-discovery` | `agent_reports/2026-06-14_ticket-139_source-provider-openalex-discovery.md` |
| 140 | ticket-140 | done | Research queue candidate ranking from discovered sources | `phase-2/ticket-140-discovered-source-queue-ranking` | `agent_reports/2026-06-14_ticket-140_discovered-source-queue-ranking.md` |
| 141 | ticket-141 | done | Enqueue discovered candidates to staging research queue | `phase-2/ticket-141-discovered-source-queue-enqueue` | `agent_reports/2026-06-14_ticket-141_discovered-source-queue-enqueue.md` |
| 142 | ticket-142 | done | Fetch staged candidate source from queue URL | `phase-2/ticket-142-staged-candidate-fetch` | `agent_reports/2026-06-14_ticket-142_staged-candidate-fetch.md` |
| 143 | ticket-143 | done | Ingest from staged fetch artifact path | `phase-2/ticket-143-staged-artifact-ingest` | `agent_reports/2026-06-14_ticket-143_staged-artifact-ingest.md` |
| 144 | ticket-144 | done | Extract claims from staged-ingested source (mock spine step) | `phase-2/ticket-144-staged-ingest-extract-spine` | `agent_reports/2026-06-14_ticket-144_staged-ingest-extract-spine.md` |
| 145 | ticket-145 | done | Link concepts on staged-ingested source (mock spine step) | `phase-2/ticket-145-staged-ingest-link-spine` | `agent_reports/2026-06-14_ticket-145_staged-ingest-link-spine.md` |
| 146 | ticket-146 | done | Build relationships on staged-ingested source (mock spine step) | `phase-2/ticket-146-staged-build-relationships-spine` | `agent_reports/2026-06-14_ticket-146_staged-build-relationships-spine.md` |
| 147 | ticket-147 | done | Detect contradictions on staged-ingested source (mock spine step) | `phase-2/ticket-147-staged-detect-contradictions-spine` | `agent_reports/2026-06-14_ticket-147_staged-detect-contradictions-spine.md` |
| 148 | ticket-148 | done | Reconcile scores on staged-ingested source (mock spine step) | `phase-2/ticket-148-staged-reconcile-scores-spine` | `agent_reports/2026-06-14_ticket-148_staged-reconcile-scores-spine.md` |
| 149 | ticket-149 | done | Generate run report on staged-ingested source (mock spine step) | `phase-2/ticket-149-staged-run-report-spine` | `agent_reports/2026-06-14_ticket-149_staged-run-report-spine.md` |
| 150 | ticket-150 | done | Principal audit checkpoint post-ticket-149 (staged Phase 3 spine completion) | `phase-2/ticket-150-principal-audit-post-ticket-149` | `agent_reports/2026-06-14_ticket-150_principal-audit-post-ticket-149.md` |
| 151 | ticket-151 | done | Staged Phase 3 full spine idempotency (mock) | `phase-2/ticket-151-staged-spine-idempotency` | `agent_reports/2026-06-14_ticket-151_staged-spine-idempotency.md` |
| 152 | ticket-152 | done | Second staged candidate fetch and ingest (mock, queue rank #2) | `phase-2/ticket-152-second-staged-candidate-spine` | `agent_reports/2026-06-14_ticket-152_second-staged-candidate-spine.md` |
| 153 | ticket-153 | done | Extract claims from second staged-ingested source (mock spine step) | `phase-2/ticket-153-second-staged-extract-spine` | `agent_reports/2026-06-14_ticket-153_second-staged-extract-spine.md` |
| 154 | ticket-154 | done | Link concepts on second staged-ingested source (mock spine step) | `phase-2/ticket-154-second-staged-link-spine` | `agent_reports/2026-06-14_ticket-154_second-staged-link-spine.md` |
| 155 | ticket-155 | done | Build relationships on second staged-ingested source (mock spine step) | `phase-2/ticket-155-second-staged-build-relationships-spine` | `agent_reports/2026-06-14_ticket-155_second-staged-build-relationships-spine.md` |
| 156 | ticket-156 | done | Detect contradictions on second staged-ingested source (mock spine step) | `phase-2/ticket-156-second-staged-detect-contradictions-spine` | `agent_reports/2026-06-14_ticket-156_second-staged-detect-contradictions-spine.md` |
| 157 | ticket-157 | done | Reconcile scores on second staged-ingested source (mock spine step) | `phase-2/ticket-157-second-staged-reconcile-scores-spine` | `agent_reports/2026-06-14_ticket-157_second-staged-reconcile-scores-spine.md` |
| 158 | ticket-158 | done | Generate run report on second staged-ingested source (mock spine step) | `phase-2/ticket-158-second-staged-run-report-spine` | `agent_reports/2026-06-14_ticket-158_second-staged-run-report-spine.md` |
| 159 | ticket-159 | superseded | Principal audit checkpoint post-ticket-158 (rank #2 staged Phase 3 spine completion) | | `agent_reports/2026-06-15_principal-audit-post-ticket-164.md` |
| 160 | ticket-160 | done | Second staged candidate full spine idempotency (mock) | `phase-2/ticket-160-second-staged-spine-idempotency` | `agent_reports/2026-06-14_ticket-160_second-staged-spine-idempotency.md` |
| 161 | ticket-161 | done | Dual-candidate staged Phase 3 idempotency on one DB (mock) | `phase-2/ticket-161-dual-candidate-staged-idempotency` | `agent_reports/2026-06-14_ticket-161_dual-candidate-staged-idempotency.md` |
| 162 | ticket-162 | done | Fixture-mode staged research run orchestration spine (mock) | `phase-2/ticket-162-fixture-mode-staged-run-spine` | `agent_reports/2026-06-14_ticket-162_fixture-mode-staged-run-spine.md` |
| 163 | ticket-163 | done | Staged fixture-mode run orchestrator idempotency (mock) | `phase-2/ticket-163-staged-run-orchestrator-idempotency` | `agent_reports/2026-06-14_ticket-163_staged-run-orchestrator-idempotency.md` |
| 164 | ticket-164 | done | README operator quickstart for staged Phase 3 --staged-spine | `phase-2/ticket-164-readme-staged-spine-quickstart` | `agent_reports/2026-06-14_ticket-164_readme-staged-spine-quickstart.md` |
| 165 | ticket-165 | done | README maturity table Phase 3 staged mock spine status | `phase-2/ticket-165-readme-phase3-staged-maturity` | `agent_reports/2026-06-15_ticket-165_readme-phase3-staged-maturity.md` |
| 166 | ticket-166 | done | Safe autocycle command for audit + run-next-ticket loop | `phase-2/ticket-166-safe-autocycle` | `agent_reports/2026-06-15_ticket-166_safe-autocycle.md` |
| 167 | ticket-167 | done | Live staged fetch validation proof | `phase-2/ticket-167-live-staged-fetch-validation` | `agent_reports/2026-06-15_ticket-167_live-staged-fetch-validation.md` |
| 168 | ticket-168 | done | Live staged ingest validation proof (opt-in network) | `phase-2/ticket-168-live-staged-ingest-validation` | `agent_reports/2026-06-15_ticket-168_live-staged-ingest-validation.md` |
| 169 | ticket-169 | done | README operator quickstart for live staged spine opt-in proofs | `phase-2/ticket-169-readme-live-staged-opt-in` | `agent_reports/2026-06-15_ticket-169_readme-live-staged-opt-in.md` |
| 170 | ticket-170 | done | AGENTS.md cross-link live staged opt-in operator proofs | `phase-2/ticket-170-agents-live-staged-opt-in` | `agent_reports/2026-06-15_ticket-170_agents-live-staged-opt-in.md` |
| 171 | ticket-171 | done | Pre-ticket audit: live staged extract mock-fixture spine | `phase-2/ticket-171-pre-ticket-live-staged-extract-mock-spine-audit` | `agent_reports/2026-06-15_ticket-171_pre-ticket-live-staged-extract-mock-spine.md` |
| 172 | ticket-172 | done | Live staged extract mock-fixture spine (opt-in network) | `phase-2/ticket-172-live-staged-extract-mock-spine` | `agent_reports/2026-06-15_ticket-172_live-staged-extract-mock-spine.md` |
| 173 | ticket-173 | done | README and AGENTS.md live staged extract opt-in proof docs | `phase-2/ticket-173-live-staged-extract-opt-in-docs` | `agent_reports/2026-06-15_ticket-173_live-staged-extract-opt-in-docs.md` |
| 174 | ticket-174 | done | Pre-ticket audit: live staged link mock-fixture spine | `phase-2/ticket-174-pre-ticket-live-staged-link-mock-spine-audit` | `agent_reports/2026-06-15_ticket-174_pre-ticket-live-staged-link-mock-spine.md` |
| 175 | ticket-175 | done | Live staged link mock-fixture spine (opt-in network) | `phase-2/ticket-175-live-staged-link-mock-spine` | `agent_reports/2026-06-15_ticket-175_live-staged-link-mock-spine.md` |
| 176 | ticket-176 | done | README and AGENTS.md live staged link opt-in proof docs | `phase-2/ticket-176-live-staged-link-opt-in-docs` | `agent_reports/2026-06-15_ticket-176_live-staged-link-opt-in-docs.md` |
| 177 | ticket-177 | done | Pre-ticket audit: live staged build-relationships mock spine | `phase-2/ticket-177-pre-ticket-live-staged-build-mock-spine-audit` | `agent_reports/2026-06-15_ticket-177_pre-ticket-live-staged-build-mock-spine.md` |
| 178 | ticket-178 | done | Live staged build mock-fixture spine (opt-in network) | `phase-2/ticket-178-live-staged-build-mock-spine` | `agent_reports/2026-06-15_ticket-178_live-staged-build-mock-spine.md` |
| 179 | ticket-179 | done | README and AGENTS.md live staged build opt-in proof docs | `phase-2/ticket-179-live-staged-build-opt-in-docs` | `agent_reports/2026-06-15_ticket-179_live-staged-build-opt-in-docs.md` |
| 180 | ticket-180 | done | Pre-ticket audit: live staged detect-contradictions mock spine | `phase-2/ticket-180-pre-ticket-live-staged-detect-mock-spine-audit` | `agent_reports/2026-06-15_ticket-180_pre-ticket-live-staged-detect-mock-spine.md` |
| 181 | ticket-181 | done | Live staged detect mock-fixture spine (opt-in network) | `phase-2/ticket-181-live-staged-detect-mock-spine` | `agent_reports/2026-06-15_ticket-181_live-staged-detect-mock-spine.md` |
| 182 | ticket-182 | done | README and AGENTS.md live staged detect opt-in proof docs | `phase-2/ticket-182-live-staged-detect-opt-in-docs` | `agent_reports/2026-06-15_ticket-182_live-staged-detect-opt-in-docs.md` |
| 183 | ticket-183 | done | Pre-ticket audit: live staged reconcile-scores mock spine | `phase-2/ticket-183-pre-ticket-live-staged-reconcile-mock-spine-audit` | `agent_reports/2026-06-15_ticket-183_pre-ticket-live-staged-reconcile-mock-spine.md` |
| 184 | ticket-184 | done | Live staged reconcile-scores spine (opt-in network) | `phase-2/ticket-184-live-staged-reconcile-mock-spine` | `agent_reports/2026-06-15_ticket-184_live-staged-reconcile-mock-spine.md` |
| 185 | ticket-185 | done | README and AGENTS.md live staged reconcile opt-in proof docs | `phase-2/ticket-185-live-staged-reconcile-opt-in-docs` | `agent_reports/2026-06-15_ticket-185_live-staged-reconcile-opt-in-docs.md` |
| 186 | ticket-186 | done | Pre-ticket audit: live staged run-report mock spine | `phase-2/ticket-186-pre-ticket-live-staged-report-mock-spine-audit` | `agent_reports/2026-06-15_ticket-186_pre-ticket-live-staged-report-mock-spine.md` |
| 187 | ticket-187 | done | Live staged generate-run-report spine (opt-in network) | `phase-2/ticket-187-live-staged-report-mock-spine` | `agent_reports/2026-06-15_ticket-187_live-staged-report-mock-spine.md` |
| 188 | ticket-188 | done | README and AGENTS.md live staged report opt-in proof docs | `phase-2/ticket-188-live-staged-report-opt-in-docs` | `agent_reports/2026-06-15_ticket-188_live-staged-report-opt-in-docs.md` |
| 189 | ticket-189 | done | Pre-ticket audit: live staged rank-2 candidate mock spine | `phase-2/ticket-189-pre-ticket-live-staged-rank2-mock-spine-audit` | `agent_reports/2026-06-15_ticket-189_pre-ticket-live-staged-rank2-mock-spine.md` |
| 190 | ticket-190 | done | Live staged rank-2 candidate mock spine (opt-in network) | `phase-2/ticket-190-live-staged-rank2-mock-spine` | `agent_reports/2026-06-15_ticket-190_live-staged-rank2-mock-spine.md` |
| 191 | ticket-191 | done | README and AGENTS.md live staged rank-2 opt-in proof docs | `phase-2/ticket-191-live-staged-rank2-opt-in-docs` | `agent_reports/2026-06-15_ticket-191_live-staged-rank2-opt-in-docs.md` |
| 192 | ticket-192 | done | Pre-ticket audit: single-command live staged orchestrator proof | `phase-2/ticket-192-pre-ticket-live-staged-orchestrator-audit` | `agent_reports/2026-06-15_ticket-192_pre-ticket-live-staged-orchestrator-audit.md` |
| 193 | ticket-193 | done | Live staged orchestrator mock spine (opt-in network) | `phase-2/ticket-193-live-staged-orchestrator-mock-spine` | `agent_reports/2026-06-15_ticket-193_live-staged-orchestrator-mock-spine.md` |
| 194 | ticket-194 | done | README and AGENTS.md live staged orchestrator opt-in proof docs | `phase-2/ticket-194-live-staged-orchestrator-opt-in-docs` | `agent_reports/2026-06-15_ticket-194_live-staged-orchestrator-opt-in-docs.md` |
| 195 | ticket-195 | done | Fix live staged pytest candidate ordering column | `phase-2/ticket-195-live-staged-candidate-ordering-fix` | `agent_reports/2026-06-15_ticket-195_live-staged-candidate-ordering-fix.md` |
| 196 | ticket-196 | done | Shared live staged candidate query test helper | `phase-2/ticket-196-live-staged-candidate-helper` | `agent_reports/2026-06-15_ticket-196_live-staged-candidate-helper.md` |
| 197 | ticket-197 | done | Shared staged domain opposing-context seed test helper | `phase-2/ticket-197-staged-domain-seed-helper` | `agent_reports/2026-06-15_ticket-197_staged-domain-seed-helper.md` |
| 198 | ticket-198 | done | Principal audit post-ticket-197 staged test hygiene checkpoint | | `agent_reports/2026-06-15_principal-audit-post-ticket-197.md` |
| 199 | ticket-199 | done | README and AGENTS live staged operator verification runbook | `phase-2/ticket-199-live-staged-operator-verification-runbook` | `agent_reports/2026-06-15_ticket-199_live-staged-operator-verification-runbook.md` |
| 200 | ticket-200 | done | Pre-ticket audit: research run without fixture-mode | | `agent_reports/2026-06-15_pre-ticket-200_research-run-non-fixture-audit.md` |
| 201 | ticket-201 | done | Live staged research run CLI entry without fixture-mode flag | `phase-2/ticket-201-live-staged-run-without-fixture-mode` | `agent_reports/2026-06-15_ticket-201_live-staged-run-without-fixture-mode.md` |
| 202 | ticket-202 | done | Principal audit post-ticket-201 research run contract checkpoint | | `agent_reports/2026-06-15_principal-audit-post-ticket-201.md` |
| 203 | ticket-203 | done | Pre-ticket audit: live LLM on staged research run spine | | `agent_reports/2026-06-15_pre-ticket-203_live-llm-staged-run-audit.md` |
| 204 | ticket-204 | done | Live staged extract live LLM opt-in proof (per-step) | `phase-2/ticket-204-live-staged-extract-live-llm-spine` | `agent_reports/2026-06-15_ticket-204_live-staged-extract-live-llm-spine.md` |
| 205 | ticket-205 | done | README and AGENTS live staged extract live LLM operator docs | `phase-2/ticket-205-live-staged-extract-live-llm-docs` | `agent_reports/2026-06-15_ticket-205_live-staged-extract-live-llm-docs.md` |
| 206 | ticket-206 | done | Principal audit post-ticket-205 staged live extract checkpoint | | `agent_reports/2026-06-15_ticket-206_principal-audit-post-ticket-205.md` |
| 207 | ticket-207 | done | Pre-ticket audit: live staged link on staged spine (per-step) | `phase-2/ticket-207-pre-ticket-live-staged-link-audit` | `agent_reports/2026-06-15_ticket-207_pre-ticket-live-staged-link-audit.md` |
| 208 | ticket-208 | done | Live staged link live LLM opt-in proof (per-step) | `phase-2/ticket-208-live-staged-link-live-llm-spine` | `agent_reports/2026-06-15_ticket-208_live-staged-link-live-llm-spine.md` |
| 209 | ticket-209 | done | README and AGENTS live staged link live LLM operator docs | `phase-2/ticket-209-live-staged-link-live-llm-docs` | `agent_reports/2026-06-15_ticket-209_live-staged-link-live-llm-docs.md` |
| 210 | ticket-210 | done | Principal audit post-ticket-209 staged live link checkpoint | | `agent_reports/2026-06-15_ticket-210_principal-audit-post-ticket-209.md` |
| 211 | ticket-211 | done | Pre-ticket audit: live staged build on staged spine (per-step) | | `agent_reports/2026-06-15_ticket-211_pre-ticket-live-staged-build-audit.md` |
| 212 | ticket-212 | done | Live staged build live LLM opt-in proof (per-step) | `phase-2/ticket-212-live-staged-build-live-llm-spine` | `agent_reports/2026-06-15_ticket-212_live-staged-build-live-llm-spine.md` |
| 213 | ticket-213 | done | Local env profile support for live staged operator runs | `phase-2/ticket-213-local-env-profile-support` | `agent_reports/2026-06-15_ticket-213_local-env-profile-support.md` |
| 214 | ticket-214 | done | README and AGENTS live staged build live LLM operator docs | `phase-2/ticket-214-live-staged-build-live-llm-docs` | `agent_reports/2026-06-15_ticket-214_live-staged-build-live-llm-docs.md` |
| 215 | ticket-215 | done | Principal audit post-ticket-213 staged live build checkpoint | | `agent_reports/2026-06-15_ticket-215_principal-audit-post-ticket-213.md` |
| 216 | ticket-216 | done | Pre-ticket audit: live staged detect on staged spine (per-step) | `phase-2/ticket-216-pre-ticket-live-staged-detect-audit` | `agent_reports/2026-06-15_ticket-216_pre-ticket-live-staged-detect-audit.md` |
| 217 | ticket-217 | done | Live staged detect live LLM opt-in proof (per-step) | `phase-2/ticket-217-live-staged-detect-live-llm-spine` | `agent_reports/2026-06-15_ticket-217_live-staged-detect-live-llm-spine.md` |
| 218 | ticket-218 | done | README and AGENTS live staged detect live LLM operator docs | `phase-2/ticket-218-live-staged-detect-live-llm-docs` | `agent_reports/2026-06-15_ticket-218_live-staged-detect-live-llm-docs.md` |
| 219 | ticket-219 | done | Principal audit post-ticket-217 staged live detect checkpoint | | `agent_reports/2026-06-15_ticket-219_principal-audit-post-ticket-217.md` |
| 220 | ticket-220 | done | .env.example and runtime config live staged detect live LLM gate | `phase-2/ticket-220-live-staged-detect-env-profile` | `agent_reports/2026-06-15_ticket-220_live-staged-detect-env-profile.md` |
| 221 | ticket-221 | done | Pre-ticket audit: live staged reconcile on staged spine (per-step) | `phase-2/ticket-221-pre-ticket-live-staged-reconcile-audit` | `agent_reports/2026-06-15_ticket-221_pre-ticket-live-staged-reconcile-audit.md` |
| 222 | ticket-222 | done | Pre-ticket audit: live staged generate-run-report on staged spine (per-step) | `phase-2/ticket-222-pre-ticket-live-staged-report-audit` | `agent_reports/2026-06-15_ticket-222_pre-ticket-live-staged-report-audit.md` |
| 223 | ticket-223 | done | Principal audit post-ticket-222 staged spine LLM surface closure | | `agent_reports/2026-06-15_ticket-223_principal-audit-post-ticket-222.md` |
| 224 | ticket-224 | done | README and AGENTS staged reconcile and report deterministic boundary docs | `phase-2/ticket-224-staged-reconcile-report-deterministic-docs` | `agent_reports/2026-06-15_ticket-224_staged-reconcile-report-deterministic-docs.md` |
| 225 | ticket-225 | done | Runtime config staged reconcile and report network-only gate docs | `phase-2/ticket-225-runtime-config-staged-reconcile-report-gates` | `agent_reports/2026-06-15_ticket-225_runtime-config-staged-reconcile-report-gates.md` |
| 226 | ticket-226 | done | README operator one-time live orchestrator checklist post-LLM-closure refresh | `phase-2/ticket-226-orchestrator-checklist-llm-closure-refresh` | `agent_reports/2026-06-15_ticket-226_orchestrator-checklist-llm-closure-refresh.md` |
| 227 | ticket-227 | done | Principal audit post-ticket-226 staged docs closure checkpoint | | `agent_reports/2026-06-15_ticket-227_principal-audit-post-ticket-226.md` |
| 228 | ticket-228 | done | Pre-ticket audit: rank-2 staged per-step live Ollama on staged spine | `phase-2/ticket-228-pre-ticket-rank-2-staged-live-llm-audit` | `agent_reports/2026-06-15_ticket-228_pre-ticket-rank-2-staged-live-llm-audit.md` |
| 229 | ticket-229 | done | Rank-2 staged source and chunk heuristic for live LLM fallthrough eligibility | `phase-2/ticket-229-rank-2-staged-spine-heuristics` | `agent_reports/2026-06-15_ticket-229_rank-2-staged-spine-heuristics.md` |
| 230 | ticket-230 | done | Live staged rank-2 extract live LLM opt-in proof (per-step) | `phase-3/ticket-230-rank2-extract-live-llm-spine` | `agent_reports/2026-06-15_ticket-230_live-staged-rank2-extract-live-llm-spine.md` |
| 236 | ticket-236 | done | Live staged rank-2 link live LLM opt-in proof (per-step) | `phase-3/ticket-236-rank2-link-live-llm-spine` | `agent_reports/2026-06-15_ticket-236_live-staged-rank2-link-live-llm-spine.md` |
| 237 | ticket-237 | done | Live staged rank-2 build live LLM opt-in proof (per-step) | `phase-3/ticket-237-rank2-build-live-llm-spine` | `agent_reports/2026-06-16_ticket-237_live-staged-rank2-build-live-llm-spine.md` |
| 238 | ticket-238 | done | Live staged rank-2 detect live LLM opt-in proof (per-step) | `phase-3/ticket-238-rank2-detect-live-llm-spine` | `agent_reports/2026-06-16_ticket-238_live-staged-rank2-detect-live-llm-spine.md` |
| 239 | ticket-239 | done | Principal audit post-ticket-238 rank-2 live LLM closure checkpoint | `phase-3/ticket-239-principal-audit-post-ticket-238` | `agent_reports/2026-06-16_ticket-239_principal-audit-post-ticket-238.md` |
| 240 | ticket-240 | done | README operator rank-2 per-step live LLM closure checklist | `phase-3/ticket-240-readme-rank2-live-closure-checklist` | `agent_reports/2026-06-16_ticket-240_readme-rank2-live-closure-checklist.md` |
| 241 | ticket-241 | done | Runtime config rank-2 live Ollama closure operator summary | `phase-3/ticket-241-runtime-config-rank2-live-closure` | `agent_reports/2026-06-16_ticket-241_runtime-config-rank2-live-closure.md` |
| 242 | ticket-242 | done | AGENTS runtime config rank-2 live closure cross-reference | `phase-3/ticket-242-agents-runtime-config-rank2-closure` | `agent_reports/2026-06-16_ticket-242_agents-runtime-config-rank2-closure.md` |
| 243 | ticket-243 | done | Detect seed mock isolation for live Ollama operator proofs | `phase-3/ticket-243-detect-seed-mock-isolation` | `agent_reports/2026-06-16_phase-3_ticket-243_detect-seed-mock-isolation.md` |
| 244 | ticket-244 | done | Principal audit post-ticket-243 detect seed mock isolation | `main` | `agent_reports/2026-06-16_principal-audit-post-ticket-243.md` |
| 245 | ticket-245 | done | README rank-2 checklist detect seed isolation note | `phase-3/ticket-245-readme-detect-seed-note` | `agent_reports/2026-06-16_phase-3_ticket-245_readme-detect-seed-note.md` |
| 246 | ticket-246 | done | AGENTS detect seed mock isolation cross-reference | `phase-3/ticket-246-agents-detect-seed-note` | `agent_reports/2026-06-16_phase-3_ticket-246_agents-detect-seed-note.md` |
| 247 | ticket-247 | done | Runtime config detect seed mock isolation cross-reference | `phase-3/ticket-247-runtime-config-detect-seed-note` | `agent_reports/2026-06-16_phase-3_ticket-247_runtime-config-detect-seed-note.md` |
| 248 | ticket-248 | done | README maturity tier detect seed doc triangle closure | `phase-3/ticket-248-readme-maturity-detect-seed-triangle` | `agent_reports/2026-06-16_phase-3_ticket-248_readme-maturity-detect-seed-triangle.md` |
| 249 | ticket-249 | done | Operator proof report addendum post detect seed doc triangle | `phase-3/ticket-249-operator-proof-addendum` | `agent_reports/2026-06-16_phase-3_ticket-249_operator-proof-addendum.md` |
| 250 | ticket-250 | done | Principal audit post-ticket-249 detect seed doc closure checkpoint | `main` @ `c964ef7` | `agent_reports/2026-06-16_principal-audit-post-ticket-249.md` |
| 251 | ticket-251 | done | Rank-2 staged candidate heuristic scan for catalog drift resilience | `phase-3/ticket-251-rank-2-candidate-heuristic-scan` | `agent_reports/2026-06-16_phase-3_ticket-251_rank-2-candidate-heuristic-scan.md` |
| 252 | ticket-252 | done | Scratch evidence review gate in operator autocycle plan | `phase-3/ticket-252-operator-autocycle-scratch-evidence-gate` | `agent_reports/2026-06-16_phase-3_ticket-252_operator-autocycle-scratch-evidence-gate.md` |
| 253 | ticket-253 | done | Runbook autocycle scratch evidence review operator note | `phase-3/ticket-253-runbook-autocycle-scratch-note` | `agent_reports/2026-06-16_phase-3_ticket-253_runbook-autocycle-scratch-note.md` |
| 254 | ticket-254 | done | Configurable rank-2 staged candidate scan window env | `phase-3/ticket-254-rank-2-scan-window-env` | `agent_reports/2026-06-16_phase-3_ticket-254_rank-2-scan-window-env.md` |
| 255 | ticket-255 | done | Principal audit post-ticket-254 staged spine env hardening checkpoint | `main` | `agent_reports/2026-06-16_principal-audit-post-ticket-254.md` |
| 256 | ticket-256 | done | Operator loop plan surfaces staged rank-2 scan window config | `phase-3/ticket-256-operator-loop-rank2-scan-config` | `agent_reports/2026-06-16_phase-3_ticket-256_operator-loop-rank2-scan-config.md` |
| 257 | ticket-257 | done | Operator autocycle plan surfaces staged rank-2 scan window config | `phase-3/ticket-257-operator-autocycle-rank2-scan-config` | `agent_reports/2026-06-16_phase-3_ticket-257_operator-autocycle-rank2-scan-config.md` |
| 258 | ticket-258 | proposed | CLI staged spine rank-2 candidate selection unit test | | |
| 231 | ticket-231 | done | Principal audit post-ticket-229 rank-2 live LLM prerequisite checkpoint | | `agent_reports/2026-06-15_ticket-231_principal-audit-post-ticket-229.md` |
| 232 | ticket-232 | done | Pre-ticket audit: rank-2 staged extract live LLM (ticket-230 scope echo) | `phase-3/ticket-232-pre-ticket-230-echo-audit` | `agent_reports/2026-06-15_pre-ticket-230_rank-2-staged-extract-live-llm-audit.md` |
| 233 | ticket-233 | done | Live OpenAlex source acquisition resilience | `phase-3/ticket-233-openalex-fetch-resilience` | `agent_reports/2026-06-15_phase-3_ticket-233_openalex-fetch-resilience.md` |
| 234 | ticket-234 | done | Decouple live staged mock-spine proofs from fixture phrases | `phase-3/ticket-234-live-staged-proof-layers` | `agent_reports/2026-06-15_phase-3_ticket-234_live-staged-proof-layers.md` |
| 235 | ticket-235 | done | README operator proof-layer runbook (unsuitable_live_artifact) | `phase-3/ticket-235-proof-layer-runbook` | `agent_reports/2026-06-15_phase-3_ticket-235_proof-layer-runbook.md` |

## Queue Notes (2026-06-14, corrective NM-1/NM-2/NM-3 integration)

- Merged `phase-2/corrective-nm1-nm2-nm3-audit-driven` to `main` @ `4a62c99`.
- Post-merge: 140 golden, 394 pytest, safety audit pass.
- Ollama `qwen2.5:7b` available; no model pull required.
- ticket-111 superseded; ticket-112 seeded as NM-4.
- Pre-ticket audit GO for ticket-112.

## Queue Notes (2026-06-13, ticket-085 ingestion readiness audit)

- **GO for ticket-086.** Ingestion spine already real and GT01-proven: `research ingest` persists source+chunks deterministically, idempotent by checksum, survives restart. Stubs (`source_discovery`/`fetcher.fetch_source`/`candidate_ranker`) are NOT on the manual path.
- Only real gap: `source_type` hardcoded `"fixture"`; no `--source-title`/`--source-type`; no manual-source dir convention.
- G1 PASS (one small gap); G2 deferred past 086 (mock extraction is canned; real-text floor needs live Qwen or seeded fixture); G3 not needed until ticket-087; G4 PASS (private DB under gitignored data/, allowlist export, local_path is a forbidden field); G5 PASS (human-gated promotion); G6 satisfied by this report (no separate pre-ticket audit needed at scoped size — no migration/validator/export change).
- First source format: local `.txt`/`.md` (PDF/URL deferred). Source location: gitignored `data/sources/manual/creativity/` (no private sources committed).
- ticket-086 scope: extend `ingest` with `--source-type`/`--source-title`, label real sources `manual_text`, prove determinism + no-export-leak + no-model-authority + unit tests. ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-13, ticket-084 master alignment audit)

- Read-only repo-wide alignment audit (docs/specs/CLI/tests/CI/domain pack).
- Verdict: engine is **general RGE MVP**, mock/fixture-proven and release-healthy; **not** yet in real domain research. `source_discovery`/`fetcher`/`candidate_ranker` remain `NotImplementedError` (Phase 3); only `ontology.yaml` labels are consumed from the creativity pack; scratch DB empty.
- Drift: tickets 068-082 over-invest in operator/scratch/doc infrastructure relative to real research content. No code changes; no domain seed; validators/tests unchanged.
- MVP redefined as two tiers: MVP-Engine (done, mock) vs MVP-Research (not done: real source -> real accepted claim -> real public card).
- Recommended next sequence (each gated): ticket-085 (domain-entry gate spec + Phase-3 ingestion readiness audit, low risk, no pre-ticket audit), ticket-086 (real manual Level-1 source ingestion, medium risk, pre-ticket audit required), ticket-087 (minimal domain pack loader for ontology+aliases, medium risk, pre-ticket audit required).
- Private local probe artifact (`agent_reports/2026-06-13_scratch-evidence-review-probe.md`) left untracked.

## Queue Notes (2026-06-13, ticket-083 principal audit checkpoint)

- Cadence satisfied: post-ticket-082 principal audit landed on `main` (tickets 080–082 since post-079).
- Local mock-only gates green: 140 golden, safety audit pass.
- GO for ticket-084 (read-only master alignment audit). ticket-059 OpenAI remains deferred.

## Queue Notes (2026-06-13, ticket-083 seed)

- Principal audit required: 3 done tickets (080–082) since post-079 checkpoint.

## Queue Notes (2026-06-13, ticket-082 agent)

- 12_RUNTIME_CONFIG.md Database and artifact paths links runbook scratch evidence checklist.

## Queue Notes (2026-06-13, ticket-081 agent)

- 04_CURSOR_BUILD_LOOP.md Builder Agent Instructions links runbook scratch evidence checklist.

## Queue Notes (2026-06-13, ticket-080 principal audit)

- Cadence satisfied: 3 done tickets (077–079) since post-076 checkpoint.
- GO for ticket-081 (Cursor build loop doc cross-link).

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
ticket-258 (proposed) — CLI staged spine rank-2 candidate selection unit test
(ticket-059 OpenAI placeholder remains deferred)
```

## Queue Notes (2026-06-16, ticket-257 operator autocycle rank-2 scan config)

- `run_autocycle --mode plan` JSON includes `staged_rank2_scan_max` (top-level + per-cycle)
- ticket-258 seeded: CLI orchestrator rank-2 selection unit test

## Queue Notes (2026-06-16, ticket-256 operator loop rank-2 scan config)

- `build_operator_plan` JSON includes `staged_rank2_scan_max` from `load_config`
- ticket-257 seeded: operator autocycle plan parity

## Queue Notes (2026-06-16, ticket-255 principal audit post-ticket-254)

- Cadence reset after 252–254; mock golden gate green (142 golden, 681 pytest)
- ticket-256 seeded: operator loop plan exposes `staged_rank2_scan_max`

## Queue Notes (2026-06-16, ticket-254 rank-2 scan window env)

- `RGE_STAGED_RANK2_SCAN_MAX` env (default 10, bounded 1–50) for rank-2 title heuristic scan
- ticket-255 seeded: principal audit (cadence after 252–254)

## Queue Notes (2026-06-16, ticket-253 runbook autocycle scratch note)

- `14_LIVE_PROBE_OPERATOR_RUNBOOK.md`: autocycle scratch gate + drift carve-out documented
- ticket-254 seeded: rank-2 scan window env (product hardening)

## Queue Notes (2026-06-16, ticket-252 autocycle scratch evidence gate)

- Autocycle surfaces run_scratch_evidence_review before drift_warning when scratch ready
- ticket-253 seeded: runbook operator note

## Queue Notes (2026-06-16, ticket-251 rank-2 candidate heuristic scan)

- `staged_candidate_selection.py`: top-N rank-2 title scan after rank-1; shared by live pytest + orchestrator
- ticket-252 seeded: scratch evidence autocycle gate

## Queue Notes (2026-06-16, ticket-250 principal audit + ticket-251 selection)

- Principal audit post-ticket-249 committed (`c964ef7`); cadence reset
- ticket-251 ready: rank-2 top-N heuristic candidate scan (product hardening; pre-ticket audit GO)
- Explicit NO-GO: orchestrator live LLM, reconcile/report live LLM, CI live_network, default-graph live proofs

## Queue Notes (2026-06-16, ticket-249 operator proof addendum)

- Operator proof report addendum: ticket-243 seed fix + doc triangle 245–248; catalog drift unchanged
- ticket-250 seeded: principal audit (cadence threshold after 247–249)

## Queue Notes (2026-06-16, ticket-248 README maturity detect seed triangle)

- Arbitrary-source pipeline maturity row notes detect seed doc triangle (245–247)
- ticket-249 seeded: operator proof report addendum

## Queue Notes (2026-06-16, ticket-247 runtime config detect seed note)

- `12_RUNTIME_CONFIG.md` seed mock isolation cross-link completes doc triangle (245/246/247)
- ticket-248 seeded: README maturity tier closure row

## Queue Notes (2026-06-16, ticket-246 AGENTS detect seed note)

- AGENTS rank-1/rank-2 detect sections note seed mock isolation (ticket-243)
- Closure checklist cross-links README Domain seed note (ticket-245)
- ticket-247 seeded: runtime config cross-reference

## Queue Notes (2026-06-16, ticket-245 README detect seed note)

- README rank-2 checklist documents GT7 seed mock isolation (ticket-243)
- principal_audit_gate latest checkpoint fix (max ticket number)
- ticket-246 seeded: AGENTS cross-reference

## Queue Notes (2026-06-16, ticket-244 principal audit post-ticket-243)

- Cadence reset; mock gate green (142 golden, 668 pytest)
- Rank-2 docs triangle + ticket-243 seed fix verified
- ticket-245 seeded: README detect seed isolation operator note

## Queue Notes (2026-06-16, ticket-243 detect seed mock isolation)

- `seed_domain_opposing_context` forces mock LLM for GT7 seed spine under live operator env
- Regression tests in rank-1/rank-2 live detect spine modules
- ticket-244 seeded: principal audit (cadence after 241/242/243)

## Queue Notes (2026-06-16, ticket-242 AGENTS runtime config cross-link)

- AGENTS rank-2 closure section links `12_RUNTIME_CONFIG.md` staged operator env profile
- Operator proof report: `agent_reports/2026-06-16_operator-proof-rank2-live-ollama-checklist.md`
- ticket-243 seeded: detect seed mock isolation (operator proof finding)

## Queue Notes (2026-06-16, ticket-241 runtime config rank-2 closure)

- `12_RUNTIME_CONFIG.md` rank-2 closure at detect + README checklist cross-link
- Both-ranks reconcile/report deterministic boundary explicit
- ticket-242 seeded: AGENTS runtime config cross-reference

- README **One-time rank-2 per-step live Ollama verification** section (shared env, gate table, checklist)
- Maturity tier + AGENTS cross-reference updated
- ticket-241 seeded: runtime config closure cross-link

## Queue Notes (2026-06-16, ticket-239 principal audit)

- Rank-2 per-step live Ollama **closed** at detect (230/236/237/238)
- Cadence reset; reconcile/report remain deterministic NO-GO for LLM
- Committed prior `principal-audit-post-ticket-235.md` for gate continuity
- ticket-240 seeded: README rank-2 live closure checklist

## Queue Notes (2026-06-16, ticket-238 rank-2 detect live LLM)

- `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1` + `--live-staged-rank2-detect-fallthrough`
- Requires `seed_domain_opposing_context` before live discover
- Mock upstream through build: `staged_fetch_second_candidate_*` fixtures
- **Rank-2 per-step live Ollama surface closed** (230/236/237/238)
- ticket-239 seeded: principal audit checkpoint

## Queue Notes (2026-06-16, ticket-237 rank-2 build live LLM)

- `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1` + `--live-staged-rank2-build-fallthrough`
- Mock extract + mock link upstream: `staged_fetch_second_candidate_extract_claims.json`,
  `staged_fetch_second_candidate_link_concepts.json`
- ticket-238 seeded: rank-2 detect live LLM (mirror ticket-217)

## Queue Notes (2026-06-16, ticket-236 rank-2 link live LLM)

- `RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM=1` + `--live-staged-rank2-link-fallthrough`
- Mock extract upstream: `staged_fetch_second_candidate_extract_claims.json`
- ticket-237 seeded: rank-2 build live LLM (mirror ticket-212)

## Queue Notes (2026-06-16, ticket-230 rank-2 extract live LLM)

- `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1` + `--live-staged-rank2-extract-fallthrough`
- Rank-2 heuristic wiring via `is_staged_rank2_fetch_spine_*`; rank-1 fallthrough unchanged
- ticket-236 seeded: rank-2 link live LLM (mirror ticket-208)

## Queue Notes (2026-06-15, ticket-235 proof-layer runbook)

- README **Live staged proof layers (tickets 233–234)** documents layers 1/2/3,
  `unsuitable_live_artifact` skip JSON, and operator retry table.
- AGENTS cross-reference added; no product code changes.

## Queue Notes (2026-06-15, ticket-232 pre-ticket-230 echo audit)

- Pre-ticket audit **GO** for rank-2 extract live LLM: `agent_reports/2026-06-15_pre-ticket-230_rank-2-staged-extract-live-llm-audit.md`
- `principal_audit_gate --next-ticket ticket-230`: `implementation_gate` → **satisfied**
- Cadence still **overdue** (4 done since ticket-231); consider principal audit around ticket-230
- ticket-230 unblocked for implementation

## Queue Notes (2026-06-15, ticket-233/234 staged spine acquisition)

- ticket-233: OA-first URL ordering, multi-URL fetch retry, migration 0008 `url_candidates_json`, top-N live fetch helper.
- ticket-234: three proof layers; combined live tests skip with `unsuitable_live_artifact` when catalog text ≠ mock markers.
- Operator brief: `agent_reports/2026-06-15_operator-live-staged-fetch-403-parallel-audit-brief.md`.
- Principal audit: `agent_reports/2026-06-15_principal-audit-staged-spine-acquisition-checkpoint.md`.
- ticket-235 seeded: README proof-layer runbook.
- ticket-230 remains blocked until pre-ticket-230 (ticket-232 echo audit).

## Queue Notes (2026-06-15, ticket-231 principal audit post-ticket-229)

- Cadence reset; rank-2 heuristics complete (229); ticket-230 needs pre-ticket-230 mechanical gate.
- ticket-232 seeded: pre-ticket-230 echo audit (GO scope from 228 + ticket-204 pattern).

## Queue Notes (2026-06-15, ticket-229 rank-2 staged spine heuristics)

- `staged_spine_heuristics.py`: rank-2 `constraint management` source/chunk helpers.
- Rank-1 auto-mock routing unchanged; 7 unit tests prove disjointness.
- ticket-230 seeded: rank-2 live extract per-step proof.

## Queue Notes (2026-06-15, ticket-228 pre-ticket rank-2 staged live LLM audit)

- Pre-ticket audit **GO (conditional)**: rank-2 live LLM requires separate gates + rank-2 heuristics.
- Rank-1 fallthrough heuristics do not match rank-2 sources (Constraint management vs co-creativity/songwriting).
- Reconcile/report on rank-2: deterministic only (NO-GO for LLM).
- ticket-229 seeded: rank-2 heuristic prerequisite before live Ollama proofs.

## Queue Notes (2026-06-15, ticket-227 principal audit post-ticket-226)

- Cadence reset; staged rank-1 LLM docs trilogy complete (224–226).
- Drift note: no product-risk code since detect (217); pause recommended.
- ticket-228 seeded: pre-ticket rank-2 live LLM audit (medium; when scoped).

## Queue Notes (2026-06-15, ticket-226 orchestrator checklist LLM closure refresh)

- README one-time orchestrator checklist: LLM boundary, not-in-scope table, deterministic reconcile/report notes.
- Staged rank-1 LLM documentation complete (224 README/AGENTS, 225 runtime config, 226 orchestrator checklist).
- ticket-227 seeded: principal audit cadence (224–226 since ticket-223).

## Queue Notes (2026-06-15, ticket-225 runtime config staged reconcile/report gates)

- `12_RUNTIME_CONFIG.md`: RECONCILE/REPORT variable rows; staged gate matrix includes deterministic steps.
- `.env.example`: network-only comments; no `*_LIVE_LLM` for reconcile/report.
- Staged rank-1 LLM documentation trilogy complete (224 README/AGENTS, 225 runtime config).
- ticket-226 seeded: operator orchestrator checklist refresh.

## Queue Notes (2026-06-15, ticket-224 staged reconcile/report deterministic docs)

- README/AGENTS: reconcile-scores and generate-run-report are deterministic Python; no live LLM fallthrough.
- Network gates (`RGE_ALLOW_LIVE_STAGED_RECONCILE` / `_REPORT`) distinguished from per-step live Ollama gates.
- Staged rank-1 LLM inventory closed at detect (204/208/212/217).
- ticket-225 seeded: runtime config + `.env.example` network-only gate callouts.

## Queue Notes (2026-06-15, ticket-223 principal audit post-ticket-222)

- Cadence reset; staged rank-1 LLM surface **closed** (extract/link/build/detect only).
- Pre-ticket 221/222: reconcile and report are deterministic — no live LLM fallthrough.
- ticket-224 seeded: docs hygiene for deterministic boundary callouts.

## Queue Notes (2026-06-15, ticket-222 pre-ticket live staged report audit)

- Pre-ticket audit **NO-GO** for live Ollama generate-run-report: `run_evaluator.py` is deterministic.
- `draft_run_summary` is Phase 0 stub; not wired to staged spine CLI.
- Staged rank-1 LLM surface closed: extract/link/build/detect only; reconcile/report deterministic.
- ticket-223 seeded: principal audit cadence (219–222 since ticket-219).

## Queue Notes (2026-06-15, ticket-221 pre-ticket live staged reconcile audit)

- Pre-ticket audit **NO-GO** for live Ollama reconcile: `score_reconciler.py` is deterministic; no LLM task.
- `RGE_ALLOW_LIVE_STAGED_RECONCILE` remains network spine gate only (ticket-184).
- No live reconcile implementation ticket seeded.
- ticket-222 seeded: pre-ticket audit for generate-run-report live LLM surface.

## Queue Notes (2026-06-15, ticket-220 live staged detect env profile)

- `.env.example` + `12_RUNTIME_CONFIG.md` now document `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1`.
- Staged gate matrix includes detect live row; domain seed note added.
- ticket-221 seeded: pre-ticket audit for live staged reconcile.

## Queue Notes (2026-06-15, ticket-219 principal audit post-ticket-217)

- Cadence reset; GO for continued staged spine work with boundaries intact.
- Per-step live detect (217) + docs (218) verified in mock gates; live Ollama proof operator opt-in.
- Hygiene gap: `.env.example` missing detect live gate — ticket-220 seeded.
- Deferred: live reconcile/report on staged spine without pre-ticket audit.

## Queue Notes (2026-06-15, ticket-218 live staged detect docs)

- README/AGENTS document live staged detect: `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1`,
  `--live-staged-detect-fallthrough`, domain seed + mock upstream chain.
- Orchestrator mock-only boundary preserved; reconcile/report remain mock-only.
- ticket-219 seeded: principal audit cadence (214–217 since ticket-215).

## Queue Notes (2026-06-15, ticket-217 live staged detect live LLM spine)

- Per-step rank-1 live detect: `--live-staged-detect-fallthrough` +
  `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1` (separate from mock detect gate).
- Mock upstream (extract/link/build) + `seed_domain_opposing_context` in pytest.
- Orchestrator unchanged (mock LLM forced).

## Queue Notes (2026-06-15, ticket-216 pre-ticket live staged detect audit)

- Pre-ticket audit GO: `agent_reports/2026-06-15_pre-ticket-216_live-staged-detect-live-llm-audit.md`.
- Per-step rank-1 live detect with domain seed + mock extract/link/build upstream.
- Env gate: `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1` (separate from mock detect gate).
- ticket-217 seeded: implementation; ticket-218 seeded: docs.

## Queue Notes (2026-06-15, ticket-214 live staged build docs)

- README/AGENTS document live staged build: `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM=1`,
  `--live-staged-build-fallthrough`, pytest `live_network and live_smoke`; mock extract + mock link upstream.
- ticket-216 seeded: pre-ticket audit for live staged detect.

## Queue Notes (2026-06-15, ticket-213 local env profile)

- `.env.example` consolidates staged mock + live Ollama gates; README/12_RUNTIME_CONFIG document `.env.local` workflow.
- Principal audit cadence overdue (210–212 since ticket-210); recommend audit after ticket-214.
- ticket-214 active: live staged build operator docs.

## Queue Notes (2026-06-15, ticket-212 live staged build live LLM)

- Live staged build fallthrough: `--live-staged-build-fallthrough` + `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM=1`.
- Pytest chain uses mock extract + mock link upstream; orchestrator remains mock-only.
- Operator live proof with `qwen3.5:9b-q4_K_M`: model-health ok; live pytest blocked by OpenAlex network timeout in builder session.
- ticket-214 recommended: README/AGENTS operator docs for live staged build.

## Queue Notes (2026-06-15, ticket-211 pre-ticket audit)

- Pre-ticket audit GO: `agent_reports/2026-06-15_pre-ticket-211_live-staged-build-live-llm-audit.md`.
- Per-step rank-1 live build with mock extract + mock link upstream; orchestrator unchanged.
- Env gate: `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM=1` (separate from mock `RGE_ALLOW_LIVE_STAGED_BUILD`).
- ticket-212 seeded: implementation; ticket-213 seeded: env docs (low-risk, after 212).
- Ollama `qwen2.5:7b` healthy; `qwen3.5:9b` not local — no pull performed.

## Queue Notes (2026-06-15, principal audit post-ticket-209)

- Cadence reset; tickets 206–209 reviewed; live staged extract + link boundaries confirmed.
- Authoritative audit: `agent_reports/2026-06-15_ticket-210_principal-audit-post-ticket-209.md`.
- ticket-211 seeded: pre-ticket audit for live staged build (per-step).

## Queue Notes (2026-06-15, ticket-209 agent)

- README/AGENTS document live staged link: `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1`,
  `--live-staged-link-fallthrough`, pytest `live_network and live_smoke`; mock extract upstream.
- ticket-210 seeded: principal audit cadence (207–209 since ticket-206).

## Queue Notes (2026-06-15, ticket-208 agent)

- Live staged link fallthrough: `--live-staged-link-fallthrough` + `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1`.
- Pytest chain uses mock extract upstream; orchestrator remains mock-only.
- ticket-209 seeded: operator docs for live staged link.

## Queue Notes (2026-06-15, ticket-207 pre-ticket audit)

- Pre-ticket audit GO for ticket-208: per-step live Ollama link on rank-1 staged source (mock extract upstream).
- Authoritative audit: `agent_reports/2026-06-15_pre-ticket-207_live-staged-link-live-llm-audit.md`.

## Queue Notes (2026-06-15, principal audit post-ticket-205)

- Cadence reset; tickets 202–205 reviewed; live staged extract boundaries confirmed.
- Authoritative audit: `agent_reports/2026-06-15_ticket-206_principal-audit-post-ticket-205.md`.
- ticket-207 seeded: pre-ticket audit for live staged link (per-step).

## Queue Notes (2026-06-15, ticket-205 agent)

- README/AGENTS document live staged extract: `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`,
  `--live-staged-fallthrough`, pytest `live_network and live_smoke`.
- Orchestrator mock-only boundary clarified in both docs.
- ticket-206 seeded: principal audit cadence (203–205 since ticket-202).

## Queue Notes (2026-06-15, ticket-204 agent)

- Live staged extract fallthrough: `--live-staged-fallthrough` + `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`.
- Orchestrator and default pytest remain mock-only; opt-in live proof in `test_live_staged_extract_live_llm_spine.py`.
- ticket-205 seeded: operator docs for live staged extract.

## Queue Notes (2026-06-15, ticket-203 pre-ticket audit)

- Pre-ticket audit GO for ticket-204: per-step live Ollama extract on staged rank-1 source.
- Authoritative audit: `agent_reports/2026-06-15_pre-ticket-203_live-llm-staged-run-audit.md`.

## Queue Notes (2026-06-15, principal audit post-ticket-201)

- Principal audit checkpoint complete; cadence reset (ticket-202).
- Research run contract: `--staged-spine` primary entry (ticket-201).
- ticket-203 seeded: pre-ticket audit for live LLM on staged run.

## Queue Notes (2026-06-15, ticket-201 agent)

- `research run --staged-spine` works without `--fixture-mode` (ticket-201).
- ticket-202 seeded: principal audit cadence checkpoint.

## Queue Notes (2026-06-15, ticket-200 pre-ticket audit)

- Pre-ticket audit GO for ticket-201: `--staged-spine` without `--fixture-mode`; full live MVP deferred.
- Authoritative audit: `agent_reports/2026-06-15_pre-ticket-200_research-run-non-fixture-audit.md`.

## Queue Notes (2026-06-15, ticket-199 agent)

- README/AGENTS one-time live orchestrator verification runbook (ticket-199).
- ticket-200 seeded: pre-ticket audit for non-fixture research run.

## Queue Notes (2026-06-15, principal audit post-ticket-197)

- Principal audit checkpoint complete; cadence reset (ticket-198).
- Hygiene arc 195–197 verified: candidate ordering, shared candidate helper, shared domain seed.
- ticket-199 seeded: operator live verification runbook (docs).

## Queue Notes (2026-06-15, ticket-197 agent)

- Shared `staged_domain_seed.seed_domain_opposing_context`; fourteen staged tests refactored (ticket-197).
- ticket-198 seeded: principal audit cadence checkpoint (three tickets since post-ticket-194).

## Queue Notes (2026-06-15, ticket-196 agent)

- Shared `live_staged_candidates` helper; all nine live staged tests refactored (ticket-196).
- ticket-197 seeded: shared `_seed_domain_opposing_context` DRY helper.

## Queue Notes (2026-06-15, ticket-195 agent)

- Fixed live staged pytest candidate ordering: `priority_score DESC` (ticket-195).
- ticket-196 seeded: shared candidate query helper (DRY).

- Documented `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR` in README/AGENTS (ticket-194).
- Principal audit post-ticket-193 bundled (cadence reset).
- ticket-195 seeded: live staged pytest ORDER BY priority_score hygiene.

- Live staged orchestrator opt-in pytest + env-gated cli branch (ticket-193).
- Operator live OpenAlex run not verified in this environment (timeout); mock gates green.

## Queue Notes (2026-06-15, ticket-192 agent)

- Pre-ticket audit GO for single-command live staged orchestrator (ticket-193).
- Authoritative audit: `agent_reports/2026-06-15_pre-ticket-192_live-staged-orchestrator-audit.md`.
- ticket-194 seeded: orchestrator opt-in docs (post-193).

## Queue Notes (2026-06-15, ticket-190 agent)

- Opt-in `live_network` pytest: live rank-2 candidate through generate-run-report.
- Uses `staged_fetch_second_candidate_*` fixtures after live ingest.
- Env: `RGE_ALLOW_LIVE_STAGED_RANK2=1`.
- 598 pytest; 15 deselected; 142 golden; safety pass.
- ticket-191 seeded: rank-2 opt-in docs.

## Queue Notes (2026-06-15, ticket-189 agent)

- Pre-ticket audit GO for live staged rank-2 mock spine (ticket-190).
- Rank-2 uses `staged_fetch_second_candidate_*` fixtures after live fetch/ingest.
- ticket-190 seeded: live staged rank-2 implementation.

## Queue Notes (2026-06-15, ticket-188 agent)

- Docs-only: README + AGENTS.md `RGE_ALLOW_LIVE_STAGED_REPORT` opt-in pytest.
- Maturity table: per-step live staged proofs through report (ticket-187).
- Principal audit post-ticket-187 committed (overdue cadence reset).
- 597 pytest; 14 deselected; 142 golden; safety pass.
- ticket-189 seeded: pre-ticket audit for live staged rank-2 mock spine.

## Queue Notes (2026-06-15, ticket-187 agent)

- Opt-in `live_network` pytest: discover through generate-run-report (deterministic).
- Domain opposing-context seed before live network (ticket-181 pattern).
- Env: `RGE_ALLOW_LIVE_STAGED_REPORT=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`.
- 597 pytest; 14 deselected; 142 golden; safety pass.
- ticket-188 seeded: report opt-in docs.

## Queue Notes (2026-06-15, ticket-186 agent)

- Pre-ticket audit GO for live staged generate-run-report spine (ticket-187).
- Report step is deterministic Python; temp DB + output-dir only.
- ticket-187 seeded: live staged report implementation.

## Queue Notes (2026-06-15, ticket-185 agent)

- Docs-only: README + AGENTS.md `RGE_ALLOW_LIVE_STAGED_RECONCILE` opt-in pytest.
- Principal audit gate post-ticket-184 satisfied.
- 596 pytest; 13 deselected; 142 golden; safety pass.
- ticket-186 seeded: pre-ticket audit for live staged run-report mock spine.

## Queue Notes (2026-06-15, ticket-184 agent)

- Opt-in `live_network` pytest: discover through reconcile-scores (deterministic Python).
- Domain opposing-context seed before live network (ticket-181 pattern).
- Env: `RGE_ALLOW_LIVE_STAGED_RECONCILE=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`.
- 596 pytest; 13 deselected; 142 golden; safety pass.
- ticket-185 seeded: reconcile opt-in docs.

## Queue Notes (2026-06-15, ticket-183 agent)

- Pre-ticket audit GO for live staged reconcile spine (ticket-184).
- Reconcile is deterministic Python after mock-fixture detect path.
- ticket-184 seeded: live staged reconcile implementation.

## Queue Notes (2026-06-15, ticket-182 agent)

- Docs-only: README + AGENTS.md `RGE_ALLOW_LIVE_STAGED_DETECT` opt-in pytest.
- Principal audit post-ticket-181 committed (overdue cadence reset).
- 595 pytest; 12 deselected; 142 golden; safety pass.
- ticket-183 seeded: pre-ticket audit for live staged reconcile mock spine.

## Queue Notes (2026-06-15, ticket-181 agent)

- Opt-in `live_network` pytest: discover through detect-contradictions (mock fixtures).
- Domain opposing-context seed before live network (ticket-147 pattern).
- Env: `RGE_ALLOW_LIVE_STAGED_DETECT=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`.
- 595 pytest; 12 deselected; 142 golden; safety pass.
- Added `pre-ticket-181` gate alias for principal_audit_gate filename match.
- ticket-182 seeded: detect opt-in docs.

## Queue Notes (2026-06-15, ticket-180 agent)

- Pre-ticket audit GO for live staged detect mock spine (ticket-181).
- Domain opposing-context seed required before live network (ticket-147 pattern).
- `principal_audit_gate --next-ticket ticket-180` satisfied.
- ticket-181 seeded: live staged detect mock-fixture implementation.

## Queue Notes (2026-06-15, ticket-179 agent)

- Docs-only: README + AGENTS.md `RGE_ALLOW_LIVE_STAGED_BUILD` opt-in pytest.
- Principal audit post-ticket-178 committed (overdue cadence reset).
- 594 pytest; 11 deselected; 142 golden; safety pass.
- ticket-180 seeded: pre-ticket audit for live staged detect mock spine.

## Queue Notes (2026-06-15, ticket-178 agent)

- Opt-in `live_network` pytest: discover through build-relationships (mock fixtures).
- Env: `RGE_ALLOW_LIVE_STAGED_BUILD=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`.
- 594 pytest; 11 deselected; 142 golden; safety pass.
- ticket-179 seeded: build opt-in docs.

## Queue Notes (2026-06-15, ticket-166 agent)

- Added `python -m rge.modules.operator_autocycle` plan + execute-safe modes.
- Stops before autonomous ticket implementation; no git push/merge.
- Skips deferred ticket-059 when resolving active ticket.
- 589 pytest; 142 golden; safety pass.
- ticket-167 seeded: live staged fetch validation proof (opt-in).

## Queue Notes (2026-06-15, ticket-165 agent)

- Docs-only: README + AGENTS.md maturity relabel for Phase 3 staged mock spine.
- 582 pytest; 142 golden; safety pass.
- ticket-166 seeded: safe autocycle command.

- Cadence checkpoint satisfied: `agent_reports/2026-06-15_principal-audit-post-ticket-164.md`.
- ticket-159 superseded (post-158 audit was on main; this audit covers tickets 160–164).
- 142 golden; 582 pytest; 63 staged unit tests; safety pass; public-site build pass.
- Gate filename sort hygiene: post-ticket-149 reference sorts after post-ticket-158 — noted for future fix.
- Next: ticket-165 README maturity table relabel.

## Queue Notes (2026-06-14, ticket-164 agent)

- Docs-only: README Operator Quickstart for `run --fixture-mode --staged-spine`.
- Documents mock LLM, network env, temp `--db`, expected counts, idempotency note.
- 582 pytest; 142 golden; safety pass.
- ticket-165 seeded: README maturity table Phase 3 staged spine status.

## Queue Notes (2026-06-14, ticket-163 agent)

- Test-forward ticket: `execute_staged_fixture_mode_run` twice on one DB; stable dual-spine counts.
- HTML fetch mock cycles rank #1/#2 across two orchestrator passes.
- 582 pytest; 142 golden; safety pass.
- ticket-164 seeded: README staged Phase 3 `--staged-spine` operator quickstart.
- Phase 3 mock spine complete: per-step, idempotency, dual-candidate, orchestrator, orchestrator idempotency.

## Queue Notes (2026-06-14, ticket-162 agent)

- Added `execute_staged_fixture_mode_run` and `research run --fixture-mode --staged-spine`.
- URL-aware network mock in unit tests (OpenAlex JSON + staged HTML fetches).
- Stable dual counts match ticket-161: 3 sources, 2 score_events, 2 run_reports, 2 qualifies.
- 581 pytest; 142 golden; safety pass.
- ticket-163 seeded: staged fixture-mode run orchestrator idempotency.

## Queue Notes (2026-06-14, ticket-161 agent)

- Test-forward ticket: rank #1 then rank #2 full spines on one DB; re-run without re-seeding domain.
- Stable dual counts: 3 sources, 2 score_events, 2 run_reports, 2 qualifies.
- 579 pytest; 142 golden; safety pass.
- ticket-162 seeded: fixture-mode staged research run orchestration.
- Phase 3 mock idempotency complete for rank #1, rank #2, and dual-candidate shared DB.

## Queue Notes (2026-06-14, ticket-160 agent)

- Test-forward ticket: rank #2 full spine idempotency (mirror ticket-151).
- Explicit `--fixture` on extract/link/build/detect; relationships_staged=2 (qualifies on base edge).
- Principal audit post-ticket-158 committed with this merge (cadence checkpoint).
- 577 pytest; 142 golden; safety pass.
- ticket-161 seeded: dual-candidate idempotency on one DB.
- ticket-159 remains proposed — principal audit deliverable now on main via ticket-160 merge.

## Queue Notes (2026-06-14, ticket-158 agent)

- Test-forward ticket: rank #2 spine through generate-run-report only; no production changes.
- Run id `run_second_staged_phase3_spine`; counters match ticket-149 minimums on rank #2 DB state.
- Idempotent re-run: one run_reports row.
- 575 pytest; 142 golden; safety pass.
- **Rank #2 mock spine complete** (discover → report).
- ticket-159 seeded: principal audit checkpoint (cadence overdue).
- Principal audit strongly recommended before further Phase 3 tickets.

## Queue Notes (2026-06-14, ticket-157 agent)

- Reconcile contract fixture + rank #2 edge matcher in score_reconciler (ticket-148 precedent).
- Extract claim confidence 0.7 → 0.85 to meet pack threshold 0.8.
- constraint may_increase human control boosted 0.5 → 0.62; one score_events row.
- Idempotent re-run: no duplicate events.
- 572 pytest; 142 golden; safety pass.
- ticket-158 seeded: generate-run-report on second staged source.
- Rank #2 spine complete through reconcile-scores only — not run report yet.

## Queue Notes (2026-06-14, ticket-156 agent)

- Test-forward ticket: detect fixture + tests only; explicit `--fixture` binding.
- Domain base seed (GT7 pattern) + rank #2 cross-edge qualification: constraint may_increase human control qualifies AI assistance may_reduce semantic diversity.
- Idempotent re-run: `already_detected`.
- 568 pytest; 142 golden; safety pass.
- ticket-157 seeded: reconcile-scores on second staged source.
- Rank #2 spine complete through detect-contradictions only — not reconcile/report yet.

## Queue Notes (2026-06-14, ticket-155 agent)

- Test-forward ticket: relationship fixture + tests only; explicit `--fixture` binding.
- Rank #2 relationship: constraint may_increase human control (scope AI-assisted creative team workflows); supports evidence.
- Idempotent re-run: `already_built`.
- 566 pytest; 142 golden; safety pass.
- ticket-156 seeded: detect-contradictions on second staged source.
- Rank #2 spine complete through build-relationships only — not detect/reconcile/report yet.

## Queue Notes (2026-06-14, ticket-154 agent)

- Test-forward ticket: link fixture + tests only; explicit `--fixture` binding.
- Rank #2 link: 3 concept links (constraint, AI assistance, human control); idempotent `already_linked`.
- Principal audit post-ticket-153 committed with this merge.
- 564 pytest; 142 golden; safety pass.
- ticket-155 seeded: build-relationships on second staged source.

## Queue Notes (2026-06-14, ticket-153 agent)

- Test-forward ticket: fixture + extract tests only; explicit `--fixture` binding.
- Rank #2 extract: 1 accepted, 1 rejected (`missing_quote_span`); scope must match claim_text verbatim.
- 562 pytest; 142 golden; safety pass.
- ticket-154 seeded: link-concepts on second staged source.
- **Principal cadence overdue after this ticket** — run `/rge-principal-audit` before or with ticket-154.

## Queue Notes (2026-06-14, ticket-152 agent)

- Test-forward ticket: no production code changes.
- Rank #2 `disc_openalex_W1234567890` fetch + ingest-staged with mock HTML; distinct artifacts per candidate.
- Rank #2 inferred `source_type`: `unknown` (fixture has no DOI/abstract).
- 2 second-candidate tests; 560 pytest; 142 golden; safety pass.
- ticket-153 seeded: extract-claims on second staged source.

## Queue Notes (2026-06-14, ticket-151 agent)

- Test-forward ticket: no production code changes.
- 2 idempotency tests: full spine twice + per-command reruns (discover→report).
- Stable staged counts documented; 558 pytest; 142 golden; safety pass.
- ticket-152 seeded: second staged candidate fetch/ingest (rank #2).

## Queue Notes (2026-06-14, ticket-150 agent)

- Principal audit checkpoint post-ticket-149: **GO** (`agent_reports/2026-06-14_principal-audit-post-ticket-149.md`).
- Cadence satisfied (13 done tickets since post-136); 142 golden, 556 pytest, safety pass.
- ticket-151 seeded: staged Phase 3 full spine idempotency (product-risk priority #1).

## Queue Notes (2026-06-14, ticket-149 agent)

- Test-forward ticket: no production code changes.
- E2E: domain seed → staged spine through reconcile → generate-run-report.
- Report run_id `run_staged_phase3_spine`; counters include discover/ingest/claims/relationships/score_events.
- 3 run-report spine tests; 556 pytest; 142 golden; safety audit pass.
- **Staged Phase 3 processing spine complete** through run report (mock-only).
- ticket-150 seeded: principal audit checkpoint (cadence overdue).
- Next: `/rge-principal-audit` or ticket-150 before further Phase 3 product-risk work.

- Deterministic score_reconciler staged may_increase matcher + extract confidence 0.85.
- Reconcile contract fixture `staged_fetch_reconcile_scores.json` (not LLM output).
- E2E: domain seed → staged spine through detect → reconcile-scores on staged source.
- co-creation may_increase semantic diversity: 0.5 → 0.62; 1 score_events row.
- 4 reconcile spine tests; 553 pytest; 142 golden; safety audit pass.
- ticket-149 seeded: generate-run-report on staged source.
- Next: pre-ticket-149 audit then ticket-149 implementation.

- Mock fixture `staged_fetch_detect_contradictions.json` + staged title heuristic in contradiction_detector.
- E2E unit test seeds domain base graph then discover→fetch→ingest→extract→link→build→detect.
- Qualification: staged co-creation claim qualifies base may_reduce edge (apparent_contradiction_metric_or_condition_difference).
- 3 spine tests; 549 pytest; 142 golden; safety audit pass.
- ticket-148 seeded: reconcile-scores on staged source.
- Next: pre-ticket-148 audit then ticket-148 implementation.

- Mock fixture `staged_fetch_build_relationships.json` + staged title heuristic in relationship_builder.
- E2E unit test: discover enqueue → fetch → ingest-staged → extract → link → build-relationships.
- Relationship: co-creation may_increase semantic diversity (songwriting workshops, supports).
- 3 spine tests; 546 pytest; 142 golden; safety audit pass.
- ticket-147 seeded: detect-contradictions on staged source.
- Next: pre-ticket-147 audit then ticket-147 implementation.

- Mock fixture `staged_fetch_link_concepts.json` + staged title heuristic in concept_linker.
- E2E unit test: discover enqueue → fetch → ingest-staged → extract → link-concepts.
- 3 spine tests; 543 pytest; 145 golden; safety audit pass.
- ticket-146 seeded: build-relationships on staged source.
- Next: pre-ticket-146 audit then ticket-146 implementation.

## Queue Notes (2026-06-14, ticket-144 agent)

- Mock fixture `staged_fetch_extract_claims.json` + auto-select in claim_extractor.
- E2E unit test: discover enqueue → fetch → ingest-staged → extract-claims.
- 4 spine tests; 540 pytest; 142 golden; safety audit pass.
- ticket-145 seeded: link-concepts on staged source.
- Next: pre-ticket-145 audit then ticket-145 implementation.

## Queue Notes (2026-06-14, ticket-137 agent)

- Principal audit post-ticket-136: GO; cadence satisfied after docs chain 134–136.
- Maturity aligned across README, AGENTS, canonical context; NM-4 evidence DB spine unchanged.
- 487 pytest; 142 golden; safety audit pass; public-site build pass.
- Next: ticket-138 (source discovery stub CLI, low risk, product-facing).

## Queue Notes (2026-06-14, ticket-131 agent)

- Extended score_reconciler matcher for live-drafted active edges; `--evidence-db-reconcile` on reconcile-scores.
- Evidence DB operator proof: follow-up reconcile 0.5 → 0.62 on AI assistance → constraint edge; 1 score_events row.
- 6 nm4 evidence tests; 484 pytest; 142 golden; safety audit pass.
- NM-4 live spine + deterministic reconcile complete on gitignored evidence DB.
- Next: ticket-132 (operator_loop evidence spine status, low risk).

## Queue Notes (2026-06-14, principal audit post-ticket-130)

- Cadence satisfied after post-ticket-130 checkpoint.
- ticket-131 retargeted: deterministic reconcile-scores on evidence DB (not Ollama).
- Pre-ticket-131 audit GO; matcher hardening required for live-drafted edges.
- Next: `/rge-run-next-ticket` for ticket-131.

## Queue Notes (2026-06-14, ticket-130 agent)

- `--live-manual-contradiction-fallthrough` on detect-contradictions; mock fail-closed for unmapped manual_text.
- Live proof on ticket-127/128/129 evidence source: `no_qualifications` (1 rejected candidate; single active edge).
- 26 manual_live_fallthrough unit tests; 478 pytest; 142 golden; safety audit pass.
- Cadence: 3 done since post-ticket-127 principal audit (128, 129, 130) — **principal audit required before ticket-131**.
- Next: principal audit post-ticket-130, then ticket-131 (live score reconciliation fall-through).

## Queue Notes (2026-06-14, ticket-129 agent)

- `--live-manual-relationship-fallthrough` on build-relationships; mock fail-closed for unmapped manual_text.
- Live proof on ticket-127/128 evidence source: 1 active relationship, 1 evidence row, 0 rejected.
- 20 manual_live_fallthrough unit tests; 472 pytest; 142 golden; safety audit pass.
- Cadence: 2 done since post-ticket-127 principal audit (128, 129) — principal audit due before ticket-131.
- Next: ticket-130 (live contradiction fall-through); requires pre-ticket audit.

## Queue Notes (2026-06-14, ticket-128 agent)

- `--live-manual-link-fallthrough` on link-concepts; mock fail-closed for unmapped manual_text.
- Live proof on ticket-127 evidence source: 2 accepted concept links, 0 rejected.
- 14 manual_live_fallthrough unit tests; 466 pytest; 142 golden; safety audit pass.
- Cadence: 1 done since post-ticket-127 principal audit — monitor before ticket-130.
- Next: ticket-129 (live relationship fall-through); requires pre-ticket audit.

## Queue Notes (2026-06-14, ticket-127 agent)

- Calibrated Ollama claim prompt v0.1.1 for `manual_text_arbitrary_live` contract mode.
- Live proof: checksum `1b8354e5…` not in fixture map; 1 accepted / 1 rejected in evidence DB.
- NM-4 extract proof complete; synthnote mock spine unchanged.
- 460 pytest pass; 142 golden; safety audit pass.
- Cadence: 2 done since post-ticket-125 audit (126, 127) — principal audit due after one more done ticket.
- Next: ticket-128 (live concept linking fall-through); requires pre-ticket audit.

## Queue Notes (2026-06-14, ticket-126 agent)

- `operator_loop --mode plan` adds read-only `domain_pack_status` for creativity pack.
- Reports pack id, identity status, loaded/missing overlay files, identity verification.
- Recenter: tickets 123–125 docs-only; next ticket is NM-4 ticket-127 (pre-ticket audit GO).
- 37 operator_loop unit tests; 142 golden; 457 pytest; safety audit pass.
- No more NM-5 docs/operator chain to be seeded.

## Queue Notes (2026-06-14, ticket-125 agent)

- `06_DOMAIN_PACK_SPEC.md` cross-links README/AGENTS NM-5 runtime loading section.
- Documents overlap-domain claim allowlist without duplicating full YAML table.
- Docs-only; 142 golden pass; 454 pytest pass; safety audit pass.
- Cadence note: 3 done tickets (123–125) since post-ticket-122 audit — run `/rge-principal-audit` before ticket-127.
- Next: ticket-126 (operator_loop domain pack health in plan mode).

## Queue Notes (2026-06-14, ticket-124 agent)

- AGENTS.md Operator Loop cross-links README NM-5 domain pack section.
- One-sentence overlap-domain claim allowlist rule for operators.
- Docs-only; 142 golden pass; 454 pytest pass; safety audit pass.
- Next: ticket-125 (06_DOMAIN_PACK_SPEC.md cross-link).

## Queue Notes (2026-06-14, ticket-123 agent)

- README Operator Quickstart documents all 10 creativity pack YAML overlays and consumers.
- Documents overlap-domain claim labels and claim_validator allowlist behavior.
- Committed post-ticket-122 principal audit report with ticket branch.
- 142 golden pass; 454 pytest pass; safety audit pass.
- Next: ticket-124 (AGENTS.md cross-link).

## Queue Notes (2026-06-14, ticket-122 agent)

- Added `claim_extraction_overlap_domain_art.json` mock fixture with `domain: art`.
- Golden tests prove overlap labels survive extract-and-validate and CLI persist paths.
- GT22 inventory updated; 142 golden pass; 454 pytest pass; safety audit pass.
- Cadence note: 3 done tickets since post-ticket-119 principal audit after this merge — run `/rge-principal-audit` before ticket-124 implementation.
- Next: ticket-123 (README NM-5 domain pack summary).

## Queue Notes (2026-06-14, ticket-121 agent)

- `claim_validator` rejects candidate domain labels outside `allowed_domains_for_pack()`.
- `extract_and_validate_for_chunk` passes `domain_pack` for overlap label acceptance.
- Creativity overlap domains (art, design, film, music, digital_media) accepted in mock validation.
- 3 new unit tests; 452 pytest pass; safety audit pass.
- Next: ticket-122 (golden overlap-domain claim mock proof).

## Queue Notes (2026-06-14, ticket-120 agent)

- Extended `domain_pack_loader` to parse `domain.yaml` (`DomainIdentityOverlay`).
- `load_domain_pack()` requires domain.yaml; validates pack directory id matches YAML id.
- Safety auditor verifies pack identity is active via `verify_pack_identity_for_audit()`.
- 6 new unit tests; domain.yaml stubs in all domain-pack temp-pack tests.
- 449 pytest pass; safety audit pass. NM-5 declarative pack loading complete.
- Principal audit: `agent_reports/2026-06-14_principal-audit-post-ticket-119.md`.
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-120_domain-pack-domain-yaml-loader-audit.md`.
- Next: ticket-121 (claim_validator domain allowlist from pack).

- Extended `domain_pack_loader` to parse `safety_notes.yaml` (multi-line notes list).
- Full safety audit verifies creativity pack guidance themes from loaded notes.
- 5 new unit tests; 443 pytest pass; safety audit pass.
- Next: ticket-120 (NM-5 completion: domain.yaml).

## Queue Notes (2026-06-14, ticket-118 agent)

- Extended `domain_pack_loader` to parse `search_templates.yaml` (query templates + preferred_source_types).
- `research_planner` follow-up scoring uses pack template keyword overlap; golden contract seeds `source_strategy.search_queries`.
- 6 new unit tests; 438 pytest pass; safety audit pass.
- Next: ticket-119 (NM-5 continuation: safety_notes.yaml).

## Queue Notes (2026-06-14, ticket-117 agent)

- Extended `domain_pack_loader` to parse `card_templates.yaml` (`required_fields` per card type).
- `export_public_cards()` passes pack templates into `validate_public_export_bundle()`.
- Template enforcement uses intersection with public allowlist only (cluster-only fields skipped).
- Pack load falls back to installed repo when temp `repo_root` lacks `domain_packs/`.
- 7 new unit tests; 432 pytest pass; safety audit pass.
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-117_domain-pack-card-templates-loader-audit.md`.
- Next: ticket-118 (NM-5 continuation: search_templates.yaml).

## Queue Notes (2026-06-14, ticket-116 agent)

- Extended `domain_pack_loader` to parse `source_preferences.yaml` (`source_type_weights`).
- `research_queue.rank_fixture_candidates()` uses pack credibility priors; marketing still code-rejected.
- `blog_post` uses 0.40 fallback (pack has no entry); GT09 unchanged.
- 7 new unit tests; 425 pytest pass; safety audit pass.
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-116_domain-pack-source-preferences-loader-audit.md`.
- Next: ticket-117 (NM-5 continuation: card_templates.yaml) requires pre-ticket audit before implementation.

## Queue Notes (2026-06-14, ticket-115 agent)

- Extended `domain_pack_loader` to parse `claim_schema.yaml`.
- `concept_linker` validates present `domain_metadata` against pack allowlists.
- `measured_dimension: idea diversity` normalized via concept alias (GT07 safe).
- Partial metadata links (no `measured_dimension`) still accepted.
- 6 new unit tests; 418 pytest pass; safety audit pass.
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-115_domain-pack-claim-schema-loader-audit.md`.
- Next: ticket-116 (NM-5 continuation: source_preferences.yaml) requires pre-ticket audit before implementation.

## Queue Notes (2026-06-14, ticket-114 agent)

- Extended `domain_pack_loader` to parse `evidence_types.yaml`.
- `claim_validator` rejects unknown evidence types via pack allowlist per domain.
- Temp-pack proof: demo pack with only `benchmark` rejects `empirical`.
- 6 new unit tests; 412 pytest pass; safety audit pass.
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-114_domain-pack-evidence-types-loader-audit.md`.
- Next: ticket-115 (NM-5 continuation: claim_schema.yaml) requires pre-ticket audit before implementation.

## Queue Notes (2026-06-14, ticket-113 agent)

- Extended `domain_pack_loader` to parse `scoring.yaml` `score_reconciliation` overlay.
- `score_reconciler` reads boost/threshold/reason/formula from pack per relationship domain.
- Temp-pack proof: 0.20 boost yields 0.5 → 0.70; creativity values unchanged (GT08, manual synthnote).
- 6 new unit tests; 406 pytest pass; safety audit pass.
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-113_domain-pack-scoring-loader-audit.md`.
- Next: ticket-114 (NM-5 continuation: evidence_types.yaml) requires pre-ticket audit before implementation.

## Queue Notes (2026-06-14, ticket-112 agent)

- Added `extract-claims --live-manual-fallthrough` for unmapped `manual_text` sources.
- Mock mode fails closed for unknown manual_text (no generic golden fixture fallback).
- 6 new unit tests; 400 pytest pass; safety audit pass.
- Live proof: fall-through works; 0 accepted / 2 rejected on arbitrary source (validator honest).
- Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-112_arbitrary-manual-live-fallthrough-audit.md`.
- Next: ticket-113 (NM-5 preview) requires pre-ticket audit before implementation.

## Corrective queue override (2026-06-14, third-party audit)

The third-party repo-direction audit (`agent_reports/2026-06-14_third-party-repo-direction-audit.md`)
directed corrective work **before** ticket-111. **Completed and merged to main @ 4a62c99.**

| Move | Status | Notes |
|------|--------|-------|
| NM-1 | **done** | Live validated extraction write (`extract-claims-live`) |
| NM-2 | **done** | Honest maturity relabel; ticket-111 superseded |
| NM-3 | **done** | Value-based cadence gate drift detection |
| NM-4 / ticket-112 | **done** | Arbitrary manual_text live fall-through |
| ticket-111 | **superseded** | Folded into NM-2 |

Next product move: **ticket-126** (operator_loop plan domain pack load health).

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
- **Temporary:** after a ticket is `done`, merge its branch to `main` and push per `AGENTS.md` step 9 until the safety evaluator agent is live.
