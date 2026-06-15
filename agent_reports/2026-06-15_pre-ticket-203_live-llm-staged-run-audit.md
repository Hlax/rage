---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-204
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: ticket-204 Live LLM Extract on Staged Spine (Per-Step)

## Verdict: **GO** (narrow per-step proof — rank-1 live extract only; orchestrator unchanged)

## Context

`execute_staged_fixture_mode_run` **always** forces `RGE_LLM_MODE=mock` (lines 507–508)
and uses mock fixtures for extract/link/build/detect (explicit `--fixture` bindings for
rank-2; auto-mock or explicit fixtures for rank-1). Per-step live staged proofs
(tickets 167–190, 193) combine **real OpenAlex** with **mock LLM** after ingest.

NM-1 live validated write exists for **evidence DB** via `extract-claims-live` /
`--live-manual-fallthrough` on **manual_text** sources absent from the fixture map — not
for OpenAlex staged ingest chunks. Staged fetch chunks auto-route to
`staged_fetch_extract_claims.json` in `_default_fixture_for_chunk` when no `--fixture`
is passed (`claim_extractor.py`).

The product gap: **live Ollama extract on a live-ingested staged OpenAlex source** within
the Phase 3 spine boundary.

## Audit answers

### 1. What does “live LLM on staged run” mean?

| Interpretation | Scope | ticket-204 |
|----------------|-------|------------|
| Full orchestrator live LLM (all steps, both ranks) | Changes `execute_staged_fixture_mode_run` | **NO-GO** |
| Per-step live extract after live ingest (rank-1) | New opt-in pytest + minimal CLI/validator gate | **GO** |
| Full live MVP (`execute_fixture_mode_run` + live LLM) | GT26 replacement | **NO-GO** |

### 2. What is already proven?

| Layer | LLM | Network |
|-------|-----|---------|
| Staged per-step through mock extract (172) | mock fixture | live OpenAlex opt-in |
| Staged orchestrator (193) | mock | live OpenAlex opt-in |
| NM-1 extract-claims-live (evidence DB) | live Ollama | N/A (manual ingest) |
| Staged extract with live Ollama | **not proven** | — |

### 3. Recommended first implementation shape (ticket-204)

Mirror ticket-172 pattern (per-step chained CLI on temp DB):

1. Live discover → fetch → ingest-staged (existing env: `RGE_ALLOW_SOURCE_NETWORK`, `OPENALEX_MAILTO`)
2. **Live** `extract-claims` on rank-1 staged source — **no** `--fixture`

Requires **new bypass** for staged-fetch auto-mock: staged chunks currently resolve to
`staged_fetch_extract_claims.json` without a fixture arg. Options (pick one in implementation):

- **Preferred:** new CLI flag `--live-staged-fallthrough` on `extract-claims` (parallel to
  `--live-manual-fallthrough`) gated by env + refuses default graph DB
- **Alternative:** env-only `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1` checked inside
  `claim_extractor` when resolving fixture for staged-fetch chunks

Do **not** change default behavior when gate is unset.

### 4. Required env gates (all must be set for operator proof)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM = "1"   # new staged-family gate
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
```

Optional existing gate for discover chain context: tests may reuse
`RGE_ALLOW_LIVE_STAGED_EXTRACT=1` for network chain naming consistency, but **live LLM
gate must be separate** from mock-fixture extract gate (172).

### 5. Mock vs live boundaries

| Surface | ticket-204 |
|---------|------------|
| OpenAlex discover/fetch/ingest | Real (operator opt-in) |
| extract-claims | **Live Ollama** when gates set |
| link/build/detect/reconcile/report | **Out of scope** — not in this ticket |
| `execute_staged_fixture_mode_run` | **Unchanged** — still forces mock |
| Default pytest / CI | Mock only; no Ollama |

### 6. Pytest markers and CI exclusion

- Mark new proof: `@pytest.mark.live_network` **and** `@pytest.mark.live_smoke`
- `pyproject.toml` already excludes both by default (`not live_smoke and not live_network`)
- Add deselect assertion in `tests/unit/test_ci_golden_gate.py` for new test name
- **No** CI workflow changes; **no** golden test changes requiring Ollama

### 7. DB and safety constraints

- Temp `--db` on `tmp_path` only; refuse default `creative_research.sqlite` for live-staged-fallthrough (mirror evidence DB guard pattern)
- No public export; no committed artifacts from live run
- Python validates all model JSON before accepted writes (unchanged)
- Assert **≥1 accepted claim** with live extract; do not require exact fixture claim counts
- Honest skip when Ollama unreachable (pytest skip, not fail CI)

### 8. Rollback plan

Remove new env gate, CLI flag (if added), test file, and ci deselect entry. Retain all
mock-only staged proofs (167–193, 201).

## Hardened scope (ticket-204 implementation)

### In

1. Staged live-extract fallthrough gate (CLI flag and/or env + `claim_extractor` bypass for staged-fetch auto-mock)
2. One opt-in pytest: live OpenAlex discover→fetch→ingest→**live extract** on rank-1
3. Env gate `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`
4. `test_ci_golden_gate.py` deselect for new test
5. Agent report; optional follow-on docs ticket (205) for README/AGENTS operator command

### Out

- Changing `execute_staged_fixture_mode_run` to use live LLM
- Live link/build/detect on staged spine
- Full orchestrator live LLM proof
- CI Ollama
- Public export/site
- Schema migrations
- Default graph DB live writes

## Deferred — separate pre-ticket audits

| Milestone | Why deferred |
|-----------|--------------|
| Live LLM on full staged orchestrator | Multi-step live LLM + non-deterministic counts |
| Live LLM on rank-2 staged candidate | Second-candidate fixture stability |
| Full live MVP run | GT26 / export / theory scope |

## Safety

- Live Ollama proposes JSON only; Python validates and repositories write
- Fail closed without triple opt-in (staged live LLM gate + `RGE_ALLOW_LIVE_LLM` + ollama mode)
- Operator-only; not CI
- Temp DB path required

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-204 per-step live staged extract proof | **GO** |
| Live LLM in `execute_staged_fixture_mode_run` default path | **NO-GO** |
| Full staged spine live LLM in one ticket | **NO-GO** |

## Operator opt-in (proposed)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_extract_live_llm_spine.py -m "live_network and live_smoke" -q
```

(Test module name proposed; implementation may adjust.)

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-204**.
