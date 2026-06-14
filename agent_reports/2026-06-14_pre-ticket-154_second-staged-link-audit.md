---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-154
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-154 Link Concepts on Second Staged-Ingested Source

## Verdict: **GO**

ticket-153 leaves rank #2 with **1 accepted claim** (`Constraint management improves AI-assisted creative team workflows.`).
ticket-154 may prove **link-concepts** with a new mock fixture — no live LLM, no build/detect spine.

## Principal / cadence gate

| Field | Value |
| ----- | ----- |
| Main tip | `f5149e7` (post ticket-153) |
| Principal cadence | satisfied by `agent_reports/2026-06-14_principal-audit-post-ticket-153.md` |
| Pre-ticket required | yes — **this report** |
| Milestone triggers | none |

## 1. Upstream state (ticket-153)

| Field | Value |
| ----- | ----- |
| source title | Constraint management in AI-assisted creative teams |
| accepted claims | 1 |
| rejected claims | 1 (`missing_quote_span`) |
| rank #1 link auto-select | `_is_staged_fetch_spine_source()` — co-creativity + songwriting only |

Rank #2 title/chunk does **not** match rank #1 heuristic → new fixture required (or explicit `--fixture`).

## 2. Fixture contract

File: `fixtures/llm_outputs/staged_fetch_second_candidate_link_concepts.json`

Mirror rank #1 (`staged_fetch_link_concepts.json`): **≥2 validated links** on the single accepted claim.

Suggested concepts (all in creativity ontology):

| concept_label | role |
| ------------- | ---- |
| constraint | subject |
| AI assistance | object |
| human control | context |

Use pack-valid `domain_metadata`:

```json
{
  "track": "human-AI",
  "creative_phase": "execution",
  "measured_dimension": "quality"
}
```

`claim_id: "placeholder"` resolves via `_resolve_link_claim_ids` to the sole accepted claim.

## 3. Minimal test design

File: `tests/unit/test_staged_second_candidate_link_spine.py`

1. Reuse ticket-153 spine through extract (`--fixture staged_fetch_second_candidate_extract_claims.json`)
2. `link-concepts --fixture staged_fetch_second_candidate_link_concepts.json`
3. Assert `link_count >= 2` on accepted claim; labels include `constraint` and `AI assistance`
4. Optional: re-run → `already_linked`; CLI JSON asserts

**Prefer explicit `--fixture`** (ticket JSON `affected_modules: []`). Optional `concept_linker.py` title heuristic for rank #2 is out of scope unless paired with auto-select unit test.

## 4. Out of scope

- build-relationships, detect, reconcile (ticket-155+ follow-ons)
- Live Ollama/network, schema, public export/site

## 5. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_link_spine.py -q
python -m pytest tests/unit/test_staged_second_candidate_extract_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-154 | **GO** |
| Next follow-on | ticket-155 — build-relationships on second staged source |
