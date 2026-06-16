# Agent Report: ticket-287 — AGENTS.md atlas coherence cross-link

**Date:** 2026-06-16  
**Ticket:** ticket-287  
**Branch:** `phase-3/ticket-287-agents-atlas-coherence-crosslink`  
**Main tip before branch:** `7b2085f`  
**Audit gate:** `agent_reports/2026-06-16_principal-audit-post-ticket-286.md` (GO)

## Summary

Cross-linked ticket-285 live staged atlas snapshot coherence proof in `AGENTS.md`:
orchestrator env gate, `live_network` pytest command, layer-3 `unsuitable_live_artifact`
skip semantics, and README Operator Quickstart pointer. Docs-only hygiene closure — does
**not** extend the infrastructure/docs streak as product work.

## Scope

**In:** `AGENTS.md` cross-link paragraph only.

**Out:** Production code, public-site, atlas schema, live LLM, runtime config cross-links.

## Changed files

| File | Change |
|------|--------|
| `AGENTS.md` | Atlas coherence operator cross-link + pytest command block |
| `tickets/ticket-287.json` | Status `done` |
| `tickets/ticket-289.json` | Seeded product-centered live atlas coherence operator report |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| AGENTS.md cross-links README + documents orchestrator gate and pytest path | **PASS** |
| `unsuitable_live_artifact` skip documented (ticket-234 consistent) | **PASS** |
| No code or public-site changes | **PASS** |
| Golden + full pytest green | **PASS** — 142 golden, 736 full |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 736 passed, 31 deselected
```

Safety audit not required — documentation-only ticket.

## Drift note — ticket-287 must not extend the streak

Tickets 284–287 closed **documentation and cross-link hygiene** for the Research Atlas
thread. This ticket is intentionally narrow and **must not** be treated as further atlas
infrastructure. The next queued work should pivot to **live/product proof**.

## Recommended next ticket

**ticket-289 — Live Atlas coherence proof v0 (operator report)**

Product-centered operator opt-in proof: run existing live staged gates → export private
`atlas_snapshot.json` → produce a **human-readable coherence verdict report** auditing
whether real research output usefully populates `runs[]`, `nodes[]`, `edges[]`, `cards[]`,
`reports[]`, `follow_up_questions[]`, lineage/domain fields, and private-field safety —
with explicit answers to frontend-readiness questions (claims linked to sources/concepts,
hypothesis/report representation, missing-field refactor risk). Mock-only CI unchanged.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: _(pending)_
