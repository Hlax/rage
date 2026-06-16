---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-251
gate_for: ticket-251
category: Phase 3 / staged spine product hardening
---

# Pre-Ticket Audit: Rank-2 Staged Candidate Heuristic Scan (ticket-251)

## Verdict: **GO** — rank-2 candidate selection may scan top-N queued candidates for
`constraint management` title markers before fetch; rank-1 OFFSET-0 selection unchanged;
no live LLM, orchestrator live LLM, or reconcile/report live scope

## Context

Operator rank-2 live Ollama checklist (2026-06-16) skipped extract/link/build with
`unsuitable_live_rank2_artifact` on candidate `disc_openalex_W4391579155` — live fetch
**succeeded** but the second-ranked OpenAlex work lacked the rank-2 staged spine marker.
Detect seed failure was fixed separately (ticket-243).

Today:

| Layer | Behavior |
|-------|----------|
| Fetch resilience (233) | Top-N URL retry on 403 — **done** |
| Mock spine decoupling (234) | Layer 2/3 proof split — **done** |
| Rank-2 selection | Blind `OFFSET 1` by `priority_score` in `select_rank2_candidate_id` and `_staged_rank_candidate_ids` |
| Post-fetch skip | `_require_rank2_chunk_or_skip` skips when artifact lacks chunk marker |

This ticket hardens **selection** so live proofs and live-discover orchestrator paths prefer
the first queued candidate (ranks 2..N) whose **title** matches
`is_staged_rank2_fetch_spine_source` before fetch. Post-fetch chunk validation remains;
`unsuitable_live_rank2_artifact` still applies when no title match exists in the scan window.

---

## Prerequisites (satisfied)

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| Rank-2 heuristics | **Done** (229) | `staged_spine_heuristics.py` |
| Fetch top-N resilience | **Done** (233) | `fetch_first_fetchable_staged_candidate` |
| Proof-layer skip semantics | **Done** (234–235) | `unsuitable_live_rank2_artifact` documented |
| Per-step rank-2 live Ollama surface | **Closed** (230/236/237/238) | separate gates; unchanged by this ticket |
| Detect seed mock isolation | **Done** (243) | `_mock_llm_seed_env` |

---

## Scope — ticket-251

### In

| Requirement | Detail |
|-------------|--------|
| Production helper | `rge/modules/staged_candidate_selection.py` (or equivalent) with `select_rank2_staged_candidate_id(conn, question_id, *, max_scan=10)` |
| Scan window | Candidates ordered by `priority_score DESC`, starting at rank index 1 (exclude rank-1 row) |
| Match rule | First candidate where `is_staged_rank2_fetch_spine_source(title)` is true |
| Failure | Structured error or pytest skip payload when no match in window (preserve `unsuitable_live_rank2_artifact` when post-fetch chunk also fails) |
| Live pytest consumers | Update `select_rank2_candidate_id` wrapper or call sites in rank-2 `live_network` spine tests |
| Orchestrator | `_staged_rank_candidate_ids` uses heuristic scan for rank-2 id when live discover produced candidates (mock/fixture orchestrator ids unchanged) |
| Tests | Unit tests with synthetic `candidate_sources` rows; no Ollama |
| Default CI | Mock-only; `live_network` tests unchanged in collection profile |

### Out

| Item | Why |
|------|-----|
| Live Ollama env gates / fallthrough flags | Per-step surface closed; no new `*_LIVE_LLM` gates |
| Orchestrator live LLM | **NO-GO** — orchestrator forces mock |
| Reconcile/report live LLM | **NO-GO** — deterministic Python |
| CI `live_network` in default pytest | **NO-GO** |
| Default graph DB live proofs | Temp `--db` only |
| Expanding rank-2 marker vocabulary | Keep `constraint management` contract from 229 |
| Post-fetch-only scan without title pre-check | Title scan is the product change; chunk skip stays secondary |
| Detect-seed docs | Doc triangle complete (245–249) |

---

## Risk assessment

| Risk | Mitigation |
|------|------------|
| Rank-2 id differs from strict OFFSET 1 | Document scan window; orchestrator + live proofs share helper |
| False positive title match | Keep existing chunk validation after fetch |
| Rank-1 bleed | Scan starts at index 1; rank-1 helper untouched |
| Operator surprise | Skip JSON includes `scanned_candidates` count when no match |

---

## Verification baseline (pre-implementation)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q    # 142 passed
python -m pytest -q                 # 669 passed, 30 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

---

## Recommendation

**GO** for `/rge-run-next-ticket` **ticket-251**. This advances staged spine **product**
risk without live LLM surface changes. Operator rank-2 live re-proof remains optional
out-of-band after merge.

## Suggested implementation prompt

```txt
/rge-run-next-ticket for ticket-251
```
