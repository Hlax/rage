You are the principal agentic QA/audit engineer for RGE.

First, commit the completed acquisition-quality improvement-ticket work if it is not already committed. The shipped work includes:

* `failure_modes_from_acquisition_summary()`
* acquisition ticket templates
* `write_improvement_tickets()` merging top failure modes with acquisition summary signals
* `recommend_from_run_report()` using `acquisition_quality_summary`
* report: `agent_reports/2026-06-19_phase-4_ticket-376_acquisition-quality-improvement-tickets.md`
* verification: focused tests passed, `python -m rge.cli verify --skip-site` passed

Then run the next audit packet. Do not implement new features first. Test and inspect whether the current system is actually producing useful research-agent inputs.

## Audit goal

Determine whether the new data-quality, evidence-atoms, research-purpose, source-handling, and acquisition-quality improvement-ticket layers give RGE enough clean structure to support:

1. small/local model calls,
2. paid API synthesis calls,
3. durable graph/Atlas insights,
4. future frontend evidence cards,
5. later automation/self-improvement loops.

This audit must specifically verify whether acquisition/parser failure signals correctly turn into useful improvement tickets and packet recommendations.

## Required test runs

Create or reuse deterministic fixtures for these questions:

1. “How does AI affect human creativity?”
2. “Does AI assistance improve idea quality or reduce diversity?”
3. “How do artists/designers describe originality, style, or visual novelty?”
4. “What makes human-AI co-creation preserve or reduce agency?”

Run mock/local-safe mode first. Do not spend paid API calls unless the repo already has a gated dry-run/canary path.

Include at least one intentionally dirty/failed acquisition fixture that triggers:

* `dirty_text`
* `blocked_by_quality_gate`
* `parse_failed`
* `webpage_dirty_text`
* `pdf_unavailable`
* missing PDF parser / unsupported backend

## What to inspect

For each run, report:

* sources discovered
* source statuses
* abstracts available
* OA/PDF/TEI locations
* skipped sources and reasons
* chunks passing/failing text-quality gates
* quote candidates
* proposed claims
* accepted/rejected claims
* top rejection reasons
* accepted claim quote-span validity
* evidence atoms created
* atom stability, concepts, scopes, source links, support/contradiction counts, and asset tags
* research-purpose labels
* evidence maturity labels
* canonical evidence-card readiness
* graph/Atlas readiness
* acquisition failure modes generated
* improvement tickets generated from acquisition summaries
* packet recommendations generated from run reports

## Specific audit questions

Answer brutally:

1. Is this now a real research-data pipeline, or still mostly scaffolding?
2. Can local Qwen/Ollama-style models operate on the evidence packets without hallucinating?
3. Would a paid API model receive enough structure to produce good insights?
4. Are evidence atoms actually useful, or redundant with claims?
5. Is the graph/Atlas layer getting meaningful objects or blobs of text?
6. Are source failures classified clearly enough to guide future automation?
7. Do acquisition-quality summaries correctly create improvement tickets?
8. Do packet recommendations point to the right next fix, or do they misdiagnose failures?
9. Is PDF/full-text still safely milestone-gated, or did it creep back into the MVP path?
10. What would break at 100 sources?
11. What would break at 1,000 sources?
12. What is the next highest-leverage fix before continuing automation/self-improvement?

## Quality bar

The system is acceptable only if:

* dirty text does not reach LLM extraction
* source status is explainable before extraction
* accepted claims are quote-grounded
* rejected claims have useful failure reasons
* evidence atoms are reusable research objects
* research-purpose labels distinguish reasoning data, visual descriptor data, eval candidates, ontology candidates, memo candidates, and public-card candidates
* acquisition failures become useful improvement tickets
* packet recommendations diagnose the real blocker
* local models get compact structured packets
* paid API calls would receive synthesized evidence packets, not raw noisy docs
* graph/Atlas objects are meaningful enough to support future UI and insight generation

## Required outputs

Write a detailed markdown report to:

`agent_reports/YYYY-MM-DD_data-quality-evidence-atoms-acquisition-audit.md`

Include:

* GO / PARTIAL / NO-GO verdict
* executive summary
* test matrix
* metrics table
* source acquisition findings
* extraction/validation findings
* evidence atom findings
* research-purpose/asset-affordance findings
* acquisition-quality improvement-ticket findings
* packet recommendation findings
* graph/Atlas readiness findings
* small-model readiness
* paid-API readiness
* frontend-card readiness
* failure taxonomy
* strongest parts
* weakest parts
* drift warnings
* top 5 fixes ranked by product impact
* recommended next packet

Also write JSON summary to:

`agent_reports/YYYY-MM-DD_data-quality-evidence-atoms-acquisition-audit-latest.json`

JSON fields:

* verdict
* tested_questions
* source_counts
* claim_counts
* rejection_counts
* evidence_atom_counts
* acquisition_failure_modes
* improvement_tickets_generated
* packet_recommendations
* graph_readiness_score
* local_model_readiness_score
* paid_api_readiness_score
* frontend_card_readiness_score
* top_blockers
* next_recommended_packet

## Verification

Run targeted tests first for:

* source resolver
* text quality gates
* evidence atoms
* purpose classifier
* claim validation
* evidence cards
* acquisition failure mode mapping
* improvement ticket generation
* run-report packet recommendation

Run full verification only if this audit touches migrations, public export schema, safety auditor, quote validation, live source download behavior, or public/private boundaries.

Suggested closeout:

* targeted pytest
* golden tests if affected
* `python -m rge.cli verify --skip-site`
* safety auditor if public/private or export behavior changed
* CLI dry run that produces inspectable artifacts

Do not hide failures. Do not overfit to green tests. If outputs look clean but the graph objects are shallow, call that out.
