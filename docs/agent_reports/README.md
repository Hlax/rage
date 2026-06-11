# Agent Reports

This folder contains generated reports from Cursor/build agents.

Reports are historical artifacts. Do not rewrite old reports except to correct obvious metadata mistakes.

Each implementation run should create a new report using:

```txt
docs/agents/templates/BUILD_REPORT_TEMPLATE.md
```

Each handoff should use:

```txt
docs/agents/templates/NEXT_AGENT_HANDOFF_TEMPLATE.md
```

Recommended filename format:

```txt
YYYY-MM-DD_phase-<n>_ticket-<id>_<slug>.md
```

Example:

```txt
2026-06-11_phase-0_ticket-001_repo-scaffold-model-runtime.md
```

Reports should include:

- Summary.
- Changed files.
- Commands run.
- Test results.
- Acceptance criteria status.
- Safety audit status.
- Known failures.
- Recommended next ticket.
- Suggested next prompt.
