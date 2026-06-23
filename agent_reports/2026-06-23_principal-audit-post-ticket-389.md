# Principal Audit — Post-ticket-389 Launch Hygiene Checkpoint

**Date:** 2026-06-23  
**Branch audited:** `main` (pre-push hotfix)  
**Decision:** **GO with caveats** — CI blocker fixed; mock-only gates green; internal MVP launch candidate holds

## Summary

Principal audit after tickets **385–389** (launch docs, product proof cross-links,
orchestrator checklist). Cadence was **overdue** (5 done since post-ticket-384).

**Hotfix included in this push:** `test_run_spec_produces_artifact` failed in CI because
`live_http_gates_missing` exported the literal key `OPENAI_API_KEY`, which violates
`assert_no_private_fields` (`api_key` substring). Fixed by remapping credential gate keys
to `operator_cloud_credential_env` in public spec artifacts only.

## Checkpoint status

| Field | Pre-audit | Post-audit |
|-------|-----------|------------|
| `status` | `overdue` | **satisfied** (this report) |
| Done since ticket-384 | 385–389 (5 tickets) | cadence reset |
| `implementation_gate` | satisfied | satisfied |

## Repo state

| Check | Result |
|-------|--------|
| `main` / `origin/main` | Aligned before hotfix commit |
| Working tree | Hotfix on `openai_synthesis_adapter_spec.py` |
| Product proof artifact | `product_verdict: GO` on disk |

## Verification (mock-only)

Environment: `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0`

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_openai_synthesis_adapter_spec.py::test_run_spec_produces_artifact` | **1 passed** (post-fix) |
| `pytest tests/golden -q` | **165 passed** |
| `pytest -q` | **1354 passed**, 49 deselected |
| `pytest --collect-only -q` \| `tests/smoke/` | **Not collected** (only blocked/opt-in smoke references) |
| `safety_auditor --audit full` | **pass** |
| `cd apps/public-site && npm run build` | **pass** |

GT22: 16 required golden areas; inventory complete. CI: `.github/workflows/golden-gate.yml` present.

## Safety boundaries

| Area | Finding |
|------|---------|
| Public write routes | Safety audit **pass** |
| Secret keys in exports | Hotfix remaps `OPENAI_API_KEY` gate key in spec artifacts |
| Live LLM default | Mock-only in golden/CI |
| Public site | Static build **pass**; fixture preview |

## Launch / maturity (post ticket-388)

| Layer | Status |
|-------|--------|
| Internal MVP launch candidate | **Declared** (ticket-388) |
| Researcher product proof GO | On disk; surfaces clear |
| Live orchestrator checklist | Documented (ticket-389); operator retry when OpenAlex artifacts suitable |
| Live OpenAI / paid cloud | Gated opt-in only |

## Hotfix detail

**File:** `rge/modules/openai_synthesis_adapter_spec.py`  
**Change:** `_public_safe_missing_gates()` remaps `OPENAI_API_KEY` / `RGE_OPENAI_API_KEY` to
`operator_cloud_credential_env` before `assert_no_private_fields` on spec artifacts.  
**Scope:** Public artifact export only; internal gate error messages unchanged.

## Recommended next tickets

| Priority | Ticket | Rationale |
|----------|--------|-----------|
| 1 | **ticket-391** (seed) | Operator live orchestrator retry on network-unrestricted machine |
| 2 | Docs hygiene | None blocking — launch docs complete |

## Recommendation

| Audience | Guidance |
|----------|----------|
| Builder | **GO** — CI should pass after hotfix push |
| Operator | Retry live orchestrator checklist when OpenAlex returns fixture-compatible artifacts |
| Cadence | **Reset** by this report |

## Stop

Audit complete. No feature tickets implemented.
