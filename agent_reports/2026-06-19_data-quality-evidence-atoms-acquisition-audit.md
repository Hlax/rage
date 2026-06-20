# Data Quality / Evidence Atoms / Acquisition Audit

Date: 2026-06-19

Role: principal QA/audit engineer

Verdict: **PARTIAL**

RGE is now more than scaffolding on the deterministic fixture path: it can produce quote-backed accepted claims, rejected claims with reasons, concept links, relationship edges, score events, cluster reports, private canonical evidence cards, evidence atoms, and Atlas-safe previews. But it is not yet a real arbitrary research-data pipeline. The abstract-first local-safe research loop is thin, question reuse is too broad, acquisition status observability is inconsistent, and packet recommendation can still misdiagnose blockers.

## Commit / Setup Check

The completed acquisition-quality improvement-ticket work was already committed in `458973e Complete Phase 4 evidence-quality packets (purpose atoms through acquisition ticket seeding).`

That commit includes the requested acquisition-quality work: `failure_modes_from_acquisition_summary()`, acquisition ticket templates, `write_improvement_tickets()` acquisition-summary merging, `recommend_from_run_report()` acquisition-quality use, focused tests, and the ticket 376 report. No extra acquisition-quality commit was needed before this audit.

## Commands Run

- `git status --short`
- `git show --stat --oneline --name-only HEAD`
- `python -m pytest tests/unit/test_source_resolver.py tests/unit/test_web_source_adapter.py tests/unit/test_text_quality_gate.py tests/unit/test_evidence_atoms.py tests/unit/test_research_purpose_classifier.py tests/unit/test_quote_first_extraction.py tests/unit/test_claim_validator_domain_pack.py tests/unit/test_evidence_card_exporter.py tests/unit/test_atlas_evidence_cards_preview.py tests/unit/test_acquisition_quality.py tests/unit/test_ticket_writer_acquisition_quality.py tests/unit/test_failure_recommender.py tests/golden/test_19_run_report.py tests/golden/test_31_evidence_card_export.py tests/golden/test_35_acquisition_quality_tickets.py -q`
- `python -m rge.cli research-run --topic "<question>" --domain creativity --fixture-mode --out <audit_qN>` for all four requested questions
- `python -m rge.cli run --topic "Does AI assistance improve idea quality or reduce diversity?" --domain creativity --fixture-mode --db data/db/audit_quality_fixture.sqlite --run-id run_audit_quality_fixture --output-dir data/reports/audit_quality_fixture --ticket-dir data/tickets/audit_quality_fixture --export-dir data/exports/audit_quality_fixture`
- `python -m rge.cli promote-evidence-atoms --domain creativity --db data/db/audit_quality_fixture.sqlite`
- `python -m rge.cli export-evidence-cards --domain creativity --db data/db/audit_quality_fixture.sqlite --output-dir data/exports/audit_evidence_cards --limit 100`
- `python -m rge.cli export-atlas-snapshot --domain creativity --db data/db/audit_quality_fixture.sqlite --out data/exports/audit_atlas_snapshot.json --fixture-mode`
- `python -m rge.cli recommend-improvement-packet --run-report data/reports/audit_quality_fixture/run_report_latest.json`
- Dirty webpage acquisition fixture exercised through `normalize_webpage_artifact()` and `run_ingest_webpage_pipeline()`

Focused tests passed: **67 passed**.

Full verification was not rerun because this audit did not implement code, change migrations, change public/private boundaries, or modify export schema.

## Test Matrix

| Question | Mode | Sources | Accepted | Rejected | Skipped | Main blocker |
|---|---:|---:|---:|---:|---:|---|
| How does AI affect human creativity? | mock fixture abstract-first | 4 | 1 | 2 | 1 | Thin abstract evidence; unsupported claim |
| Does AI assistance improve idea quality or reduce diversity? | mock fixture abstract-first + full fixture graph | 4 abstract / 3 graph | 1 abstract / 15 graph | 2 abstract / 1 graph | 1 | Full graph works, abstract path remains thin |
| How do artists/designers describe originality, style, or visual novelty? | mock fixture abstract-first | 4 | 1 | 2 | 1 | Purpose label is right, evidence corpus is wrong |
| What makes human-AI co-creation preserve or reduce agency? | mock fixture abstract-first | 4 | 1 | 2 | 1 | Co-creation ranks, but accepted claim is still diversity, not agency |

Each abstract-first run resolved the same source status mix:

- `abstract_available`: 1
- `metadata_only`: 1
- `oa_tei_available`: 1
- `oa_pdf_available`: 1

Each run produced 3 completed abstract cards, 1 metadata-only skipped source, 1 accepted quote-backed claim, and 2 rejected claims. The common rejections were `overgeneralized_scope` and `unsupported_claim`; the skipped metadata-only source contributed `abstract_missing` to recommendation logic.

## Metrics

Full fixture graph path:

| Metric | Count |
|---|---:|
| Sources ingested | 3 |
| Chunks | 3 |
| Accepted claims | 15 |
| Rejected claims | 1 |
| Claim quote rows | 15 |
| Accepted claims without primary quote | 0 |
| Active relationships | 2 |
| Relationship evidence rows | 4 |
| Score events | 1 |
| Evidence atoms persisted | 14 |
| Evidence cards exported | 15 |
| Public cards exported | 2 |
| Atlas nodes | 24 |
| Atlas edges | 2 |
| Atlas evidence-card previews | 8 |

Evidence atom maturity:

- `weak`: 11
- `promising`: 3
- `clustered`: 0
- `training_suitability`: all 14 persisted atoms are `not_ready`

The atom promotion command reported 15 promotions but only 14 persisted unique atoms because one duplicate atom ID merged. That is good for stability, but the report should expose dedupe count directly.

## Source Acquisition Findings

The abstract-first resolver is useful as a local-safe front door. It surfaces source statuses before extraction, including metadata-only, abstract-only, OA PDF, and OA TEI availability. It also tells the operator whether abstract extraction is possible and whether full text is fetchable.

The dirty webpage fixture correctly blocked before extraction:

- `acquisition_status`: `dirty_text`
- pipeline status: `blocked_dirty_text`
- extraction: `null`
- quality metrics showed `is_clean: false` and `extractable: false`

The synthetic acquisition summary produced the expected failure modes:

- `blocked_by_quality_gate`
- `parse_failed`
- `webpage_dirty_text`
- `pdf_parser_unavailable`

The weakness: the full fixture graph run report had `sources_with_metadata: 3` but empty `acquisition_status_counts`, `parser_backend_counts`, and `source_type_counts`. That means acquisition diagnostics exist in newer paths, but are not consistently persisted into source metadata across the DB-backed fixture graph path.

## Extraction / Validation Findings

The strongest result is quote grounding. In the full graph fixture, there were 15 accepted claims, 15 quote rows, and zero accepted claims without a primary quote. Rejected claims remain visible; the full graph path preserved one `missing_quote_span` rejection.

The abstract-first path is much weaker. It accepts one claim and rejects two per run. The quote spans on accepted claims are present and compact, but the fixture output repeats the same AI-diversity evidence even for style/originality and agency questions. That makes the current abstract-first loop a proof of plumbing, not a proof of broad research understanding.

## Evidence Atom Findings

Evidence atoms are useful, not redundant, because they package:

- stable atom ID
- canonical claim text
- source claim IDs
- source quote IDs
- concept labels
- stance profile
- support/contradiction counts
- scope
- evidence type
- asset tags
- maturity and training labels

They are not ready as model-training packets yet. Most atoms are single-claim, `weak`, and `not_ready`. The current atom layer is best understood as a reusable, quote-grounded indexing object for retrieval, graph packets, and frontend cards, not as final synthesis material.

## Purpose / Asset Affordance Findings

The deterministic purpose classifier works for broad routing. The style/originality question correctly receives `style_taxonomy`, `visual_descriptor_mining`, `visual_descriptor_candidate`, and `style_vocabulary_candidate`. The other questions route to `theory_building`, `evidence_review`, `reasoning_training_candidate`, `argument_map_candidate`, and `concept_ontology_candidate`.

The problem is downstream evidence mismatch: purpose labels do not force source selection or extraction fixtures to match the requested purpose. A style question still receives AI-diversity evidence. An agency question ranks a co-creation TEI source, but the accepted evidence still centers idea diversity.

## Evidence Cards / Frontend Readiness

Canonical private evidence cards are good enough for operator review and future frontend evidence-card design. They include claim, quote, source metadata, stance, evidence type, scope, concepts, confidence, limitations, asset tags, and maturity.

Atlas-safe previews correctly strip quotes and claim/private identifiers. The fixture Atlas snapshot exported 8 evidence-card previews.

Frontend readiness is **70/100**: schema shape is promising, but maturity labels are conservative, most cards are fixture/synthetic padding, and public cards are still only 2 cards from the fixture path.

## Graph / Atlas Readiness

The graph is receiving meaningful objects, not just text blobs. The full fixture graph has typed concept nodes and relationship edges:

- `AI assistance may_reduce semantic diversity` scoped to short-form writing tasks
- `AI assistance may_increase diversity` scoped to divergent prompting

The graph also preserves the qualification relation as `apparent_contradiction_metric_or_condition_difference`.

Graph readiness is **62/100**. The typed edges are real, but there are only two relationship edges and a narrow domain slice. The Atlas snapshot is useful for proof and preview, not yet for broad insight generation.

## Model Readiness

Local-model readiness: **58/100**.

Local Qwen/Ollama-style models can use the full fixture evidence packets better than raw source text because claims are scoped, quote-backed, concept-linked, and labeled with limitations. But the abstract-first packets are too thin and too repetitive. A local model could still overgeneralize from one accepted abstract claim unless packet builders enforce minimum evidence counts, disagreement inclusion, and source diversity.

Paid-API readiness: **68/100**.

A paid model would receive enough structure to produce better insights than with raw documents: claims, quotes, concepts, scopes, relationships, score events, and cluster packets. But it would still be working from fixture-heavy, narrow, partially synthetic evidence. Paid synthesis should remain gated until acquisition status and source diversity are stronger.

## Improvement-Ticket Findings

Dirty/failed acquisition summaries generate useful improvement tickets. The dirty acquisition fixture and synthetic parser summary generated builder-consumable tickets for:

- `blocked_by_quality_gate`
- `parse_failed`
- `pdf_parser_unavailable`
- `webpage_dirty_text`

The templates include affected modules, expected files, acceptance criteria, test plans, non-goals, risk levels, and rollback plans.

The full fixture graph path generated no draft tickets because `missing_quote_span` is golden-covered and suppressed by ticket generation. That is defensible for not spamming known golden failures, but it creates a reporting mismatch when the packet recommender sees the same reason.

## Packet Recommendation Findings

The recommender is correct for dirty acquisition:

- dominant signal: `webpage_dirty_text`
- recommended packet: `Phase4-P6-web-adapter`
- rationale: webpage HTML normalized to dirty text

The recommender is incomplete for the full fixture run report:

- dominant signal: `missing_quote_span`
- recommended packet: `MVP-P7-demo-loop`
- rationale: no known signal matched

That is a misdiagnosis. If `missing_quote_span` is intentionally golden-covered, the recommender should either suppress it like ticket generation does or map it to quote-first extraction/validator calibration. Falling through to demo-loop polish hides the real blocker.

## Brutal Answers

Is this a real research-data pipeline or still scaffolding?

**Partial.** The full fixture graph path is a real local deterministic research-data spine. The arbitrary research loop is still scaffolding-plus: source resolution, abstract cards, and recommendations work, but question-specific evidence depth is not there.

Can local Qwen/Ollama-style models use the evidence packets without hallucinating?

**Not safely by default.** They can use full fixture packets with less hallucination risk than raw text, but the packets need minimum evidence thresholds and contradiction/source diversity constraints before local synthesis should be trusted.

Would paid API models receive enough structure for good insights?

**Somewhat.** Paid models would get useful structure, but not enough real source breadth. Good insights would be possible on the fixture topic, not on arbitrary questions like artist style or agency.

Are evidence atoms useful or redundant?

**Useful.** They are a stable bridge between claims, quotes, concepts, graph packets, cards, and model inputs. They are weak today because most are one-claim atoms, not because the abstraction is wrong.

Is the graph receiving meaningful objects or text blobs?

**Meaningful objects.** It has concept nodes, scoped predicates, evidence links, and qualification metadata. The issue is small graph size, not object quality.

Do acquisition failures generate correct improvement tickets?

**Yes on direct acquisition summaries.** Dirty text, parse failure, webpage dirty text, and PDF parser unavailable produce useful tickets.

Do packet recommendations diagnose the real blocker?

**Mixed.** Dirty acquisition is diagnosed correctly. Full fixture `missing_quote_span` is misdiagnosed as low-priority demo-loop diagnostics.

Is PDF/full text safely milestone-gated?

**Mostly yes.** Abstract-first extraction runs without requiring full text. Full-text fetchability is surfaced, and selective full text stays fixture/local-safe in this audit. PDF parser unavailable is correctly treated as a milestone packet, not silently folded into MVP success.

What breaks at 100 sources?

- Serial fixture-style orchestration becomes slow and noisy.
- Repeated JSON report writes become hard to inspect.
- Run reports need better source-status aggregation and pagination.
- One-claim atoms will flood packets unless dedupe/cluster promotion improves.
- Ranking will need stronger topic-purpose alignment.

What breaks at 1,000 sources?

- SQLite can store the rows, but current report builders and packet constructors are too broad-scan oriented.
- Evidence card export and Atlas snapshot generation need pagination/windowing.
- Claim validation and quote-span checks need batch diagnostics.
- Source acquisition failures need durable rows for blocked sources, not just transient command output.
- Packet recommendation needs weighted precedence, otherwise minor validation failures can mask acquisition/parser walls.

## Readiness Scores

| Area | Score | Reason |
|---|---:|---|
| Graph / Atlas | 62/100 | Typed objects and useful edges, but tiny graph and inconsistent acquisition metadata |
| Local model packets | 58/100 | Good structure on full fixture packets, too thin for arbitrary questions |
| Paid API synthesis | 68/100 | Structured enough for constrained synthesis, not enough real source breadth |
| Frontend evidence cards | 70/100 | Canonical card shape and previews work; content maturity remains weak |

## Strongest Parts

- Accepted claims are quote-backed in the full graph path.
- Rejected claims keep machine-readable reasons.
- Evidence atoms provide stable reusable research objects.
- Cluster packets include claims, sources, score events, and top atoms.
- Atlas snapshot contains meaningful concept nodes and scoped relationship edges.
- Dirty acquisition blocks before extraction.
- Acquisition failure summaries can generate builder-consumable tickets.

## Weakest Parts

- Abstract-first runs are too shallow and reuse the same evidence across different questions.
- Acquisition status/parser metadata is not consistently persisted into DB-backed run reports.
- Packet recommendation can misdiagnose known claim failures.
- Evidence atoms are mostly weak/not-ready and one-claim.
- Purpose labels do not yet constrain source selection enough.
- The full fixture graph contains synthetic padding claims to hit cluster thresholds.

## Drift Warnings

- Do not mistake fixture graph success for arbitrary-source readiness.
- Do not ship paid synthesis on abstract-first packets until minimum evidence and source-diversity gates exist.
- Do not add automation before acquisition failures are durable and queryable.
- Do not make evidence cards public-facing until maturity/source-type labels are visually obvious.

## Top 5 Fixes

1. **Persist acquisition status everywhere.** Blocked dirty sources, parser failures, PDF unavailable, source type, and parser backend need durable source/acquisition rows that run reports and cluster reports can aggregate.
2. **Fix packet recommender precedence.** Align recommender suppression/mapping with ticket generation for `missing_quote_span`, and weight acquisition/parser failures above minor known fixture rejections.
3. **Make question-purpose constrain retrieval.** Style/originality and agency questions should not accept generic AI-diversity evidence as sufficient.
4. **Upgrade evidence atom maturity logic.** Promote clustered/multi-source atoms when claims share scope/relationship context, and expose dedupe counts.
5. **Add scale-safe packet builders.** Add source windows, pagination, batch diagnostics, and per-cluster packet limits before 100+ source runs.

## Recommended Next Packet

**Phase4-P6-web-adapter plus acquisition-status persistence and recommender precedence fix.**

The next highest-leverage fix is not more automation. It is making acquisition/parser/quality-gate state durable, visible, and correctly prioritized in packet recommendations. Once that is reliable, automation can choose the right next build packet instead of polishing the wrong layer.
