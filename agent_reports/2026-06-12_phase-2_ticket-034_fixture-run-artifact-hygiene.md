---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 2 / ticket-034 / fixture-run-artifact-hygiene

## 1. Summary

Made fixture-mode `research run` repo-clean: canonical export serialization with stable field ordering, fixed fixture timestamps, deliberate `source_count: 3` reconciliation, default improvement-ticket output routed to gitignored `data/tickets/`, and full `data/` gitignore. Added four GT26 determinism tests. All 123 golden tests pass; safety audit passes; repeated fixture runs leave the working tree clean after commit.

## 2. Ticket

- Ticket ID: ticket-034
- Ticket title: Make fixture-mode run repo-clean and export serialization deterministic
- Branch: `phase-2/ticket-034-fixture-run-artifact-hygiene`
- Phase: 2
- Agent/model: Cursor builder agent
- Date: 2026-06-12
- Main tip before branch: `d9c0e99`

## 3. Scope

### In Scope

- Deterministic public export serialization in fixture mode.
- Stable fixture timestamps and `source_count` reconciliation.
- Default improvement-ticket artifact path under `data/tickets/`.
- Gitignore `data/` runtime output.
- GT26 determinism/idempotency tests.
- Queue housekeeping: ticket-033 done, ticket-034 seeded.

### Out of Scope / Non-goals

- Ollama, live providers, UI polish, README rewrite, schema migrations.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/card_exporter.py` | Canonical JSON helpers, fixture export mode, stable field order, `default_ticket_output_dir()`. |
| `rge/cli.py` | Fixture export flags; default ticket dir → `data/tickets/`. |
| `.gitignore` | Ignore entire `data/` directory. |
| `apps/public-site/public/data/public_cards.json` | Reconciled `source_count: 3`, canonical formatting. |
| `tests/golden/test_26_full_mvp_run.py` | Four new determinism/hygiene tests. |
| `tickets/ticket-033.json` | Status `done`. |
| `tickets/ticket-034.json` | New ticket; status `done`. |
| `tickets/TICKET_QUEUE.md` | ticket-033 done; ticket-034 in progress → done. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-phase-2_principal-audit.md` (ticket-033).
- `source_count: 3` is correct after the three-source fixture MVP spine; committed snapshots updated deliberately.
- Non-fixture `export-public` still uses live `utc_now_iso()` timestamps.
- `data/exports/` is now gitignored; fixture runs may write there without dirtying git.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Fixture run twice leaves clean tree | PASS | Verified post-commit manual check. |
| Committed snapshots match regenerated output | PASS | GT26 byte-for-byte test. |
| Deterministic export serialization | PASS | Stable field order + sorted cards by id. |
| Fixture timestamps stable | PASS | `FIXTURE_EXPORT_TIMESTAMP`. |
| `source_count` drift reconciled | PASS | Committed + fixture export force `3`. |
| Improvement tickets not in `tickets/` | PASS | Default → `data/tickets/`. |
| Generated artifacts gitignored | PASS | `data/` in `.gitignore`. |
| `pytest tests/golden` | PASS | 123/123. |
| `pytest` | PASS | 123/123. |
| Safety audit | PASS | `status: pass`. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_26_full_mvp_run.py` | PASS | 8/8. |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS | 123 passed. |
| `RGE_LLM_MODE=mock python -m pytest` | PASS | 123 passed. |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS | exit 0. |
| Manual clean-tree fixture run ×2 | PASS | Empty `git status --short` after commit. |

## 8. Manual CLI Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli run `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --fixture-mode
# git status --short → empty (×2)
```

Improvement tickets written to `data/tickets/improvement_ticket_latest.json` (gitignored).

## 9. Safety Audit

Full safety audit passes after public snapshot update (`source_count` only; no new fields).

## 10. Merge to Main

- Merge commit: (recorded after merge)
- Branch: `phase-2/ticket-034-fixture-run-artifact-hygiene` merged to `main`.

## 11. Recommended Next Ticket

**ticket-035**: README and operator setup refresh (see Phase 2 roadmap).

## 12. Suggested Next Prompt

```txt
/rge-run-next-ticket
```

Seed `tickets/ticket-035.json` from the Phase 2 roadmap before implementation.
