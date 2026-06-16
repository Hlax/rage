# Audit Gate Block: ticket-293 — Pre-ticket audit required before implementation

**Date:** 2026-06-16  
**Ticket:** ticket-293 (not implemented)  
**Main tip at gate check:** `cec85a2`  
**Gate rule:** `risk_level: high` requires `agent_reports/*pre-ticket-293*` before implementation

## Verdict: **STOP** — do not implement ticket-293 until pre-ticket audit completes

## Gate evidence

| Item | Value |
|------|-------|
| Selected ticket | ticket-293 — Live NM-1 extraction expansion + Atlas coherence quality proof v0 |
| Ticket risk level | **high** |
| Pre-ticket audit for ticket-293 | **Missing** — no `agent_reports/*pre-ticket-293*` |
| Cadence status | **Satisfied** — 1 done ticket since pre-ticket-291 (ticket-292); threshold 3 |
| Principal audit gate | `status: satisfied` (`python -m rge.modules.principal_audit_gate`) |
| Implementation gate | **Blocked** — high-risk ticket without pre-ticket audit |

Cadence is clear, but the **risk rule** is mandatory regardless of cadence:

> If the selected ticket JSON `risk_level` is `medium` or `high` and no pre-ticket audit
> exists for that ticket ID, **stop**.

## Milestone triggers (ticket-293)

| Trigger | Applies? | Notes |
|---------|----------|-------|
| Live Ollama | **Yes** | Operator opt-in NM-1 / NM-4 evidence DB spine; not default pytest |
| Live network | **Possible** | Ticket scope centers NM-1 manual path; staged network optional |
| Public export / site | **No** | Private atlas snapshot + operator report only |
| Schema migrations | **No** | |
| Theory / inference | **No** | |

## ticket-293 scope (unchanged; deferred)

Product-centered operator proof — no default CI live tests:

1. Opt-in live research run on gitignored evidence DB (`RGE_ALLOW_LIVE_LLM=1`, Ollama), **or**
   document exact gate/environment blocker honestly.
2. Private `atlas_snapshot.json` from live-derived temp/evidence DB via `export-atlas-snapshot`.
3. `atlas-coherence-report` on that snapshot.
4. Human-readable quality verdict (**GO / PARTIAL / NO-GO**) covering claims, sources,
   concepts, edges, follow-ups, lineage, frontend-readiness.
5. Recommend next concrete improvement from observed live behavior.
6. Mock golden + full pytest remain green; no public routes/site/schema/review_batch.

**Expected deliverable:** `agent_reports/2026-06-16_phase-3_ticket-293_live-nm1-atlas-quality-proof-v0.md`

## Required action

Write a focused pre-ticket audit before resuming implementation:

```txt
/rge-principal-audit
```

Scope the audit to ticket-293: hardened NM-1/NM-4 operator path, temp/evidence DB only,
no default pytest live collection, fail-closed export/coherence boundaries, and honest
NO-GO when Ollama or live gates are unavailable.

## Recommended sequence

1. **Pre-ticket-293 audit** — GO/NO-GO with hardened scope (mirror ticket-285 pattern)
2. **ticket-293** — operator live quality proof + agent report (resume after audit GO)

## Drift note

Ticket-292 closed the Atlas regression-proof layer. ticket-293 is the intended
product-centered pivot; do not substitute another operator-tooling-only ticket while
this gate is open.

## Suggested next prompt

```txt
/rge-principal-audit
```
