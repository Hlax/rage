# Internal MVP Launch Checkpoint v0 (ticket-388)

**Date:** 2026-06-23  
**Repo:** `main` @ `c5badf0` (aligned with `origin/main`)  
**Hardening pass:** launch-candidate verification with existing GO product proof artifact  
**Decision:** **Internal MVP launch candidate — GO with documented non-launch blockers**

## Executive summary

The Research Graph Engine is cleared as an **internal MVP launch candidate** on mock-first
operator rails. A local `researcher_product_proof_latest.json` artifact reports
`product_verdict: GO` with mock-only synthesis, passing safety audit, and visible public atlas
preview fixtures. Verify, operator loop plan, and operator autocycle all recognize the artifact;
none recommend or block on `run_researcher_product_proof`.

This is **not** a public or paid-cloud launch. Live OpenAI, unattended paid execution, and
live arbitrary-source research remain explicitly gated.

---

## Repo state (pre-check)

```text
## main...origin/main
?? agent_reports/2026-06-23_principal-audit-post-ticket-379.md
```

| Check | Result |
|-------|--------|
| Branch | `main` @ `c5badf0` |
| `origin/main` | Aligned |
| Working tree | Clean except one untracked legacy audit report |

Recent commits:

```text
c5badf0 docs: record main merge hash for ticket-386
30da5f8 Merge branch 'phase-3/ticket-386-readme-researcher-product-proof-crosslink'
d8fcd3c Implement ticket-386 README researcher product proof cross-link
1c2c223 docs: record main merge hash for ticket-384
```

---

## Product proof artifact summary

**Path:** `data/reports/researcher_product_proof_latest.json` (gitignored)

| Field | Value | Required | OK |
|-------|-------|----------|-----|
| `product_verdict` | `GO` | GO | ✓ |
| `mock_llm_only` | `true` | true | ✓ |
| `live_openai_used` | `false` | false | ✓ |
| `source_count` | `3` | present | ✓ |
| `claim_count` | `2` | present | ✓ |
| `evidence_count` | `2` | present | ✓ |
| `synthesis.status` | `completed` | completed | ✓ |
| `synthesis.no_accepted_graph_writes` | `true` | true | ✓ |
| `benchmark.reports_per_hour_estimate` | `2300037.309` | present | ✓ |
| `benchmark.cloud_call_made_any` | `false` | false | ✓ |
| `safety_audit.status` | `pass` | pass | ✓ |
| `atlas_preview.public_preview_visible` | `true` | true | ✓ |

Scratch work dir: `data/tmp/researcher_product_proof_work/`  
Proof bundle: `fixture_staged_rank1`, `usable_output: true`  
Atlas preview: `snap_staged_fixture_preview_v0_001`, 2 clusters

---

## Status surfaces

Environment: `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0`

### `python -m rge.cli verify --skip-site`

| Check | Result |
|-------|--------|
| Overall status | **pass** (exit 0) |
| Golden tests | 165 passed |
| Full pytest | 1354 passed, 49 deselected |
| Safety audit (embedded) | pass |
| `researcher_product_proof_status.product_verdict` | **GO** |
| `product_proof_recommended` | **false** |

### `python -m rge.modules.operator_loop --mode plan`

| Check | Result |
|-------|--------|
| `researcher_product_proof_status.product_verdict` | **GO** |
| `product_proof_recommended` | **false** |
| `next_recommended_action` | `begin_ticket_implementation` (ticket-387 docs) — **not** `run_researcher_product_proof` |

Note: `drift_warning` still lists ticket-class cadence text (*"No product-risk or live-research
proof advanced in the last 3 completed tickets"*). Product-proof recommendation is **not**
driven by missing artifact when GO artifact exists.

### `python -m rge.modules.operator_autocycle --mode plan`

| Check | Result |
|-------|--------|
| `researcher_product_proof_status.product_verdict` | **GO** |
| `product_proof_recommended` | **false** (top-level and per-cycle) |
| `operator_action_blocked_automation: run_researcher_product_proof` | **absent** |
| Exit code | 1 (`status: stopped` — dirty-tree / review-gated ticket gate; not product proof) |

---

## Acceptance criteria

| Criterion | Result |
|-----------|--------|
| verify reports `product_verdict: GO` | **PASS** |
| operator_loop does not recommend product proof for missing artifact | **PASS** |
| autocycle does not block on `run_researcher_product_proof` | **PASS** |
| No live LLM/API calls during checks | **PASS** (mock env only) |
| No accepted graph writes from synthesis | **PASS** (`no_accepted_graph_writes: true` in artifact) |
| Public preview fixture/safe | **PASS** |
| Safety audit passes | **PASS** |

**Surface wiring fix required:** None — all surfaces recognize GO artifact.

---

## Tests run (hardening pass)

| Command | Result |
|---------|--------|
| `python -m rge.cli verify --skip-site` | **pass** |
| `python -m pytest tests/golden -q` | **165 passed** |
| `python -m rge.modules.safety_auditor --audit full` | **pass** |
| `python -m rge.modules.operator_loop --mode plan` | exit 0 |
| `python -m rge.modules.operator_autocycle --mode plan` | exit 1 (non-product-proof stop) |

---

## Drift clearance

| Drift type | Cleared? |
|------------|----------|
| Product proof missing artifact | **Yes** — GO artifact on disk |
| `product_proof_recommended` | **false** on verify / plan / autocycle |
| Principal-audit ticket-class warning | **Partial** — text may still appear; does not trigger product proof action |
| Arbitrary-source proof bundle | **Satisfied** (`proof_artifact_satisfied: true`) |

---

## Internal MVP launch candidate declaration

**Status: INTERNAL MVP LAUNCH CANDIDATE (mock-first operator profile)**

Qualified for internal operator use when:

- Mock LLM mode is enforced for verification and product proof
- Safety audit passes before any public export
- Public site consumes committed fixture preview JSON only
- Live cloud and live Ollama paths remain opt-in with explicit env gates

### Launch command sequence (operator)

```powershell
# 1. Environment — mock-first internal profile
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"

# 2. Verification gate
python -m rge.cli verify --skip-site

# 3. Product proof (refresh or first-time; scratch paths only)
python -m rge.cli prove-researcher-product `
  --work-dir data/tmp/researcher_product_proof_work `
  --artifact-out data/reports/researcher_product_proof_latest.json `
  --benchmark-runs 25

# 4. Confirm GO artifact
Get-Content data/reports/researcher_product_proof_latest.json | Select-String product_verdict

# 5. Operator plan (should not recommend product proof)
python -m rge.modules.operator_loop --mode plan

# 6. Safety audit before any public export
python -m rge.modules.safety_auditor --audit full

# 7. Public site (fixture preview; optional for internal API-only use)
cd apps/public-site; npm run build
```

### Artifact paths (launch record)

| Path | Role |
|------|------|
| `data/reports/researcher_product_proof_latest.json` | GO product proof ledger |
| `data/tmp/researcher_product_proof_work/` | Scratch DB, staged sources, synthesis output |
| `data/reports/operator_proof_bundle/operator_proof_bundle.json` | Arbitrary-source mock proof (satisfied) |
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Committed public atlas preview fixture |
| `apps/public-site/public/data/atlas_coherence_preview.json` | Committed coherence fixture |

---

## Remaining non-launch blockers (explicit)

| Blocker | Status |
|---------|--------|
| Live OpenAI synthesis | Gated — `RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP` + keys required; not default |
| Public site live graph | **Fixture preview only** — not live research graph export |
| Unattended paid cloud execution | **Blocked** — no autocycle publish/merge; cost caps on live profiles |
| Bare `research run --topic --domain` | **not_implemented** without fixture/staged flags |
| Full live arbitrary-source MVP | Partial — operator pytest proofs only, not CI |
| Autocycle unattended implementation | **Blocked** — review-gated tickets; dirty-tree stops |

---

## Recommended next product ticket (post-launch)

**ticket-389 (proposed)** — Operator one-time live staged orchestrator verification checklist run
(temp DB only; `pytest -m live_network`; documents pass/skip JSON). Advances live-research
maturity without new engine features or safety gate changes.

Queued hygiene (non-product): **ticket-387** — AGENTS.md researcher product proof cross-link.

---

## Scope compliance (ticket-388)

- No new research features implemented
- No safety gates loosened
- No CLI or export code changes
- Report-only launch checkpoint
