---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-068 Scratch DB Reviewed Live Probe Persistence Audit

- Audit type: focused pre-ticket readiness (isolated SQLite for operator-reviewed probe reports)
- Date: 2026-06-12
- Baseline HEAD: `9c33eca` (post-ticket-067 principal audit on main)
- Principal gate: `cadence_status: satisfied` for ticket-068

## 1. Executive verdict

**GO — seed ticket-068 with narrowed scope**

Ticket-067 proved 3/4 suite fixtures pass report-only floors. Operators need a
**separate scratch SQLite** to accumulate **explicitly reviewed** probe metadata
for evidence review — not accepted graph claims, not public export, not model
authority.

## 2. Is ticket-068 safe to seed?

**Yes**, if implementation stays within the hardened scope below. Risk is
**medium** (new DB write surface) but isolated from `creative_research.sqlite`
and from `export-public`.

## 3. What exact DB is being written?

| Property | Value |
| -------- | ----- |
| Default path | `data/db/live_probe_scratch.sqlite` |
| Engine | SQLite via existing `rge.db.connection.connect` |
| Schema | **Dedicated** `rge/db/live_probe_scratch_schema.sql` — **not** main `schema_migrations` |
| Tables | Single table `reviewed_live_probe_reports` (metadata only) |
| Main DB | `data/db/creative_research.sqlite` — **never written** by this ticket |

## 4. Isolation from default graph DB

- Separate file path constant (`LIVE_PROBE_SCRATCH_DB_PATH` ≠ `DEFAULT_DB_PATH`)
- No imports of `ClaimRepository`, `RelationshipRepository`, or main migrations
- No writes to `claims`, `relationships`, `claim_concepts`, or public export tables
- `data/` remains gitignored (covers `data/db/*.sqlite`)

## 5. What command triggers writes?

**Only** explicit operator CLI (proposed):

```powershell
python -m rge.cli probe-persist-reviewed-report --report <path> --confirm-review
```

Optional: `--scratch-db`, `--note`.

**Not triggered by:** `probe-mini-run`, `probe-mini-run-suite`, individual stage
probes, mock/live LLM tasks, or model output callbacks.

Require `--confirm-review` flag (fail closed without it).

## 6. How do we prove ordinary live probes still do not write?

- Unit test: run `run_probe_mini_run` with mock client; assert scratch DB file
  absent or mtime unchanged
- Existing live probe reports retain `db_writes: false`
- No calls from `live_probe.py` to scratch persist module

## 7. How do we prove scratch data cannot be exported publicly?

- `export-public` / `card_exporter` unchanged — reads accepted claims from **main** DB only
- Scratch table stores **sanitized metadata** (counts, modes, relative report path, diagnostics summary) — no raw prompts, no full accepted claim payloads as graph rows
- Safety auditor adds evidence check: scratch module exists; no export route reads scratch DB
- Golden GT11 unchanged; scratch DB path under gitignored `data/`

## 8. Persisted fields (sanitized)

- report identity: relative `report_path`, `report_created_at`, `command`
- run context: `fixture_source`, `run_mode`, `strict_chain`, `status`, `floors_met`
- stage counts: accepted/rejected per stage
- `contradiction_input_mode`, `effective_llm_mode`, `provider`, `model` (from report)
- capped `rejection_diagnostics` JSON (strings only, max length)
- `operator_reviewed_at`, optional `operator_note`, `ingested_at`

**Not persisted:** raw prompts, API keys, absolute paths, full accepted claim/relationship objects as graph entities.

## 9. Required tests

- Insert/read round-trip on scratch repository
- CLI persists fixture mini-run report with `--confirm-review`
- CLI fails without `--confirm-review`
- Malformed / wrong report_type fails closed
- Missing report path fails closed
- Ordinary mini-run does not create/write scratch DB
- Safety audit pass with new evidence file

## 10. Out of scope

- Followup contradiction calibration (ticket-067 gap)
- ticket-059 / OpenAI
- Public export of probe reports
- Import into accepted graph DB
- Auto-persist on mini-run completion
- Qwen ticket authority
- Broad DB layer refactor

## 11. Rollback plan

Revert scratch schema module, CLI command, tests, runbook docs, and safety auditor
evidence hook. Delete local `data/db/live_probe_scratch.sqlite` if created. No main
schema migration to roll back.

## 12. Recommendation

**Seed ticket-068** and implement on branch
`phase-2/ticket-068-scratch-db-reviewed-live-probe-persistence`.
