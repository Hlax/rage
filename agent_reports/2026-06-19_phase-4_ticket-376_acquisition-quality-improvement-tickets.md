# Agent Report — Phase 4 / ticket-376 / Packet 9

**Date:** 2026-06-19  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Ticket:** ticket-376 — seed improvement tickets from `acquisition_quality_summary` + quality-gate blocks  
**Status:** GO

## Summary

Packet 9 closes the Phase 4 packets 5–9 kickoff by wiring acquisition/parser metrics into the self-improvement loop:

1. **`failure_modes_from_acquisition_summary()`** in `rge/modules/acquisition_quality.py` maps `dirty_text`, `parse_failed`, webpage dirty combos, and `pdf_unavailable` parser backend counts to ticket/recommender failure reasons.
2. **`ACQUISITION_FAILURE_TEMPLATES`** + merged **`IMPROVEMENT_FAILURE_TEMPLATES`** in `rge/modules/ticket_writer.py` — builder-consumable tickets for `blocked_by_quality_gate`, `parse_failed`, `webpage_dirty_text`, and `pdf_parser_unavailable`.
3. **`write_improvement_tickets()`** now merges `top_failure_modes` with acquisition summary signals and attaches `acquisition_quality:*` evidence lines.
4. **`recommend_from_run_report()`** in `rge/modules/failure_recommender.py` — `--run-report` CLI path now consumes `acquisition_quality_summary` for packet recommendations (quality gates, web adapter, PDF parser).

## Files changed

| File | Change |
|------|--------|
| `rge/modules/acquisition_quality.py` | `failure_modes_from_acquisition_summary()` |
| `rge/modules/ticket_writer.py` | Acquisition templates, merged lookup, evidence lines |
| `rge/modules/failure_recommender.py` | `recommend_from_run_report()`, `pdf_parser_unavailable` packet |
| `tests/unit/test_acquisition_quality.py` | Failure-mode derivation tests |
| `tests/unit/test_ticket_writer_acquisition_quality.py` | Ticket seeding tests |
| `tests/unit/test_failure_recommender.py` | Run-report recommendation tests |
| `tests/golden/test_35_acquisition_quality_tickets.py` | Golden GT35 |
| `tests/golden/test_21_builder_ticket_consumption.py` | `IMPROVEMENT_FAILURE_TEMPLATES` coverage |
| `tests/golden/test_22_builder_golden_gate.py` | Register GT35 optional |
| `tickets/ticket-376.json` | `done` |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_acquisition_quality.py tests/unit/test_ticket_writer_acquisition_quality.py tests/unit/test_failure_recommender.py tests/golden/test_35_acquisition_quality_tickets.py -q
# 20 passed

python -m rge.cli verify --skip-site
# PASS (golden + full pytest + safety audit)
```

## Packets 5–9 status

| Packet | Ticket | Status |
|--------|--------|--------|
| 5 follow-on — atlas evidence card preview | 377 | GO |
| 6 — ingest-webpage CLI | 373 | GO |
| 7 — parser metrics + GROBID fixture | 374 | GO |
| 8 — asset export candidates | 375 | GO |
| 9 — acquisition-quality ticket seeding | 376 | GO |

## Next recommendation

Phase 4 packet kickoff is complete. Next smallest moves (outside this branch scope unless ticketed):

- Operator live GROBID proof (deferred; fixture proof in GT33)
- Public-site UI for `evidence_cards_preview` (separate ticket)
- Scrapling/live URL fetch for web adapter (separate ticket)
