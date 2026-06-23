# Ticket-386 — README operator quickstart researcher product proof cross-link v0

**Date:** 2026-06-23  
**Branch:** `phase-3/ticket-386-readme-researcher-product-proof-crosslink`  
**Ticket:** ticket-386  
**Audit gate:** satisfied — `agent_reports/2026-06-23_principal-audit-post-ticket-384.md`

## Summary

Documented the mock-first `prove-researcher-product` operator workflow in README Operator
Quickstart: CLI and script commands, gitignored artifact path, key artifact fields,
`researcher_product_proof_status` plan/verify/autocycle fields, and autocycle blocking note.
Added artifact path rows to the README Artifact Paths table.

## Scope

**In:** `README.md` Operator Quickstart section + artifact paths table.

**Out:** CLI code, operator loop, verify, autocycle, AGENTS.md (ticket-387 follow-on).

## Changed files

| File | Change |
|------|--------|
| `README.md` | Researcher product proof quickstart + status field table + artifact paths |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| README documents `prove-researcher-product` and gitignored artifact path | **PASS** |
| README notes `researcher_product_proof_status` / `product_verdict` without full plan JSON dump | **PASS** |
| No CLI or export code changes | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `python -m pytest tests/golden -q` | **165 passed** |

Safety audit not required (docs-only; no public export or route changes).

## Merge to main

Merge commit: `30da5f8278828f4b606383ce1b9f9d30811d54ea`

Post-merge `python -m pytest -q`: 1353 passed, 1 failed (flaky
`test_export_atlas_snapshot_matches_committed_fixture_after_summary`; passed on isolated re-run).
Golden gate unchanged at 165 passed.

## Recommended next ticket

**ticket-387** — AGENTS.md operator loop researcher product proof cross-link v0 (mirror README;
non-goal for ticket-386).

## Suggested next prompt

```
/rge-run-next-ticket
```

Or operator one-time: `python -m rge.cli prove-researcher-product --work-dir data/tmp/researcher_product_proof_work` to populate artifact and clear drift.
