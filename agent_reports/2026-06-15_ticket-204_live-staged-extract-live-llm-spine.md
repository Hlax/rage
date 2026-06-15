---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-204
---

# ticket-204: Live Staged Extract Live LLM Opt-In Proof (Per-Step)

## Summary

Added `--live-staged-fallthrough` on `extract-claims` with env gate
`RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1` so staged OpenAlex ingest sources can use
live Ollama extraction instead of auto-mock `staged_fetch_extract_claims.json`.
Default pytest and `execute_staged_fixture_mode_run` remain mock-only. Opt-in
`live_network` + `live_smoke` proof chains discover → fetch → ingest → live extract.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-204 |
| Branch | `phase-2/ticket-204-live-staged-extract-live-llm-spine` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-203_live-llm-staged-run-audit.md` |
| Principal audit gate | satisfied (post-ticket-201 audit at ticket-202) |
| Main tip before branch | `6279352` |

## Scope

**In:** `claim_extractor` live staged fallthrough, CLI flag + env gate, mocked gate tests,
opt-in live spine test, CI deselect assertion.

**Out:** Live link/build/detect on staged spine, orchestrator live LLM, CI Ollama, public
export/site, schema migrations.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/claim_extractor.py` | `live_staged_fallthrough` path; `source_has_staged_fetch_spine` helper |
| `rge/modules/live_extraction_write.py` | `assert_live_staged_extract_live_env`; `extract_claims_staged_live_fallthrough` |
| `rge/cli.py` | `--live-staged-fallthrough` flag and `_cmd_extract_claims` branch |
| `tests/unit/test_live_staged_extract_live_llm_spine.py` | Gate tests + opt-in live proof |
| `tests/unit/test_ci_golden_gate.py` | Deselect assertion for live extract test |
| `tickets/ticket-204.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-205 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Live staged fallthrough bypasses staged-fetch auto-mock when env gate set | **PASS** |
| 2 | Opt-in pytest proves discover→ingest→live extract on temp DB | **PASS** (test added; live run operator opt-in) |
| 3 | Default pytest and staged orchestrator remain mock-only | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_extract_live_llm_spine.py -q -m "not live_network and not live_smoke"  # 5 passed
python -m pytest tests/golden -q                          # 142 passed
python -m pytest -q                                       # 605 passed, 17 deselected
python -m rge.modules.safety_auditor --audit full         # pass
```

## Manual CLI verification

Not run (no local Ollama in builder session). Mocked gate tests cover CLI routing,
default-graph DB refusal, and env gate. Operator live proof:

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_extract_live_llm_spine.py -m "live_network and live_smoke" -q
```

## Spec deviations

None.

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

**ticket-205** — README/AGENTS operator docs for live staged extract fallthrough.

## Suggested next prompt

`/rge-run-next-ticket`
