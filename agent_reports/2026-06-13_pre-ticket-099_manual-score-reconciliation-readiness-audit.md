---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-099 Manual Score Reconciliation Readiness Audit

- Audit type: focused pre-ticket readiness (manual source score reconciliation)
- Date: 2026-06-13
- Scope: read-only design audit. No implementation in this report.
- Baseline HEAD: `2e14aa0` (main)
- Principal gate: `agent_reports/2026-06-13_principal-audit-post-ticket-098.md`

## Executive verdict

**GO — seed ticket-099 with hardened scope**

Manual synthnote spine (tickets 088–098) does **not** produce score_events today:
primary claims use confidence 0.72/0.7 (below 0.8 gate) and claim text uses
"narrowed the range of themes" (does not match `claim_supports_relationship`
fragment gate `"semantic diversity"` + `"reduced"`/`"reduce"`).

Follow **Golden Test 8 pattern**: base spine on synthnote, then a **second
`manual_text` follow-up source** with a calibrated mock claim fixture (confidence
≥ 0.8, supporting text compatible with existing reconciler gates).

## Repo state

| Check | Result |
| ----- | ------ |
| `score_reconciler.py` | Deterministic; no model use; GT08-proven on fixture sources |
| Synthnote accepted claims | 2 claims; max confidence 0.72; no score_events on reconcile |
| `reconcile-scores` CLI | Exists; scoped by `--source` |
| Manual fixture map | Checksum-keyed tasks through `detect_contradictions` |
| Validator / schema / export | Unchanged in ticket scope |

## Design decisions

| Question | Answer |
| -------- | ------ |
| Change `STRONGER_CLAIM_CONFIDENCE_THRESHOLD`? | **No** — keep 0.8 |
| Change GT08 golden fixtures? | **No** |
| Hardcode synthnote fragments in Python? | **No** — follow-up source + fixture map entry |
| Live Qwen? | **No** — mock fixture only |
| Schema migration? | **No** |
| Export changes? | **No** |

## Hardened implementation scope (ticket-099)

1. Add committed follow-up source `fixtures/sources/manual_synthnote_followup.txt`
   (short operator-style replication note; quote-span-grounded text).
2. Add `fixtures/llm_outputs/claim_extraction_manual_synthnote_followup.json`
   with **one accepted claim**: confidence ≥ 0.85, claim text containing
   `"reduced semantic diversity"` (matches existing `claim_supports_relationship`
   without core hardcoding).
3. Extend `fixtures/manual_source_fixture_map.json` with follow-up checksum →
   `extract_claims` fixture (no new pipeline tasks required).
4. Add `tests/unit/test_manual_score_reconciliation.py`:
   - Run full synthnote spine (ingest→detect) on temp `--db`
   - Ingest follow-up `manual_text` source (checksum map resolves extract fixture)
   - `reconcile-scores --source <followup_id>` → 1 `score_events` row, relationship
     confidence increases per `golden_v0.1.0` formula
   - Idempotent re-run → no duplicate score_events
5. **Optional** `score_reconciler` change: only if needed for manual checksum
   resolution on extract — prefer zero production changes if follow-up claim text
   satisfies existing gates.

## Out of scope

- Lowering credibility threshold for synthnote primary claims
- Rewriting `claim_supports_relationship` with creativity-specific branches
- Public export or site changes
- Live Ollama calibration

## GO / NO-GO

**GO for ticket-099** after this report is on `main`.

Suggested prompt: `/rge-run-next-ticket`
