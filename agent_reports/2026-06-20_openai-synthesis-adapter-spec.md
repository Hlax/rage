# Agent Report: OpenAI Synthesis Adapter Spec (ticket-059)

**Date:** 2026-06-20  
**Packet:** openai-synthesis-adapter-spec  
**Verdict:** GO (spec only — **no implementation**)

## Goal

Define a fail-closed, evidence-packet-only contract for future paid cloud synthesis
without calling OpenAI or any paid API.

## Deliverables

| Artifact | Purpose |
|----------|---------|
| `rge/contracts/synthesis_evidence_packet_v0.py` | Ref-only input schema validation |
| `rge/modules/openai_synthesis_adapter_spec.py` | Env gates, readiness checks, spec document |
| `scripts/run_openai_synthesis_adapter_spec.py` | Operator validation entry (no API) |
| `tests/unit/test_openai_synthesis_adapter_spec.py` | Mock-only unit tests |

## Spec highlights

- **Input:** atoms, claims, source_refs, trace_refs only — no raw PDF/HTML/text
- **Output (future):** every synthesis sentence must cite claim/atom/source refs
- **Env gates:** `RGE_CLOUD_LLM_ENABLED=1`, `RGE_ALLOW_OPENAI_SYNTHESIS=1`, `OPENAI_API_KEY`
- **Readiness:** requires `synthesis_ready_cluster_count ≥ 1` (from multi-claim clustering)
- **Cost caps:** `RGE_CLOUD_MAX_USD_PER_RUN`, `RGE_CLOUD_MAX_TOKENS_PER_CALL`
- **CI:** mock client only; real API calls forbidden
- **execute-safe:** cloud synthesis explicitly forbidden

## Operator command

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_openai_synthesis_adapter_spec.py --sync-public
```

## Next step

**ticket-059-implementation** — human promotion required before any cloud adapter code.
