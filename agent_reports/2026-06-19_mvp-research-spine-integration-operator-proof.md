# MVP Research Spine Integration — Operator Proof

**Date:** 2026-06-19  
**Branch:** `phase/mvp-research-spine-integration`

## Env profile (opt-in)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_STAGED_SELECTIVE_FULLTEXT = "1"
$env:RGE_ALLOW_LIVE_SELECTIVE_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "0"   # fixture staged path
$env:OPENALEX_MAILTO = "operator@example.com"
```

## Results

| Proof | Command | Result |
|-------|---------|--------|
| Staged orchestrator + selective full-text | `pytest tests/unit/test_staged_orchestrator_selective_fulltext.py::test_execute_staged_fixture_mode_run_selective_fulltext_opt_in` | **PASS** — `selective_fulltext_wiring` accepted_claims ≥ 1 |
| Live selective fetch gate | `pytest tests/unit/test_live_selective_fulltext_validation.py -m live_network` | **PASS** (2 tests) |
| Research-run DB persist | `research-run --fixture-mode --mode full-text-augmented --db ... --persist-claims` | **PASS** — 1 full-text claim in DB (`clm_9a844fbbb085e818`) |

## Notes

- Bare `research run --staged-spine` with network on but **without** `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=0` attempted live OpenAlex fetch and skipped with `unsuitable_live_artifact` (expected publisher blocks).
- Fixture staged + selective full-text proof uses patched OpenAlex HTML in pytest (same as ticket-162 spine tests).

## Verdict

**GO** — opt-in gates proven on temp/scratch paths.
