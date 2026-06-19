# Packet 001 Evidence Report: Purpose + Evidence Atom Schema Foundation

Date: 2026-06-19
Branch: `phase-4/packet-001-purpose-evidence-atoms`
Status: GO

## Summary

Implemented the Packet 1 foundation for research-purpose metadata, evidence atoms,
canonical operator-private evidence cards, and conservative maturity/training labels.
The implementation is deterministic and mock-only; it does not add live network/API
behavior and does not change public export allowlists.

## Evidence

- Added versioned Pydantic contracts for:
  - `research_intent`
  - `asset_affordance`
  - `evidence_maturity`
  - `training_suitability`
  - `evidence_atom`
  - canonical operator-private `evidence_card`
- Added deterministic purpose classifier stubs for:
  - AI + creativity questions
  - art/design/visual descriptor questions
  - benchmark/evaluation questions
  - conservative generic fallback
- Added SQLite migration `0009_purpose_evidence_atoms`:
  - `research_contracts.purpose_metadata_json`
  - operator-private `evidence_atoms`
- Updated `schema.sql` and repository persistence for purpose metadata.
- Added claim-backed atom/card builders that require accepted quote-backed claims.
- Propagated purpose/maturity/training metadata into:
  - run report JSON
  - cluster report JSON
  - cluster evidence packet `top_evidence_atoms`
- Kept public export behavior unchanged.

## Changed Files

- `rge/contracts/__init__.py`
- `rge/contracts/evidence_atom_v0.py`
- `rge/db/migrations/0009_purpose_evidence_atoms.sql`
- `rge/db/repositories.py`
- `rge/db/schema.sql`
- `rge/modules/cluster_reporter.py`
- `rge/modules/evidence_atoms.py`
- `rge/modules/research_planner.py`
- `rge/modules/research_purpose.py`
- `rge/modules/run_evaluator.py`
- `tests/golden/test_00_scaffold.py`
- `tests/golden/test_01_ingestion.py`
- `tests/golden/test_13_cluster_report.py`
- `tests/golden/test_19_run_report.py`
- `tests/unit/test_evidence_atoms.py`
- `tests/unit/test_research_purpose_classifier.py`

## Commands Run

- `python -m pytest tests/unit/test_research_purpose_classifier.py tests/unit/test_evidence_atoms.py tests/golden/test_00_scaffold.py tests/golden/test_13_cluster_report.py tests/golden/test_19_run_report.py -q`
  - First run: failed on an over-broad `design` keyword in the classifier.
  - Fix: narrowed visual/design matching to visual/art/product-design contexts.
- `python -m pytest tests/unit/test_research_purpose_classifier.py tests/unit/test_evidence_atoms.py tests/golden/test_00_scaffold.py tests/golden/test_13_cluster_report.py tests/golden/test_19_run_report.py -q`
  - Result: 25 passed.
- `python -m rge.cli verify --skip-site`
  - First run: failed because `tests/golden/test_01_ingestion.py` hard-coded the migration list and did not include `0009_purpose_evidence_atoms`.
  - Safety audit step in that run passed.
- `python -m pytest tests/golden/test_01_ingestion.py tests/unit/test_research_purpose_classifier.py tests/unit/test_evidence_atoms.py tests/golden/test_13_cluster_report.py tests/golden/test_19_run_report.py -q`
  - Result: 19 passed.
- `python -m rge.cli verify --skip-site`
  - Result: pass.
  - Golden tests: 157 passed.
  - Full pytest: 934 passed, 35 deselected.
  - Safety audit: pass.

## Acceptance Criteria

- Purpose metadata can be stored on research contracts: PASS.
- Purpose metadata appears in report outputs: PASS.
- Evidence atom schema exists: PASS.
- Claim-backed evidence atom promotion exists: PASS.
- Canonical evidence card schema exists: PASS.
- Deterministic classifier stubs exist: PASS.
- Conservative maturity/training defaults are used: PASS.
- Tests prove propagation into reports/artifacts: PASS.

## Safety Notes

- No public write routes added.
- No public ingestion routes added.
- No public agent execution routes added.
- No model output writes directly to accepted tables.
- Evidence atoms/cards are operator-private foundations.
- Public card allowlists were intentionally left unchanged.
- Canonical evidence cards include short quote spans only and are not exported publicly.
