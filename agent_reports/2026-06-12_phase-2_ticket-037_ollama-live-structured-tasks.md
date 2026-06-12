---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 2 / ticket-037 / ollama-live-structured-tasks

## 1. Summary

Implemented Ollama structured tasks behind an explicit `RGE_ALLOW_LIVE_LLM=1` opt-in gate. Added `rge/llm/mode.py` effective-mode resolver, replaced hard-forced mock env hacks in four pipeline modules, implemented live `extract_claims` / `link_concepts` / `draft_relationships` / `detect_contradictions` in `OllamaModelClient` with prompt + JSON parse + schema validation, added 8 canned unit tests (mocked HTTP), extended safety audit live-LLM evidence check, and updated runtime docs. Golden and fixture runs remain mock-only. All 137 tests pass; safety audit passes.

## 2. Ticket

- Ticket ID: ticket-037
- Ticket title: Implement Ollama structured tasks behind explicit live-mode opt-in
- Branch: `phase-2/ticket-037-ollama-live-structured-tasks`
- Phase: 2
- Agent/model: Cursor builder agent
- Date: 2026-06-12
- Main tip before branch: `5ac7199`
- Audit gate satisfied by: `agent_reports/2026-06-12_pre-ticket-037_ollama-live-structured-tasks-readiness-audit.md` (2026-06-12, committed `5ac7199`)

## 3. Scope

### In Scope

- `RGE_ALLOW_LIVE_LLM` config + fail-closed parsing
- `effective_llm_mode()` / `live_llm_enabled()` in `rge/llm/mode.py`
- Ollama structured-call helper + four pipeline task implementations
- Pipeline module refactor (no env hacks)
- Extractor metadata records actual provider/model
- Unit tests with mocked HTTP
- GT00 opt-in gate tests
- Safety auditor `live_llm_policy` evidence check
- Docs: `12_RUNTIME_CONFIG.md`, `.env.example`, `.env.smoke.example`

### Out of Scope / Non-goals

- Cloud providers, public export/site changes, LangGraph, live discovery, pytest `live_smoke` marker, `model-health` CLI (ticket-038), ticket-038+ implementation

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/config.py` | Added `allow_live_llm` / `RGE_ALLOW_LIVE_LLM` with fail-closed parsing |
| `rge/llm/mode.py` | New effective-mode resolver |
| `rge/llm/registry.py` | Optional `mode` override for pipeline selection |
| `rge/llm/ollama_client.py` | Structured tasks via `/api/generate` + JSON validation; `OllamaStructuredCallError` |
| `rge/modules/claim_extractor.py` | Effective mode; dynamic extractor metadata |
| `rge/modules/concept_linker.py` | Effective mode; mock fixture kwarg only for mock client |
| `rge/modules/relationship_builder.py` | Effective mode |
| `rge/modules/contradiction_detector.py` | Effective mode |
| `rge/modules/safety_auditor.py` | `live_llm_policy` evidence check in full audit |
| `tests/unit/test_ollama_structured_tasks.py` | 8 canned unit tests (mocked HTTP) |
| `tests/golden/test_00_model_runtime.py` | Opt-in gate tests; non-pipeline tasks still unimplemented |
| `docs/agents/12_RUNTIME_CONFIG.md` | Document opt-in contract and updated pipeline behavior |
| `.env.example` / `.env.smoke.example` | `RGE_ALLOW_LIVE_LLM` placeholders |
| `tickets/ticket-037.json` | Status done |
| `tickets/ticket-038.json` | Seeded follow-on (proposed) |
| `tickets/TICKET_QUEUE.md` | ticket-037 done; ticket-038 proposed |

## 5. Implementation Notes

- Effective mode: mock unless `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`.
- `execute_fixture_mode_run()` unchanged — still forces mock for GT26 determinism.
- Live unreachable Ollama raises `OllamaStructuredCallError`; no silent mock fallback when opt-in is set.
- Claim extraction prompts include the untrusted-source delimiter from `10_SAFETY_MODEL.md`.
- `draft_run_summary` / `draft_ticket` remain `OllamaNotAvailableInPhase0` (not pipeline-critical).

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| RGE_ALLOW_LIVE_LLM in config + docs | PASS | `.env.example`, `.env.smoke.example`, doc 12 |
| Shared effective-mode resolver in four pipeline modules | PASS | `rge/llm/mode.py` |
| Fixture/golden remain mock-only | PASS | CLI fixture path unchanged; golden autouse mock |
| Ollama structured tasks for four pipeline methods | PASS | Implemented with validation chain |
| Without opt-in → mock behavior | PASS | Unit + GT00 tests |
| With opt-in + unreachable Ollama → clear error | PASS | Unit test |
| Live extract-claims with running Ollama | NOT RUN | Ollama not verified in agent environment; manual operator step documented below |
| No direct model writes to accepted tables | PASS | Validators + repos unchanged |
| Canned unit tests (mocked HTTP) | PASS | 8 tests |
| Golden tests pass without Ollama | PASS | 129/129 |
| Full pytest + safety audit | PASS | 137/137; audit pass |
| No cloud providers | PASS | Zero additions |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/unit/test_ollama_structured_tasks.py` | PASS | 8/8 |
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_00_model_runtime.py` | PASS | 9/9 |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS | 129 passed |
| `RGE_LLM_MODE=mock python -m pytest` | PASS | 137 passed |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS | exit 0 |
| Mock `extract-claims` on temp DB | PASS | 2 accepted, 0 rejected |

## 8. Manual CLI Verification

**Mock path (verified):**

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli ingest fixtures/sources/creativity_ai_diversity_short.txt --domain creativity --db <temp.sqlite>
python -m rge.cli extract-claims --source <source_id> --db <temp.sqlite>
# → status: completed, accepted_count: 2
```

**Live Ollama path (operator manual — not run in this agent session):**

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
# Ensure Ollama is running with qwen2.5:7b pulled
python -m rge.cli ingest fixtures/sources/creativity_ai_diversity_short.txt --domain creativity --db <temp.sqlite>
python -m rge.cli extract-claims --source <source_id> --db <temp.sqlite>
```

## 9. Safety Audit

Full safety audit passes including new `live_llm_policy` evidence check. No public export or route changes.

## 10. Merge to Main

- Merge commit: `4e05271`
- Branch: `phase-2/ticket-037-ollama-live-structured-tasks` merged to `main`; post-merge pytest: 137 passed.

## 11. Recommended Next Ticket

**ticket-038**: Gate live smoke tests behind env opt-in and add model-health command (Phase 2 roadmap; pre-audit folded into ticket-037's audit scope for gating/marker work).

## 12. Suggested Next Prompt

```txt
/rge-run-next-ticket
```

Implement only ticket-038 (live smoke gating + model-health CLI).
