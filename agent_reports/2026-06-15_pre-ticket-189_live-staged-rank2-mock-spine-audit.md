---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-190
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-190 Live Staged Rank-2 Candidate Mock Spine

## Verdict: **GO**

## Context

ticket-187 proves live OpenAlex rank-1 through generate-run-report. ticket-158 proves
rank-2 staged mock spine with explicit `staged_fetch_second_candidate_*` fixtures on
patched network. This ticket bridges: **real discover/fetch for rank-2 candidate only**,
then **mock-fixture extract→report** (second-candidate fixture set).

## Hardened scope

### In

1. `tests/unit/test_live_staged_rank2_report_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_RANK2=1`, `RGE_ALLOW_SOURCE_NETWORK=1`,
   `OPENALEX_MAILTO`
3. **Local-only** domain opposing-context seed before live discover (ticket-181 pattern)
4. Live discover → select **rank-2** candidate (`ORDER BY rank ASC LIMIT 1 OFFSET 1`)
   → fetch → ingest
5. Explicit mock fixtures:
   `staged_fetch_second_candidate_extract_claims.json` through
   `staged_fetch_second_candidate_detect_contradictions.json`, then deterministic
   `reconcile-scores` and `generate-run-report`
6. Assert `run_reports` ≥ 1 and second-candidate source ingested (title match
   `%Constraint%` or rank-2 candidate row)
7. Env gate skip test; `test_ci_golden_gate.py` deselect assertion

### Out

- Rank-1 + rank-2 dual live orchestration in one test (defer to fixture-mode orchestrator)
- Live LLM, export-public, schema changes, CI live network

## Safety

- Network: OpenAlex discover/fetch for single rank-2 candidate after local seed
- Temp DB and `--output-dir` only

## Operator opt-in

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_report_mock_spine.py -m live_network -q
```

## Rollback

Remove test file; retain ticket-187 rank-1 proof.

## Recommendation

**GO** — implement ticket-190; seed ticket-191 docs cross-link.
