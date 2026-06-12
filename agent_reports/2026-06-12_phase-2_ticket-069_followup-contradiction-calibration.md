---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-069: Followup contradiction calibration

- Date: 2026-06-12
- Branch: `phase-2/ticket-069-followup-contradiction-calibration`
- Baseline HEAD: `b43e965` (ticket-068 on main)
- Implementation SHA: `c4f1690`
- Risk level: low-medium

## Summary

Closed the remaining live mini-run suite gap for
`creativity_ai_diversity_followup_short.txt`. Root cause was hybrid overlay
handoff: the followup fixture extracts an opposing-only claim (`reduced semantic
diversity`) but overlay logic treated it as the qualifying source claim, causing
validator `same_claim_pair` rejection. Fixed by opposing-only overlay path plus
contradiction prompt claim-id guidance. Live suite now **4/4** floors.

## Root cause

| Layer | Finding |
| ----- | ------- |
| Validator | Correct — rejected identical qualifying/opposing claim ids |
| Model | Partial — omitted claim ids; triples otherwise valid |
| Handoff | **Primary** — opposing-only input overlaid as qualifying source |
| Fixture | By design — replication text is opposing-only; bundle supplies qualifying claim |

Artifact before fix: `probe_mini_run_2026-06-12T220753Z.json` — contradiction
0/1, diagnostic `qualifying_claim_id and opposing_claim_id must differ`.

## Changes

| File | Change |
| ---- | ------ |
| `rge/modules/live_probe.py` | Opposing-only hybrid overlay; preserve bundle qualifying source |
| `rge/llm/ollama_client.py` | Explicit qualifying/opposing claim-id rules in contradiction prompt |
| `tests/unit/test_live_probe_mini_run_cli.py` | Handoff + validation unit tests |
| `tests/unit/test_ollama_contradiction_prompt.py` | Prompt assertion updates |
| `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` | Followup fixture note |
| `tickets/ticket-069.json`, `TICKET_QUEUE.md` | Done status |

## Live suite before / after

| Fixture | Before (ticket-067) | After (ticket-069) |
| ------- | ------------------- | ------------------ |
| `live_probe_claim_calibration_short.txt` | pass | pass |
| `live_probe_diversity_calibration_short.txt` | pass | pass |
| `creativity_ai_diversity_followup_short.txt` | **fail** (contradiction 0/1) | **pass** (1/0) |
| `live_probe_contradiction_calibration_short.txt` | pass | pass |

| Suite metric | Before | After |
| ------------ | ------ | ----- |
| `fixtures_passed` | 3 | **4** |
| `fixtures_failed` | 1 | **0** |
| `status` | partial | **ok** |

Before artifact: `probe_mini_run_suite_2026-06-12T220829Z.json`
After artifact: `probe_mini_run_suite_2026-06-12T231236Z.json`

**4/4 achieved** on local Ollama (`qwen2.5:7b`).

## Mock verification

| Command | Result |
| ------- | ------ |
| `pytest tests/unit/test_ollama_contradiction_prompt.py tests/unit/test_live_probe_mini_run_cli.py -q` | **11 passed** |
| `pytest tests/golden -q` | **140 passed** |
| `pytest -q` | **286 passed**, 6 deselected |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| `python -m rge.modules.principal_audit_gate --next-ticket ticket-070` | **satisfied** |

Public site / export **not touched** — no build re-run required.

## Safety confirmations

- Validators and floors unchanged
- `db_writes: false` on suite and mini-run reports
- Scratch DB remains operator-only (`probe-persist-reviewed-report --confirm-review`)
- No public export changes
- ticket-059 OpenAI remains deferred

## Remaining risks

- Live suite still depends on local Ollama + Qwen; model variance may reintroduce flakiness on other stages
- Opposing-only overlay heuristic keys on claim text fragments; novel phrasing may need future calibration
- Principal audit cadence: 2 done tickets since post-ticket-067 checkpoint (068, 069); threshold 3 before next medium-risk ticket

## Merge

- Merge commit SHA: `c4f1690` (fast-forward to main)
- Golden Gate run: _(pending CI on push)_

## Recommended next move

**ticket-070 — Scratch DB run summary** (deterministic Python, read-only over scratch rows, no model authority) once operator approves seeding.
