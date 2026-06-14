---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-146
---

# ticket-146: Build Relationships on Staged-Ingested Source (Mock Spine Step)

## Summary

Added **`staged_fetch_build_relationships.json`** mock fixture and staged-source title heuristic in
`relationship_builder`. Unit test extends the Phase 3 spine through **build-relationships** after
discover → enqueue → fetch → ingest-staged → extract-claims → link-concepts.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-146 |
| Branch | `phase-2/ticket-146-staged-build-relationships-spine` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-146_staged-build-relationships-spine-audit.md` (GO) |
| Main tip before branch | `c7cb6e3` |

## Scope

### In

- `fixtures/llm_outputs/staged_fetch_build_relationships.json`
- `relationship_builder._is_staged_fetch_spine_source()` + fixture routing + staged claim fallback
- `tests/unit/test_staged_ingest_relationship_spine.py` (3 tests)

### Out

- Live LLM, detect-contradictions, score reconciliation, run report, schema, public site, full research run

## Changed files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_build_relationships.json` | mock relationship fixture |
| `rge/modules/relationship_builder.py` | staged spine fixture selection + claim id heuristic |
| `tests/unit/test_staged_ingest_relationship_spine.py` | e2e spine through build-relationships |
| `agent_reports/2026-06-14_pre-ticket-146_staged-build-relationships-spine-audit.md` | pre-ticket audit (GO) |
| `tickets/ticket-146.json` | status done |
| `tickets/ticket-147.json` | seeded detect-contradictions follow-on |

## Relationship persisted

One active edge from the staged fixture:

| Subject | Predicate | Object | Scope | Stance | Confidence |
|---------|-----------|--------|-------|--------|------------|
| co-creation | may_increase | semantic diversity | songwriting workshops | supports | 0.5 (medium) |

Evidence links the accepted co-creativity claim (`Human-AI co-creativity supports diverse songwriting outputs.`).

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Staged relationship fixture exists and is deterministic | **PASS** |
| 2 | Relationship builder routes staged source to fixture in mock path | **PASS** |
| 3 | Unit test proves full staged spine through build-relationships | **PASS** |
| 4 | At least one relationship row persisted | **PASS** |
| 5 | ticket-144/145 staged spine tests remain green | **PASS** |
| 6 | Golden tests pass | **PASS** (142) |
| 7 | Full pytest passes | **PASS** (546, 6 deselected) |
| 8 | Safety audit passes | **PASS** |
| 9 | No public export/site changes | **PASS** |
| 10 | ticket-147 seeded | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_staged_ingest_extract_spine.py -q   # 4 passed
python -m pytest tests/unit/test_staged_ingest_link_spine.py -q      # 3 passed
python -m pytest tests/unit/test_staged_ingest_relationship_spine.py -q  # 3 passed
python -m pytest tests/golden -q                                      # 142 passed
python -m pytest -q                                                   # 546 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                       # pass
```

## No-live / no-network / no-public-export

Mock LLM only (`RGE_LLM_MODE=mock`). OpenAlex/HTML fetch mocked in unit tests. No schema migration,
public export, public site, live Ollama, or real network calls.

## Spec deviations

- No `cli.py` changes; existing `build-relationships --fixture` sufficient for explicit fixture path.

## Merge to main

Merged to `main` as `f3831be133ad08d57cda658132bbe3913bbbc3e8` (2026-06-14).
Post-merge pytest: 546 passed, 6 deselected.

## Recommended next ticket

**ticket-147** — Detect contradictions on staged-ingested source (pre-ticket audit required).

## Suggested next prompt

Write pre-ticket-147 audit, then `/rge-run-next-ticket` for ticket-147.
