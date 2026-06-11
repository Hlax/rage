---
template_id: next_agent_handoff
template_version: 1.0.0
status: current
---

# Next Agent Handoff: <Current Phase> / <Current Ticket>

## 1. Current State

Summarize the repo state in plain language.

## 2. Current Branch

```txt
<branch-name>
```

## 3. Last Completed Ticket

- Ticket ID:
- Ticket title:
- Report path:

## 4. What Works

- ...

## 5. What Does Not Work Yet

- ...

## 6. Commands Last Run

| Command | Result | Notes |
|---|---|---|
| `pytest` | PASS / FAIL / NOT RUN | ... |

## 7. Important Files

| File | Why It Matters |
|---|---|
| `path/to/file` | ... |

## 8. Known Constraints

- Follow `AGENTS.md`.
- Follow `docs/agents/11_AGENT_OPERATING_PROTOCOL.md`.
- Keep one ticket per branch.
- Do not broaden scope.
- Do not bypass safety rules.
- Use mock LLM mode for golden tests.

## 9. Recommended Next Ticket

```json
{
  "title": "",
  "problem": "",
  "evidence": [],
  "affected_modules": [],
  "expected_files": [],
  "acceptance_criteria": [],
  "test_plan": [],
  "non_goals": [],
  "risk_level": "",
  "rollback_plan": ""
}
```

## 10. Paste-Ready Prompt for Next Agent

```txt
You are continuing implementation of the Research Graph Engine.

Read:
- AGENTS.md
- docs/agents/11_AGENT_OPERATING_PROTOCOL.md
- latest report in agent_reports/
- the current ticket in tickets/

Implement only the next ticket described below.

<insert ticket>

Before reporting success:
- run the required test plan
- write a build report to agent_reports/
- recommend the next smallest ticket
```
