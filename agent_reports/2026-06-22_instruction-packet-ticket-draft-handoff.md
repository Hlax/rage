# Agent Report: Instruction Packet Ticket Draft Handoff

**Date:** 2026-06-22  
**Packet:** Instruction Packet Ticket Draft Handoff  
**Verdict:** GO

## Summary

Implemented a safe local handoff path that converts governor GO / auto-signed-off synthesis instruction packets into draft implementation tickets under `data/operator/draft_tickets/`. The flow never writes to the canonical ticket queue, never promotes tickets, and never edits product code.

## CLI commands added

```powershell
python scripts/run_instruction_packet_ticket_draft.py --latest
python scripts/run_instruction_packet_ticket_draft.py --instruction-packet PATH
python scripts/run_instruction_packet_ticket_draft.py --latest --dry-run
python scripts/run_instruction_packet_ticket_draft.py --latest --out-dir data/operator/draft_tickets/
```

Public-safe JSON summary fields: `verdict`, `source_instruction_packet`, `draft_ticket_path`, `recommended_files`, `acceptance_criteria_count`, `tests_recommended`, `safety_notes`, `non_goals`.

## Draft ticket path behavior

- Input: latest or explicit markdown under `data/operator/instruction_packets/`
- Output: JSON draft under `data/operator/draft_tickets/draft_<timestamp>_<packet_id>.json`
- Status sidecar: `data/operator/instruction_packet_ticket_draft_status_latest.json`
- Canonical `tickets/` and `TICKET_QUEUE.md` are never touched

## Validation gates

| Gate | Behavior |
|------|----------|
| Missing packet | Reject with exit code 2 |
| Stale packet | Reject when governor ledger GO points to a different instruction packet |
| Missing refs | Reject when claim/atom and source refs are absent |
| PARTIAL/NO-GO | Reject when Safety Notes governor verdict is not GO |
| Forbidden actions | Reject merge/push/publish/promote language in recommendation sections |
| Secrets/private content | Reject raw prompts, HTML/PDF markers, local paths, private notes |

Explicit non-goals that say "do not merge/push/publish/promote" are allowed.

## Operator loop behavior

Priority preserved for dirty tree, verify, safety, and public/private blockers. Within synthesis governor flow:

1. **Circuit breaker open** → `run_circuit_breaker_inspection` (review_gated)
2. **Governor pending** → `run_autonomous_synthesis_governor`
3. **GO, no instruction packet** → `run_instruction_packet_generation`
4. **GO, packet exists, no draft** → `run_instruction_packet_ticket_draft` (safe_autonomous)
5. **Draft ticket exists** → `run_local_implementation_handoff` (safe_autonomous)

Autocycle allows `run_instruction_packet_ticket_draft` and `run_local_implementation_handoff` as safe_autonomous actions; circuit breaker still blocks synthesis downstream actions.

## Execute-safe circuit-breaker status behavior

After successful execute-safe checks, `refresh_circuit_breaker_status_report()` runs read-only inspection and writes `data/operator/autonomy_circuit_breaker_status_latest.json`. It does not reset the breaker, run synthesis, or call paid APIs.

## Atlas/operator artifact changes

- `governor_summary` now includes `latest_draft_ticket_path`, `draft_ticket_status`, `instruction_packet_ticket_draft_recommended`, `local_implementation_handoff_recommended`
- `/atlas-preview` shows draft ticket path, status, and handoff recommendation
- No raw instruction packet body in public fixtures; paths and counts only

## Files changed

| File | Change |
|------|--------|
| `rge/modules/instruction_packet_ticket_draft.py` | Draft helper, validation, CLI main |
| `scripts/run_instruction_packet_ticket_draft.py` | Standalone operator script |
| `rge/modules/autonomous_synthesis_governor.py` | Draft status in governor summary/plan; circuit breaker status report |
| `rge/modules/operator_loop.py` | Draft/handoff recommendations; execute-safe status refresh |
| `rge/modules/operator_autocycle.py` | Safe action allowlist |
| `apps/public-site/lib/atlasPreview.ts` | Draft ticket types |
| `apps/public-site/app/atlas-preview/page.tsx` | Draft ticket UI |
| `tests/unit/test_instruction_packet_ticket_draft_handoff.py` | Acceptance tests |

## Tests run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_instruction_packet_ticket_draft_handoff.py -q
python -m pytest tests/unit/test_autonomous_governor_operator_surface.py -q
python -m pytest tests/unit/test_operator_autocycle_synthesis_sign_off.py -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

| Check | Result |
|-------|--------|
| Ticket draft handoff tests (18) | PASS |
| Governor operator surface tests (14) | PASS |
| Autocycle synthesis sign-off tests (4) | PASS |
| Safety audit full | PASS |
| Public-site build | PASS |

## Safety audit result

**PASS** — no blocked routes, export leaks, or secret patterns in public artifacts.

## What remains human-approved

- Merge, push, publish, public export promotion
- Canonical ticket promotion into `tickets/` / `TICKET_QUEUE.md`
- Circuit-breaker reset (`--confirm-reset`)
- PARTIAL/NO-GO governor recovery and re-run
- Local implementation from draft ticket (CLI/IDE/Codex agent pickup)

## Next recommended packets

1. **Local implementation agent pickup contract** — document how Codex/IDE agents consume `data/operator/draft_tickets/*.json` without queue promotion
2. **Draft ticket staleness refresh** — invalidate draft when a newer GO instruction packet supersedes the source
3. **Operator autocycle execute-safe hook** for `--latest` ticket draft when plan recommends it (mirror autonomous loop refresh pattern)
