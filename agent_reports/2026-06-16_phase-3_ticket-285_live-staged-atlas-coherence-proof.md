# Agent Report: ticket-285 — Live staged atlas snapshot coherence proof

**Date:** 2026-06-16  
**Ticket:** ticket-285  
**Branch:** `phase-3/ticket-285-live-staged-atlas-coherence-proof`  
**Main tip before branch:** `baffc0b`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-285_live-staged-atlas-coherence-proof-audit.md` (GO)

## Summary

Added opt-in `live_network` pytest proof that runs the single-command staged orchestrator on a
temp DB, exports a private atlas snapshot via `export-atlas-snapshot` (without `--fixture-mode`),
and audits contract coherence (`validate_atlas_snapshot`, private-field scan, minimum graph
thresholds). Layer-3 preflight skips with machine-readable `unsuitable_live_artifact` when live
OpenAlex fetch succeeds but mock-spine marker phrases are absent.

## Scope

**In:** New test module + coherence audit helper; ticket queue/report updates.

**Out:** CI enforcement, public export/site, schema migrations, live Ollama, `atlas_snapshot_builder` production changes.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_live_staged_atlas_snapshot_coherence.py` | Live orchestrator → atlas export coherence proof |
| `tickets/ticket-285.json` | Status `done` |
| `tickets/ticket-286.json` | Seeded follow-on README cross-link |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Opt-in `live_network` pytest: staged spine + private atlas export + coherence assertions | **PASS** — test module + env gate unit test |
| Coherence audit documents thresholds and skip reasons | **PASS** — table below + `unsuitable_live_artifact` skip JSON |
| Default pytest and golden unchanged | **PASS** — 142 golden, 736 full (31 deselected) |
| No public export or public-site changes | **PASS** |

## Coherence audit fields

| Field | Pass criterion | Operator run (2026-06-16) |
|-------|----------------|---------------------------|
| `cards` | `>= 1` | Skipped at preflight (`unsuitable_live_artifact`) |
| `nodes` | `>= 1` | Skipped at preflight |
| `edges` | `>= 1` or skip with reason | Skipped at preflight |
| `follow_up_questions` | informational (may be 0) | n/a — preflight skip |
| `runs` | `>= 1` | n/a — preflight skip |
| Private-field scan | zero violations | n/a — preflight skip |
| Contract validation | pydantic pass | n/a — preflight skip |

Operator `live_network` run on this machine skipped honestly: live OpenAlex candidates fetched
successfully but none contained checksum-pinned mock marker phrases (`human-ai co-creativity`,
`songwriting`). This matches ticket-234 proof-layer semantics — not a regression.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -q
# 1 passed, 1 deselected

python -m pytest tests/golden -q
# 142 passed

python -m pytest -q
# 736 passed, 31 deselected

# Operator opt-in (may skip with unsuitable_live_artifact):
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
# 1 skipped (unsuitable_live_artifact on 2026-06-16 operator run)
```

Safety audit not required — temp DB/private JSON only; no public export or site changes.

## Manual CLI verification

Not performed separately; proof is encapsulated in the pytest module per pre-ticket audit hardened scope.

## Spec deviations

None.

## Merge to main

Merge commit: `4472c33`

## Recommended next ticket

**ticket-286** — README operator quickstart cross-link for live staged atlas snapshot coherence proof.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
