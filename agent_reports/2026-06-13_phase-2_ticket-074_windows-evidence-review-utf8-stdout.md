---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-074: Windows-safe UTF-8 stdout for probe-scratch-evidence-review

- Date: 2026-06-13
- Branch: `phase-2/ticket-074-windows-evidence-review-utf8-stdout`
- Baseline HEAD: `db3ec6b` (principal audit post-ticket-073)
- Risk level: low

## Summary

Replaced the Unicode review-window arrow (`→`) with ASCII `->` in
`format_evidence_review_markdown()` so default markdown stdout works on Windows
cp1252 consoles without `PYTHONIOENCODING=utf-8`. JSON and `--out` paths unchanged.

## Audit gate

- Principal cadence: satisfied via `agent_reports/2026-06-13_principal-audit-post-ticket-073.md`
- Pre-ticket audit: not required (`risk_level: low`, no milestone triggers)
- Gate check: `python -m rge.modules.principal_audit_gate --next-ticket ticket-074` → satisfied

## Scope

**In:** Markdown formatter ASCII arrow; cp1252 encoding unit tests.

**Out:** No broad CLI stdout refactor; no public export/site changes.

## Files changed

| File | Change |
| ---- | ------ |
| `rge/modules/live_probe_evidence_review.py` | ASCII `->` in review window line |
| `tests/unit/test_live_probe_evidence_review.py` | cp1252 encode + CLI markdown tests |
| `tickets/ticket-074.json`, `TICKET_QUEUE.md` | Done + ticket-075 seed |

## Acceptance criteria

| Criterion | Status |
| --------- | ------ |
| Default markdown prints on Windows without UnicodeEncodeError | **pass** |
| JSON and `--out` behavior unchanged | **pass** |
| Unit test covers markdown encoding safety | **pass** |
| Golden/mock gates pass | **pass** |

## Verification

| Command | Result |
| ------- | ------ |
| `pytest tests/unit/test_live_probe_evidence_review.py -q` | **16 passed** |
| `pytest tests/golden -q` | **140 passed** |
| `pytest -q` | **328 passed**, 6 deselected |
| `python -m rge.cli probe-scratch-evidence-review --allow-empty` (no UTF-8 env) | **exit 0**, markdown printed |

Safety audit not required (formatter-only; no public/safety surface change).

## Manual CLI verification

```powershell
Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
python -m rge.cli probe-scratch-evidence-review --allow-empty
```

Review window line: `None -> None` — no encode error on cp1252 stdout.

## Merge

- Merge commit SHA: _(filled after merge)_
- Golden Gate run: _(filled after CI)_

## Recommended next ticket

**ticket-075 (proposed)** — Live probe runbook Windows console encoding note (document cp1252-safe operator CLIs post-074).

## Suggested next prompt

Run `/rge-run-next-ticket` for ticket-075, or populate scratch DB and re-run evidence review with real reviewed rows.
