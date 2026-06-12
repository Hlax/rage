---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-018 Audit: Question Generation Readiness

- Audit type: pre-implementation readiness audit
- Date: 2026-06-12
- Agent/model: Cursor builder agent (Auto)

## Summary

**Ready for ticket-018** with hardening folded into the ticket. Main at `90316c6`; 73 golden tests pass. `validate-contract` / `validate_followup_for_contract` (GT10) provides contract gating; ticket-018 adds batch generation from cluster/theory context via `generate-followup-questions` CLI.

## Contract decisions

1. Reuse `research_queue` follow-up rows (`item_type='question'`) — no new migration.
2. Extend out-of-scope matching for labor-displacement phrasing ("replace" + "job").
3. Golden GT16 uses deterministic question batch + cluster/theory context merge.
4. CLI: `generate-followup-questions` with `--contract`, `--db`, optional `--cluster-report`.

Recommendation: **proceed with ticket-018**.
