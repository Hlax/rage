---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-212
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: ticket-212 Live Staged Build on Staged Spine (Per-Step)

## Verdict: **GO** (narrow per-step rank-1 live build proof; mock extract + mock link upstream; orchestrator unchanged)

## Context

`execute_staged_fixture_mode_run` **always** forces `RGE_LLM_MODE=mock` and binds mock
fixtures for link/build/detect after ingest. Per-step live staged proofs (tickets
167–190, 193) use **real OpenAlex** through ingest, then **mock LLM** for pipeline steps
unless an explicit live-LLM fallthrough gate is set.

ticket-204 proved **per-step live Ollama extract** via `--live-staged-fallthrough` and
`RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`. ticket-208 proved **per-step live Ollama
link** via `--live-staged-link-fallthrough` and `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1`.

**Build** still auto-routes staged OpenAlex sources to `staged_fetch_build_relationships.json`
in `_default_relationship_fixture_for_source` (`relationship_builder.py`) when no
`--fixture` is passed — detected by staged source **title** (`human-ai co-creativity` +
`songwriting`), not chunk text.

ticket-178 proved **mock-fixture build** after live OpenAlex ingest (`RGE_ALLOW_LIVE_STAGED_BUILD=1`).
That gate is separate from live Ollama build.

The product gap: **live Ollama relationship building on a staged rank-1 source** after
accepted claims and concept links exist (typically from mock upstream steps).

---

## Audit answers

### 1. What does “live staged build” mean in this repo?

| Interpretation | Scope | ticket-212 |
|----------------|-------|------------|
| Full orchestrator live LLM (all steps, both ranks) | Changes `execute_staged_fixture_mode_run` | **NO-GO** |
| Per-step live build after live ingest + mock extract + mock link (rank-1) | Opt-in pytest + CLI gate | **GO** |
| Live build on rank-2 second-candidate spine | Second-candidate stability | **NO-GO** (defer) |
| Full live MVP (`execute_fixture_mode_run` + live LLM) | GT26 replacement | **NO-GO** |

“Live staged build” means: operator opt-in live Ollama **relationship drafting** on a
staged OpenAlex-ingested rank-1 source, bypassing the staged-fetch auto-mock fixture
path, with Python validation before persistence.

### 2. Which stage is currently live and which remains mock?

| Stage | Default pytest / orchestrator | Per-step operator opt-in |
|-------|------------------------------|--------------------------|
| discover → fetch → ingest-staged | mock (unit) / live (opt-in `live_network`) | live OpenAlex |
| extract-claims | mock fixture | live Ollama (204) or mock fixture |
| link-concepts | mock fixture | live Ollama (208) or mock fixture |
| build-relationships | mock fixture | **not proven** — ticket-212 target |
| detect-contradictions | mock fixture | **mock only** |
| reconcile-scores / report | mock | **mock only** |
| `execute_staged_fixture_mode_run` | **mock LLM forced** | unchanged |

### 3. What did ticket-204 add for live extract?

- CLI flag `--live-staged-fallthrough` on `extract-claims`
- Env gate `RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1` (separate from mock
  `RGE_ALLOW_LIVE_STAGED_EXTRACT=1`)
- `claim_extractor.py` / `live_extraction_write.py`: bypass staged-fetch auto-mock when
  gate set; refuse default graph DB; require staged title heuristic
- Opt-in pytest `test_live_staged_extract_live_llm_spine.py` (`live_network` + `live_smoke`)
- Mocked gate tests + CI deselect assertion

### 4. What did ticket-208 add for live link?

- CLI flag `--live-staged-link-fallthrough` on `link-concepts`
- Env gate `RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1` (separate from mock
  `RGE_ALLOW_LIVE_STAGED_LINK=1`)
- `concept_linker.py`: `link_concepts_staged_live_fallthrough`; bypass staged-fetch
  auto-mock; require accepted claims; refuse `--fixture` combination
- Opt-in pytest chain: discover → ingest → **mock extract** → **live link**
- Mocked gate tests + CI deselect assertion

### 5. What module/command currently builds relationships?

- **CLI:** `python -m rge.cli build-relationships --source <id> [--fixture <name>] [--db <path>]`
- **Module:** `rge/modules/relationship_builder.py`
  - `build_relationships_for_source()` — main persistence path
  - `propose_relationship_drafts()` / `draft_relationships_for_source()` — model proposals
  - `validate_relationship_candidates()` — Python validation before write
  - `build_relationships_manual_live_fallthrough()` — NM-4 manual_text live path only

Tables: `relationships`, `relationship_evidence` via `RelationshipRepository`,
`RelationshipEvidenceRepository`.

### 6. How does staged build currently auto-route to fixtures?

In `propose_relationship_drafts()`, when the client is `MockModelClient`:

```python
draft_kwargs["fixture_name"] = fixture_name or _default_relationship_fixture_for_source(source)
```

`_default_relationship_fixture_for_source()` (`relationship_builder.py`):

1. Checksum-pinned `manual_text` → `fixtures/manual_source_fixture_map.json`
2. Unmapped `manual_text` → fail closed (ValueError)
3. `_is_staged_fetch_spine_source(source)` (title contains `human-ai co-creativity` +
   `songwriting`) → `staged_fetch_build_relationships.json`
4. Default golden → `relationship_drafting_creativity_diversity.json`

When `--fixture` is passed explicitly, auto-routing is bypassed (ticket-178 mock build proof).

There is **no** staged live build fallthrough today. `--live-manual-relationship-fallthrough`
applies only to `manual_text` sources absent from the fixture map.

### 7. What minimal CLI flag/env gate would allow per-step live build?

Mirror ticket-208 link pattern:

- **CLI flag:** `--live-staged-build-fallthrough` on `build-relationships`
- **Env gate:** `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM=1` (separate from mock build gate
  `RGE_ALLOW_LIVE_STAGED_BUILD=1`)
- **Standard live gates:** `RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`
- **Network gates (pytest chain):** `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
- **Eligibility:** source matches `_is_staged_fetch_spine_source`; ≥1 accepted claim;
  concept links present (build requires linked concepts for validation)
- **Mutual exclusion:** cannot combine with `--fixture` or `--live-manual-relationship-fallthrough`
- **DB:** non-default `--db` required (refuse `creative_research.sqlite`)

Implementation helper: `build_relationships_staged_live_fallthrough()` +
`assert_live_staged_build_live_env()` in `relationship_builder.py` or shared
`live_extraction_write.py` pattern.

### 8. Should live build use live extract + live link upstream, or mock upstream for isolation?

**Recommendation: mock extract + mock link upstream in pytest** (same rationale as ticket-208).

| Upstream | pytest (ticket-212) | Manual operator CLI |
|----------|---------------------|---------------------|
| extract | mock `staged_fetch_extract_claims.json` | optional live (204) |
| link | mock `staged_fetch_link_concepts.json` | optional live (208) |
| build | **live Ollama** | **live Ollama** |

Rationale:

- ticket-178 already proves network chain through mock link; live build proof should
  isolate relationship drafting non-determinism
- Stable accepted claims + concept labels reduce live build flake surface
- Operators may manually chain live extract + live link + live build; combined live pytest
  is a **separate follow-on** after build is proven alone

### 9. Should this be rank-1 only?

**Yes.** Rank-1 staged candidate selection is stable via `select_rank1_candidate_id`.
Second-candidate metadata and fixture stability are unproven for live LLM steps.

### 10. Should rank-2 be deferred?

**Yes — NO-GO for ticket-212.** Defer to a separate pre-ticket audit after rank-1 live
build is proven and documented (same pattern as extract/link).

### 11. How will the staged orchestrator remain mock-only?

No changes to `execute_staged_fixture_mode_run` (`rge/cli.py`):

- Line 507: `os.environ["RGE_LLM_MODE"] = "mock"` for entire orchestrator run
- Build steps invoke `build-relationships` without live fallthrough flags
- Mock fixtures bound explicitly in orchestrator spine for rank-1/rank-2

Default `build_relationships_for_source()` path unchanged when fallthrough gate unset.

### 12. How will CI/default pytest exclude the live proof?

- Mark proof: `@pytest.mark.live_network` **and** `@pytest.mark.live_smoke`
- `pyproject.toml` already deselects both markers in default collection
- Add deselect assertion in `tests/unit/test_ci_golden_gate.py` for
  `test_live_openalex_discover_through_live_build` (or equivalent name)
- Mocked gate tests run in default pytest (no Ollama, no network) — mirror
  `test_live_staged_link_live_llm_spine.py` pattern (~5 gate tests)

### 13. How will temp DB enforcement work?

Reuse `live_extraction_write.py` helpers:

- `resolve_live_evidence_db()` / `is_default_graph_db()` — refuse default graph DB
- Pytest uses `tmp_path / "live_staged_build_live_llm.sqlite"`
- No committed live-run artifacts; no public export from temp DB

### 14. How will model output still be validated by Python before persistence?

Unchanged architecture:

1. Ollama proposes `CandidateRelationshipBatch_v0_1` JSON via `OllamaModelClient.draft_relationships()`
2. Pydantic schema validation on model output
3. `validate_relationship_candidates()` checks concept labels, scope, stance, predicate,
   supporting claim IDs, confidence labels
4. `RelationshipRepository.insert()` + `RelationshipEvidenceRepository.insert()` only for
   validated accepted candidates
5. Rejected candidates returned in payload; never written to accepted tables

No model output writes directly to accepted DB tables.

### 15. What exact tests are needed?

**New file:** `tests/unit/test_live_staged_build_live_llm_spine.py`

| Test | Collection | Purpose |
|------|------------|---------|
| `test_require_live_staged_build_live_llm_skips_without_opt_in` | default | Env gate skip |
| `test_live_staged_build_fallthrough_refuses_default_graph_db` | default | DB safety |
| `test_live_staged_build_fallthrough_requires_staged_source` | default | Eligibility |
| `test_live_staged_build_fallthrough_rejects_fixture_combo` | default | Mutual exclusion |
| `test_cli_live_staged_build_fallthrough_routing` | default | CLI branch (stub Ollama) |
| `test_live_openalex_discover_through_live_build` | `live_network` + `live_smoke` | Full operator proof |

Live proof chain:

```
discover → fetch → ingest-staged →
extract-claims --fixture staged_fetch_extract_claims.json →
link-concepts --fixture staged_fetch_link_concepts.json →
build-relationships --live-staged-build-fallthrough
```

Assert: `relationship_count >= 1`; honest skip when Ollama unreachable.

**Update:** `tests/unit/test_ci_golden_gate.py` — deselect assertion for live build test name.

### 16. What files are expected to change?

| File | Change |
|------|--------|
| `rge/modules/relationship_builder.py` | `live_staged_build_fallthrough`; `build_relationships_staged_live_fallthrough`; `assert_live_staged_build_live_env` |
| `rge/cli.py` | `--live-staged-build-fallthrough` flag; `_cmd_build_relationships` branch |
| `tests/unit/test_live_staged_build_live_llm_spine.py` | Gate tests + opt-in live proof |
| `tests/unit/test_ci_golden_gate.py` | Deselect assertion |
| `tickets/ticket-212.json` | Implementation ticket |
| `tickets/TICKET_QUEUE.md` | Queue update |
| `agent_reports/2026-06-15_ticket-212_live-staged-build-live-llm-spine.md` | Implementation report |

Optional follow-on **ticket-213** (docs): README/AGENTS operator section for live staged build.

### 17. What is out of scope?

- Live LLM in `execute_staged_fixture_mode_run`
- Live detect / reconcile / report on staged spine
- Rank-2 live build
- Live extract + live link + live build in single pytest
- CI Ollama
- Public export / site changes
- Cloud providers (ticket-059)
- Schema migrations
- Playwright / Scrapfly / browser scraping
- Default model config changes (`RGE_LOCAL_LLM` / qwen3.5 migration)
- Changing mock gate `RGE_ALLOW_LIVE_STAGED_BUILD=1` behavior (ticket-178)

### 18. What is the rollback plan?

Remove:

- `--live-staged-build-fallthrough` CLI flag and `_cmd_build_relationships` branch
- `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM` env gate and assert helper
- `build_relationships_staged_live_fallthrough()` function
- `tests/unit/test_live_staged_build_live_llm_spine.py`
- CI deselect entry in `test_ci_golden_gate.py`

Retain mock-only staged proofs (146, 178+) and live extract (204) / live link (208) proofs.

---

## Hardened scope (ticket-212 implementation)

### In

1. `--live-staged-build-fallthrough` on `build-relationships`
2. Env gate `RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM=1`
3. Live OpenAlex discover/fetch/ingest in opt-in pytest
4. Mock extract + mock link upstream (stable isolation)
5. Live Ollama only for relationship building
6. Temp `--db` required; refuse default graph DB
7. Mark proof `live_network` + `live_smoke`
8. Mocked gate tests for default pytest
9. CI deselect assertion

### Out

See section 17 above.

---

## Safety

- Live Ollama proposes JSON only; Python validates and repositories write
- Fail closed without triple opt-in (staged live build gate + `RGE_ALLOW_LIVE_LLM` + ollama mode)
- Operator-only; not CI
- Temp DB path required
- Source must have accepted claims and resolvable concept labels before build

---

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-212 per-step live staged build proof | **GO** |
| Live LLM in `execute_staged_fixture_mode_run` | **NO-GO** |
| Rank-2 or orchestrator-wide live build | **NO-GO** |
| Live detect/reconcile/public export in same ticket | **NO-GO** |

---

## Operator opt-in (proposed)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_BUILD_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_build_live_llm_spine.py -m "live_network and live_smoke" -q
```

Manual CLI (after implementation):

```powershell
python -m rge.cli build-relationships --source <source_id> --db <temp.sqlite> --live-staged-build-fallthrough
```

---

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-212**.
