# Path Convention Recheck

**Date:** 2026-06-11  
**Scope:** Verify root `agent_reports/` and `tickets/` convention after migration from `docs/`.

---

## Folder Layout

| Path | Expected | Result |
|---|---|---|
| `agent_reports/` at repo root | Exists | **Pass** |
| `tickets/` at repo root | Exists | **Pass** |
| `docs/agent_reports/` | Absent | **Pass** |
| `docs/tickets/` | Absent | **Pass** |

Root contents verified:

- `agent_reports/README.md`
- `agent_reports/cursor_capability_check.md`
- `tickets/TICKET_QUEUE.md`

---

## Doc References to Root Paths

| File | `agent_reports/` | `tickets/` |
|---|---|---|
| `AGENTS.md` | Pass | Pass (after docs patch) |
| `.cursor/commands/*` | Pass | Pass (`rge-next-ticket.md`) |
| `.cursor/rules/rge-core.mdc` | Pass | N/A |
| `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` | Pass | Pass (after docs patch) |
| `tickets/TICKET_QUEUE.md` | Pass | N/A (is the queue) |
| `docs/agents/templates/NEXT_AGENT_HANDOFF_TEMPLATE.md` | Pass | Pass |

Runtime artifact paths in MVP specs (`tickets/improvement_ticket_latest.json`) remain under root `tickets/` and are consistent with the queue folder name.

---

## Stale `docs/agent_reports` / `docs/tickets` References

| Scope | Result |
|---|---|
| Repo files except `agent_reports/cursor_capability_check.md` | **Pass** — no stale paths |
| `agent_reports/cursor_capability_check.md` | Historical only — describes pre-migration state; left unchanged |

---

## Docs Patch Applied

1. `AGENTS.md` — workflow step 1 and new **Ticket Queue Location** section point to `tickets/TICKET_QUEUE.md` and `tickets/`.
2. `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` — **Ticket Rules** opens with explicit queue and ticket JSON paths.

---

## Verdict

**Pass.** Root path convention is in place; harness docs now explicitly name `tickets/` where they previously only named `agent_reports/`.
