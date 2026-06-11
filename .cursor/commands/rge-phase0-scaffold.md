# RGE Phase 0 / 0.5 Scaffold

Read:

- `AGENTS.md`
- `docs/agents/01_RESEARCH_GRAPH_ENGINE_CANONICAL_CONTEXT_v1.md`
- `docs/agents/02_ARCHITECTURE.md`
- `docs/agents/03_MODEL_RUNTIME_SPEC.md`
- `docs/agents/04_CURSOR_BUILD_LOOP.md`
- `docs/agents/07_MVP_ACCEPTANCE_TESTS.md`
- `docs/agents/10_SAFETY_MODEL.md`
- `docs/agents/11_AGENT_OPERATING_PROTOCOL.md`

## Task

Implement only Phase 0 and Phase 0.5 scaffold.

## Scope

- Repo/package skeleton.
- CLI stub.
- SQLite schema placeholder.
- Module stubs.
- `rge/llm/` adapter layer stubs.
- Mock LLM mode.
- `.env.example`.
- Fixture directories.
- Public site placeholder.
- Golden test placeholders.
- Agent report template if missing.

## Do not

- Do not implement full claim extraction.
- Do not implement full LangGraph orchestration.
- Do not add live web crawling.
- Do not add public write routes.
- Do not let models write directly to accepted DB tables.
- Do not add model-controlled shell or Git access.
- Do not hardcode creativity fields into core schema.

## Before reporting success, run

```bash
pytest
research --help
cd apps/public-site && npm run build
```

If a command is unavailable in this phase, report it clearly.

## Required final report

End by writing an agent report to:

```txt
agent_reports/<date>_phase-0_ticket-001_scaffold.md
```

The report must include changed files, tests run, failures, known gaps, and recommended next ticket.
