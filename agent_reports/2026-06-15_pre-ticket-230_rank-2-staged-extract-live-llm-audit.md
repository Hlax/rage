---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-230
gate_for: ticket-230
authoritative_prior: agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md
echo_of: ticket-232
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: Rank-2 Staged Extract Live Ollama (ticket-230 scope echo)

## Verdict: **GO** — rank-2 per-step live Ollama **extract** may proceed with separate env gate, rank-2 candidate selection, and rank-2 heuristic wiring; rank-1 fallthrough unchanged; reconcile/report remain deterministic

This report satisfies the mechanical `principal_audit_gate` requirement for
`agent_reports/*pre-ticket-230*` before ticket-230 implementation. Scope is
**extract-only**; authoritative multi-step rank-2 live LLM policy remains
`agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md`.

---

## Prerequisites (satisfied)

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| Rank-2 mock network spine | **Done** (ticket-190) | `test_live_staged_rank2_report_mock_spine.py` |
| Rank-2 source/chunk heuristics | **Done** (ticket-229) | `staged_spine_heuristics.py`, 7 unit tests |
| Rank-1 extract live Ollama pattern | **Done** (ticket-204) | `test_live_staged_extract_live_llm_spine.py`, `--live-staged-fallthrough` |
| Live acquisition resilience | **Done** (ticket-233) | OA-first URLs, top-N fetch |
| Proof-layer separation | **Done** (ticket-234) | Layer 1 acquisition independent of fixture phrases |

**ticket-229 deliverable confirmed:** `is_staged_rank2_fetch_spine_source/chunk` use
`constraint management` markers aligned with OpenAlex fixture W1234567890. Rank-1
auto-mock routing in `claim_extractor` / `concept_linker` / `relationship_builder` /
`contradiction_detector` remains rank-1-only (`human-ai co-creativity` + `songwriting`).

---

## Scope echo — ticket-230 (extract only)

### In

| Requirement | Detail |
|-------------|--------|
| Env gate | `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1` (distinct from rank-1 `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM`) |
| Shared live gates | `RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO` |
| Network spine gate | `RGE_ALLOW_LIVE_STAGED_RANK2=1` for live discover → fetch → ingest on **rank-2** candidate |
| Candidate selection | `select_rank2_candidate_id(conn, question_id)` — requires ≥2 queued candidates (`rank_index=1`) |
| Heuristic wiring | When rank-2 extract live gate + CLI fallthrough active, validate via `is_staged_rank2_fetch_spine_*` only |
| CLI | New fallthrough flag (e.g. `--live-staged-rank2-extract-fallthrough`) — **must not** reuse rank-1 `--live-staged-fallthrough` without rank detection |
| DB | Temp `--db` only; refuse default graph DB (mirror ticket-204) |
| Test module | `tests/unit/test_live_staged_rank2_extract_live_llm_spine.py` |
| Markers | `live_network` + `live_smoke`; excluded from default pytest and CI |
| Docs | README / AGENTS / `docs/agents/12_RUNTIME_CONFIG.md` operator block |

### Out (unchanged from pre-ticket-228)

- Rank-2 link / build / detect live Ollama (separate future tickets)
- Orchestrator live LLM (forces mock)
- Live reconcile / report (deterministic Python; pre-ticket audits 221/222)
- CI Ollama
- Public export / site changes
- Schema migrations
- Broadening rank-1 auto-mock routing or reusing rank-1 gates on rank-2 sources

---

## Mirror pattern — ticket-204 rank-1 extract

Rank-1 today:

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_extract_live_llm_spine.py -m "live_network and live_smoke" -q
```

Rank-2 extract (proposed operator profile for ticket-230):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_extract_live_llm_spine.py -m "live_network and live_smoke" -q
```

Implementation must chain: live discover (≥2 candidates) → fetch **rank-2**
candidate → ingest-staged → live Ollama extract with rank-2 heuristic validation.

---

## Rank-2 candidate selection

| Rank | Helper | SQL offset | Fixture work |
|------|--------|------------|--------------|
| 1 | `select_rank1_candidate_id` | 0 | W2741809807 — co-creativity / songwriting |
| 2 | `select_rank2_candidate_id` | 1 | W1234567890 — constraint management |

Live rank-2 pytest must assert `count_staged_candidates >= 2` before selecting rank-2.
Do **not** assume rank-1 is fetchable when proving rank-2 extract.

Reference: `tests/unit/live_staged_candidates.py`, `test_live_staged_rank2_report_mock_spine.py`.

---

## Heuristic wiring (required in ticket-230)

Current rank-1 fallthrough paths reject rank-2 sources:

| Module | Rank-1 check | Rank-2 today |
|--------|--------------|--------------|
| `claim_extractor.source_has_staged_fetch_spine` | rank-1 chunk markers | **Rejects** rank-2 chunks |
| `live_extraction_write.extract_claims_staged_live_fallthrough` | same | **Rejects** rank-2 chunks |

**GO condition:** ticket-230 adds a **parallel** rank-2 fallthrough entry that:

1. Requires `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1`
2. Validates chunks with `is_staged_rank2_fetch_spine_chunk` / `source_has_staged_rank2_fetch_spine`
3. Leaves rank-1 `--live-staged-fallthrough` + `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM` behavior unchanged

Do **not** extend rank-1 gates with implicit rank detection (pre-ticket-228 recommendation).

---

## Interaction with proof layers (ticket-234)

Ticket-234 layer-3 combined proofs use rank-1 mock markers (`human-ai co-creativity`,
`songwriting`) and `unsuitable_live_artifact` skips — **rank-1 scope**.

Rank-2 live extract pytest is **out of band** for rank-1 proof layers. Ticket-230 may
apply an analogous rank-2 compatibility skip when live rank-2 fetched text lacks
`constraint management` — that is catalog drift, not an extract-engine regression.

---

## Safety

| Area | Assessment |
|------|------------|
| Model → DB | Python validates; repositories persist — unchanged |
| Temp DB only | Required |
| Public export | Out of scope |
| Non-determinism | Operator opt-in; excluded from CI/default pytest |
| Dual-rank live orchestrator | **NO-GO** |
| Rank-1 live surface | Closed at detect (204/208/212/217); do not regress |

---

## Verification baseline (audit session)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q    # 142 passed
python -m pytest -q                 # 642 passed, 26 deselected
python -m rge.modules.principal_audit_gate --next-ticket ticket-230
# post-report: implementation_gate → satisfied; cadence may remain overdue (see note)
```

Audit-only — no product code changes.

---

## Cadence note

Principal checkpoint cadence is **overdue** (4 done tickets since ticket-231 checkpoint:
231, 233, 234, 235). This pre-ticket audit **unblocks ticket-230 implementation gate**
only. Consider `/rge-principal-audit` before or immediately after ticket-230 if cadence
policy requires reset.

---

## Recommendation

**GO** — implement **ticket-230** (rank-2 staged extract live Ollama per-step proof)
following ticket-204 pattern with rank-2-specific gate, CLI flag, heuristic wiring, and
pytest module. Defer rank-2 link/build/detect live LLM to subsequent tickets.

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-230** (rank-2 staged extract live LLM opt-in proof).
