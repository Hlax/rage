# Phase 2 Ticket-052 — Quote Span Char Offsets

- Ticket: ticket-052
- Branch: `phase-2/ticket-052-quote-span-offsets`
- Date: 2026-06-12
- Status: done

## Summary

Persist `char_start`/`char_end` on primary `claim_quotes` when quote spans match chunk text (exact or collapsed-whitespace). Validation rules unchanged. GT02 asserts offsets on accepted fixture claims.

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_claim_quote_offsets.py -q   # 4 passed
python -m pytest tests/golden/test_02_claim_extraction.py -q  # 4 passed
python -m pytest -q                                            # 187 passed, 1 deselected
```
