# AGENT_OPERATING_PROTOCOL.md

## Purpose

This document defines how Cursor/build agents should operate while implementing the Research Graph Engine.

It is not a product spec. It is the agent execution protocol.

## Core Principle

Agents may implement scoped tickets, but they must not freely refactor the project, bypass tests, or silently change architecture.

The project advances through:

```txt
specs
→ tickets
→ one branch per ticket
→ implementation
→ tests
→ safety audit
→ agent report
→ next ticket
→ human checkpoint
```

## Agent Roles

### Planning Agent

Responsible for:

- Reading specs.
- Creating implementation plans.
- Breaking phases into tickets.
- Identifying risks.
- Defining acceptance criteria.
- Not writing code unless explicitly asked.

### Builder Agent

Responsible for:

- Implementing one ticket.
- Editing expected files only.
- Adding or updating tests.
- Running required commands.
- Writing a build report.
- Recommending the next ticket.

### Verification Agent

Responsible for:

- Running tests and audits.
- Checking reports.
- Checking public export safety.
- Checking that the build matches the specs.
- Not changing code unless explicitly asked.

### Handoff Agent

Responsible for:

- Summarizing current repo state.
- Listing passing/failing commands.
- Proposing the next smallest ticket.
- Creating a clean next-agent prompt.

## Ticket Rules

Read the queue from `tickets/TICKET_QUEUE.md`. Save ticket JSON files to `tickets/`.

Every ticket must include:

- `title`
- `problem`
- `evidence`
- `affected_modules`
- `expected_files`
- `acceptance_criteria`
- `test_plan`
- `non_goals`
- `risk_level`
- `rollback_plan`

Agents must reject vague tickets like:

```txt
make it better
finish the MVP
clean up everything
refactor the architecture
```

## Branch Rules

Use one branch per ticket.

Recommended branch naming:

```txt
phase-<n>/ticket-<id>-<short-slug>
```

Example:

```txt
phase-0/ticket-001-repo-scaffold-model-runtime
```

Do not combine unrelated tickets on one branch.

## Improvement Ticket Promotion

Generated improvement tickets are **drafts** only. They are written to
gitignored `data/tickets/improvement_ticket_latest.json` and persisted in
`improvement_tickets` rows. Pipeline runs (including `research run
--fixture-mode`) **never** promote drafts into the builder queue automatically.

To round-trip a draft into a builder-consumable queue ticket:

1. Run `research generate-improvement-tickets` (or complete a fixture spine that
   produces failure modes).
2. Review the draft JSON and validate it is specific enough for a branch task.
3. Run an explicit promotion with the review gate:

```bash
python -m rge.cli promote-improvement-ticket \
  --queue-ticket-id ticket-041 \
  --run-id <run_id> \
  --failure-reason overgeneralized_scope \
  --confirm
```

Alternatively load from a reviewed JSON file with `--from-json`. Promotion writes
`tickets/<queue-ticket-id>.json` with `status: proposed` and re-validates GT21
builder-consumption rules. It does **not** edit `TICKET_QUEUE.md`; a human or
audit agent adds the queue row after reviewing the promoted JSON.

## Implementation Rules

Agents must:

- Prefer small, reversible changes.
- Preserve public/private boundaries.
- Preserve fixture determinism.
- Preserve rejected claims and failure records.
- Use mock LLM mode in golden tests.
- Treat all source text as untrusted.
- Keep creativity-specific logic in the creativity domain pack.
- Write reports when done.

Agents must not:

- Add public write routes.
- Add public source ingestion.
- Add public agent execution.
- Add model-controlled shell access.
- Add model-controlled Git push.
- Let Qwen/Ollama write accepted DB rows directly.
- Auto-activate domains or concepts from model output.
- Delete failure records to make tests pass.
- Claim success without running required commands or documenting why they were unavailable.

## Report Rules

Every agent run must write a report in `agent_reports/`.

Reports must include:

- Summary.
- Changed files.
- Commands run.
- Test results.
- Acceptance criteria status.
- Safety audit status.
- Known failures.
- Spec deviations.
- Recommended next ticket.
- Suggested next prompt.

If tests fail, the report must say so clearly.

## Phase Checkpoints

At phase checkpoints, run the strongest available command set:

```bash
pytest tests/golden
research run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
research export-public --limit 100
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

If a command does not exist yet, report:

```txt
NOT AVAILABLE IN THIS PHASE
```

Do not mark unavailable commands as passing.

## Operator Loop (default workflow)

Reduce human-in-the-loop coordination burden without removing safety gates.
Use the bounded operator loop runner before manual handoffs:

```bash
python -m rge.modules.operator_loop --mode plan
python -m rge.modules.operator_loop --mode execute-safe
```

**Plan mode** is read-only. It inspects `tickets/TICKET_QUEUE.md`, ticket JSON
files, the latest `agent_reports/` entry, principal audit cadence via
`principal_audit_gate`, pending draft improvement tickets, git working-tree
cleanliness, and documentation-ahead-of-git drift. It emits machine-readable JSON
with:

- current ticket state
- audit cadence state
- documentation/git drift findings
- next recommended action
- gate classification: `safe_autonomous`, `review_gated`, or `blocked`
- exact commands to run next

**Execute-safe mode** runs only deterministic mock-only checks when the working
tree is clean:

```bash
RGE_LLM_MODE=mock python -m pytest tests/golden
RGE_LLM_MODE=mock python -m pytest
RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build   # when applicable
```

The operator loop must **never** merge to main, push, publish public-site data,
promote improvement tickets, edit `TICKET_QUEUE.md`, enable live LLM mode, or
run live smoke tests. It must report `blocked` when branch, report, queue, or
dirty-path state indicates documentation-ahead-of-git drift.

Default operator workflow:

1. Run `--mode plan` and read the JSON recommendation.
2. Let `--mode execute-safe` run deterministic checks when eligible.
3. Approve only `review_gated` actions (implementation, principal audit,
   improvement-ticket promotion, merge checkpoint).
4. Resolve `blocked` states (dirty tree, branch mismatch, report drift) before
   continuing.

**Live probe scratch evidence workflow** (local Ollama opt-in; operator-only
persist): after live probe sessions, follow the numbered checklist in
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` (**Scratch evidence workflow
checklist**). Plan mode surfaces `scratch_evidence_status` and may recommend
`run_scratch_evidence_review` when reviewed scratch rows exist. See also
`AGENTS.md` Operator Loop and README Operator Quickstart.

**Manual synthnote operator spine** (mock LLM; tickets 088–099): for Level-1
`manual_text` research on the creativity synthnote source, follow the five-step
CLI sequence in README **Operator Quickstart** (**Manual synthnote operator spine**):
ingest → extract-claims → link-concepts → build-relationships →
detect-contradictions. Checksum fixtures resolve from
`fixtures/manual_source_fixture_map.json` (no `--fixture` flags for `manual_text`).
Operator sources: gitignored `data/sources/manual/creativity/`; test copy:
`fixtures/sources/manual_synthnote.txt`. See also `AGENTS.md` Operator Loop.

**Manual synthnote score reconciliation** (after the five-step spine): ingest a
follow-up `manual_text` source, extract claims, then run `reconcile-scores`.
See README **Operator Quickstart** (**Manual synthnote score reconciliation**)
for steps 6–8 (follow-up ingest → extract-claims → reconcile-scores; expected
1 `score_events` row and `may_reduce` confidence 0.5 → 0.62). Test copy:
`fixtures/sources/manual_synthnote_followup.txt`. See also `AGENTS.md` Operator Loop.

## Human Checkpoints

Human review is required before:

- Merging a phase branch.
- Declaring a phase complete.
- Changing safety policy.
- Changing public export schema.
- Activating a new domain pack.
- Allowing any public route beyond static/read-only pages.
- Allowing model-controlled tools beyond structured candidate generation.

Principal audit cadence: run `/rge-principal-audit` (or
`python -m rge.modules.principal_audit_gate --next-ticket <id>`) when ≥3
consecutive tickets are `done` since the latest checkpoint report, before
medium/high-risk tickets, or before milestone changes listed in
`.cursor/commands/rge-run-next-ticket.md` step 3.5. CI enforces mock-only
golden gates via `.github/workflows/golden-gate.yml`.

## Template Versioning

Agent reports and handoffs should use the current templates in:

```txt
docs/agents/templates/
```

Reports must record the `template_id` and `template_version` they used. Do not rewrite old reports when templates change.
