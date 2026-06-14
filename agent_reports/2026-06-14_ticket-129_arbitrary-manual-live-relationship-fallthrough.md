---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-129
---

# ticket-129: Arbitrary Manual Live Relationship Fall-Through

## Summary

Extended NM-4 with live Ollama relationship drafting for arbitrary `manual_text`
sources absent from the checksum fixture map. Mock mode now fail-closed for
unmapped relationship fixtures (no silent diversity fallback). Live operator run
on the ticket-127/128 evidence source persisted **1 active relationship** and
**1 evidence row** in the gitignored evidence DB.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-129 |
| Branch | `phase-2/ticket-129-arbitrary-manual-live-relationship-fallthrough` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-129_arbitrary-manual-live-relationship-fallthrough-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-127.md` (cadence satisfied) |
| Main tip before branch | `4b133da` |

## Scope

### In

- `--live-manual-relationship-fallthrough` on `build-relationships`
- Mock fail-closed for unmapped `manual_text` relationship fixtures
- `build_relationships_manual_live_fallthrough()` orchestration in `relationship_builder.py`
- Ollama relationship prompt calibration for `manual_text_arbitrary_live`
- Unit tests (+6 relationship fall-through tests)
- Live operator proof on evidence DB (ticket-127/128 source chain)

### Out

- Contradiction live fall-through
- Validator weakening
- Public export/site changes
- Docs cross-link chain

## Changed files

| File | Change |
|------|--------|
| `rge/modules/manual_source_fixtures.py` | `manual_text_lacks_relationship_fixture()` |
| `rge/modules/relationship_builder.py` | Fail-closed mock; live relationship fall-through |
| `rge/llm/ollama_client.py` | Manual arbitrary relationship prompt calibration |
| `rge/cli.py` | `--live-manual-relationship-fallthrough` |
| `tests/unit/test_manual_live_fallthrough.py` | +6 relationship tests (20 total) |
| `agent_reports/2026-06-14_pre-ticket-129_arbitrary-manual-live-relationship-fallthrough-audit.md` | Pre-ticket audit GO |
| `tickets/ticket-129.json` | status done |
| `tickets/ticket-130.json` | seeded next NM-4 step |
| `tickets/TICKET_QUEUE.md` | ticket-129 done |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Live relationships after extract+link on unmapped manual_text | **PASS** |
| 2 | ≥1 validated active relationship in gitignored DB | **PASS** (live: 1 rel, 1 evidence) |
| 3 | Synthnote mock paths deterministic | **PASS** |
| 4 | Golden mock-only pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |
| 6 | Public export/site untouched | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_manual_live_fallthrough.py -q   # 20 passed
python -m pytest tests/golden -q                                 # 142 passed
python -m pytest -q                                              # 472 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                # pass
```

## Manual CLI verification (live)

```powershell
$env:RGE_LLM_MODE = "ollama"; $env:RGE_ALLOW_LIVE_LLM = "1"

python -m rge.cli build-relationships --source src_1b8354e5f2203f82 `
  --db data/db/live_research_evidence.sqlite --live-manual-relationship-fallthrough
```

| Field | Value |
|-------|-------|
| Source checksum | `1b8354e5…` (not in fixture map) |
| Prior steps | ticket-127 live extract; ticket-128 live link |
| `relationship_count` | **1** (`AI assistance` → `constraint`, supports) |
| `rejected_relationship_count` | **0** |
| `evidence_count` | **1** |
| `db_writes` | true |
| Model | `qwen2.5:7b` |

## Spec deviations

None.

## Merge to main

Merged @ **`24b14a4`** (`Merge branch 'phase-2/ticket-129-arbitrary-manual-live-relationship-fallthrough'`).
Pushed to `origin/main`.

## Recommended next ticket

**ticket-130** — Arbitrary manual live contradiction fall-through (NM-4 pipeline
continuation). Requires pre-ticket audit (medium risk, live Ollama).

## Suggested next prompt

Write pre-ticket audit for ticket-130, then `/rge-run-next-ticket`.
