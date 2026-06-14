---
template_id: implementation_report
status: done
date: 2026-06-14
workstream: NM-2
risk_level: low
---

# NM-2: Maturity Relabel Report

## Goal

Remove false confidence from README/status docs; distinguish engine plumbing,
checksum-pinned fixtures, live report-only probes, and the new NM-1 live validated
write proof.

## Files updated

- `README.md` — honest two-tier status table; checksum fixture clarification;
  `extract-claims-live` operator steps
- `AGENTS.md` — maturity tiers; live validated extraction pointer
- `docs/agents/02_ARCHITECTURE.md` — LangGraph/FastAPI marked planned/not implemented
- `docs/agents/11_AGENT_OPERATING_PROTOCOL.md` — checksum mock clarification;
  drift_warning interpretation (NM-3 cross-link)
- `docs/agents/12_RUNTIME_CONFIG.md` — manual synthnote mock vs live write paths
- `tickets/TICKET_QUEUE.md` — ticket-111 superseded; corrective override table

## ticket-111 disposition

**Superseded** and folded into this corrective doc pass. The README pipeline proof
test pointer is already covered by existing operator quickstart sections; a standalone
ticket-111 cross-link would not reduce product risk.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q   # 140 passed
python -m pytest -q                # 390 passed
python -m rge.modules.safety_auditor --audit full  # pass
```

No production behavior changes.

## Acceptance

- [x] No doc claims checksum fixtures are arbitrary live extraction
- [x] MVP-Research not called "done" without live/fixture distinction
- [x] Architecture marks LangGraph/FastAPI as planned
- [x] README honest status block with NM-1/NM-4/cloud tiers
- [x] ticket-111 superseded in queue
