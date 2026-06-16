# Agent Report: ticket-292 — Fixture-mode export + atlas coherence CLI pipeline e2e

**Date:** 2026-06-16  
**Ticket:** ticket-292  
**Branch:** `phase-3/ticket-292-atlas-coherence-cli-pipeline-fixture`  
**Main tip before branch:** `221393e`  
**Audit gate:** `agent_reports/2026-06-16_principal-audit-post-ticket-291.md` (GO)

## Summary

Added network-free default pytest that builds a fixture-mode MVP DB, chains
`export-atlas-snapshot` CLI → `atlas-coherence-report` CLI, and asserts coherence
verdict plus population thresholds. Closes the Research Atlas regression-proof layer
alongside ticket-291's opt-in live_network CLI pipeline proof.

## Scope

**In:** Fixture-mode CLI pipeline e2e test module.

**Out:** Production code changes, public export/site, schema migrations, README/AGENTS
cross-links, live_network proof, public atlas route/UI, review_batch persistence.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_atlas_coherence_cli_pipeline_fixture.py` | Network-free CLI pipeline e2e |
| `tickets/ticket-292.json` | Status `done` |
| `tickets/ticket-293.json` | Seeded next product ticket |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Network-free pytest: fixture MVP DB → export CLI → coherence CLI | **PASS** |
| Asserts `overall_coherence_verdict` pass/partial + population thresholds | **PASS** |
| Golden + full pytest green | **PASS** — 142 golden, 745 full |
| No public export/site/schema changes | **PASS** |

## Pipeline proof artifact

**Primary artifact:** `tests/unit/test_atlas_coherence_cli_pipeline_fixture.py::test_fixture_mode_export_and_coherence_cli_pipeline`

This test proves the Atlas export + coherence report pipeline works without network by:

1. Building a fixture-mode MVP DB via `execute_fixture_mode_run` (mock LLM).
2. Running `export-atlas-snapshot --fixture-mode` and asserting CLI stdout + written snapshot.
3. Running `atlas-coherence-report` and asserting CLI stdout + written JSON/markdown report.

## Stability characterization

| Stage | Stability |
|-------|-----------|
| Atlas snapshot export (`--fixture-mode`) | **Byte-stable** — exported snapshot bytes match committed `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` |
| Coherence report JSON | **Structurally stable** — verdict enum, population thresholds, and safety fields asserted; exact byte identity not required (report includes runtime-derived metadata) |

## Private-field scanning and validation

**Yes — both stages enforce validation before write:**

- **Export:** Test asserts `validate_atlas_snapshot(snapshot)` and `assert_no_private_fields(snapshot) == []` on the written snapshot. Export CLI delegates to `export_atlas_snapshot_to_path`, which runs private-field scan and contract validation before disk write (fail-closed).
- **Coherence report:** Written report JSON asserts `safety.contract_valid is True` and `safety.private_field_violations == []`.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_coherence_cli_pipeline_fixture.py -q  # 1 passed
python -m pytest tests/golden -q                                              # 142 passed
python -m pytest -q                                                           # 745 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                             # pass
cd apps/public-site && npm run build                                          # success
```

Safety audit run — no public surface changes; confirms existing boundary posture.

## Manual CLI verification

Encapsulated in fixture pipeline test; no separate manual run required.

## Spec deviations

None.

## Drift note

Ticket-292 **closes the Research Atlas regression-proof layer** (fixture-mode default
pytest + ticket-291 live_network opt-in). The next ticket should **not** be another
operator-tooling-only or docs-only ticket. **ticket-293** shifts to product-centered
live NM-1 extraction expansion with Atlas coherence quality assessment.

## Recommended next ticket

**ticket-293** — Live NM-1 extraction expansion + Atlas coherence quality proof v0

Goal: prove live research extraction produces meaningful research graph data, not just
pipeline mechanics. Operator opt-in live gates only; private atlas snapshot export +
coherence report with human-readable quality verdict (GO/PARTIAL/NO-GO).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: _(pending)_
