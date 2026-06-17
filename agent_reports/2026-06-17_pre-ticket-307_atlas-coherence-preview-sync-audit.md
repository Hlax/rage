---
template_id: audit_report
template_version: 1.0.0
status: current
date: 2026-06-17
phase: 3
checkpoint_before: ticket-307
---

# Pre-Ticket-307 Audit: Atlas Coherence Preview JSON Sync

- Audit type: pre-ticket audit (atlas export producer + public preview JSON)
- Date: 2026-06-17
- Baseline HEAD: `9975b1e` (`main`)
- Prior checkpoint: `agent_reports/2026-06-17_pre-ticket-306_atlas-coherence-summary-inline-audit.md`
- Trigger: ticket-307 (`risk_level: medium`; touches public preview JSON)

## Executive summary

**GO — implement ticket-307 with hardened scope below.**

Codify `build_atlas_coherence_preview()` derived from atlas snapshot +
`build_atlas_coherence_report` population counts and inline `coherence_summary`.
Refresh committed `atlas_coherence_preview.json` via export helper (no hand edits).

## Gate output

```json
{
  "status": "go",
  "implementation_gate": "satisfied",
  "pre_ticket_audit_required": true,
  "pre_ticket_audit_written": true
}
```

## Hardened scope

**In:**

- `ATLAS_COHERENCE_PREVIEW_SCHEMA_VERSION = "atlas_coherence_preview_v0"`
- `build_atlas_coherence_preview(snapshot)` — fields:
  `overall_coherence_verdict`, `preview_label` from `coherence_summary`;
  `population` from coherence report; `schema_version` constant
- `export_atlas_coherence_preview_to_path(snapshot, path)`
- Optional `coherence_preview_path` on `export_atlas_snapshot_to_path` (write sidecar when set)
- Regenerate committed `apps/public-site/public/data/atlas_coherence_preview.json`
- Unit tests in `test_atlas_coherence_preview_sync.py`

**Out:**

- Removing `atlas_coherence_preview.json`
- `export-public` changes
- Schema migrations
- Full coherence report body in preview JSON

## Safety boundary

| Check | Posture |
|-------|---------|
| Allowed fields | verdict, preview_label, population counts, schema_version only |
| Private-field scan | Preview derived from already-scanned snapshot |
| Public site | JSON file update only; no new routes |
| export-public | **Unchanged** |

## Recommendation

| Action | Verdict |
|--------|---------|
| `/rge-run-next-ticket` for ticket-307 | **GO** |
