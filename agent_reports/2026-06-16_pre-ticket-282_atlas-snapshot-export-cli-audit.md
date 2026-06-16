---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-282
category: Phase 3 / Research Atlas / private export CLI
---

# Pre-Ticket Audit: ticket-282 Private Atlas Snapshot Export CLI v0

## Verdict: **GO** (operator-private write path — not public export)

Adds `export-atlas-snapshot` CLI writing validated `atlas_snapshot_v0.1.0` JSON to an
operator-specified `--out` path. Reuses ticket-279/281 builder validation and
private-field leak checks before any disk write.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | Separate command from `export-public`; private operator path only |
| Public site | **No** | None |
| Schema migrations | **No** | None |
| Theory / inference | **No** | Read-only projection |
| Live Ollama | **No** | Mock/fixture tests only |
| Overdue principal audit | **No** | 1 done ticket since pre-ticket-281 |

## Hardened scope

### In scope

1. `export_atlas_snapshot_to_path` helper (builder module)
2. `export-atlas-snapshot` CLI with `--out`, `--db`, `--fixture-mode`, topic/domain args
3. Unit tests: write, byte-identical re-run, fail-closed leak
4. Scaffold help lists new subcommand

### Out of scope

- Public routes or public-site JSON consumption
- `research_questions` table
- Agent Lab persistence

## Safety

- Fail-closed: `assert_no_private_fields` + `validate_atlas_snapshot` before write
- Output path is operator-controlled; no default write under `apps/public-site/`
- `--fixture-mode` uses pinned metadata for deterministic bytes

## Recommendation

**GO** — implement private atlas snapshot export CLI.
