# Agent Report: ticket-316 — Live staged-spine operator proof refresh v0

**Date:** 2026-06-18  
**Ticket:** ticket-316  
**Branch:** `phase-3/ticket-316-live-staged-spine-operator-proof-refresh-v0`  
**Main tip before branch:** `b409354`  
**Audit gate:** `agent_reports/2026-06-18_pre-ticket-316_live-staged-spine-operator-proof-refresh-audit.md` (GO)

## Summary

Refreshed operator-private staged-spine atlas export proof using layer-2 mock orchestrator
(fixture OpenAlex + dual-candidate spine on gitignored DB). **Graph materially richer than
ticket-315** (3 runs, 2 cards, 3 edges, 2 reports vs 1/1/1/1). **Product verdict PARTIAL**
— export mechanics and multi-source graph are Atlas-useful, but `overall_coherence_verdict`
is **partial** because `clusters[]` is empty on the staged default export path (evidence DB
hooks populate clusters; staged orchestrator DB does not invoke them).

Layer-3 live OpenAlex pytest skipped honestly with `unsuitable_live_artifact` (live fetch
succeeds but lacks mock-spine marker phrases — not a regression).

## Scope

**In:** Pre-ticket audit; layer-2 operator CLI proof; layer-3 live_network attempt;
comparison vs ticket-315; regression pytest + verify.

**Out:** Production code (no regression found), README-only docs, public export/site, CI
live_network enforcement, schema migrations, live Ollama.

## Changed files

| File | Change |
|------|--------|
| `agent_reports/2026-06-18_pre-ticket-316_live-staged-spine-operator-proof-refresh-audit.md` | Pre-ticket GO |
| `agent_reports/2026-06-18_phase-3_ticket-316_live-staged-spine-operator-proof-refresh-v0.md` | This report |
| `tickets/ticket-316.json` | Status `done` |
| `tickets/ticket-317.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

**Operator artifacts (gitignored):**

| Path | Purpose |
|------|---------|
| `data/db/ticket316_staged_spine_refresh.sqlite` | Layer-2 staged orchestrator DB |
| `data/atlas/ticket316/atlas_snapshot_v316.json` | Private atlas export |
| `data/atlas/ticket316/atlas_coherence_report_v316.json` | Coherence JSON |
| `data/atlas/ticket316/atlas_coherence_report_v316.md` | Coherence markdown |
| `data/operator/ticket316_staged_spine_proof.py` | One-off operator runner (gitignored) |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Operator proof via staged-spine gate or layer-2 fallback | **PASS** — layer-2 mock orchestrator + export + coherence |
| Private atlas + coherence with product verdict | **PASS** — **PARTIAL** (see below) |
| Compare vs ticket-315 baseline | **PASS** — table below |
| No public export/site changes | **PASS** |
| Golden + full pytest; live_network opt-in only | **PASS** — 144 golden, 789 pytest |

## Staged spine vs ticket-315 comparison

| Metric | ticket-315 (evidence DB) | ticket-316 (staged spine) | Delta |
|--------|-------------------------:|--------------------------:|-------|
| `overall_coherence_verdict` | pass | **partial** | clusters gap |
| runs | 1 | **3** | +2 (rank1/rank2 + evidence hook run) |
| cards | 1 | **2** | +1 (golden fixture cards) |
| edges | 1 | **3** | +2 (contradiction-qualified relationships) |
| reports | 1 | **2** | +1 (dual rank run reports) |
| follow_up_questions | 1 | 1 | — |
| clusters | 1 | **0** | −1 (staged path gap) |
| nodes | 24 | 24 | — (domain ontology catalog) |

**Product assessment:**

1. **Multi-run lineage:** rank1 + rank2 runs with `research_question_id`; rank2 has `parent_question_id` — clearer than ticket-315 single-run evidence path.
2. **Graph richness:** 3 active relationship edges including contradiction qualification (`may_reduce` vs `may_increase` on semantic diversity) — materially better for Research Atlas graph UI.
3. **Cards/sources:** 2 cards with concept labels and source metadata (fixture staged sources).
4. **Coherence gap:** `missing_fields_create_refactor_risk` warns `clusters[] empty` — staged export does not call evidence DB cluster hooks (ticket-296 scope).
5. **Layer-3 live:** skipped `unsuitable_live_artifact` — live OpenAlex catalog incompatible with mock fixture markers; same semantics as ticket-285/234.

## Product verdict

**PARTIAL**

- **Richer than evidence DB baseline** — staged spine produces multi-source, multi-edge atlas data suitable for frontend graph exploration.
- **Not full GO** — overall coherence **partial** due to empty `clusters[]`; not weak extraction quality or export mechanics failure.
- **Failure root cause (if treating partial as fail):** missing **Atlas projection field** on staged default export (cluster summaries), not command/export breakage.

## Operator commands

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

# Layer-2 (network-free with patched fixtures — see data/operator/ticket316_staged_spine_proof.py)
python data/operator/ticket316_staged_spine_proof.py

# Layer-3 opt-in (may skip unsuitable_live_artifact):
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -q
# 1 passed, 1 deselected

python -m rge.cli verify --skip-site
# 144 golden, 789 pytest, safety audit pass

# Layer-3 attempt:
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -rs
# 1 skipped — unsuitable_live_artifact (live fetch OK; mock markers absent)
```

Safety audit not required — gitignored operator paths only; no public surface changes.

## Drift advisory

Advances **live-research operator proof** via staged-spine atlas refresh (not docs-only).
Live layer-3 remains blocked by fixture-marker preflight on real OpenAlex catalog — expected.
Next product move: **Atlas projection field repair** (staged cluster projection), not another
README or public preview UI iteration until coherence reaches pass on staged path.

## Recommended next ticket

**ticket-317** — Staged spine atlas cluster projection hook (mirror ticket-296 evidence DB
pattern for `export-atlas-snapshot` on staged orchestrator DBs).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: _(pending)_
