---
template_id: pre_ticket_audit
status: GO
date: 2026-06-18
risk_level: medium
ticket: ticket-328
category: Phase 3 / live research proof / Research Atlas layer-3
supersedes_note: Refreshes ticket-285 pre-audit after public atlas preview thread (320–326); no new live proof code in ticket-328 scope.
---

# Pre-Ticket Audit: ticket-328 Live Layer-3 Staged Atlas Snapshot Coherence (refresh)

## Verdict: **GO** (existing operator opt-in proof; docs-only follow-ons cleared)

Re-validates the **already-shipped** live layer-3 staged atlas coherence proof
(`tests/unit/test_live_staged_atlas_snapshot_coherence.py`, ticket-285) against the
**closed** mock staged-spine public preview thread (tickets 320–326). Confirms boundaries
before any medium-risk follow-on work.

## Milestone triggers

| Trigger | Applies to live layer-3 proof? | Mitigation |
|---------|-------------------------------|------------|
| Public export (`export-public`) | **No** | Private `export-atlas-snapshot` to temp path only |
| Public site / committed public JSON | **No** | Live proof writes **no** `apps/public-site/public/data/` files; public preview is mock-only via `scripts/refresh_atlas_preview_from_staged_spine.py` (320–326) |
| Schema migrations | **No** | Temp `--db` via staged orchestrator |
| Theory / inference | **No** | Atlas projection assertions only |
| Live Ollama | **No** | Orchestrator forces `RGE_LLM_MODE=mock` |
| Live network | **Yes** | `live_network` marker; excluded from default pytest/CI |

## Public JSON boundary (critical after 320–326)

| Surface | Data source | Live layer-3 may write? |
|---------|-------------|-------------------------|
| `/atlas-preview` committed JSON | Mock staged-spine script + curator (320–326) | **No** |
| `fixtures/atlas/atlas_snapshot_staged_spine_preview.json` | Same mock export (322, 325) | **No** |
| Operator temp atlas JSON | `export-atlas-snapshot` on temp DB (285) | **Yes** (gitignored/temp only) |

**Honest framing:** public preview proves **mock** staged-spine shape for the static site.
Live layer-3 proof validates **private** atlas export after real OpenAlex discover/fetch;
skip with `unsuitable_live_artifact` when catalog text lacks mock-spine markers — **not**
a public preview regression.

## Env gates (operator-only)

| Variable | Required | Purpose |
|----------|----------|---------|
| `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1` | Yes | Staged orchestrator on temp `--db` |
| `RGE_ALLOW_SOURCE_NETWORK=1` | Yes | Live OpenAlex discover + fetch |
| `OPENALEX_MAILTO` | Yes | OpenAlex polite pool |
| `RGE_LLM_MODE=mock` | Yes | Mock LLM upstream (orchestrator-enforced) |
| `RGE_ALLOW_LIVE_LLM=1` | **No** | Not used; per-step live Ollama is separate surface |

## Skip semantics (machine-readable; not failures)

| Skip reason | When | Regression? |
|-------------|------|-------------|
| `unsuitable_live_artifact` | Layer-3 preflight: live fetch succeeds but artifacts lack `MOCK_STAGED_ARTIFACT_MARKERS` (`human-ai co-creativity`, `songwriting`) | **No** — catalog mismatch |
| Missing `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR` | Env gate | **No** — opt-in |
| Missing `RGE_ALLOW_SOURCE_NETWORK` / `OPENALEX_MAILTO` | Env gate | **No** — opt-in |
| `no_relationship_edges_in_atlas` | Orchestrator completed; atlas has cards/nodes/runs but zero edges | **No** — honest partial coherence |

Preflight: `_preflight_mock_spine_compatible` → `require_mock_spine_compatible_fetch_or_skip`
in `tests/unit/live_staged_proof_layers.py`.

## Existing proof flow (ticket-285; unchanged)

1. Layer-3 preflight on throwaway probe DB
2. `research run --fixture-mode --staged-spine` on temp `--db` (mock LLM)
3. `export-atlas-snapshot` **without** `--fixture-mode` → temp `atlas_snapshot.json`
4. Assert: `validate_atlas_snapshot`, `assert_no_private_fields`, `cards/nodes/runs >= 1`, `edges >= 1` or skip

Operator command (documented in README Operator Quickstart):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```

## Hardened scope for allowed follow-on tickets (post-GO)

### Cleared (low risk)

1. **README boundary cross-link** — explicit note that live layer-3 private atlas proof does
   **not** refresh `/atlas-preview` or `fixtures/atlas/` (ticket-329 candidate).
2. **Orphan `agent_reports` hygiene** — delete/supersede ticket-308 orphan file.

### Requires separate pre-ticket audit (NOT cleared by this report)

1. **Relaxing `MOCK_STAGED_ARTIFACT_MARKERS` or layer-3 preflight** — high scrutiny; changes skip rate semantics.
2. **Publishing live atlas export to public site or `fixtures/atlas/`** — public boundary milestone; new pre-ticket audit required.
3. **CI/default pytest collection of `live_network`** — live smoke constraint change.
4. **Live Ollama on staged orchestrator** — closed surface; separate per-step proofs only.

## Safety checklist

| Check | Status |
|-------|--------|
| No `export-public` in live layer-3 path | **PASS** |
| No public-site writes from live proof | **PASS** |
| Default pytest mock-only | **PASS** |
| Private-field scan on exported snapshot | **PASS** (test asserts) |
| Mock golden gate unaffected | **PASS** — 144 golden, 800 pytest |

## Recommendation

| Action | Verdict |
|--------|---------|
| Re-run ticket-285 operator proof (opt-in) | **GO** — honest skip or pass |
| Docs-only follow-on (README boundary) | **GO** — ticket-329 |
| Marker relaxation / public JSON from live proof | **NO-GO** without new audit |
| Implement ticket-328 (this audit) | **DONE** by this report |
