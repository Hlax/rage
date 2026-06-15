---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-217
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: ticket-217 Live Staged Detect on Staged Spine (Per-Step)

## Verdict: **GO** (narrow per-step rank-1 live detect proof; mock extract + mock link + mock build upstream; domain seed required; orchestrator unchanged)

## Context

`execute_staged_fixture_mode_run` **always** forces `RGE_LLM_MODE=mock` and binds mock
fixtures for detect after ingest. Per-step live staged proofs use **real OpenAlex**
through ingest, then **mock LLM** for pipeline steps unless an explicit live-LLM
fallthrough gate is set.

ticket-204/208/212 proved per-step live Ollama extract, link, and build. **Detect**
still auto-routes staged OpenAlex sources to `staged_fetch_detect_contradictions.json`
in `_default_contradiction_fixture_for_source` (`contradiction_detector.py`) when no
`--fixture` is passed.

ticket-181 proved **mock-fixture detect** after live OpenAlex ingest with
`seed_domain_opposing_context()` (domain-wide opposing relationship required for
qualification edges). That gate is separate from live Ollama detect.

The product gap: **live Ollama contradiction detection on a staged rank-1 source** after
relationships exist, with domain opposing context seeded on temp DB.

---

## Audit answers

### 1. What does “live staged detect” mean in this repo?

| Interpretation | Scope | ticket-217 |
|----------------|-------|------------|
| Full orchestrator live LLM (all steps, both ranks) | Changes `execute_staged_fixture_mode_run` | **NO-GO** |
| Per-step live detect after live ingest + mock upstream (rank-1) | Opt-in pytest + CLI gate | **GO** |
| Live detect on rank-2 second-candidate spine | Second-candidate stability | **NO-GO** (defer) |
| Full live MVP (`execute_fixture_mode_run` + live LLM) | GT26 replacement | **NO-GO** |

“Live staged detect” means: operator opt-in live Ollama **contradiction/qualification
detection** on a staged rank-1 source, bypassing staged-fetch auto-mock, with Python
validation before persistence.

### 2. Which stage is currently live and which remains mock?

| Stage | Default pytest / orchestrator | Per-step operator opt-in |
|-------|------------------------------|--------------------------|
| discover → fetch → ingest-staged | mock (unit) / live (opt-in) | live OpenAlex |
| extract / link / build | mock fixture | live Ollama (204/208/212) or mock |
| detect-contradictions | mock fixture | **not proven** — ticket-217 target |
| reconcile-scores / report | mock | **mock only** |
| `execute_staged_fixture_mode_run` | **mock LLM forced** | unchanged |

### 3. What did ticket-181 add for mock staged detect?

- `tests/unit/test_live_staged_detect_mock_spine.py` with `live_network`
- Env gate `RGE_ALLOW_LIVE_STAGED_DETECT=1` (mock LLM only)
- `seed_domain_opposing_context(temp_db)` before live discover (GT7-style base graph)
- Chain: discover → ingest → mock extract → mock link → mock build → mock detect
- Assert `relationship_evidence` rows with `stance = 'qualifies'` (count ≥ 1)

### 4. What module/command currently detects contradictions?

- **CLI:** `python -m rge.cli detect-contradictions --source <id> [--fixture] [--db]`
- **Module:** `rge/modules/contradiction_detector.py`
  - `detect_contradictions_for_source()` — uses **all domain claims** + **all active relationships**
  - `validate_contradiction_candidates()` — requires matching base/new relationship triples in graph
  - `detect_contradictions_manual_live_fallthrough()` — NM-4 manual_text only

Persistence: `relationship_evidence` rows with `stance = 'qualifies'`.

### 5. How does staged detect currently auto-route to fixtures?

In `propose_contradictions()`, when client is `MockModelClient`:

```python
detect_kwargs["fixture_name"] = fixture_name or _default_contradiction_fixture_for_source(source)
```

Staged title heuristic → `staged_fetch_detect_contradictions.json`.

No staged live detect fallthrough today. `--live-manual-contradiction-fallthrough` is
manual_text only.

### 6. What minimal CLI flag/env gate would allow per-step live detect?

Mirror ticket-212 build pattern:

- **CLI flag:** `--live-staged-detect-fallthrough` on `detect-contradictions`
- **Env gate:** `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1` (separate from mock
  `RGE_ALLOW_LIVE_STAGED_DETECT=1`)
- **Standard live gates:** `RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`
- **Network gates:** `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
- **Eligibility:** staged title heuristic; ≥1 accepted claim; active relationships including seeded opposing context
- **Mutual exclusion:** no `--fixture`; not combinable with `--live-manual-contradiction-fallthrough`
- **DB:** non-default `--db` required

Helpers: `detect_contradictions_staged_live_fallthrough()` +
`assert_live_staged_detect_live_env()`.

### 7. Should live detect use live or mock upstream?

**Recommendation: mock extract + mock link + mock build upstream in pytest** (same as build audit).

| Upstream | pytest (ticket-217) |
|----------|---------------------|
| extract | mock `staged_fetch_extract_claims.json` |
| link | mock `staged_fetch_link_concepts.json` |
| build | mock `staged_fetch_build_relationships.json` |
| detect | **live Ollama** |

Rationale: ticket-181 already proves network + mock upstream through build; live detect
proof should isolate contradiction non-determinism. **Must retain**
`seed_domain_opposing_context(temp_db)` before discover (non-negotiable for qualification
graph shape).

### 8. Should this be rank-1 only?

**Yes.** Stable rank-1 selection via `select_rank1_candidate_id`.

### 9. Should rank-2 be deferred?

**Yes — NO-GO for ticket-217.**

### 10. How will the staged orchestrator remain mock-only?

No changes to `execute_staged_fixture_mode_run` — still forces `RGE_LLM_MODE=mock`;
detect steps without live fallthrough flags.

### 11. How will CI/default pytest exclude the live proof?

- Mark: `@pytest.mark.live_network` **and** `@pytest.mark.live_smoke`
- Add deselect assertion for `test_live_openalex_discover_through_live_detect`
- Mocked gate tests in default pytest (~5 tests, mirror build spine)

### 12. How will temp DB enforcement work?

Reuse `resolve_live_evidence_db()` / `is_default_graph_db()` — refuse default graph DB.
Pytest uses `tmp_path` sqlite. Domain seed runs on same temp DB before live discover.

### 13. How will model output still be validated by Python before persistence?

Unchanged: Ollama proposes JSON → Pydantic → `validate_contradiction_candidates()` checks
claim IDs, relationship triples exist in graph, classification labels →
`RelationshipEvidenceRepository.insert()` only for accepted qualifications.

Assert **≥1 qualifies edge** when status is `completed`; tolerate `no_qualifications`
only in mocked stub tests — live proof should require ≥1 qualifies or honest skip when
Ollama unreachable.

### 14. What exact tests are needed?

**New:** `tests/unit/test_live_staged_detect_live_llm_spine.py`

| Test | Collection |
|------|--------------|
| Env gate skip | default |
| Default graph DB refusal | default |
| Staged source eligibility | default |
| Fixture mutual exclusion | default |
| Stub Ollama routing | default |
| `test_live_openalex_discover_through_live_detect` | `live_network` + `live_smoke` |

Live chain:

```
seed_domain_opposing_context → discover → fetch → ingest →
mock extract → mock link → mock build → live detect (--live-staged-detect-fallthrough)
```

### 15. What files are expected to change?

| File | Change |
|------|--------|
| `rge/modules/contradiction_detector.py` | staged live fallthrough + env assert |
| `rge/cli.py` | `--live-staged-detect-fallthrough` |
| `tests/unit/test_live_staged_detect_live_llm_spine.py` | gate + live proof |
| `tests/unit/test_ci_golden_gate.py` | deselect assertion |

### 16. What is out of scope?

- Live reconcile/report on staged spine
- Rank-2 live detect
- Live extract/link/build + live detect combined pytest
- Orchestrator live LLM
- CI Ollama
- Public export/site
- Schema migrations
- Removing domain seed requirement

### 17. What is the rollback plan?

Remove env gate, CLI flag, test file, CI deselect entry. Retain mock detect proof (181+).

### 18. Risk notes specific to detect

- **Higher flake surface** than build: model must propose valid qualification linking
  existing relationship triples from seed + mock build
- **Domain-wide context:** detect reads all domain claims and active relationships —
  temp DB pollution must stay confined to pytest DB
- Recommend assert `qualification_count >= 1` not exact fixture classification strings

---

## Hardened scope (ticket-217 implementation)

### In

1. `--live-staged-detect-fallthrough` on `detect-contradictions`
2. `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1`
3. Live OpenAlex discover/fetch/ingest + `seed_domain_opposing_context`
4. Mock extract + mock link + mock build upstream
5. Live Ollama only for detect
6. Temp `--db`; refuse default graph DB
7. `live_network` + `live_smoke` markers
8. Mocked gate tests + CI deselect

### Out

See section 16.

---

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-217 per-step live staged detect proof | **GO** |
| Orchestrator live LLM | **NO-GO** |
| Rank-2 or combined all-live upstream pytest | **NO-GO** |
| Live reconcile/public export in same ticket | **NO-GO** |

---

## Operator opt-in (proposed)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"

python -m pytest tests/unit/test_live_staged_detect_live_llm_spine.py -m "live_network and live_smoke" -q
```

---

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-217**.
