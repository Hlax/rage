# RGE Principal Audit

You are the Research Graph Engine **principal audit** agent. This command runs a
read-only checkpoint: repo state, safety boundaries, golden-gate health, audit
cadence, and (when requested) hardened scope for the next ticket.

**Do not** implement queued tickets in this pass. Audits may patch runner/docs
only.

## 0. Preconditions

- Work in the Research Graph Engine repo root.
- Use `python -m rge.cli` when `research.exe` is not on PATH (Windows).
- Working tree should be clean at audit start (document honestly if not).

## 1. Checkpoint status (run first)

```bash
python -m rge.modules.principal_audit_gate --next-ticket ticket-040
```

Interpret `status`:

| `status` | Meaning | Builder action |
|---|---|---|
| `satisfied` | Cadence OK and implementation gate clear | May proceed if other preconditions pass |
| `not_due` | Fewer than 3 done tickets since latest checkpoint | May proceed; monitor cadence |
| `overdue` | ≥3 done tickets since latest checkpoint without fresh audit | **Stop** — complete this principal audit before next implementation |
| `blocked` | Next ticket is medium/high risk without `pre-ticket-<id>` audit | **Stop** — write focused pre-ticket audit first |

Also read `cadence_status`, `implementation_gate`, and `pre_ticket_audit_report`.

### When checkpoints are required

**Cadence (overdue rule):** after **≥3 consecutive `done` tickets** since the
latest principal or pre-ticket audit report in `agent_reports/`.

**Milestone rule (from `/rge-run-next-ticket` step 3.5):** a focused
`pre-ticket-<id>` audit is required before implementation when the next ticket
touches:

- public export / `card_exporter` / export policy
- public site or committed public JSON
- schema migrations
- theory / inference generation
- live Ollama or live smoke constraints

**Risk rule:** `risk_level` `medium` or `high` in the ticket JSON requires a
matching `agent_reports/*pre-ticket-<id>*` report before `/rge-run-next-ticket`.

Pre-ticket audits **also reset** the cadence window for tickets at or after
that ticket number.

## 2. Read required context

1. `AGENTS.md`
2. `tickets/TICKET_QUEUE.md`
3. Latest `agent_reports/*principal-audit*` or relevant `*pre-ticket-*` report
4. `docs/agents/11_AGENT_OPERATING_PROTOCOL.md`
5. `docs/agents/12_RUNTIME_CONFIG.md`
6. `tests/golden/test_22_builder_golden_gate.py` (merge gate inventory)
7. `.github/workflows/golden-gate.yml` (CI golden gate)

## 3. Verification commands (deterministic, mock-only)

```bash
git checkout main
git pull origin main
git status

$env:RGE_LLM_MODE = "mock"          # PowerShell
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q
python -m pytest -q
python -m pytest --collect-only -q   # live_smoke must NOT appear in default collection
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

**CI parity:** `.github/workflows/golden-gate.yml` runs the same mock-only
gates on `main` and pull requests. CI must **not** require Ollama, live LLM
mode, `--publish`, local DB state, or cloud credentials.

## 4. Audit scope checklist

Document findings for:

| Area | Questions |
|---|---|
| Repo / main | Clean tree? Aligned with `origin/main`? Unmerged branches? |
| Ticket queue | Statuses consistent with reports? Active ticket correct? |
| Golden gate | `pytest tests/golden` pass count? GT22 inventory complete? |
| Safety | Full audit `pass`? Public routes read-only? No secret leakage? |
| Public site | Static build succeeds? No `process.env` secrets in build? |
| Live LLM | Golden/fixture runs mock-only? `live_smoke` excluded by default? |
| CI | `golden-gate.yml` present with mock env + golden + safety + site build? |
| Docs | README/runtime docs match repo reality? |

## 5. Phase / roadmap assessment (when applicable)

At phase boundaries (e.g. pre-Phase-2, pre-Phase-3):

- Summarize what is **real** vs **stub/mock-only** vs **intentionally absent**
- List must-fix hygiene issues before broadening scope
- Recommend the **smallest next tickets** (do not implement them here)
- State **GO / NO-GO** with explicit caveats

Use `agent_reports/2026-06-12_pre-phase-2_principal-audit.md` as the reference
shape for a full principal audit.

## 6. Write the audit report

Save to:

```txt
agent_reports/YYYY-MM-DD_pre-phase-<n>_principal-audit.md
```

or, for a focused next-ticket audit:

```txt
agent_reports/YYYY-MM-DD_pre-ticket-<id>_<slug>-readiness-audit.md
```

Include:

- Summary and recommendation (proceed / stop / GO with caveats)
- Repo and queue status tables
- Commands run and results (never claim pass without running)
- Safety boundary answers
- Hardened scope for the next ticket (if applicable)
- Checkpoint status (`satisfied` / `overdue` / `not_due` / `blocked`) with evidence

## 7. Stop

After the report is written, **stop**. Do not implement the queued ticket in
the same invocation.

## Relationship to other commands

| Command | Role |
|---|---|
| `/rge-principal-audit` | Read-only checkpoint + planning (this command) |
| `/rge-run-next-ticket` | Single-ticket implementation; checks audit gate at step 3.5 |
| `/rge-verify` | Test-only verification without planning |
| CI `Golden Gate` workflow | Mechanical enforcement of mock-only gates on merge |
