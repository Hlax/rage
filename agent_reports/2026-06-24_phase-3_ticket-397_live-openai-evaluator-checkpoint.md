# Ticket-397 — Document live OpenAI evaluator canary runbook and checkpoint

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-397-live-openai-evaluator-runbook`  
**Ticket:** ticket-397  
**Main tip before branch:** `c263c09617f61b4e5e0772d745d77c5874d03d97`  
**Audit gate:** not required — docs-only ticket, `risk_level: low`; last principal audit `agent_reports/2026-06-23_principal-audit-post-ticket-389.md` (ticket-398 queued as next audit checkpoint)

## Summary

Documented the opt-in live OpenAI synthesis evaluator canary runbook across README
Operator Quickstart, `12_RUNTIME_CONFIG.md`, and `13_MODEL_ESCALATION_POLICY.md`.
Operators now have explicit env-gate tables, cost-cap requirements, scratch output
paths, pass/fail interpretation, bridge-to-instruction-draft commands, and maturity
framing (MVP-Engine mock vs operator live canary). No engine code changes.

## Scope

**In:** README runbook section, runtime config env precedence + evaluator artifact
table, escalation policy cloud/evaluator subsection, checkpoint agent report.

**Out:** New engine features, safety gate changes, CI live HTTP, public-site changes,
live canary execution in this run.

## Changed files

| File | Change |
|------|--------|
| `README.md` | *Live OpenAI synthesis evaluator canary runbook* — gates, caps, steps, pass/fail, bridge commands, operator_loop notes |
| `docs/agents/12_RUNTIME_CONFIG.md` | `.env` → `.env.local` → shell precedence; public-site must not load operator env; evaluator artifact paths and commands |
| `docs/agents/13_MODEL_ESCALATION_POLICY.md` | Mock-first cloud synthesis; evaluator canary as operator-only candidate output; output storage table |
| `tickets/ticket-397.json` | Status `done` |
| `tickets/ticket-398.json` | Proposed principal audit post 393–397 sequence |
| `tickets/TICKET_QUEUE.md` | ticket-397 done; ticket-398 proposed |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| README documents live canary command, env gates, cost caps, output path, pass criteria | **PASS** |
| Runtime docs: `.env.local` for operator secrets; shell overrides file; public-site must not read operator env | **PASS** |
| Escalation policy preserves mock-first; live synthesis is candidate output only | **PASS** |
| Agent report records mock test status, live canary (if any), `no_accepted_graph_writes`, maturity caveats | **PASS** |
| Docs omit API keys, raw prompts, private source text, public publish instructions | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `RGE_LLM_MODE=mock python -m pytest tests/golden -q` | **165 passed** |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | **pass** |
| `RGE_LLM_MODE=mock python -m rge.cli verify --skip-site` | **pass** |

## Optional live canary

**NOT RUN** in this implementation run (per non_goals and mock-first policy). Operator
live canary remains opt-in behind explicit gates and `--confirm`; documented command:

```powershell
python -m rge.cli synthesize `
  --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json `
  --provider openai --confirm --load-operator-env `
  --output-dir data/tmp/openai_synthesis_canary
```

## Safety boundaries and maturity caveats

- **`no_accepted_graph_writes`:** Live OpenAI synthesis and evaluator artifacts are
  candidate/review JSON only; Python validation and repositories own accepted graph
  writes. Docs state this explicitly.
- **MVP-Engine (mock):** CI, golden tests, `verify`, and `execute-safe` remain
  mock-first; injected-HTTP and fixture evaluator tests prove the spine without
  `OPENAI_API_KEY`.
- **Operator live canary:** Charges API usage; never CI, autocycle, or execute-safe.
- **Next checkpoint:** ticket-398 principal audit before further cloud-synthesis or
  operator-automation implementation.

## Manual CLI verification

Not required — documentation-only ticket. Operator plan field
`openai_synthesis_evaluator_status` and documented commands cross-reference tickets
394–396.

## Spec deviations

None.

## Merge to main

Merge commit: `b115cbadd7127ee6da7fc08f7c3fbbe12e9bfabd`.

## Recommended next ticket

**ticket-398** — Principal audit post OpenAI synthesis evaluator sequence (393–397).

## Suggested next prompt

```txt
Run principal audit for ticket-398, then /rge-run-next-ticket when audit is GO.
```
