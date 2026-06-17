# Agent Report: ticket-307 — Atlas coherence preview JSON sync from snapshot export

**Date:** 2026-06-17  
**Ticket:** ticket-307  
**Branch:** `phase-3/ticket-307-atlas-coherence-preview-sync`  
**Main tip before branch:** `9975b1e`  
**Audit gate:** Satisfied — `agent_reports/2026-06-17_pre-ticket-307_atlas-coherence-preview-sync-audit.md` (GO, 2026-06-17)

## Summary

Codified `build_atlas_coherence_preview()` and `export_atlas_coherence_preview_to_path()`
so `atlas_coherence_preview.json` is derived from atlas snapshot export (inline
`coherence_summary` + coherence report population counts). Optional
`coherence_preview_path` on `export_atlas_snapshot_to_path` writes the sidecar.
Committed preview JSON regenerated via export pipeline. No `export-public` changes.

## Scope

**In:**

- `build_atlas_coherence_preview()` + export helpers in `atlas_snapshot_builder.py`
- Optional `coherence_preview_path` on snapshot export
- Regenerated `atlas_coherence_preview.json` (byte-stable via export)
- Unit tests

**Out:**

- Removing separate coherence preview file
- `export-public` changes
- Schema migrations
- CLI flag (deferred)

## Changed files

| File | Change |
|------|--------|
| `rge/modules/atlas_snapshot_builder.py` | Coherence preview build/export + sidecar param |
| `apps/public-site/public/data/atlas_coherence_preview.json` | Regenerated via export |
| `tests/unit/test_atlas_coherence_preview_sync.py` | 6 unit tests (new) |
| `agent_reports/2026-06-17_pre-ticket-307_atlas-coherence-preview-sync-audit.md` | Pre-ticket audit |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Pre-ticket audit written | **PASS** |
| Fixture-mode export derives preview from snapshot + population | **PASS** |
| Committed coherence preview matches export | **PASS** |
| No `export-public` semantic changes | **PASS** |
| Golden + full pytest + safety audit | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_coherence_preview_sync.py -q   # 6 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 788 passed, 33 deselected
python -m rge.modules.safety_auditor --audit full                     # pass
```

## Manual CLI verification

Fixture-mode `export_atlas_snapshot_to_path(..., coherence_preview_path=...)` produces
preview JSON matching committed file byte-for-byte.

## Spec deviations

None.

## Recommended next ticket

**ticket-308** — `export-atlas-snapshot --coherence-preview-out` CLI flag wiring
(operator convenience; low risk).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: `e4e50a9`
