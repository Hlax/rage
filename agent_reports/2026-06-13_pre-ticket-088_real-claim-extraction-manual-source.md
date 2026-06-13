---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-088 Real Claim Extraction from Manual Source Audit

- Audit type: focused pre-ticket readiness (manual source claim extraction floor)
- Date: 2026-06-13
- Scope: read-only design audit. No implementation in this report.
- Baseline HEAD: `86f3a57` (main; ticket-087 landed)
- Principal gate (`--next-ticket ticket-088`): **satisfied** (cadence OK)

## Executive verdict

**GO — seed ticket-088**

Ticket-086 proved manual ingestion; ticket-087 wired domain pack aliases. The next
smallest proof is **deterministic claim extraction** from an operator manual source
(`synthnote.txt`) using a **calibrated mock fixture** with quote spans grounded in the
source text — not live Qwen (CI-safe, mock-only).

## Repo state

| Check | Result |
| ----- | ------ |
| Manual sources | `test.txt`, `synthnote.txt` under `data/sources/manual/creativity/` (gitignored) |
| synthnote source id | `src_2c53bfdfdf3c6853` (ingested `manual_text`) |
| Mock extraction today | `_default_fixture_for_chunk` uses content heuristics for fixture diversity source only |
| `--fixture` CLI flag | Already exists on `extract-claims` |
| Live LLM | Disabled; effective mode mock |

## Design decisions

| Question | Answer |
| -------- | ------ |
| Live Qwen or mock? | **Mock fixture** calibrated to synthnote checksum (ticket-085 G2 deferred live floor) |
| Hardcode creativity in core? | **No** — checksum → fixture map in `fixtures/manual_source_fixture_map.json` |
| Validator changes? | **None** — use existing quote-span / scope / rejection rules |
| Schema migration? | **None** |
| Export changes? | **None** |

## Implementation target

1. Add `fixtures/llm_outputs/claim_extraction_manual_synthnote.json` with ≥1 accepted
   scoped claim (quote span in source text) and ≥1 rejected claim (`missing_quote_span`).
2. Add `fixtures/manual_source_fixture_map.json` mapping synthnote `raw_text_checksum`
   → fixture filename.
3. Extend `claim_extractor` to resolve fixtures for `manual_text` sources via checksum map
   before existing chunk heuristics.
4. Unit tests: ingest synthnote (or copy), extract-claims, assert accepted+rejected counts.
5. Golden GT02 unchanged (fixture source path unchanged).

## Out of scope

- Live Ollama extraction, OpenAI/cloud
- Concept linking on manual source (ticket-089 follow-on)
- Validator changes, schema migrations, export
- Automatic fixture generation from model output

## Rollback plan

Revert fixture map, synthnote fixture, claim_extractor checksum lookup, and unit tests.

## GO / NO-GO

**GO for ticket-088.**
