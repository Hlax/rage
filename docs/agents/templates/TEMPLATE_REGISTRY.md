# TEMPLATE_REGISTRY.md

## Purpose

This file tracks current and historical agent report templates.

Agents must use the current template unless a ticket explicitly says otherwise.

## Current Templates

| Template ID | Current File | Current Version | Purpose |
|---|---|---:|---|
| `build_report` | `BUILD_REPORT_TEMPLATE.md` | `1.0.0` | End-of-ticket implementation report |
| `next_agent_handoff` | `NEXT_AGENT_HANDOFF_TEMPLATE.md` | `1.0.0` | Handoff from one agent to the next |

## Versioning Rules

Use semantic versioning:

```txt
PATCH: wording or formatting only
MINOR: new optional fields
MAJOR: changed required fields or workflow behavior
```

## Upgrade Rules

When upgrading a template:

1. Copy the old template into `docs/agents/templates/archive/`.
2. Update the current template file.
3. Update this registry.
4. Add a short changelog entry.
5. Do not rewrite old agent reports.

## Archive Path

Historical templates should live in:

```txt
docs/agents/templates/archive/
```

Recommended archive naming:

```txt
BUILD_REPORT_TEMPLATE.v1.0.0.md
NEXT_AGENT_HANDOFF_TEMPLATE.v1.0.0.md
```

## Changelog

### 1.0.0

Initial template set.
