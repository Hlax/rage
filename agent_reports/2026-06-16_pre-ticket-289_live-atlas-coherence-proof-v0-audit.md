---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: high
ticket: ticket-289
category: Phase 3 / live research proof / Research Atlas product validation
---

# Pre-Ticket Audit: ticket-289 Live Atlas Coherence Proof v0

## Verdict: **GO** (operator opt-in `live_network` + fixture unit tests)

Extends ticket-285 with a deterministic `atlas_coherence_report` module that emits
human-readable JSON + markdown verdict artifacts from a private atlas snapshot. Live flow
reuses existing staged orchestrator gates; mock LLM upstream only.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | temp private atlas JSON + operator report paths only |
| Public site | **No** | no site changes |
| Schema migrations | **No** | read-only snapshot inspection |
| Theory / inference | **No** | report-only verdict on existing projection |
| Live Ollama | **No** | `RGE_LLM_MODE=mock` |
| Live network | **Yes** | opt-in `live_network`; excluded from default pytest/CI |

## Hardened scope

### In scope

1. **`rge/modules/atlas_coherence_report.py`**
   - `build_atlas_coherence_report(snapshot)` → structured JSON with population, lineage,
     domain, linkage, safety, and verdict sections
   - `format_atlas_coherence_report_markdown(report)` → operator-readable markdown
   - `write_atlas_coherence_report(snapshot, json_path, md_path)` → temp file writer
2. **`tests/unit/test_atlas_coherence_report.py`** — fixture snapshot (network-free)
3. **`tests/unit/test_live_staged_atlas_coherence_report.py`** — live orchestrator → export →
   report (reuse ticket-285 preflight/skip semantics)
4. **Agent report** with coherence verdict table

### Out of scope

- `atlas_snapshot_builder` production changes unless bugfix required for report accuracy
- CI enforcement of `live_network`
- Public atlas route/UI, schema migrations, review_batch persistence
- Live Ollama, README/AGENTS cross-links
- Refactoring ticket-285 test module (may import shared helpers only)

### Verdict sections (required in report JSON)

| Question | Pass signal |
|----------|-------------|
| Meaningful atlas data from live loop? | cards/nodes/runs thresholds + contract valid |
| Claims linked to sources/concepts? | cards have concepts; edges reference known nodes |
| Reports/hypotheses frontend-ready? | reports[] populated with run_id + report_type when runs exist |
| Missing fields → refactor risk? | explicit `refactor_risk_notes[]` for empty optional arrays / lineage gaps |

## Safety

- Temp paths only; no writes under `apps/public-site/` or committed `data/exports/`
- Reuse `validate_atlas_snapshot` + `assert_no_private_fields`
- Layer-3 `unsuitable_live_artifact` skip unchanged

## Recommendation

**GO** — implement product-centered operator coherence report module.
