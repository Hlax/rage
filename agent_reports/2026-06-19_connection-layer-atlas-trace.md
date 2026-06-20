# Connection Layer + Atlas Trace Contract

- Template: `connection-layer-atlas-trace`
- Date: 2026-06-19
- Scope: persist acquisition/source status, fix recommender precedence, add Atlas trace contract and graph connection metrics.

## Summary

Implemented a backend connection layer that carries acquisition/parser status into durable `sources` metadata, DB-backed run reports, improvement-packet recommendations, and Atlas snapshot projections.

Added private Atlas trace rows for source -> quote -> claim -> atom -> concept -> cluster debugging, plus Atlas-safe trace previews that strip private IDs and raw text. Added graph connection metrics that expose low relationship density, orphan claims, orphan atoms, and contradiction/qualification edge counts.

## Changed Files

- `rge/modules/acquisition_quality.py`
- `rge/modules/web_source_adapter.py`
- `rge/modules/research_spine.py`
- `rge/modules/failure_recommender.py`
- `rge/modules/atlas_trace.py`
- `rge/modules/run_evaluator.py`
- `rge/modules/atlas_snapshot_builder.py`
- `rge/modules/atlas_coherence_report.py`
- `rge/contracts/atlas_snapshot_v0.py`
- `tests/unit/test_connection_layer_atlas_trace.py`
- `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`

## Verification

- `python -m pytest tests/unit/test_connection_layer_atlas_trace.py tests/unit/test_acquisition_quality.py tests/unit/test_failure_recommender.py tests/unit/test_atlas_snapshot_builder.py -q` -> pass, `28 passed`
- `python -m pytest tests/unit/test_safety_auditor_atlas_preview.py tests/unit/test_atlas_snapshot_contract.py tests/unit/test_atlas_coherence_report.py -q` -> pass, `16 passed`
- `python -m pytest tests/golden/test_19_run_report.py tests/golden/test_35_acquisition_quality_tickets.py -q` -> pass, `7 passed`
- `python -m rge.modules.safety_auditor --audit full` -> pass
- `ReadLints` on edited Python/test files -> no linter errors

Full verification was not run because this packet did not add migrations, change public card export schema, alter quote validation, or change source download behavior. The Atlas-safe preview and safety boundary were covered by targeted tests and full safety audit.

## Acceptance Criteria Status

- Acquisition/source status persistence: complete. Dirty webpage sources and failed selective full-text acquisitions now upsert durable `sources` rows with normalized metadata.
- DB-backed run reports include acquisition counts: complete. Reports now include source/acquisition/parser/source-type/quality-gate/extractable/failure/resolver/availability summaries.
- Recommender precedence: complete. Acquisition/parser blockers outrank extractor/demo-loop signals, and `missing_quote_span` maps to quoteability remediation.
- Atlas trace object: complete. Private trace export includes question, cluster, atom, claim, quote, source, concept, relationship, connection type, maturity, visibility, and why-connected fields.
- Public-safe trace preview: complete. Snapshot preview strips private IDs and raw text.
- Graph/Atlas connection metrics: complete. Run reports and Atlas snapshots expose per-cluster density and orphan metrics.

## Safety

Private quote/claim/source IDs are only present in private trace export objects. Atlas snapshot previews use non-private keys (`trace_ref`, counts, maturity, connection type, explanation) and pass the existing private-field scan and full safety audit.

## Known Risks

- Existing evidence atoms are still mostly one-claim atoms; this packet measures that weakness but does not densify atoms.
- Relationship density is now visible, but relationship generation itself is unchanged.
- Public-site UI was intentionally not built or broadened.

## Next 3 Recommended Packets

1. Multi-claim Evidence Atom Consolidation: merge compatible quote-backed claims into stronger atoms, preserving contradiction/qualification profiles.
2. Relationship Density Expansion: generate and validate additional typed relationships per cluster, with tests for source diversity and non-duplicative edges.
3. Question-Aware Source Diversification: prevent abstract-first runs from reusing narrow evidence across unrelated questions by adding question/source-fit memory and diversity penalties.
