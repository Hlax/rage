# Live OpenAI Evaluator Ticket Seeding

## Summary

Seeded a five-ticket proposed sequence for making the live OpenAI synthesis
canary pass honestly under existing safety gates and then routing evaluator
output into the existing governor, instruction-packet, and draft-ticket handoff
path.

## Changed Files

- `tickets/ticket-393.json`
- `tickets/ticket-394.json`
- `tickets/ticket-395.json`
- `tickets/ticket-396.json`
- `tickets/ticket-397.json`
- `tickets/TICKET_QUEUE.md`
- `agent_reports/2026-06-23_phase-3_ticket-393-397_live-openai-evaluator-ticket-seeding.md`

## Ticket Sequence

- `ticket-393` — Hydrate live OpenAI synthesis grounding input.
- `ticket-394` — Add deterministic live OpenAI synthesis evaluator artifact.
- `ticket-395` — Bridge OpenAI synthesis evaluator suggestions to
  instruction-packet draft tickets.
- `ticket-396` — Surface OpenAI synthesis evaluator status in operator plan.
- `ticket-397` — Document live OpenAI evaluator canary runbook and checkpoint.

All tickets are `proposed`. Existing `ticket-392` remains the current active
proposed ticket in the queue summary.

## Commands Run

```powershell
python -c "<ticket JSON and queue validation script>"
```

First attempt failed due to PowerShell quoting of newline escapes in the inline
Python command. The command was rerun with safer `exec(...)` quoting and passed:

```txt
validated_ticket_json_and_queue_rows=ticket-393,ticket-394,ticket-395,ticket-396,ticket-397
```

## Acceptance Criteria Status

- Ticket JSON files created with required builder-consumable fields: complete.
- Queue rows added for `ticket-393` through `ticket-397`: complete.
- Queue note documents the sequence and safety boundary: complete.
- Plan file left unchanged: complete.

## Safety Notes

- No live OpenAI call was made during ticket seeding.
- No API keys or `.env.local` contents were read, printed, copied, or committed.
- The proposed sequence preserves mock-first defaults and keeps live OpenAI
  operator-only behind explicit gates, cost caps, and `--confirm`.
- No accepted graph tables, public-site JSON, or public publish path were
  changed.

## Known Failures

- None after the validation rerun.

## Recommended Next Ticket

Implement `ticket-393` first on its own branch:
`phase-3/ticket-393-live-openai-grounding-input`.
