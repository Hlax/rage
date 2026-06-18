---
template_id: pre_ticket_audit
status: GO
date: 2026-06-18
risk_level: medium
ticket: ticket-316
category: Phase 3 / live staged spine / operator proof
---

# Pre-Ticket Audit: ticket-316 Live Staged-Spine Operator Proof Refresh v0

## Verdict: **GO** (operator report + regression pytest; optional opt-in `live_network`)

Refreshes operator-private staged-spine atlas export proof after ticket-315 evidence DB
refresh (PARTIAL product verdict). Confirms whether the staged orchestrator path produces
**richer** private atlas graph data than the single-source evidence DB baseline, with
honest fallback to layer-2 mock staged spine when live OpenAlex preflight skips.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | Private `export-atlas-snapshot` to gitignored `data/atlas/ticket316/` only |
| Public site | **No** | No site or committed public JSON changes |
| Schema migrations | **No** | Temp/gitignored DB via existing staged orchestrator |
| Theory / inference | **No** | Read-only atlas + coherence reporting |
| Live Ollama | **No** | `RGE_LLM_MODE=mock`; orchestrator forces mock LLM upstream |
| Live network | **Optional** | Layer-3 opt-in via existing `test_live_staged_atlas_snapshot_coherence.py`; layer-2 mock spine fallback required when skip |

## Hardened scope

### In scope

1. **Operator proof (primary):**
   - Layer-2 fallback: `research run --fixture-mode --staged-spine` on gitignored temp DB
     (patched OpenAlex/fetcher I/O same as unit tests — network-free)
   - `export-atlas-snapshot` without `--fixture-mode`
   - `atlas-coherence-report` on exported snapshot
   - Artifacts under gitignored `data/db/ticket316_*` and `data/atlas/ticket316/`
2. **Layer-3 attempt (optional):** operator `pytest -m live_network` on
   `test_live_staged_atlas_snapshot_coherence.py` when env gates set; document skip JSON
   honestly (`unsuitable_live_artifact` not a regression)
3. **Product comparison table** vs ticket-315 baseline (runs, cards, edges, nodes, reports,
   follow-ups, clusters, overall coherence, product verdict GO/PARTIAL/NO-GO)
4. **Regression:** `pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -q` (non-live);
   `python -m rge.cli verify`
5. **Agent report** with audit gate reference and next product ticket recommendation

### Out of scope

- Production code changes unless regression found in pytest
- README-only documentation
- Public atlas UI or `export-public`
- CI enforcement of `live_network`
- Live Ollama per-step fallthrough
- Schema migrations / `review_batch` persistence
- New test modules (reuse ticket-285 module)

### Product verdict rubric (report)

| Verdict | Criteria |
|---------|----------|
| **GO** | Staged spine atlas materially richer than ticket-315 (multi-card and/or multi-edge) with coherence pass |
| **PARTIAL** | Coherence pass but graph only marginally richer than ticket-315 single-claim baseline |
| **NO-GO** | Export/coherence fails or staged path does not populate atlas meaningfully |

## Safety

- Gitignored operator paths only — no writes under `apps/public-site/` or `data/exports/`
- Mock LLM upstream on staged orchestrator (existing contract)
- No public write routes

## Audit gate for implementation

Principal audit cadence **satisfied** (2 done since ticket-314 checkpoint; threshold 3).
This pre-ticket audit satisfies **medium-risk** gate for ticket-316.

## Recommended implementation order

1. Run layer-2 mock staged orchestrator CLI spine → export → coherence
2. Attempt layer-3 live_network pytest; record skip or pass
3. Compare population vs ticket-315 table
4. Full verify + agent report
