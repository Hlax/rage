---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-131
---

# ticket-131: NM-4 Evidence DB Score Reconciliation Operator Proof

## Summary

Completed NM-4 deterministic score reconciliation on the gitignored evidence DB.
Extended `claim_supports_relationship` to match live-drafted active edges (not only
the golden `may_reduce` / `semantic diversity` triple). Operator proof on the
ticket-127 evidence chain plus follow-up source produced **1 score_events row** and
boosted the `AI assistance` → `constraint` edge from **0.5 → 0.62**.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-131 |
| Branch | `phase-2/ticket-131-nm4-evidence-db-score-reconciliation` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-131_nm-4-evidence-db-score-reconciliation-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-130.md` (cadence satisfied) |
| Main tip before branch | `bbb521e` |

## Scope

### In

- Evidence-graph matcher hardening in `score_reconciler.py`
- `--evidence-db-reconcile` on `reconcile-scores` (gitignored DB guard)
- Follow-up fixture + mock extract map entry
- Unit tests (`test_nm4_evidence_score_reconciliation.py`)
- Live operator proof on evidence DB

### Out

- Ollama / live LLM in score reconciliation
- New `--live-manual-*` reconcile flags
- Public export/site changes
- Docs cross-link chain

## Changed files

| File | Change |
|------|--------|
| `rge/modules/score_reconciler.py` | Golden + active-edge matchers |
| `rge/cli.py` | `--evidence-db-reconcile` |
| `fixtures/sources/ticket131_nm4_evidence_followup.txt` | Follow-up operator text |
| `fixtures/llm_outputs/claim_extraction_ticket131_nm4_evidence_followup.json` | Mock extract fixture |
| `fixtures/manual_source_fixture_map.json` | Follow-up checksum map entry |
| `tests/unit/test_nm4_evidence_score_reconciliation.py` | NM-4 evidence proof tests |
| `tickets/ticket-131.json` | status done |
| `tickets/ticket-132.json` | seeded next step |
| `tickets/TICKET_QUEUE.md` | ticket-131 done |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Follow-up ingest + extract + reconcile on evidence DB | **PASS** |
| 2 | Domain-pack boost (formula_version, stronger_evidence_boost) | **PASS** (0.5 → 0.62) |
| 3 | Matcher covers live-drafted edges | **PASS** |
| 4 | Synthnote mock reconcile unchanged | **PASS** (5 tests) |
| 5 | Golden mock-only pass | **PASS** (142) |
| 6 | Safety audit pass | **PASS** |
| 7 | Public export/site untouched | **PASS** |
| 8 | No Ollama in score_reconciler | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_nm4_evidence_score_reconciliation.py -q   # 6 passed
python -m pytest tests/unit/test_manual_score_reconciliation.py -q         # 5 passed
python -m pytest tests/golden -q                                           # 142 passed
python -m pytest -q                                                        # 484 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                          # pass
```

## Manual CLI verification (evidence DB)

```powershell
$env:RGE_LLM_MODE = "mock"

python -m rge.cli ingest fixtures/sources/ticket131_nm4_evidence_followup.txt `
  --domain creativity --source-type manual_text `
  --source-title "Ticket-131 NM-4 evidence follow-up" `
  --db data/db/live_research_evidence.sqlite

python -m rge.cli extract-claims --source src_044a97ae8419e35a `
  --db data/db/live_research_evidence.sqlite

python -m rge.cli reconcile-scores --source src_044a97ae8419e35a `
  --db data/db/live_research_evidence.sqlite --evidence-db-reconcile
```

| Field | Value |
|-------|-------|
| Prior NM-4 source | `src_1b8354e5f2203f82` (live spine 127–130) |
| Follow-up source | `src_044a97ae8419e35a` |
| `score_events_created` | **1** |
| Edge | `AI assistance` → `constraint` (`supports`) |
| Confidence | **0.5 → 0.62** |
| `formula_version` | `golden_v0.1.0` |

## Spec deviations

None.

## Merge to main

Merged @ **`a103ff5`** (`Merge branch 'phase-2/ticket-131-nm4-evidence-db-score-reconciliation'`).
Pushed to `origin/main`.

## Recommended next ticket

**ticket-132** — Operator loop NM-4 evidence DB spine status (read-only plan surface).

## Suggested next prompt

`/rge-run-next-ticket` for ticket-132, or run principal audit post-ticket-131 if cadence desired before further NM-4 docs.
