# Agent Report: ticket-308 — export-atlas-snapshot coherence preview sidecar CLI flag

**Date:** 2026-06-17  
**Ticket:** ticket-308  
**Branch:** `phase-3/ticket-308-export-coherence-preview-cli`  
**Main tip before branch:** `238ad07`  
**Audit gate:** Not required — `risk_level: low`; CLI-only; no public site or export-public changes.

## Summary

Added optional `--coherence-preview-out PATH` to `export-atlas-snapshot`. When set, the
CLI writes the public-site `atlas_coherence_preview.json` sidecar via ticket-307 export
helpers. Unit test covers fixture-mode happy path on temp paths.

## Scope

**In:**

- `_cmd_export_atlas_snapshot` passes `coherence_preview_path` to export helper
- Argparse `--coherence-preview-out` on `export-atlas-snapshot`
- CLI unit test in `test_atlas_coherence_preview_sync.py`

**Out:**

- Public site changes
- `export-public` changes
- Schema migrations

## Changed files

| File | Change |
|------|--------|
| `rge/cli.py` | `--coherence-preview-out` flag + handler wiring |
| `tests/unit/test_atlas_coherence_preview_sync.py` | CLI happy-path test |
| `tickets/ticket-308.json` | Status `done` |
| `tickets/ticket-309.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| `export-atlas-snapshot` accepts `--coherence-preview-out` | **PASS** |
| CLI writes coherence preview JSON when flag set | **PASS** |
| Unit test covers CLI happy path | **PASS** |
| Golden + full pytest pass | **PASS** — 144 golden, 789 full (+1) |
| No `export-public` semantic changes | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_coherence_preview_sync.py -q   # 7 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 789 passed, 33 deselected
```

Safety audit not required — operator CLI flag only; no public export or site surface changes.

## Manual CLI verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli export-atlas-snapshot --help
# shows --coherence-preview-out
```

Fixture-mode export with sidecar exercised via unit test on temp DB paths.

## Spec deviations

None.

## Recommended next ticket

**ticket-309** — Atlas preview nodes section links to `/concepts/[slug]` when slug exists
(product-facing; pre-ticket audit required).

## Suggested next prompt

```txt
/rge-principal-audit
```

(cadence advisory: 2 done tickets since pre-ticket-307 — monitor before more public-site work)

## Merge to main

_(pending)_
