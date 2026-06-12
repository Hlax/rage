# AGENTS.md

## Purpose

This file is the root operating guide for AI builder agents working in the Research Graph Engine repo.

The repo implements a local-first Research Graph Engine. The system turns sources into scoped claims, concept links, evidence relationships, reports, public cards, and improvement tickets.

Agents must follow the implementation specs in `docs/agents/`.

## Source Priority

Read sources in this order:

1. `docs/agents/01_RESEARCH_GRAPH_ENGINE_CANONICAL_CONTEXT_v1.md`
2. `docs/agents/00_GOLDEN_TESTS.md`
3. `docs/agents/02_ARCHITECTURE.md`
4. `docs/agents/03_MODEL_RUNTIME_SPEC.md`
5. `docs/agents/04_CURSOR_BUILD_LOOP.md`
6. `docs/agents/05_DATA_MODEL.md`
7. `docs/agents/06_DOMAIN_PACK_SPEC.md`
8. `docs/agents/07_MVP_ACCEPTANCE_TESTS.md`
9. `docs/agents/08_REPORTING_SPEC.md`
10. `docs/agents/09_RESEARCH_RUN_CONTRACT.md`
11. `docs/agents/10_SAFETY_MODEL.md`
12. `docs/agents/000_init.md` only as historical seed context

If documents conflict, follow the higher-priority document.

## Non-Negotiable Rules

- One ticket per branch.
- Do not broaden implementation scope without creating a new ticket.
- Do not hardcode creativity-specific fields into the core engine.
- Qwen/Ollama proposes candidate JSON only; Python validates and writes.
- Golden tests must support mock LLM mode and must not require Ollama to be running.
- No model output may write directly to accepted DB tables.
- No public write routes.
- No public source ingestion routes.
- No public agent execution routes.
- No raw prompts, local paths, secrets, private notes, or raw source text in public exports.
- Every implementation run must end with an agent report in `agent_reports/`.
- Never claim success unless required commands were run, or failures are explicitly documented.

## Operator Loop (human default)

Before coordinating the next ticket manually, run the bounded operator loop:

```bash
python -m rge.modules.operator_loop --mode plan
python -m rge.modules.operator_loop --mode execute-safe
```

Plan mode is read-only and recommends the next action with gate classification
(`safe_autonomous`, `review_gated`, `blocked`). Execute-safe runs mock-only
golden tests, pytest, safety audit, and public-site build when the working
tree is clean. It never merges, pushes, promotes tickets, or edits the queue.
See `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` for the full workflow.

## Expected Agent Workflow

1. Read the active ticket from `tickets/TICKET_QUEUE.md` or create the smallest next ticket in `tickets/`.
2. Confirm the phase and scope.
3. Identify expected files.
4. Implement only the ticket scope.
5. Run the required tests.
6. Run safety audit if relevant.
7. Write an agent report.
8. Recommend the next smallest ticket.
9. **Temporary merge checkpoint (until safety evaluator agent is live):** after a
   ticket is marked `done` and the agent report is written, merge the ticket
   branch into `main` and push `origin main`. Document the merge commit hash in
   the agent report. Do not force-push. If merge or push fails, leave the ticket
   `in_progress` or `blocked` and document the failure honestly.
   When the safety evaluator agent owns merge gating, remove this step and
   restore human/checkpoint merge per `docs/agents/04_CURSOR_BUILD_LOOP.md`.

## Default Verification Commands

Use the strongest available verification for the current phase.

**Preferred:** one mock-only suite (golden tests, full pytest, safety audit, optional site build):

```bash
export RGE_LLM_MODE=mock
python -m rge.cli verify
```

```powershell
# PowerShell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify
```

Add `--skip-site` when Node.js is unavailable or you only need Python checks:

```bash
python -m rge.cli verify --skip-site
```

On Windows, `research` may not be on PATH after `pip install -e ".[dev]"`. Use
`python -m rge.cli` for all CLI commands (including `verify`); do not treat a
missing `research` command as a verification failure when the module form works.

`operator_loop --mode execute-safe` resolves `npm` via `shutil.which` for the
public-site build step. If Node.js is not installed, use `verify --skip-site` or
rely on CI Golden Gate for the site build.

Individual checks (same gates, decomposed):

```bash
pytest
pytest tests/golden
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
research --help
research run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
research export-public --limit 100
```

If a command is not available yet, report that clearly instead of pretending it passed.

## Required Report Location

Write implementation reports to:

```txt
agent_reports/
```

Report filenames should use:

```txt
YYYY-MM-DD_phase-<n>_ticket-<id>_<slug>.md
```

Example:

```txt
agent_reports/2026-06-11_phase-0_ticket-001_repo-scaffold-model-runtime.md
```

## Ticket Queue Location

Read the active queue from:

```txt
tickets/TICKET_QUEUE.md
```

Save new ticket JSON files to:

```txt
tickets/
```
