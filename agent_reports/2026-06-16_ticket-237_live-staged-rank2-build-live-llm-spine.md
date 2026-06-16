# Agent Report: ticket-237 — Live staged rank-2 build live LLM opt-in proof

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-237  
**Branch:** `phase-3/ticket-237-rank2-build-live-llm-spine`  
**Status:** implemented

## Summary

Added per-step rank-2 live Ollama build on staged OpenAlex ingest with mock extract + mock link upstream,
mirroring ticket-212 with separate env gate (`RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1`),
CLI flag (`--live-staged-rank2-build-fallthrough`), and rank-2 title heuristic via
`is_staged_rank2_fetch_spine_source`. Rank-1 `--live-staged-build-fallthrough` unchanged.

## Audit gate

- Pre-ticket: `agent_reports/2026-06-16_pre-ticket-237_rank-2-staged-build-live-llm-audit.md` (GO)

## Scope in / out

**In:** rank-2 build fallthrough, env gate, CLI flag, pytest spine, operator docs.

**Out:** rank-2 detect, orchestrator live LLM, CI Ollama, public export, schema migrations.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/relationship_builder.py` | `live_staged_rank2_build_fallthrough`, `build_relationships_staged_rank2_live_fallthrough` |
| `rge/cli.py` | `--live-staged-rank2-build-fallthrough` handler |
| `tests/unit/test_live_staged_rank2_build_live_llm_spine.py` | 6 mock + 1 live_network/live_smoke |
| `README.md`, `AGENTS.md`, `docs/agents/12_RUNTIME_CONFIG.md`, `.env.example` | Operator docs |
| `tickets/TICKET_QUEUE.md`, `tickets/ticket-237.json`, `tickets/ticket-238.json` | Queue updates |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM` + CLI fallthrough | **PASS** |
| 2 | Rank-2 heuristics; rank-1 unchanged | **PASS** |
| 3 | Opt-in live_network pytest; excluded default | **PASS** (29 deselected) |
| 4 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_rank2_build_live_llm_spine.py -q  # 6 passed, 1 deselected
python -m pytest tests/golden -q                                                 # 142 passed
python -m pytest -q                                                            # 660 passed, 29 deselected
```

Safety audit not required — live LLM opt-in only; no public export or schema changes.

## Merge to main

- Merge commit: `c4bda34d3257f1cd72be1f9633c064d3e4e757fc`
- Post-merge pytest: 660 passed, 29 deselected

## Recommended next ticket

**ticket-238** — rank-2 staged detect live LLM (mirror ticket-217; requires pre-ticket audit).

## Suggested next prompt

Write pre-ticket audit for ticket-238, then `/rge-run-next-ticket` for rank-2 detect.
