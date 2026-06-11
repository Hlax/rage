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

## Human Checkpoints

Human review is required before:

- Merging a phase branch.
- Declaring a phase complete.
- Changing safety policy.
- Changing public export schema.
- Activating a new domain pack.
- Allowing any public route beyond static/read-only pages.
- Allowing model-controlled tools beyond structured candidate generation.

## Template Versioning

Agent reports and handoffs should use the current templates in:

```txt
docs/agents/templates/
```

Reports must record the `template_id` and `template_version` they used. Do not rewrite old reports when templates change.
