# Agent Report: ticket-320 — Public atlas preview fixture refresh

**Date:** 2026-06-18  
**Ticket:** ticket-320  
**Branch:** `phase-3/ticket-320-public-atlas-preview-fixture-refresh`  
**Main tip before branch:** `e62d47b`  
**Audit gate:** `agent_reports/2026-06-18_pre-ticket-320_public-atlas-preview-fixture-refresh-audit.md` (GO)

## Summary

Refreshed committed `/atlas-preview` JSON from a mock staged-spine `export-atlas-snapshot`
(temp DB). Added `atlas_preview_curator` to map `active` follow-ups to `queued` for UI,
pin deterministic preview metadata, and validate before write. Operator regenerate script:
`scripts/refresh_atlas_preview_from_staged_spine.py`.

## Scope

**In:** Public preview JSON, curator module, unit tests, coherence sync test updates, regenerate script.

**Out:** `export-public`, live_network, schema migrations, README-only docs, new API routes.

## Changed files

| File | Change |
|------|--------|
| `apps/public-site/public/data/atlas_snapshot_preview.json` | Staged-spine snapshot (2 runs, 2 clusters, 1 follow-up) |
| `apps/public-site/public/data/atlas_coherence_preview.json` | Matching coherence preview |
| `rge/modules/atlas_preview_curator.py` | Curate + validate public preview fixtures |
| `scripts/refresh_atlas_preview_from_staged_spine.py` | Operator regenerate helper |
| `tests/unit/test_public_atlas_preview_fixture.py` | Committed fixture contract tests |
| `tests/unit/test_atlas_coherence_preview_sync.py` | Align committed sync with staged preview |
| `tickets/ticket-320.json` | Status `done` |
| `tickets/ticket-321.json` | Seeded atlas preview page copy refresh |
| `tickets/TICKET_QUEUE.md` | Queue update |
| `agent_reports/2026-06-18_*` | Audit artifacts (principal-319, pre-ticket-320) |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Preview fixture has clusters[] + follow_up_questions[] | **PASS** — 2 clusters, 1 queued follow-up |
| `validate_atlas_snapshot` + private-field scan | **PASS** — unit tests + export path |
| Public-site build; no write routes | **PASS** |
| Pre-ticket audit | **PASS** |

## Population (committed preview)

| Field | Value |
|-------|------:|
| `overall_coherence_verdict` | pass |
| runs | 2 (staged rank1/rank2) |
| clusters | 2 |
| follow_up_questions | 1 |
| cards | 2 |
| edges | 3 |
| nodes | 24 |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/refresh_atlas_preview_from_staged_spine.py
python -m pytest tests/unit/test_public_atlas_preview_fixture.py -q    # 5 passed
python -m pytest tests/golden/test_12_public_site_static_render.py -q    # pass (after build)
python -m pytest tests/golden -q                                         # 144 passed
python -m pytest -q                                                    # 798 passed
python -m rge.modules.safety_auditor --audit full                      # pass
cd apps/public-site && npm run build
```

## Spec deviations

- Ticket JSON listed `atlas_snapshot.json`; committed paths remain
  `atlas_snapshot_preview.json` / `atlas_coherence_preview.json` per pre-ticket audit.
- `fixtures/atlas/` unchanged; golden creativity fixture retained for contract tests.

## Recommended next ticket

**ticket-321** — Atlas preview page copy refresh (staged-spine labeling in static UI).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `648e3a5`. Pushed `origin/main`.
