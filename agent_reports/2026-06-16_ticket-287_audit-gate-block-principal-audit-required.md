# Audit Gate Block: ticket-287 — Principal audit required before implementation

**Date:** 2026-06-16  
**Ticket:** ticket-287 (not implemented)  
**Main tip at gate check:** `af6d996`  
**Gate rule:** ≥3 consecutive `done` tickets since last principal audit checkpoint

## Verdict: **STOP** — do not implement ticket-287 until principal audit completes

## Cadence evidence

| Item | Value |
|------|-------|
| Latest principal audit | `agent_reports/2026-06-16_principal-audit-post-ticket-283.md` |
| Done tickets since checkpoint | **3** — ticket-284, ticket-285, ticket-286 |
| Threshold | 3 |
| Selected ticket | ticket-287 (AGENTS.md atlas coherence cross-link; low risk, docs-only) |

Ticket-287 is docs-only and low risk, but the mandatory cadence gate applies regardless of
risk level when three consecutive implementation tickets landed since the last principal
audit.

## Required action

Run a principal audit checkpoint before resuming ticket-287:

```txt
/rge-principal-audit
```

Or implement seeded **ticket-288** (principal audit post-ticket-286) as a dedicated audit
run — read-only checkpoint; may update runner/docs but must not implement ticket-287 in the
same pass.

## ticket-287 scope (unchanged; deferred)

- Cross-link README Operator Quickstart atlas coherence proof in `AGENTS.md`
- Document `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` and
  `tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network`
- No code or public-site changes

## Recommended sequence

1. **ticket-288** — Principal audit post-ticket-286 (cadence checkpoint)
2. **ticket-287** — AGENTS.md cross-link (resume after audit GO)

## Suggested next prompt

```txt
/rge-principal-audit
```
