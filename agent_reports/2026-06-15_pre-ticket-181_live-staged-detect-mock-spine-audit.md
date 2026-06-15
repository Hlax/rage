---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-181
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-181 Live Staged Detect Mock-Fixture Spine

## Verdict: **GO**

Authoritative scope prepared in ticket-180:
`agent_reports/2026-06-15_pre-ticket-180_live-staged-detect-mock-spine-audit.md`.
This file satisfies `principal_audit_gate` filename matching for ticket-181.

## Hardened scope (summary)

- `tests/unit/test_live_staged_detect_mock_spine.py` with `live_network` marker
- Env: `RGE_ALLOW_LIVE_STAGED_DETECT=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
- Local domain opposing-context seed before live discover (mock LLM only)
- Live discover → fetch → ingest → mock extract/link/build → mock detect fixtures
- Assert `relationship_evidence` with `stance = 'qualifies'` ≥ 1

## Rollback

Remove test file; retain ticket-178 build proof.

## Recommendation

**GO** — implement ticket-181; seed ticket-182 docs cross-link.
