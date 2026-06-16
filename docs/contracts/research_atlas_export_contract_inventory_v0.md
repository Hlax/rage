# Research Atlas Export Contract Inventory v0

- Inventory schema: `research_atlas_export_inventory_v0.1.0`
- Atlas snapshot contract: `atlas_snapshot_v0.1.0`

## Current DB tables

- `candidate_sources`
- `chunks`
- `claim_concepts`
- `claim_quotes`
- `claims`
- `cluster_reports`
- `concepts`
- `domain_proposals`
- `improvement_tickets`
- `node_reports`
- `ontology_proposals`
- `public_cards`
- `relationship_evidence`
- `relationships`
- `research_contracts`
- `research_queue`
- `research_runs`
- `run_reports`
- `safety_audits`
- `score_events`
- `sources`
- `theory_candidates`

## Schema / contract files

- `rge/db/schema.sql` — sqlite canonical schema
- `rge/models/schemas.py` — core entity schema stub / data model mirror
- `rge/llm/schemas.py` — versioned pydantic candidate model outputs
- `rge/contracts/atlas_snapshot_v0.py` — Research Atlas snapshot v0 contract
- `rge/modules/atlas_snapshot_builder.py` — Research Atlas snapshot DB projection + export helper
- `rge/contracts/review_batch_v0.py` — Agent Lab review_batch v0 private contract
- `rge/safety/public_export_policy.py` — public card export allowlist policy

## Report JSON shapes

- **run_report** (0.1.0) [operator_private] — rge/modules/run_evaluator.py: `run_id`, `topic`, `domain_pack`, `contract_id`, `claims_accepted`, `claims_rejected`, `top_failure_modes`, `safety_audit_status`
- **cluster_report** (0.1.0) [operator_private] — rge/modules/cluster_reporter.py: `cluster_id`, `claim_ids`, `summary`, `stance_mix`
- **theory_candidate_report** (0.1.0) [operator_private] — rge/modules/theory_generator.py: `theory_id`, `hypothesis`, `supporting_claim_ids`
- **operator_proof_bundle** (implicit) [operator_private] — rge/modules/operator_proof_bundle.py: `pipeline_mode`, `source_id`, `claim_count`, `export_path`, `usable_output`
- **safety_audit_report** (implicit) [operator_private] — rge/modules/safety_auditor.py: `audit_type`, `status`, `blocked_reasons`

## Export JSON shapes

- **public_cards.json** (0.1.0) [public_safe_when_curated] — rge/modules/card_exporter.py: `id`, `type`, `title`, `summary`, `confidence`, `concepts`, `source_count`, `public_caveats`, `public_source_metadata`, `related_cards`, `public_detail_level`, `evidence_type`, `public_run_timestamp`, `updated_at`
- **build_info.json** (0.1.0) [public_safe] — rge/modules/card_exporter.py: `export_schema_version`, `generated_at`, `phase`, `card_count`, `memo_count`
- **public_memos.json** (0.1.0) [public_safe_when_curated] — rge/modules/card_exporter.py: `id`, `title`, `summary`, `updated_at`
- **snapshot_manifest.json** (implicit) [operator_private] — rge/modules/card_exporter.py: `generated_at`, `bundle_files`, `card_count`
- **review_batch.json** (review_batch_v0.1.0) [agent_lab_private] — rge/contracts/review_batch_v0.py (contract only; persistence TBD): `schema_version`, `batch_id`, `classification`, `review_scope`, `model_runtime`, `inputs`, `outputs`, `safety`
- **atlas_snapshot.json** (atlas_snapshot_v0.1.0) [operator_private] — rge/cli.py export-atlas-snapshot (rge/modules/atlas_snapshot_builder.py): `schema_version`, `generated_at`, `snapshot_id`, `root`, `domains`, `runs`, `nodes`, `edges`, `clusters`, `reports`, `cards`, `safety`

## Public-site data readers

- `apps/public-site/lib/publicCards.ts` — PublicCard type + card/concept helpers
- `apps/public-site/app/page.tsx` — imports public_cards.json, public_memos.json, build_info.json
- `apps/public-site/app/about/page.tsx` — imports build_info.json
- `apps/public-site/app/cards/[id]/page.tsx` — static card detail via generateStaticParams
- `apps/public-site/app/concepts/[id]/page.tsx` — concept pages from exported card concepts

## Golden test coverage

- `tests/golden/test_00_model_runtime.py`
- `tests/golden/test_00_public_site_static.py`
- `tests/golden/test_00_scaffold.py`
- `tests/golden/test_01_ingestion.py`
- `tests/golden/test_02_claim_extraction.py`
- `tests/golden/test_02_claim_extraction_overlap_domain.py`
- `tests/golden/test_05_concept_linking.py`
- `tests/golden/test_06_relationship_builder.py`
- `tests/golden/test_07_contradiction_detection.py`
- `tests/golden/test_08_score_reconciliation.py`
- `tests/golden/test_09_research_queue.py`
- `tests/golden/test_10_research_contract_drift.py`
- `tests/golden/test_11_public_card_export.py`
- `tests/golden/test_12_public_site_static_render.py`
- `tests/golden/test_13_cluster_report.py`
- `tests/golden/test_15_theory_generator.py`
- `tests/golden/test_16_question_generation.py`
- `tests/golden/test_17_ontology_pressure.py`
- `tests/golden/test_18_domain_proposal.py`
- `tests/golden/test_19_run_report.py`
- `tests/golden/test_20_improvement_tickets.py`
- `tests/golden/test_21_builder_ticket_consumption.py`
- `tests/golden/test_22_builder_golden_gate.py`
- `tests/golden/test_23_safety_audit_gate.py`
- `tests/golden/test_24_prompt_injection.py`
- `tests/golden/test_25_public_site_debug_details.py`
- `tests/golden/test_26_full_mvp_run.py`

## Private / public safety classification

- **sqlite research graph (claims, sources, relationships)** — `operator_private`: Never exported raw; public export uses curated cards only
- **public_cards.json / public_memos.json / build_info.json** — `public_safe_when_curated`: Fail-closed export policy in public_export_policy.py
- **run_report / cluster_report / theory_candidate** — `operator_private`: Reporting spec envelopes; not on public site today
- **improvement_tickets** — `agent_lab_private`: Structured builder queue; must not clutter public atlas
- **model invocation metadata / live_probe scratch** — `operator_private`: Scattered invocation metadata; review_batch contract is separate durable envelope
- **review_batch_v0.1.0** — `agent_lab_private`: Private principal review envelope; contract defined ticket-280
- **atlas_snapshot_v0.1.0** — `operator_private`: Validated snapshot content is curated public-safe; export-atlas-snapshot writes operator-private JSON (ticket-282)
- **media / images** — `deferred`: Text-first graph; optional media_assets table reserved for later

## Gaps vs Research Atlas + Agent Lab needs

- **[medium]** no_explicit_public_atlas_snapshot_export: Operator-private export-atlas-snapshot CLI exists (ticket-282); public atlas route and public-site consumption still deferred
- **[medium]** no_review_batch_or_synthesis_batch_object: review_batch_v0.1.0 contract shape defined (ticket-280); persistence and stronger-model wiring deferred
- **[medium]** domain_links_not_normalized_for_ui: Domain pack supports overlap/parent/child; atlas needs stable domain_links[]
- **[low]** research_question_lineage_not_explicit: runs[] projection adds optional lineage fields (ticket-281); dedicated research_questions table still deferred
- **[medium]** agent_lab_not_separated_from_research_graph: Improvement tickets should export to private Agent Lab layer by default
- **[expected]** nodes_edges_clusters_empty_in_v0_contract: v0 reserves arrays; fixture-mode DB population wired (ticket-279); full live graph projection deferred
- **[intentional]** images_not_in_core_graph: Text-first; reserve optional asset metadata only; no base64 in graph JSON
