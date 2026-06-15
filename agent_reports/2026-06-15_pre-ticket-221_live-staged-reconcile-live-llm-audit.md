---
template_id: pre_ticket_audit
status: NO-GO
date: 2026-06-15
risk_level: medium
ticket: N/A (no follow-on implementation ticket)
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: Live Staged Reconcile on Staged Spine (Per-Step Live LLM)

## Verdict: **NO-GO** (reconcile-scores is deterministic Python by design; no LLM task exists; do not add live Ollama reconcile fallthrough)

## Context

Per-step live staged proofs (tickets 204/208/212/217) add operator opt-in **Ollama**
fallthrough for pipeline tasks where the model proposes candidate JSON and Python
validates before persistence.

ticket-184 proved **live OpenAlex + mock LLM through detect + deterministic
reconcile-scores** on temp DB (`RGE_ALLOW_LIVE_STAGED_RECONCILE=1` is a **network spine
gate**, not an LLM gate). Pre-ticket-183 explicitly scoped reconcile as deterministic
Python with **no live LLM**.

This audit evaluates whether a per-step **live Ollama reconcile** proof is a valid next
milestone.

---

## Audit answers

### 1. What does “live staged reconcile” mean in this repo today?

| Interpretation | Scope | Verdict |
|----------------|-------|---------|
| Live OpenAlex spine through `reconcile-scores` (ticket-184) | Network + mock LLM upstream; deterministic reconcile | **Already proven** |
| Per-step live Ollama score reconciliation on staged rank-1 | New LLM fallthrough + env gate | **NO-GO** |
| Full orchestrator live LLM reconcile | Changes `execute_staged_fixture_mode_run` | **NO-GO** |
| NM-4 `--evidence-db-reconcile` on manual_text evidence DB | Separate operator spine (127–133) | Out of staged spine scope |

### 2. Does reconcile-scores use an LLM?

**No.** `rge/modules/score_reconciler.py` module docstring:

```text
Update confidence scores and write score events. Deterministic; no model use.
```

- **CLI:** `python -m rge.cli reconcile-scores --source <id> [--db]`
- **Entry:** `reconcile_scores_for_source()` — domain-pack YAML overlay
  (`score_reconciliation` from `domain_packs/creativity/scoring.yaml`) drives
  `stronger_evidence_boost`, confidence thresholds, and formula version.
- **Persistence:** append-only `score_events` via `persist_relationship_score_update()`.
- **No** `get_model_client`, `MockModelClient`, or Ollama structured task for reconcile.
- **No** `--fixture` on reconcile CLI (contract fixtures in tests assert expected boosts only).

`generate-run-report` (`run_evaluator.py`) is also **deterministic; no model use** —
separate from this audit but relevant for roadmap (report is not an LLM step either).

### 3. What is `RGE_ALLOW_LIVE_STAGED_RECONCILE`?

Opt-in env for **live_network pytest** proving discover→…→detect→reconcile on temp DB
(`tests/unit/test_live_staged_reconcile_mock_spine.py`). It gates **OpenAlex network**
spine execution, not Ollama. Naming parallels mock-spine gates (`RGE_ALLOW_LIVE_STAGED_*`);
there is **no** `RGE_ALLOW_LIVE_STAGED_RECONCILE_LIVE_LLM` and none should be added without
a new LLM task spec and schema.

### 4. Should a live LLM reconcile fallthrough be added?

**NO-GO** for the following reasons:

1. **Architecture:** Scores are derived from validated graph state and pack rules; the
   safety model requires deterministic, auditable score changes with formula version in
   every `score_events` row.
2. **No model surface:** Adding live reconcile would require inventing a new structured
   LLM task, validator, and persistence path — out of scope for a “per-step fallthrough”
   ticket and contrary to `05_DATA_MODEL.md` score semantics.
3. **Existing proof:** ticket-184 + manual synthnote reconcile (GT8) already prove reconcile
   on real graph shapes; non-determinism would weaken golden acceptance.
4. **Orchestrator:** `execute_staged_fixture_mode_run` should remain mock LLM for all
   model-assisted steps; reconcile stays Python-only in orchestrator chains.

### 5. Env gates separate from mock spine?

Not applicable for live LLM — **no live LLM reconcile gate**. Document clearly:

| Gate | Purpose |
|------|---------|
| `RGE_ALLOW_LIVE_STAGED_RECONCILE=1` | Opt-in live OpenAlex spine through deterministic reconcile (ticket-184) |
| (none) | No live Ollama reconcile — by design |

### 6. Orchestrator mock-only boundary

**Unchanged.** Staged orchestrator forces mock LLM for extract/link/build/detect; reconcile
and report steps remain deterministic Python in all orchestrator paths.

### 7. Rank-1 / rank-2 / upstream chain

If reconcile live LLM were ever reconsidered (not recommended), it would still require
pre-ticket schema for LLM-proposed score deltas — **deferred indefinitely**. Rank-2 staged
reconcile mock spine is proven via ticket-190; no rank-specific live LLM variant applies.

### 8. Recommended operator documentation

Ensure README/AGENTS continue to describe reconcile as **deterministic** (already true in
ticket-184/185 docs). Optional low-risk hygiene: explicit “no live LLM path for reconcile”
callout — not required for this audit verdict.

---

## Hardened scope — follow-on implementation

**None.** Do **not** seed a ticket-222 live reconcile LLM implementation.

## Recommended next tickets (smallest useful work)

| Priority | Ticket idea | Risk | Rationale |
|----------|-------------|------|-----------|
| 1 | Pre-ticket audit: live staged **generate-run-report** live LLM | medium | Close staged-spine LLM surface review (expected NO-GO; report is deterministic) |
| 2 | Principal audit post-ticket-220 | low | Cadence after 218–220 infrastructure window |
| 3 | Rank-2 / orchestrator / theory milestones | varies | Separate pre-ticket audits per milestone rules |

## Safety

- No new model write paths proposed.
- Existing reconcile remains validated Python + append-only score events.

## Operator reference (existing deterministic reconcile spine)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
```

Requires `seed_domain_opposing_context(temp_db)` before live discover (same as detect spine).

## Recommendation

**NO-GO** for live Ollama staged reconcile. Proceed with non-LLM milestones or pre-ticket
audit for report (expected NO-GO). Do not implement `--live-staged-reconcile-fallthrough`
or `RGE_ALLOW_LIVE_STAGED_RECONCILE_LIVE_LLM`.
