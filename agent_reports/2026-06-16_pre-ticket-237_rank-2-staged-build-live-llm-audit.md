---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-237
gate_for: ticket-237
authoritative_prior: agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md
echo_of: ticket-236 pattern + ticket-212 rank-1 build
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: Rank-2 Staged Build Live Ollama (ticket-237 scope echo)

## Verdict: **GO** — rank-2 per-step live Ollama **build** may proceed with separate env gate, rank-2 candidate selection, mock extract + mock link upstream, and rank-2 title heuristic wiring; rank-1 build fallthrough unchanged

This report satisfies the mechanical `principal_audit_gate` requirement for
`agent_reports/*pre-ticket-237*` before ticket-237 implementation. Scope is
**build-only** (mock extract + mock link upstream); authoritative multi-step rank-2 live LLM policy
remains `agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md`.

---

## Prerequisites (satisfied)

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| Rank-2 heuristics | **Done** (ticket-229) | `staged_spine_heuristics.py` |
| Rank-2 mock network spine | **Done** (ticket-190) | `staged_fetch_second_candidate_*` fixtures |
| Rank-1 build live Ollama pattern | **Done** (ticket-212) | `--live-staged-build-fallthrough`, `test_live_staged_build_live_llm_spine.py` |
| Rank-2 link live Ollama | **Done** (ticket-236) | `--live-staged-rank2-link-fallthrough` |
| Live acquisition resilience | **Done** (ticket-233) | top-N fetch, OA-first URLs |

**ticket-236 confirmed:** rank-2 link uses `is_staged_rank2_fetch_spine_source` with
`RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM=1` only when rank-2 link fallthrough
is active. Rank-1 build path still validates **title** via `is_staged_fetch_spine_source`
(human-ai co-creativity / songwriting) — **rejects rank-2 sources today**.

---

## Scope echo — ticket-237 (build only)

### In

| Requirement | Detail |
|-------------|--------|
| Env gate | `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1` (distinct from rank-1 `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM`) |
| Shared live gates | `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO` |
| Network spine gate | `RGE_ALLOW_LIVE_STAGED_RANK2=1` for live discover → fetch rank-2 → ingest |
| Upstream in pytest | **Mock extract** (`staged_fetch_second_candidate_extract_claims.json`) + **mock link** (`staged_fetch_second_candidate_link_concepts.json`) — mirror ticket-212 mock-upstream pattern |
| Candidate selection | `select_rank2_candidate_id(conn, question_id)` — requires ≥2 queued candidates |
| Heuristic wiring | When rank-2 build live gate + CLI fallthrough active, validate source title via `is_staged_rank2_fetch_spine_source` only |
| CLI | New fallthrough flag: `--live-staged-rank2-build-fallthrough` — **must not** reuse rank-1 `--live-staged-build-fallthrough` |
| DB | Temp `--db` only; refuse default graph DB (mirror ticket-212) |
| Test module | `tests/unit/test_live_staged_rank2_build_live_llm_spine.py` |
| Markers | `live_network` + `live_smoke`; excluded from default pytest and CI |
| Docs | README / AGENTS / `docs/agents/12_RUNTIME_CONFIG.md` operator block |

### Out (unchanged from pre-ticket-228)

- Rank-2 detect live Ollama (separate future ticket)
- Orchestrator live LLM
- Live reconcile / report (deterministic Python)
- CI Ollama
- Public export / site / schema migrations
- Broadening rank-1 auto-mock routing or reusing rank-1 build gates on rank-2 sources

---

## Mirror pattern — ticket-212 rank-1 build

Rank-1 today:

```powershell
$env:RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_build_live_llm_spine.py -m "live_network and live_smoke" -q
```

Chain: live discover → fetch rank-1 → ingest → **mock extract** + **mock link** → live Ollama **build** (`--live-staged-build-fallthrough`).

Rank-2 build (proposed operator profile for ticket-237):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_build_live_llm_spine.py -m "live_network and live_smoke" -q
```

Chain: live discover (≥2 candidates) → fetch **rank-2** → ingest → **mock extract** + **mock link**
→ live Ollama build with rank-2 gate.

---

## Heuristic wiring (required in ticket-237)

Current rank-1 build fallthrough rejects rank-2 sources:

| Module | Rank-1 check | Rank-2 today |
|--------|--------------|--------------|
| `build_relationships_for_source` | `is_staged_fetch_spine_source` (title) | **Rejects** rank-2 title |
| `build_relationships_staged_live_fallthrough` | same | **Rejects** rank-2 title |

**GO condition:** ticket-237 adds a **parallel** rank-2 build fallthrough entry that:

1. Requires `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1`
2. Validates source via `is_staged_rank2_fetch_spine_source(source_record)`
3. Adds `live_staged_rank2_build_fallthrough` to `build_relationships_for_source` with mutual exclusion vs rank-1 staged build fallthrough
4. Leaves rank-1 `--live-staged-build-fallthrough` + `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM` unchanged

Do **not** extend rank-1 gates with implicit rank detection (pre-ticket-228).

---

## Rank-2 mock fixtures (upstream)

| Step | Rank-2 explicit fixture |
|------|-------------------------|
| extract (mock upstream) | `staged_fetch_second_candidate_extract_claims.json` |
| link (mock upstream) | `staged_fetch_second_candidate_link_concepts.json` |
| build (live under test) | live Ollama — no fixture |
| build (mock reference) | `staged_fetch_second_candidate_build_relationships.json` |

Reference: `tests/unit/test_live_staged_rank2_report_mock_spine.py`.

---

## Interaction with proof layers (ticket-234)

Rank-2 build live pytest is **out of band** — uses rank-2 candidate + rank-2 title heuristic.
Live network test may `pytest.skip` when fetched rank-2 artifact lacks `constraint management`
(catalog drift, not build-engine regression) — mirror ticket-236 `unsuitable_live_rank2_artifact`
pattern.

---

## Safety

| Area | Assessment |
|------|------------|
| Model → DB | Python validates; repositories persist — unchanged |
| Temp DB only | Required |
| Public export | Out of scope |
| Non-determinism | Operator opt-in; excluded from CI/default pytest |
| Dual-rank live orchestrator | **NO-GO** |
| Rank-1 build surface | Closed pattern at detect upstream; do not regress |

---

## Verification baseline (audit session)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q    # 142 passed
```

Audit-only — no product code changes.

---

## Recommendation

**GO** — implement **ticket-237** (rank-2 staged build live Ollama per-step proof)
following ticket-212 pattern with rank-2-specific gate, CLI flag, title heuristic wiring,
mock-extract + mock-link upstream, and pytest module. Defer rank-2 detect to ticket-238.

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-237** (rank-2 staged build live LLM opt-in proof).
