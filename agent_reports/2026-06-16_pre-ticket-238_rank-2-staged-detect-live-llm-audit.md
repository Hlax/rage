---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-238
gate_for: ticket-238
authoritative_prior: agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md
echo_of: ticket-237 pattern + ticket-217 rank-1 detect
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: Rank-2 Staged Detect Live Ollama (ticket-238 scope echo)

## Verdict: **GO** — rank-2 per-step live Ollama **detect** may proceed with separate env gate, rank-2 candidate selection, mock extract + mock link + mock build upstream, **mandatory** `seed_domain_opposing_context`, and rank-2 title heuristic wiring; rank-1 detect fallthrough unchanged

This report satisfies the mechanical `principal_audit_gate` requirement for
`agent_reports/*pre-ticket-238*` before ticket-238 implementation. Scope is
**detect-only** (mock upstream through build); authoritative multi-step rank-2 live LLM policy
remains `agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md`.

**Closure note:** ticket-238 completes the rank-2 per-step live Ollama surface
(extract/link/build/detect per pre-ticket-228). Reconcile/report remain deterministic Python
on both ranks — **NO-GO for live LLM** (pre-ticket audits 221/222).

---

## Prerequisites (satisfied)

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| Rank-2 heuristics | **Done** (ticket-229) | `staged_spine_heuristics.py` |
| Rank-2 mock network spine | **Done** (ticket-190) | `staged_fetch_second_candidate_*` fixtures |
| Rank-1 detect live Ollama pattern | **Done** (ticket-217) | `--live-staged-detect-fallthrough`, `test_live_staged_detect_live_llm_spine.py` |
| Rank-2 build live Ollama | **Done** (ticket-237) | `--live-staged-rank2-build-fallthrough` |
| Domain opposing seed helper | **Done** (ticket-197) | `tests/unit/staged_domain_seed.py` |
| Rank-2 mock detect spine | **Done** (ticket-156) | `staged_fetch_second_candidate_detect_contradictions.json` |

**ticket-237 confirmed:** rank-2 build uses `is_staged_rank2_fetch_spine_source` with
`RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1` only when rank-2 build fallthrough
is active. Rank-1 detect path still validates **title** via `is_staged_fetch_spine_source`
(human-ai co-creativity / songwriting) — **rejects rank-2 sources today**.

---

## Scope echo — ticket-238 (detect only)

### In

| Requirement | Detail |
|-------------|--------|
| Env gate | `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1` (distinct from rank-1 `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM`) |
| Shared live gates | `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO` |
| Network spine gate | `RGE_ALLOW_LIVE_STAGED_RANK2=1` for live discover → fetch rank-2 → ingest |
| Domain seed | **`seed_domain_opposing_context(temp_db)` before live discover** — non-negotiable (mirror ticket-217 / ticket-181) |
| Upstream in pytest | **Mock extract** (`staged_fetch_second_candidate_extract_claims.json`) + **mock link** (`staged_fetch_second_candidate_link_concepts.json`) + **mock build** (`staged_fetch_second_candidate_build_relationships.json`) |
| Candidate selection | `select_rank2_candidate_id(conn, question_id)` — requires ≥2 queued candidates |
| Heuristic wiring | When rank-2 detect live gate + CLI fallthrough active, validate source title via `is_staged_rank2_fetch_spine_source` only |
| CLI | New fallthrough flag (recommended: `--live-staged-rank2-detect-fallthrough`) — **must not** reuse rank-1 `--live-staged-detect-fallthrough` |
| DB | Temp `--db` only; refuse default graph DB (mirror ticket-217) |
| Test module | `tests/unit/test_live_staged_rank2_detect_live_llm_spine.py` |
| Markers | `live_network` + `live_smoke`; excluded from default pytest and CI |
| Docs | README / AGENTS / `docs/agents/12_RUNTIME_CONFIG.md` operator block |

### Out (unchanged from pre-ticket-228)

- Orchestrator live LLM
- Live reconcile / report (deterministic Python)
- CI Ollama
- Public export / site / schema migrations
- Broadening rank-1 auto-mock routing or reusing rank-1 detect gates on rank-2 sources
- Further rank-2 per-step live fallthrough flags after detect (surface **closed** at detect)

---

## Mirror pattern — ticket-217 rank-1 detect

Rank-1 today:

```powershell
$env:RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_detect_live_llm_spine.py -m "live_network and live_smoke" -q
```

Chain: `seed_domain_opposing_context` → live discover → fetch rank-1 → ingest → **mock extract** + **mock link** + **mock build** → live Ollama **detect** (`--live-staged-detect-fallthrough`).

Rank-2 detect (proposed operator profile for ticket-238):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_detect_live_llm_spine.py -m "live_network and live_smoke" -q
```

Chain: `seed_domain_opposing_context` → live discover (≥2 candidates) → fetch **rank-2** → ingest → **mock extract** + **mock link** + **mock build** → live Ollama detect with rank-2 gate.

---

## Heuristic wiring (required in ticket-238)

Current rank-1 detect fallthrough rejects rank-2 sources:

| Module | Rank-1 check | Rank-2 today |
|--------|--------------|--------------|
| `detect_contradictions_for_source` | `_is_staged_fetch_spine_source` (title) | **Rejects** rank-2 title |
| `detect_contradictions_staged_live_fallthrough` | `is_staged_fetch_spine_source` | **Rejects** rank-2 title |

**GO condition:** ticket-238 adds a **parallel** rank-2 detect fallthrough entry that:

1. Requires `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1`
2. Validates source via `is_staged_rank2_fetch_spine_source(source_record)`
3. Adds `live_staged_rank2_detect_fallthrough` to `detect_contradictions_for_source` with mutual exclusion vs rank-1 staged detect fallthrough
4. Leaves rank-1 `--live-staged-detect-fallthrough` + `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM` unchanged

Do **not** extend rank-1 gates with implicit rank detection (pre-ticket-228).

---

## Rank-2 mock fixtures (upstream + reference)

| Step | Rank-2 explicit fixture |
|------|-------------------------|
| extract (mock upstream) | `staged_fetch_second_candidate_extract_claims.json` |
| link (mock upstream) | `staged_fetch_second_candidate_link_concepts.json` |
| build (mock upstream) | `staged_fetch_second_candidate_build_relationships.json` |
| detect (live under test) | live Ollama — no fixture |
| detect (mock reference) | `staged_fetch_second_candidate_detect_contradictions.json` |

Mock detect fixture qualification edge (reference for stub Ollama client in mocked gate tests):

- **base:** `AI assistance` / `may_reduce` / `semantic diversity` (from domain seed)
- **new:** `constraint` / `may_increase` / `human control` (from rank-2 mock build)

Reference: `tests/unit/test_staged_second_candidate_detect_contradictions_spine.py`,
`tests/unit/test_live_staged_rank2_report_mock_spine.py`.

---

## Domain seed requirement (detect-specific)

Detect reads **all domain claims** and **all active relationships** — not source-scoped
like extract/link/build. Without `seed_domain_opposing_context()`:

- No `AI assistance` / `may_reduce` / `semantic diversity` base edge exists
- Rank-2 mock build adds `constraint` / `may_increase` / `human control`
- Live Ollama qualification proposals referencing the base triple would fail validation

**Non-negotiable:** call `seed_domain_opposing_context(temp_db)` in the rank-2 detect pytest
fixture **before** enqueueing discovered candidates (mirror ticket-217).

---

## Detect-specific risk notes (rank-2)

| Risk | Mitigation |
|------|------------|
| Higher flake than build | Assert `qualification_count >= 1`; skip when Ollama unreachable |
| Domain-wide graph pollution | Temp `--db` only; seed + staged ingest confined to pytest DB |
| Model proposes wrong triples | Python `validate_contradiction_candidates()` before persistence — unchanged |
| Live network catalog drift | `unsuitable_live_rank2_artifact` skip when fetched artifact lacks `constraint management` marker (ticket-234 pattern) |

---

## Interaction with proof layers (ticket-234)

Rank-2 detect live pytest is **out of band** — uses rank-2 candidate + rank-2 title heuristic.
Live network test may `pytest.skip` when fetched rank-2 artifact lacks `constraint management`
(catalog drift, not detect-engine regression) — mirror ticket-236/237 `unsuitable_live_rank2_artifact`
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
| Rank-1 detect surface | Do not regress |
| Rank-2 live surface after detect | **Closed** — no further `*_LIVE_LLM` fallthrough flags planned |

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

**GO** — implement **ticket-238** (rank-2 staged detect live Ollama per-step proof)
following ticket-217 pattern with rank-2-specific gate, CLI flag, title heuristic wiring,
mandatory domain seed, mock-upstream through build, and pytest module.

After ticket-238, rank-2 per-step live Ollama is **complete**; next milestones are operator
live proof sessions and/or rank-2 deterministic reconcile/report network proofs (no LLM).

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-238** (rank-2 staged detect live LLM opt-in proof).
