---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-229 (heuristic prerequisite) then ticket-230+ (per-step rank-2 live LLM)
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: Rank-2 Staged Per-Step Live Ollama on Staged Spine

## Verdict: **GO (conditional)** — rank-2 per-step live Ollama may proceed **only** with separate env gates, rank-2 candidate selection, and rank-2 source/chunk heuristics; **do not** reuse rank-1 fallthrough on rank-2 sources without code changes

## Context

Rank-1 staged per-step live Ollama surface is **closed** (extract/link/build/detect;
tickets 204/208/212/217; principal audit ticket-223). Reconcile/report are
**deterministic Python** on both ranks (pre-ticket audits 221/222).

Rank-2 **mock** spine is proven (ticket-190): live OpenAlex discover → select
**second-ranked** candidate (`select_rank2_candidate_id`, `rank_index=1`) → fetch →
ingest → **explicit** `staged_fetch_second_candidate_*` mock fixtures → deterministic
reconcile/report. Env gate: `RGE_ALLOW_LIVE_STAGED_RANK2=1` (network spine only).

This audit evaluates whether per-step **live Ollama** on rank-2 staged ingest is a valid
next milestone.

---

## Audit answers

### 1. What does rank-2 staged spine mean today?

| Layer | Rank-1 | Rank-2 |
|-------|--------|--------|
| Candidate selection | `select_rank1_candidate_id` (OFFSET 0) | `select_rank2_candidate_id` (OFFSET 1) |
| Typical source title | Human-AI co-creativity / songwriting | Constraint management in AI-assisted creative teams |
| Mock fixtures | `staged_fetch_*` (auto-route on rank-1 heuristic) | `staged_fetch_second_candidate_*` (explicit `--fixture` in pytest) |
| Network proof env | `RGE_ALLOW_LIVE_STAGED_*` per step or orchestrator | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |
| Live Ollama per-step | 204/208/212/217 with `RGE_ALLOW_LIVE_STAGED_*_LIVE_LLM=1` | **Not implemented** |
| Reconcile / report | Deterministic Python | Deterministic Python (same modules) |

Reference: `tests/unit/test_live_staged_rank2_report_mock_spine.py`, `tests/unit/live_staged_candidates.py`.

### 2. Can rank-1 live fallthrough gates be reused on rank-2 without changes?

**NO-GO (as-is).** Rank-1 staged heuristics are **rank-1-specific**:

| Module | Heuristic | Rank-2 match? |
|--------|-----------|---------------|
| `claim_extractor._is_staged_fetch_spine_chunk` | `"human-ai co-creativity"` + `"songwriting"` in chunk | **No** — rank-2 chunk uses Constraint management text |
| `concept_linker._is_staged_fetch_spine_source` | same markers in **title** | **No** — rank-2 title is Constraint management… |
| `relationship_builder.is_staged_fetch_spine_source` | same | **No** |
| `contradiction_detector` | uses `is_staged_fetch_spine_source` | **No** |

Rank-2 mock pytest passes explicit `--fixture staged_fetch_second_candidate_*.json`;
live fallthrough validators would **reject** rank-2 sources or auto-route to wrong rank-1
fixtures if rank-1 gates were enabled blindly.

**Required before rank-2 live proofs:** rank-2 staged source/chunk eligibility helper(s)
(e.g. `"constraint management"` title/chunk markers aligned with
`fixtures/source_providers/openalex_works_sample.json` rank-2 work).

### 3. What does “live staged rank-2 per-step live Ollama” mean?

| Interpretation | Verdict |
|----------------|---------|
| Full orchestrator live LLM (dual rank) | **NO-GO** — `execute_staged_fixture_mode_run` forces mock |
| Reuse rank-1 `*_LIVE_LLM` gates on rank-2 ingest without heuristic work | **NO-GO** |
| Per-step live Ollama on rank-2 after live ingest + mock upstream (mirror 204–217) | **GO (conditional)** |
| Live Ollama reconcile/report on rank-2 | **NO-GO** — deterministic by design (221/222) |
| Combined rank-1 + rank-2 all-live chain in one pytest | **NO-GO** — defer; per-step only |

### 4. Reconcile/report on rank-2 path

**NO-GO for live LLM** (unchanged from rank-1):

- `reconcile-scores` → `score_reconciler.py` — deterministic; rank-2 mock spine already
  uses domain-pack rules including `_matches_staged_second_candidate_may_increase_human_control`
- `generate-run-report` → `run_evaluator.py` — deterministic DB aggregation
- `RGE_ALLOW_LIVE_STAGED_RANK2` gates **network** spine only (ticket-190), not Ollama
- Do **not** add `RGE_ALLOW_LIVE_STAGED_RANK2_RECONCILE_LIVE_LLM` or report equivalents

### 5. Recommended env gate pattern (rank-2 live LLM)

Use **separate** rank-2 live gates (distinct from rank-1) to avoid operator confusion:

| Step | Proposed live Ollama gate | Network / mock spine gate |
|------|---------------------------|---------------------------|
| extract | `RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1` | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |
| link | `RGE_ALLOW_LIVE_STAGED_RANK2_LINK_LIVE_LLM=1` | same |
| build | `RGE_ALLOW_LIVE_STAGED_RANK2_BUILD_LIVE_LLM=1` | same |
| detect | `RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1` | same |
| reconcile / report | — (no LLM gate) | `RGE_ALLOW_LIVE_STAGED_RANK2=1` |

Shared requirements (mirror rank-1):

- `RGE_LLM_MODE=ollama`, `RGE_ALLOW_LIVE_LLM=1`
- `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
- Temp `--db` only (refuse default graph DB)
- `seed_domain_opposing_context()` before live discover (detect path)
- CLI fallthrough flags per step (e.g. `--live-staged-rank2-extract-fallthrough` or scoped variant — **implementation ticket must choose one pattern and document**)
- `live_network` + `live_smoke` markers; excluded from default pytest and CI

Alternative (not recommended): extend rank-1 gates with implicit rank detection — higher
operator error risk; pre-ticket audit prefers explicit rank-2 gates.

---

## Hardened scope — recommended implementation sequence

### ticket-229 (prerequisite — medium)

**Rank-2 staged source/chunk heuristic for live fallthrough eligibility**

- Add `is_staged_rank2_fetch_spine_source()` / chunk helper aligned with rank-2 OpenAlex fixture
- Wire into fallthrough validators **only when rank-2 live gate set** (do not broaden rank-1 auto-mock routing)
- Unit tests for heuristic positive/negative cases
- **No** live Ollama pytest yet

### ticket-230+ (per-step — medium each, after 229)

Mirror rank-1 pattern one step at a time:

1. Live rank-2 extract (live ingest → live Ollama extract; mock downstream not required in same test)
2. Live rank-2 link (mock extract upstream)
3. Live rank-2 build (mock extract + link upstream)
4. Live rank-2 detect (mock upstream + domain seed)

Each ticket: env gate, CLI flag, module fallthrough entry, `tests/unit/test_live_staged_rank2_*_live_llm_spine.py`, CI deselect assertion, README/AGENTS/runtime config docs.

### Out (all rank-2 live tickets)

- Orchestrator live LLM
- Live reconcile/report
- CI Ollama
- Public export
- Schema migrations
- Reusing rank-1 gates without rank-2 heuristics

---

## Safety

| Area | Assessment |
|------|------------|
| Temp DB only | Required — same as rank-1 live proofs |
| Model → DB | Python validates; repositories persist — unchanged |
| Public export | Out of scope |
| Non-determinism | Operator opt-in only; excluded from CI/default pytest |
| Dual-rank live orchestrator | **NO-GO** |

---

## Verification baseline (audit session)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q    # 142 passed
python -m pytest -q                 # 621 passed, 20 deselected
```

Audit patches: report only (no runner changes).

---

## Operator opt-in reference (existing rank-2 mock spine)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_report_mock_spine.py -m live_network -q
```

Live rank-2 per-step proofs **do not exist yet**; do not enable rank-1 `*_LIVE_LLM` gates
expecting rank-2 behavior.

---

## Recommendation

**GO (conditional)** — rank-2 per-step live Ollama is architecturally sound and mirrors
proven rank-1 patterns, but **requires ticket-229 heuristic prerequisite** before any
live Ollama rank-2 proof. Reconcile/report remain deterministic (**NO-GO for LLM**).
Defer dual-rank live orchestrator indefinitely.

**Pause alternative:** complete rank-1 operator live proof sessions before investing in
rank-2 live LLM (ticket-227 recommendation still valid).

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-229** (rank-2 staged source heuristic prerequisite),
or pause for rank-1 operator live proofs.
