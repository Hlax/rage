---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-187
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-187 Live Staged Generate-Run-Report Spine

## Verdict: **GO**

## Context

ticket-184 proves live OpenAlex discover→reconcile with mock LLM fixtures through detect.
ticket-149 proves full mock spine through `generate-run-report` on staged-ingested sources
(deterministic Python; no LLM). This ticket bridges: **real network through reconcile**,
then **deterministic generate-run-report** on the temp DB.

## Hardened scope

### In

1. `tests/unit/test_live_staged_report_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_REPORT=1`, `RGE_ALLOW_SOURCE_NETWORK=1`,
   `OPENALEX_MAILTO`
3. **Local-only** domain opposing-context seed before live discover (ticket-181 pattern)
4. Real discover → fetch → ingest → extract/link/build/detect with explicit mock fixtures
   → `reconcile-scores` (deterministic)
5. `generate-run-report` with fixed `--run-id`, `--topic`, `--domain`, `--output-dir`
   (temp paths only; **not** public export)
6. Assert `run_reports` row count ≥ 1 and `run_report_latest.json` written to temp dir
7. Env gate skip test in default collection
8. `test_ci_golden_gate.py` — deselect assertion for live report test

### Out

- Live LLM, `export-public`, public site changes
- Writing reports outside temp `--output-dir` / `--db` in tests
- Schema migrations, CI live network

## Safety

- Network: OpenAlex discover/fetch only (after local seed)
- Report generation reads DB metrics only; output to operator temp dir in test
- No public export boundary changes

## Operator opt-in

```powershell
$env:RGE_ALLOW_LIVE_STAGED_REPORT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_report_mock_spine.py -m live_network -q
```

## Rollback

Remove test file; retain ticket-184 reconcile proof.

## Recommendation

**GO** — implement ticket-187; seed ticket-188 docs cross-link.
