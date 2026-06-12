---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 2 / ticket-038 / live-smoke-gating

## 1. Summary

Gated optional live Ollama smoke tests behind a `live_smoke` pytest marker excluded from default runs, added `research model-health` CLI (always exits 0 with JSON), and blocked live-mode `export-public` from writing `apps/public-site/public/data/` unless `--publish` is passed. Extended safety audit with `live_smoke_policy` evidence check. Golden tests and default pytest pass without Ollama (140 passed, 1 live smoke test deselected).

## 2. Ticket

- Ticket ID: ticket-038
- Ticket title: Gate live smoke tests behind env opt-in and add model-health command
- Branch: `phase-2/ticket-038-live-smoke-gating`
- Phase: 2
- Agent/model: Cursor builder agent
- Date: 2026-06-12
- Main tip before branch: `801c159`
- Audit gate satisfied by: `agent_reports/2026-06-12_pre-ticket-037_ollama-live-structured-tasks-readiness-audit.md` (2026-06-12; folded smoke/marker scope per roadmap)

## 3. Scope

### In Scope

- `live_smoke` pytest marker + default exclusion in `pyproject.toml`
- `tests/smoke/test_live_ollama_smoke.py` (env-gated, skipped without opt-in)
- `research model-health` CLI surfacing `OllamaModelClient.health_check()` without raising
- Live-mode export publish guard in `card_exporter.py` + `--publish` on `export-public`
- Safety auditor `live_smoke_policy` evidence check
- Runtime docs update (`12_RUNTIME_CONFIG.md`)
- Golden scaffold help test includes `model-health`

### Out of Scope / Non-goals

- Cloud providers, public export schema changes, removing `RGE_ALLOW_LIVE_LLM` gate, ticket-039+ implementation

## 4. Changed Files

| File | Change Summary |
|---|---|
| `pyproject.toml` | `live_smoke` marker; `addopts = "-m 'not live_smoke'"` |
| `rge/cli.py` | `model-health` subcommand; `export-public --publish`; publish passed to exporter |
| `rge/modules/card_exporter.py` | `resolve_export_targets`, publish guard, `publish_public` param |
| `rge/modules/safety_auditor.py` | `live_smoke_policy` check in full audit |
| `tests/smoke/test_live_ollama_smoke.py` | Optional live health smoke (marker + env skip) |
| `tests/unit/test_export_publish_gate.py` | Publish gate unit tests (no Ollama) |
| `tests/golden/test_00_scaffold.py` | Help text includes `model-health` |
| `docs/agents/12_RUNTIME_CONFIG.md` | Smoke marker, model-health, publish gate docs |
| `tickets/ticket-038.json` | Status done |
| `tickets/ticket-039.json` | Seeded follow-on (proposed) |
| `tickets/TICKET_QUEUE.md` | ticket-038 done; ticket-039 proposed |

## 5. Implementation Notes

- Default pytest collects 140 tests; 1 `live_smoke` test deselected via marker filter.
- `model-health` always exits 0; reports `reachable`, `model_available`, `live_llm_enabled`, `effective_llm_mode`.
- Live mode (`RGE_ALLOW_LIVE_LLM=1` + `RGE_LLM_MODE=ollama`): default export targets = `data/exports/` only; `--publish` or `fixture_mode=True` restores public-site writes.
- Explicit `--output-dir` pointing at public-site path blocked in live mode without `--publish`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| pytest / golden collect zero live smoke by default | PASS | 1 deselected; collect-only shows no live_smoke runs |
| `research model-health` reports without raising | PASS | Exit 0 with JSON (Ollama unreachable in agent env) |
| Live mode cannot write public-site without publish | PASS | Unit tests + `resolve_export_targets` guard |
| Safety audit extended with smoke-gate evidence | PASS | `live_smoke_policy` check passes |
| Golden + default pytest pass without Ollama | PASS | 129 golden + 140 total pytest |

## 7. Commands Run and Results

| Command | Result |
|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS — 129 passed |
| `RGE_LLM_MODE=mock python -m pytest` | PASS — 140 passed, 1 deselected |
| `python -m rge.modules.safety_auditor --audit full` | PASS |
| `python -m rge.cli model-health` | PASS — exit 0, reachable=false (no Ollama) |
| `python -m pytest -m live_smoke` | NOT RUN — requires local Ollama + opt-in |

## 8. Manual CLI Verification

- `model-health`: JSON report with `command`, `reachable`, `live_llm_enabled`, `effective_llm_mode`.
- `export-public --help`: shows `--publish` flag.

## 9. Spec Deviations

None.

## 10. Merge to Main

Placeholder — updated after merge.

## 11. Recommended Next Ticket

**ticket-039**: Validate improvement-ticket round-trip into the builder queue with review gate (Phase 2 roadmap).

## 12. Suggested Next Prompt

```
/rge-run-next-ticket
```

Implement only ticket-039 (improvement-ticket promotion round-trip with explicit review gate).
