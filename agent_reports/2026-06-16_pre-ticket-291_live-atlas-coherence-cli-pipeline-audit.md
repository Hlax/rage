---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: high
ticket: ticket-291
category: Phase 3 / live research proof / Research Atlas operator pipeline
---

# Pre-Ticket Audit: ticket-291 Live Atlas Coherence CLI Pipeline

## Verdict: **GO** (opt-in `live_network` pytest only)

Chains existing CLIs on temp paths after staged orchestrator: `export-atlas-snapshot` →
`atlas-coherence-report`. No new production CLI surface; validates operator pipeline
end-to-end via stdout JSON.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | temp private paths only |
| Public site | **No** | no site changes |
| Schema migrations | **No** | temp DB |
| Theory / inference | **No** | read-only report assertions |
| Live Ollama | **No** | mock LLM |
| Live network | **Yes** | `live_network` excluded from default pytest |

## Hardened scope

### In scope

1. **`tests/unit/test_live_staged_atlas_coherence_cli_pipeline.py`**
2. Flow: preflight → orchestrator → `export-atlas-snapshot` CLI → `atlas-coherence-report` CLI
3. Assert coherence CLI stdout: `overall_coherence_verdict`, `json_path`, `markdown_path`
4. Layer-3 `unsuitable_live_artifact` skip unchanged
5. Env gate unit test (non-live_network)

### Out of scope

- New CLI commands or builder changes
- CI live_network
- Public routes/site/schema
- README/AGENTS

## Recommendation

**GO** — implement CLI pipeline live_network proof test module.
