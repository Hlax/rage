---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-037 Ollama Live Structured-Tasks Readiness Audit

- Audit type: focused pre-ticket audit — live Ollama structured-task adapter and explicit opt-in gate
- Date: 2026-06-12
- Agent/model: Cursor audit agent
- Scope: read-only audit of model runtime, pipeline forced-mock posture, safety boundaries, and test harness before seeding ticket-037. No runtime, schema, or export changes were made.

## Summary

Ticket-037 (Ollama structured tasks behind explicit live-mode opt-in) is **safe to begin** with the hardened scope below. The adapter boundary is real (`ModelClient`, registry, mock client, Pydantic schemas, deterministic validators, repository writes), but live structured inference is intentionally blocked today: four pipeline modules hard-force `RGE_LLM_MODE=mock`, fixture orchestration also forces mock, and `OllamaModelClient` structured methods raise `OllamaNotAvailableInPhase0`. Only `health_check()` may touch the network. Zero cloud-provider code exists. All 127 golden tests pass; full safety audit passes. This report satisfies the audit-gate requirement for ticket-037.

**Recommendation: proceed with ticket-037 as an explicit opt-in Ollama structured-task ticket.**

## Repo / Main Status

| Check | Result |
|---|---|
| Branch | `main`, aligned with `origin/main` (`## main...origin/main`) |
| Working tree | clean |
| Main tip | `ab9e22a` (docs: record main merge hash for ticket-036) |
| ticket-036 merge commit | `2547632` — present in `git log` |
| Unmerged branches | `git branch --all --no-merged main` → none |
| ticket-037 JSON | does not exist yet (this pass seeds it) |

## Ticket / Queue Status

| Ticket | Status | Verified |
|---|---|---|
| ticket-033 (principal audit) | done | Phase 2 GO; ticket-037 flagged medium-high risk, audit-gated |
| ticket-034 (artifact hygiene) | done | fixture runs repo-clean |
| ticket-035 (README refresh) | done | operator docs current |
| ticket-036 (public-site polish) | done | merged `2547632`; no runtime changes |
| ticket-037 | **not seeded** | correct next roadmap item per sequence 034→035→036→037 |

ticket-038+ intentionally not seeded in this pass. ticket-038 (live smoke gating, `model-health` CLI, pytest marker) should follow ticket-037 and may fold additional safety-audit tightening.

## Model Runtime Current State

### What exists and is verified

| Component | State |
|---|---|
| `rge/llm/base.py` | `ModelClient` ABC with 6 structured tasks; returns typed candidates only |
| `rge/llm/registry.py` | Fail-closed selection: `mock` → `MockModelClient`, `ollama` → `OllamaModelClient`, unknown → `LlmModeError`; no silent fallback |
| `rge/llm/mock_client.py` | Deterministic fixture loader; all structured tasks implemented |
| `rge/llm/ollama_client.py` | `health_check()` live; all structured tasks raise `OllamaNotAvailableInPhase0` |
| `rge/llm/schemas.py` | Versioned Pydantic candidate batches; `validate_schema_version` fails closed |
| `rge/config.py` | Reads 9 env vars; valid modes `mock`/`ollama` only |
| `tests/golden/test_00_model_runtime.py` | Registry, deterministic mock, schema mismatch, ollama stub honesty, no DB imports in llm package |
| Pipeline validators | `claim_validator.py` etc. gate all accepted writes |

### What is not implemented

- Ollama prompt templates and `/api/generate` (or chat) structured-call path
- `RGE_ALLOW_LIVE_LLM` (or equivalent) opt-in gate
- Central effective-mode resolver replacing per-module env hacks
- `research model-health` CLI (ticket-038)
- `live_smoke` pytest marker / scratch export defaults (ticket-038)
- Cloud providers (OpenAI, OpenRouter, Anthropic, Gemini, Vertex) — **zero code references**

## Forced-Mock Findings

Mock mode is **hard-forced** in five places before `get_model_client()`:

| Location | Mechanism | Must change in ticket-037? |
|---|---|---|
| `rge/modules/claim_extractor.py` (`extract_candidate_claims`) | `os.environ["RGE_LLM_MODE"] = "mock"` | **Yes** — replace with effective-mode resolver |
| `rge/modules/concept_linker.py` (`link_claim_concepts`) | same | **Yes** |
| `rge/modules/relationship_builder.py` (`draft_relationships_for_source`) | same | **Yes** |
| `rge/modules/contradiction_detector.py` (`detect_contradictions_for_source`) | same | **Yes** |
| `rge/cli.py` (`execute_fixture_mode_run`) | forces mock for entire fixture orchestration | **No** — must stay mock forever for GT26 determinism |

Additionally, **every golden test module** sets `RGE_LLM_MODE=mock` via autouse fixtures or monkeypatch (17 modules under `tests/golden/`). This is the primary guarantee that `pytest tests/golden` never requires Ollama.

**Config default nuance:** `rge/config.py` `_DEFAULTS` still default `RGE_LLM_MODE` to `"ollama"`, but committed `.env.example` defaults to `mock` (ticket-035). Pipeline forced-mock makes the code default harmless for golden/fixture runs today.

## Live-Mode Safety Boundaries

### Audit question answers

| Question | Answer |
|---|---|
| Is ticket-037 safe to begin? | **Yes**, with explicit opt-in, canned unit tests, fixture orchestration staying mock, and no cloud work |
| Where is mock forced? | Four pipeline modules + `execute_fixture_mode_run`; golden autouse fixtures |
| Explicit live opt-in? | **`RGE_ALLOW_LIVE_LLM=1`** required in addition to `RGE_LLM_MODE=ollama` (principal audit + pre-ticket-028 alignment) |
| Fail closed without opt-in? | Effective mode resolves to **mock** for pipeline calls (behavior identical to today); structured Ollama methods must **not** run. Optionally log/raise if caller sets `ollama` without opt-in on a non-fixture CLI path — but golden/fixture behavior must remain mock-only |
| Fail closed with opt-in but no Ollama? | Raise a clear runtime error (network unreachable, model missing); **no silent fallback to mock** |
| First structured task path? | **`extract_claims` / claim extraction** — foundational (GT2), named in roadmap acceptance, feeds all downstream validators |
| One task or all mock tasks? | Implement **shared Ollama structured-call helper + all four pipeline tasks** (`extract_claims`, `link_concepts`, `draft_relationships`, `detect_contradictions`) in `ollama_client.py`; manual live verification minimum = `research extract-claims`. Defer `draft_run_summary` / `draft_ticket` unless trivial via same helper (not used by forced-mock pipeline modules today) |
| Canned tests without Ollama? | New unit tests mocking `urllib.request.urlopen` (or injectable transport): valid JSON → Pydantic batch; malformed JSON; schema_version mismatch; invalid batch shape; prompt includes untrusted-source delimiter; effective-mode resolver without opt-in → mock |
| Golden tests never require Ollama? | Keep golden autouse mock; keep fixture orchestration mock; unit tests mock HTTP; update GT00 to assert opt-in gate instead of `OllamaNotAvailableInPhase0` once implemented |
| Model output never writes to accepted tables? | **Already enforced:** clients return candidates only; `claim_extractor` → `validate_candidate_claims` → `ClaimRepository.insert_accepted/rejected`. Ticket-037 must record `extractor_provider`/`extractor_model` from client metadata, not hardcoded `"mock"` |
| Safety audit extension needed? | **Light extension recommended in ticket-037:** existence check for live opt-in helper + unit test module (same pattern as GT24/GT25 evidence checks). Full behavioral live-mode gating belongs in ticket-038 |
| Env vars to document? | See table below |

### Proposed effective-mode contract

```txt
effective_mode = mock
  unless RGE_LLM_MODE=ollama AND RGE_ALLOW_LIVE_LLM=1
    then effective_mode = ollama

execute_fixture_mode_run() and pytest tests/golden → always mock regardless
```

Implement via a small shared helper (e.g. `rge/llm/mode.py`: `effective_llm_mode(config) -> str` and `live_llm_enabled(config) -> bool`) used by the four pipeline modules instead of inline `os.environ[...] = "mock"`.

### Env vars for ticket-037 documentation

| Variable | Role | Ticket-037 action |
|---|---|---|
| `RGE_LLM_MODE` | `mock` or `ollama` | unchanged; read by registry |
| **`RGE_ALLOW_LIVE_LLM`** | **`1` enables live structured calls** | **add to `config.py`, `.env.example`, `.env.smoke.example`, `12_RUNTIME_CONFIG.md`** |
| `RGE_TEST_LLM_MODE` | documented test default | unchanged (`mock`) |
| `OLLAMA_BASE_URL` | local Ollama endpoint | unchanged |
| `RGE_LOCAL_LLM` | model tag (e.g. `qwen2.5:7b`) | unchanged |
| `RGE_LLM_TIMEOUT_SECONDS` | request timeout | unchanged |
| `RGE_LLM_TEMPERATURE` | sampling temperature | unchanged |
| `RGE_LLM_SCHEMA_VERSION` | candidate schema version | unchanged |

Do **not** add cloud API keys or provider vars in ticket-037.

### Write-path safety (must not regress)

```txt
OllamaModelClient.extract_claims(...)
  → CandidateClaimBatch_v0_1 (Pydantic)
  → claim_validator.validate_candidate_claims(...)
  → ClaimRepository.insert_accepted / insert_rejected (Python only)
```

No `rge.db` imports in `rge/llm/*` (GT00 already asserts this). No new public export paths. No change to `public_export_policy.py`.

## Proposed Ticket-037 Scope

### In scope

1. **`RGE_ALLOW_LIVE_LLM` opt-in** in `rge/config.py` with fail-closed parsing (`1`/`true`/`yes` only).
2. **Shared effective-mode resolver**; replace forced-mock env hacks in four pipeline modules.
3. **`OllamaModelClient` structured implementation** for the four pipeline tasks using prompt + JSON parse + `validate_schema_version` + Pydantic validation + `ModelCallMetadata`.
4. **Prompt templates** (version `0.1.0`, aligned with mock metadata) with explicit untrusted-source delimiters per `10_SAFETY_MODEL.md`.
5. **Unit tests** with mocked HTTP (no Ollama dependency) covering parse/validation/opt-in gate.
6. **Update GT00** (`test_ollama_structured_tasks_fail_honestly_in_phase_0`) to reflect post-037 opt-in behavior.
7. **Docs:** `12_RUNTIME_CONFIG.md`, `.env.smoke.example`, README live-mode section pointer.
8. **Optional light safety-audit evidence check** for opt-in helper + unit tests.
9. **Manual live smoke** documented in agent report only (not in default pytest).

### Out of scope (ticket-037 non-goals)

- Cloud providers (OpenAI, OpenRouter, Anthropic, Gemini, Vertex)
- Public export / public-site changes
- LangGraph integration
- `research run` without `--fixture-mode` (live discovery)
- `live_smoke` pytest marker, CI changes, `model-health` CLI (ticket-038)
- Removing mock forcing from `execute_fixture_mode_run`
- ticket-038+

### Risk controls

| Risk | Mitigation |
|---|---|
| Live nondeterminism in golden tests | Fixture orchestration + golden autouse mock unchanged |
| Silent mock fallback hiding live failures | With opt-in set, unreachable Ollama raises; without opt-in, mock (same as today) |
| Model writes accepted graph directly | Clients return candidates only; validators + repos unchanged |
| Prompt injection via live model | Existing deterministic rejection path unchanged; prompts must delimit untrusted source text |

## Blockers

**None** that prevent seeding and starting ticket-037.

Caveats for the implementation agent:

1. **No prompt templates exist yet** — ticket-037 must author them; use fixture JSON shapes as the canonical output examples.
2. **`extractor_provider`/`extractor_model` hardcoded to `"mock"`** in `claim_extractor.py` persistence — must be fixed to reflect actual client when live.
3. **`config.py` default `RGE_LLM_MODE=ollama`** vs `.env.example=mock` — document clearly; do not change golden behavior.
4. **Safety audit live checks are existence-only today** — acceptable for ticket-037 if unit tests cover behavior; ticket-038 can add marker isolation.

## Tests Run (exact results)

| Command | Result |
|---|---|
| `git status --short --branch` | `## main...origin/main` — clean |
| `git log --oneline --decorate -30` | tip `ab9e22a`; merges `2547632` (036), `27fdae7` (035), `2e1dd9d` (034) present |
| `git branch --all --no-merged main` | empty |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | **127 passed** in 35.90s |
| `RGE_LLM_MODE=mock python -m pytest` | **127 passed** in 35.75s |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | `status: pass`, `blocked_reasons: []`, exit 0 |

## Recommendation

Recommendation: proceed with ticket-037 as an explicit opt-in Ollama structured-task ticket.
