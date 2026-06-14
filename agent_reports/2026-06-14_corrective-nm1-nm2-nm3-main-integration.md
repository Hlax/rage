---
template_id: integration_report
status: done
date: 2026-06-14
---

# Corrective NM-1/NM-2/NM-3 Main Integration

## Branch merged

`phase-2/corrective-nm1-nm2-nm3-audit-driven` → `main`

**Merge commit:** `4a62c99`

**Included commits:**
- `e61d46b` — NM-1: `extract-claims-live` + live proof
- `e3d13df` — NM-2: maturity relabel + ticket-111 superseded
- `ad4d037` — NM-3: value-based cadence gate

## Pre-merge verification (corrective branch)

| Check | Result |
|-------|--------|
| Golden tests | 140 passed |
| Full pytest | 394 passed, 6 deselected |
| Safety audit | pass |
| `principal_audit_gate --next-ticket ticket-111` | `drift_warning` + `recommended_override` emitted |

## Post-merge verification (main @ 4a62c99)

| Check | Result |
|-------|--------|
| Golden tests | 140 passed |
| Full pytest | 394 passed, 6 deselected |
| Safety audit | pass |

## Push

`origin/main` updated: `c60f4a2..4a62c99`

## Ollama / Qwen check

| Item | Value |
|------|-------|
| Ollama installed | Yes — `C:\Users\guestt\AppData\Local\Programs\Ollama\ollama.exe` |
| Version | `0.21.0` |
| Qwen models found | `qwen2.5:7b`, `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `qwen2.5-coder:32b` |
| Model pulled this pass | **No** — `qwen2.5:7b` already present |
| `model-health` | pass (`reachable: true`, `model_available: true`, `configured_model: qwen2.5:7b`) |

## ticket-111

**Superseded** — folded into NM-2 corrective doc pass. Do not implement.

## Next ticket recommendation

**ticket-112** — Arbitrary manual text live extraction fall-through (NM-4).
Pre-ticket audit required before implementation.
