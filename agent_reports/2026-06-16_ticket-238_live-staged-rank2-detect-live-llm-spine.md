# Agent Report: ticket-238 — Live staged rank-2 detect live LLM opt-in proof

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-238  
**Branch:** `phase-3/ticket-238-rank2-detect-live-llm-spine`  
**Status:** implemented

## Summary

Added per-step rank-2 live Ollama detect on staged OpenAlex ingest with mandatory
`seed_domain_opposing_context` and mock extract + mock link + mock build upstream,
mirroring ticket-217 with separate env gate (`RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1`),
CLI flag (`--live-staged-rank2-detect-fallthrough`), and rank-2 title heuristic.
**Completes rank-2 per-step live Ollama surface** (extract/link/build/detect).

## Audit gate

- Pre-ticket: `agent_reports/2026-06-16_pre-ticket-238_rank-2-staged-detect-live-llm-audit.md` (GO)

## Scope in / out

**In:** rank-2 detect fallthrough, env gate, CLI flag, pytest spine, operator docs.

**Out:** orchestrator live LLM, live reconcile/report, CI Ollama, public export, schema migrations.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/contradiction_detector.py` | `live_staged_rank2_detect_fallthrough`, `detect_contradictions_staged_rank2_live_fallthrough` |
| `rge/cli.py` | `--live-staged-rank2-detect-fallthrough` handler |
| `tests/unit/test_live_staged_rank2_detect_live_llm_spine.py` | 6 mock + 1 live_network/live_smoke |
| `README.md`, `AGENTS.md`, `docs/agents/12_RUNTIME_CONFIG.md`, `.env.example` | Operator docs |
| `tickets/TICKET_QUEUE.md`, `tickets/ticket-238.json`, `tickets/ticket-239.json` | Queue updates |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM` + CLI fallthrough | **PASS** |
| 2 | Rank-2 heuristics; rank-1 unchanged | **PASS** |
| 3 | `seed_domain_opposing_context` before live discover | **PASS** |
| 4 | Opt-in live_network pytest; excluded default | **PASS** (30 deselected) |
| 5 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_rank2_detect_live_llm_spine.py -q  # 6 passed, 1 deselected
python -m pytest tests/golden -q                                                 # 142 passed
python -m pytest -q                                                            # 666 passed, 30 deselected
```

Safety audit not required — live LLM opt-in only; no public export or schema changes.

## Merge to main

Pending merge commit hash (recorded after step 12).

## Recommended next ticket

**ticket-239** — principal audit post rank-2 live LLM closure checkpoint.

## Suggested next prompt

`/rge-principal-audit` or `/rge-run-next-ticket` for **ticket-239** (audit-only checkpoint).
