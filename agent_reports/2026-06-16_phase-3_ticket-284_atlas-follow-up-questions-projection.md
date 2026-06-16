# Agent Report: ticket-284 — Atlas snapshot follow_up_questions[] projection v0

**Date:** 2026-06-16  
**Ticket:** ticket-284  
**Branch:** `phase-3/ticket-284-atlas-follow-up-questions-projection`  
**Main tip before branch:** `705b709`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-284_atlas-follow-up-questions-v0-audit.md` (GO)

## Summary

Added optional `follow_up_questions[]` to `atlas_snapshot_v0.1.0`, projected from existing
`research_queue` question rows via `ResearchQueueRepository.list_followups_for_contract()`.
Question text is exposed as `question_text` (not `last_error`). Creativity fixture regenerated
with six follow-up entries (three queued, three parked).

## Scope

**In:** Contract field + constants, builder projection, fixture, builder tests.

**Out:** Public-site UI, public export routes, schema migrations, review_batch persistence, live Ollama.

## Changed files

| File | Change |
|------|--------|
| `rge/contracts/atlas_snapshot_v0.py` | `follow_up_questions` + `ATLAS_FOLLOW_UP_QUESTION_FIELDS` |
| `rge/contracts/__init__.py` | Re-export |
| `rge/modules/atlas_snapshot_builder.py` | `_build_follow_up_questions()` |
| `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` | Regenerated |
| `tests/unit/test_atlas_snapshot_builder.py` | Follow-up questions test (7 total) |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| `follow_up_questions[]` from research_queue when present | **PASS** — 6 items in fixture |
| Creativity fixture updated deterministically | **PASS** |
| validate_atlas_snapshot + no private leak | **PASS** |
| Golden + full pytest | **PASS** — 142 golden, 735 full |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_snapshot_builder.py -q  # 7 passed
python -m pytest tests/golden -q                              # 142 passed
python -m pytest -q                                           # 735 passed, 30 deselected
```

Safety audit not required — read-only DB projection; no public export or site changes.

## Manual CLI verification

Regenerated fixture via `python scripts/regenerate_atlas_creativity_fixture.py`.
Export CLI byte-match tests pass against updated creativity fixture.

## Spec deviations

None.

## Merge to main

Merge commit: `930e45d`

## Drift note — stop Atlas-only infrastructure streak

Tickets 278–284 closed the Research Atlas **contract thread** (shape → population → lineage →
private export → inventory → follow-up questions). The backend can now shape validated atlas
JSON from fixture-mode DBs, but we still lack **live-research/product proof** that real staged
runs produce meaningful graph data—not just well-formed envelopes.

## Recommended next ticket

**ticket-285** — Opt-in live staged research run → private atlas snapshot export + coherence audit
(operator `live_network` pytest; temp DB only; not CI).

## Suggested next prompt

```txt
/rge-run-next-ticket
```
