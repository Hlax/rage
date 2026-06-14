---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-153
---

# ticket-153: Extract Claims from Second Staged-Ingested Source (Mock Spine Step)

## Summary

Added mock LLM fixture and unit tests proving **extract-claims** on OpenAlex rank #2
(`disc_openalex_W1234567890`) after ticket-152 fetch/ingest-staged. Uses explicit
`--fixture staged_fetch_second_candidate_extract_claims.json`. No production code changes.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-153 |
| Branch | `phase-2/ticket-153-second-staged-extract-spine` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-153_second-staged-extract-audit.md` (GO) |
| Principal audit gate | Cadence at threshold (post ticket-150); pre-ticket audit satisfied |
| Main tip before branch | `8dbd290` |

## Scope

### In

- `fixtures/llm_outputs/staged_fetch_second_candidate_extract_claims.json`
- `tests/unit/test_staged_second_candidate_extract_spine.py` (2 tests)

### Out

- Link/build/detect, live LLM/network, schema, public export/site

## Changed files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_second_candidate_extract_claims.json` | 1 accepted + 1 rejected |
| `tests/unit/test_staged_second_candidate_extract_spine.py` | discover→fetch→ingest→extract |
| `agent_reports/2026-06-14_pre-ticket-153_second-staged-extract-audit.md` | pre-ticket audit (GO) |
| `tickets/ticket-153.json` | status done |
| `tickets/ticket-154.json` | seeded link-concepts on second staged source |
| `tickets/TICKET_QUEUE.md` | ticket-153 done |

## Extract results

| Metric | Value |
|--------|-------|
| accepted | 1 (`Constraint management improves…`) |
| rejected | 1 (`missing_quote_span`) |
| scope (accepted) | `AI-assisted creative team workflows` (verbatim in claim_text) |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | extract-claims with deterministic fixture on rank #2 | **PASS** |
| 2 | Distinct mock HTML/fixture for constraint-management candidate | **PASS** |
| 3 | No live LLM in default collection | **PASS** |
| 4 | Golden mock-only pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_extract_spine.py -q   # 2 passed
python -m pytest tests/unit/test_staged_second_candidate_spine.py -q           # 2 passed
python -m pytest tests/golden -q                                                # 142 passed
python -m pytest -q                                                             # 562 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                               # pass
```

## Spec deviations

- Accepted claim `scope` must appear verbatim in `claim_text` per `claim_validator`; used `AI-assisted creative team workflows` (not plural `teams` from pre-ticket audit draft).
- No `claim_extractor` auto-select heuristic (explicit `--fixture` per hardened audit scope).

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

**ticket-154** — Link concepts on second staged-ingested source (mock spine step).

Principal cadence note: run `/rge-principal-audit` after ticket-154 (4 done since post-ticket-149 checkpoint).

## Suggested next prompt

`/rge-run-next-ticket` for ticket-154 with pre-ticket audit (medium risk).
