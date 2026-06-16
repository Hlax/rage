---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: high
ticket: ticket-285
category: Phase 3 / live research proof / Research Atlas validation
---

# Pre-Ticket Audit: ticket-285 Live Staged Atlas Snapshot Coherence Proof

## Verdict: **GO** (operator opt-in `live_network` pytest only)

Adds an opt-in live staged spine proof that exports a **private** atlas snapshot from a
temp DB after real OpenAlex discover/fetch + mock-LLM upstream spine, then audits whether
the snapshot contains meaningful research graph data under the `atlas_snapshot_v0.1.0`
contract.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export | **No** | `export-atlas-snapshot` to temp path only; no `export-public` |
| Public site | **No** | No site or committed public JSON changes |
| Schema migrations | **No** | Temp DB via existing staged orchestrator |
| Theory / inference | **No** | Read-only atlas projection assertions |
| Live Ollama | **No** | `RGE_LLM_MODE=mock`; orchestrator forces mock LLM |
| Live network | **Yes** | Opt-in `live_network` marker; excluded from default pytest/CI |

## Hardened scope

### In scope

1. **New test module:** `tests/unit/test_live_staged_atlas_snapshot_coherence.py`
2. **Flow (mirror ticket-193 orchestrator pattern):**
   - Env: `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1`, `RGE_ALLOW_SOURCE_NETWORK=1`,
     `OPENALEX_MAILTO`, `RGE_LLM_MODE=mock`, temp `--db`, `--staging-dir`, `--output-dir`
   - `research run --fixture-mode --staged-spine` on temp paths
   - `research export-atlas-snapshot --out <tmp>/atlas_snapshot.json` (**not** `--fixture-mode`)
3. **Coherence assertions (minimum thresholds):**
   - `validate_atlas_snapshot(snapshot)` passes
   - `assert_no_private_fields(snapshot)` empty
   - `len(cards) >= 1`
   - `len(nodes) >= 1`
   - `len(edges) >= 1` when mock spine produced relationships (else document skip)
   - `schema_version == atlas_snapshot_v0.1.0`
4. **Skip path:** reuse `unsuitable_live_artifact` / proof-layer helpers when live fetch
   artifact is incompatible with mock spine — machine-readable skip JSON; **not** a failure
5. **Unit test:** env gate skips without opt-in (same pattern as orchestrator test)
6. **Agent report** with operator pytest command and coherence audit table

### Out of scope

- Production changes to `atlas_snapshot_builder` unless a minimal coherence helper is needed
  for test readability (prefer inline assertions in test)
- CI / default `pytest` collection of `live_network`
- Live Ollama per-step fallthrough flags
- Public atlas route or public-site UI
- `review_batch` persistence
- Rank-2 orchestrator variant (rank-1 only for v0 proof)

### Coherence audit fields (report table)

Document in agent report:

| Field | Pass criterion |
|-------|----------------|
| `cards` | `>= 1` |
| `nodes` | `>= 1` |
| `edges` | `>= 1` or skip with reason |
| `follow_up_questions` | informational (may be 0 on live) |
| `runs` | `>= 1` |
| Private-field scan | zero violations |
| Contract validation | pydantic pass |

## Safety

- Temp DB and temp atlas JSON only — no write under `apps/public-site/` or `data/exports/`
- No live LLM; mock fixtures after live ingest (existing staged orchestrator contract)
- OpenAlex network opt-in mirrors tickets 167–193 proofs
- Skip on `unsuitable_live_artifact` is honest non-regression, not a pass claim

## Operator verification command (post-implementation)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```

## Recommendation

**GO** — implement live staged atlas coherence proof test module; stop atlas-only
infrastructure streak; default mock CI unchanged.
