---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-208
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: ticket-208 Live LLM Link on Staged Spine (Per-Step)

## Verdict: **GO** (narrow per-step proof — rank-1 live link only; mock extract upstream; orchestrator unchanged)

## Context

`execute_staged_fixture_mode_run` **always** forces `RGE_LLM_MODE=mock` and binds mock
fixtures for link/build/detect after ingest. Per-step live staged proofs (tickets
167–190, 193) use **real OpenAlex** through ingest, then **mock LLM** for pipeline steps.

ticket-204 proved **per-step live Ollama extract** via `--live-staged-fallthrough` and
`RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`. **Link** still auto-routes staged OpenAlex
sources to `staged_fetch_link_concepts.json` in `_default_link_fixture_for_source`
(`concept_linker.py`) when no `--fixture` is passed — detected by staged source **title**
(`human-ai co-creativity` + `songwriting`), not chunk text.

NM-4 manual live link exists via `--live-manual-link-fallthrough` on **manual_text**
sources absent from the fixture map — not for staged OpenAlex ingest.

The product gap: **live Ollama concept linking on a staged rank-1 source** after accepted
claims exist (typically from mock or live extract).

## Audit answers

### 1. What does “live LLM link on staged spine” mean?

| Interpretation | Scope | ticket-208 |
|----------------|-------|------------|
| Full orchestrator live LLM (all steps, both ranks) | Changes `execute_staged_fixture_mode_run` | **NO-GO** |
| Per-step live link after live ingest + extract (rank-1) | Opt-in pytest + CLI gate | **GO** |
| Live link on rank-2 second-candidate spine | Second-candidate fixture stability | **NO-GO** (defer) |
| Full live MVP (`execute_fixture_mode_run` + live LLM) | GT26 replacement | **NO-GO** |

### 2. What is already proven?

| Layer | LLM | Network |
|-------|-----|---------|
| Staged per-step through mock link (175) | mock fixture | live OpenAlex opt-in |
| Staged per-step live extract (204) | live Ollama extract | live OpenAlex opt-in |
| Staged orchestrator (193) | mock | live OpenAlex opt-in |
| NM-4 manual live link (128) | live Ollama | N/A (manual ingest) |
| Staged link with live Ollama | **not proven** | — |

### 3. Recommended implementation shape (ticket-208)

Mirror ticket-175 mock link spine, swapping link step to live Ollama:

1. Live discover → fetch → ingest-staged (existing network env)
2. **Mock** extract with `--fixture staged_fetch_extract_claims.json` (isolates link step; stable accepted claims)
3. **Live** `link-concepts` — no `--fixture`

Rationale: ticket-175 already proves the network chain through extract; live link proof
should not depend on live extract non-determinism in the same pytest. Operators may
optionally chain live extract (204) + live link in manual CLI runs; ticket-208 pytest
should use mock extract unless a follow-on ticket explicitly proves both live steps.

Requires **new bypass** for staged-fetch auto-mock on link:

- **Preferred:** `--live-staged-link-fallthrough` on `link-concepts` (parallel to
  `--live-manual-link-fallthrough`) gated by env + refuses default graph DB
- **Env gate:** `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1` (separate from mock gate
  `RGE_ALLOW_LIVE_STAGED_LINK=1`)

Eligibility: source must match `_is_staged_fetch_spine_source` and have ≥1 accepted claim.

Do **not** change default behavior when gate is unset.

### 4. Required env gates (operator proof)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM = "1"   # new staged-family gate
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
```

Mock link gate `RGE_ALLOW_LIVE_STAGED_LINK=1` is for ticket-175; **live LLM gate must be
separate**.

### 5. Mock vs live boundaries

| Surface | ticket-208 |
|---------|------------|
| OpenAlex discover/fetch/ingest | Real (operator opt-in) |
| extract-claims (pytest chain) | **Mock fixture** (stable upstream) |
| link-concepts | **Live Ollama** when gates set |
| build/detect/reconcile/report | **Out of scope** |
| `execute_staged_fixture_mode_run` | **Unchanged** — still forces mock |
| Default pytest / CI | Mock only; no Ollama |

### 6. Pytest markers and CI exclusion

- Mark new proof: `@pytest.mark.live_network` **and** `@pytest.mark.live_smoke`
- Add deselect assertion in `tests/unit/test_ci_golden_gate.py`
- Mocked gate tests (no Ollama) required for default pytest — mirror
  `test_live_staged_extract_live_llm_spine.py` pattern from ticket-204

### 7. DB and safety constraints

- Temp `--db` on `tmp_path` only; refuse default `creative_research.sqlite`
- No public export; no committed live-run artifacts
- Python validates all model JSON before accepted writes
- Assert **≥1 accepted link** (`claim_concepts` row); do not require exact fixture link counts
- Honest skip when Ollama unreachable
- `manual_text_arbitrary_live` calibration applies to manual sources only; staged link
  uses default Ollama link prompt unless a follow-on calibration ticket is scoped

### 8. Rollback plan

Remove env gate, CLI flag, test file, and ci deselect entry. Retain mock-only staged
proofs (175+) and live extract proof (204).

## Hardened scope (ticket-208 implementation)

### In

1. Staged live-link fallthrough gate (`concept_linker.py` + `cli.py`)
2. One opt-in pytest: live OpenAlex discover→fetch→ingest→mock extract→**live link** rank-1
3. Env gate `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1`
4. Mocked gate tests for default pytest
5. `test_ci_golden_gate.py` deselect for live test name
6. Agent report; optional docs ticket (209) for README/AGENTS

### Out

- Changing `execute_staged_fixture_mode_run` to use live LLM
- Live build/detect on staged spine
- Rank-2 live link
- Live extract + live link in single pytest (defer)
- CI Ollama
- Public export/site
- Schema migrations
- Default graph DB live writes

## Deferred — separate pre-ticket audits

| Milestone | Why deferred |
|-----------|--------------|
| Live LLM on full staged orchestrator | Multi-step live LLM + non-deterministic counts |
| Live link on rank-2 staged candidate | Second-candidate fixture stability |
| Live extract + live link combined pytest | Higher Ollama flake surface; prove link first |
| Full live MVP run | GT26 / export / theory scope |

## Safety

- Live Ollama proposes JSON only; Python validates and repositories write
- Fail closed without triple opt-in (staged live link gate + `RGE_ALLOW_LIVE_LLM` + ollama mode)
- Operator-only; not CI
- Temp DB path required
- Source must have accepted claims before link (unchanged validator gate)

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-208 per-step live staged link proof | **GO** |
| Live LLM in `execute_staged_fixture_mode_run` default path | **NO-GO** |
| Rank-2 or orchestrator-wide live link in one ticket | **NO-GO** |

## Operator opt-in (proposed)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_link_live_llm_spine.py -m "live_network and live_smoke" -q
```

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-208**.
