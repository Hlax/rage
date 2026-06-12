# RGE Run Next Ticket

You are the Research Graph Engine **implementation** agent. This command runs **exactly one** ticket from the queue end-to-end: code, tests, report, queue update, merge, and push.

**Do not** only propose a ticket, summarize scope, or hand the user a prompt. **Implement** the selected ticket in this run.

## 0. Preconditions

- Work in the Research Graph Engine repo root.
- Use `python -m rge.cli` when `research.exe` is not on PATH (common on Windows).
- One ticket per branch. Do not broaden scope beyond the selected ticket JSON.
- Force mock LLM mode in tests (`RGE_LLM_MODE=mock`). Do not require Ollama.
- No model output may write directly to accepted DB tables; Python validates and repositories write.

## 1. Start from updated main

```bash
git checkout main
git pull origin main
git status
```

Stop with an honest audit note if the working tree is not clean (unless the user explicitly asked you to continue on dirty state).

Record `main` tip SHA before branching.

## 2. Read required context (in order)

1. `AGENTS.md`
2. `tickets/TICKET_QUEUE.md`
3. Selected ticket JSON (see step 3)
4. Latest relevant agent report or pre-ticket audit in `agent_reports/` for the selected ticket or its immediate predecessor
5. Applicable golden test section in `docs/agents/00_GOLDEN_TESTS.md`
6. Relevant sections of `docs/agents/05_DATA_MODEL.md` for tables touched by the ticket

If a pre-ticket audit exists for the selected ticket, follow its **hardened scope** and contract decisions.

## 3. Select the next ticket

From `tickets/TICKET_QUEUE.md`, pick the **lowest-order** ticket with status:

```txt
proposed
ready
```

(in that priority order among open statuses — prefer `ready` over `proposed` when both exist).

- Load `tickets/<ticket-id>.json` (e.g. `tickets/ticket-011.json`).
- If the JSON is missing, stop and write an honest failure note; do not invent scope.
- Set ticket status to `in_progress` in the JSON only after creating the branch (step 4).

**Do not** select tickets marked `done`, `blocked`, `rejected`, or `superseded`.

**Do not** implement multiple tickets in one run.

## 3.5 Audit gate (mandatory stop)

Before selecting or implementing a ticket, check whether a **principal audit** is required. If the gate is unmet, **stop immediately**: do not create a branch, do not implement, and tell the user to run a principal audit checkpoint first (or produce an audit report in `agent_reports/` if you are the audit agent).

Require a current pre-ticket audit report (`agent_reports/*pre-ticket-*` or explicit user audit command) when **any** of the following is true:

| Milestone | Examples | Why |
|---|---|---|
| **Public export** | First or changed `export-public`, `card_exporter`, `public_export_policy` | Public data boundary; fail-closed export must be reviewed |
| **Public site changes** | `apps/public-site/**`, static JSON consumed by the site | Read-only surface, routing, HTML safety |
| **Schema migrations** | New/edited `rge/db/migrations/*.sql` | Irreversible graph shape changes |
| **Theory / inference generation** | First or changed `theory_generator`, candidate-theory CLI, `theory_candidates` persistence, theory report artifacts | Higher-level semantic synthesis must not present speculation as fact or bypass validation |
| **Live Ollama** | Removing mock-only constraints, live model paths in tests | Non-deterministic / environment-dependent behavior |
| **Overdue checkpoint** | ≥3 consecutive `done` tickets since last principal audit | Loop outran intended review cadence |

Additional rules:

- If the selected ticket JSON `risk_level` is `medium` or `high` and no pre-ticket audit exists for that ticket ID, **stop**.
- If the user invoked this command right after a batch of merges without an audit, **stop** and recommend audit before the next implementation.
- Audits are read-only checkpoints: they may patch runner/docs but must not implement the queued ticket.

Record in the implementation report when an audit gate was satisfied (audit file path + date).

## 4. Create the implementation branch

Branch name pattern from queue or ticket JSON:

```txt
phase-<n>/ticket-<id>-<slug>
```

Example:

```bash
git checkout -b phase-1/ticket-011-mock-contradiction-detection
```

Set ticket status to `in_progress` in the JSON only after creating the branch.

## 5. Implement exactly one ticket

Implement **only** what the ticket JSON lists under:

- `affected_modules`
- `expected_files`
- `acceptance_criteria`

Respect `non_goals` strictly (no Ollama, no public export, no LangGraph, no scope creep).

Follow existing repo patterns:

- Model proposes candidate JSON; Python validates; repositories persist.
- Machine-readable rejection/skip reasons for invalid candidates.
- Idempotent CLI re-runs where prior tickets established that pattern.
- Deterministic mock fixtures under `fixtures/llm_outputs/`.
- Golden tests under `tests/golden/` without live model dependency.

Add or update files listed in `expected_files`. Update scaffold golden tests when CLI or schema surface changes.

## 6. Run the ticket test plan

Run commands from the ticket's `test_plan` at minimum:

```bash
python -m pytest <ticket-specific-golden-test-file>
python -m pytest tests/golden
python -m pytest
```

If any command fails, fix within ticket scope or stop and document failures honestly in the agent report (do not mark the ticket `done`).

## 7. Manual CLI verification (when relevant)

When the ticket adds or changes CLI commands, run a fresh DB spine on a temp `--db` path:

```bash
python -m rge.cli ingest <fixture> --domain creativity --db <temp.sqlite>
python -m rge.cli extract-claims --source <source_id> --db <temp.sqlite>
python -m rge.cli link-concepts --source <source_id> --db <temp.sqlite>
# ... subsequent commands per ticket ...
```

Verify machine-readable JSON output and SQLite rows for the acceptance criteria.

On Windows, prefer small helper scripts or separate commands over fragile inline `python -c` quoting.

## 8. Safety audit (when relevant)

Run when the ticket touches public export, public routes, or safety-sensitive surfaces:

```bash
python -m rge.modules.safety_auditor --audit full
```

Otherwise note in the report that safety audit was not required and why.

## 9. Write the agent report

Save to:

```txt
agent_reports/YYYY-MM-DD_phase-<n>_ticket-<id>_<slug>.md
```

Include at minimum:

- Summary
- Ticket ID, branch, date
- Scope in/out
- Changed files
- Acceptance criteria status table
- Commands run and results
- Manual CLI verification (if performed)
- Spec deviations (if any)
- Merge to main section (placeholder until step 12)
- Recommended next ticket
- Suggested next prompt for the following ticket

Use the structure of prior reports in `agent_reports/` (e.g. ticket-009, ticket-010).

## 10. Update ticket queue and JSON files

- Mark the implemented ticket `done` in `tickets/TICKET_QUEUE.md` (branch, report path, queue notes).
- Mark the ticket JSON `status: done`.
- Update **Current Active Ticket** in `TICKET_QUEUE.md` to the next proposed ticket or `none`.
- Create the **next smallest** follow-on ticket as `tickets/ticket-<next-id>.json` (and optional slug duplicate JSON if the repo uses that convention).
- Add the new ticket row to `TICKET_QUEUE.md` as `proposed`.

Do not silently reorder the queue without explaining why in queue notes.

## 11. Commit all changes

Stage all ticket-related files (implementation, tests, fixtures, tickets, agent report).

```bash
git add -A
git commit -m "Implement ticket-<id> <short slug>"
```

Only commit ticket work for this run. Do not amend unless AGENTS.md/user rules allow.

## 12. Merge to main and push (AGENTS.md step 9)

Temporary checkpoint until the safety evaluator agent owns merge gating:

```bash
git checkout main
git pull origin main
git merge --no-ff phase-<n>/ticket-<id>-<slug> -m "Merge branch 'phase-<n>/ticket-<id>-<slug>'"
python -m pytest
git push origin main
```

- Record the merge commit hash in the agent report.
- If merge or push fails, leave ticket `in_progress` or `blocked` in queue/docs, document the failure, and **do not** claim success.
- Do not force-push.

Optional doc follow-up commit on `main` for merge hash (match ticket-009/010 pattern):

```bash
git add agent_reports/<report>.md
git commit -m "docs: record main merge hash for ticket-<id>"
git push origin main
```

## 13. Stop

After push succeeds (or after documenting a merge/push failure), **stop**. Do not start the next ticket in the same run.

## Failure rules

- Never claim tests passed unless you ran them.
- Never mark a ticket `done` without an agent report.
- Never implement the next queued ticket in the same invocation.
- Never merge unrelated dirty changes.
- If the selected ticket is not ready (missing schema, blocking audit finding), stop, write an honest agent report or audit note, and recommend the smallest hardening ticket instead of improvising broad scope.
