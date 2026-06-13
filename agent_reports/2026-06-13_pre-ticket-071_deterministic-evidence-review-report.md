---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-071 Deterministic Evidence Review Report Audit

- Audit type: focused pre-ticket readiness (operator reporting over scratch evidence)
- Date: 2026-06-13
- Baseline HEAD: `64f4686` (post-ticket-070 principal audit on main)
- Human direction: `/rge-next-ticket` after post-ticket-070 checkpoint

## 1. Executive verdict

**GO — deterministic evidence review report (no LLM, no graph writes)**

Ticket-070 added `probe-scratch-summary`, which aggregates scratch SQLite rows into
machine-readable JSON/markdown with safety flags. Operators still lack a **single,
formatted evidence review artifact** suitable for principal/human review before
seeding improvement tickets. Ticket-071 should compose that artifact from the
existing summary builder only — no new DB surface, no model calls.

## 2. Is ticket-071 safe to seed?

**Yes**, if scope stays:

- Read-only reuse of `build_scratch_summary()` / scratch DB `mode=ro`
- Output only to private paths (`agent_reports/`, `data/reports/`)
- Factual counts and tables only — **no ticket recommendations from code**
- No LLM, OpenAI, or cloud API

## 3. Inputs and read surface

| Input | Access |
| ----- | ------ |
| Scratch DB `reviewed_live_probe_reports` | Read-only via existing summary module |
| Scratch summary JSON | Derived in-process; not re-parsed from public export |
| Live probe JSON reports | **Out of scope** — summary rows already sanitized |

## 4. Write behavior

| Surface | Mutates? |
| ------- | -------- |
| Scratch DB | **No** |
| Accepted graph DB | **No** |
| `--out` evidence review file | **Optional** — private path only when flag provided |
| stdout | **Yes** — formatted report text when no `--out` |

Summary command already validates private output prefixes. Ticket-071 must reuse
the same validation helper or equivalent rules.

## 5. Edge cases

| Case | Behavior |
| ---- | -------- |
| Missing scratch DB | Fail closed (reuse summary error) unless `--allow-empty` passed through |
| Empty scratch DB | Valid empty evidence review with explicit zero state |
| Invalid schema | Fail closed via summary layer |
| Missing `--out` | Print to stdout only; no file write |

## 6. Public export isolation

- Must not import `card_exporter`
- Output paths blocked under `data/exports/` and `apps/public-site/public/`
- Report must not include raw prompts, model responses, operator note bodies, or API keys
- Safety attestation block mirrors summary flags

## 7. Required tests

- Unit: evidence review renders deterministic markdown/JSON from seeded scratch DB
- Unit: repeated runs produce identical output
- Unit: missing DB fail closed / `--allow-empty`
- Unit: `--out` rejects public export paths
- Unit: output excludes forbidden private patterns
- Unit: no scratch DB mutation; no graph DB touch
- Regression: existing scratch summary tests still pass

## 8. Out of scope

- LLM synthesis or ticket seeding from report content
- OpenAI / ticket-059
- Scratch schema changes
- Accepted graph persistence
- Public site / export changes
- Live probe behavior changes
- Duplicating full summary logic (reuse ticket-070 module)

## 9. Rollback plan

Revert evidence review module, CLI, tests, docs; operators retain
`probe-scratch-summary` unchanged.

## 10. Recommendation

Seed **ticket-071 — Deterministic scratch evidence review report** on branch
`phase-2/ticket-071-deterministic-evidence-review-report`.

Do **not** seed ticket-059 without separate operator approval and audit.
