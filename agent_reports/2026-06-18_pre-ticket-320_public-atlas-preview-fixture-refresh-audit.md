---
template_id: pre_ticket_audit
status: GO
date: 2026-06-18
risk_level: medium
ticket: ticket-320
category: Phase 3 / public atlas preview
---

# Pre-Ticket Audit: ticket-320 Public Atlas Preview Fixture Refresh

## Verdict: **GO** (committed static JSON refresh only; no export-public; pre-commit safety gates)

Refresh `/atlas-preview` committed fixtures from a **mock staged-spine** `export-atlas-snapshot` so the public
read-only surface reflects operator proof shape (multi-run staged spine, 2 rank clusters, populated follow-ups)
without widening `export-public` or adding API routes.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export (`export-public`, `card_exporter`) | **No** | Use private `export-atlas-snapshot` + manual curation to preview paths only |
| Public site / committed public JSON | **Yes** | Pre-commit `validate_atlas_snapshot` + `assert_no_private_fields`; safety auditor full pass |
| Schema migrations | **No** | Atlas contract v0.1.0 unchanged |
| Theory / inference generation | **No** | Snapshot projection only |
| Live Ollama | **No** | Mock staged orchestrator on temp `--db` |

## Current vs target

| Field | Current preview (`atlas_snapshot_preview.json`) | Target (staged spine export) |
|-------|--------------------------------------------------|------------------------------|
| `snapshot_id` | `snap_creativity_fixture_v0_001` | New deterministic operator snapshot id |
| `runs[]` | 1 golden MVP run | ≥3 staged rank runs |
| `clusters[]` | 1 golden cluster | ≥2 rank-scoped staged clusters |
| `follow_up_questions[]` | 6 GT16 (`queued`/`parked`) | ≥1 staged follow-up visible in UI |
| `coherence_summary` | pass (fixture) | pass or partial (document honestly) |
| Data source | Golden fixture-mode DB shape | Mock staged orchestrator temp DB |

**Path correction:** ticket JSON lists `atlas_snapshot.json`; committed files are
`apps/public-site/public/data/atlas_snapshot_preview.json` and `atlas_coherence_preview.json`.

## Hardened scope

### In scope

1. **Operator generation (mock, temp DB only):**
   - Run staged fixture orchestrator (`research run --fixture-mode --staged-spine` or test harness equivalent)
   - `export-atlas-snapshot --db <temp> --topic "<operator topic>" --out <scratch.json>` (no `--fixture-mode` on export)
   - `atlas-coherence-report` → companion `atlas_coherence_preview.json` population block

2. **Curated public preview write:**
   - Copy curated snapshot + coherence summary into:
     - `apps/public-site/public/data/atlas_snapshot_preview.json`
     - `apps/public-site/public/data/atlas_coherence_preview.json`
   - Ensure `coherence_summary` inline on snapshot matches coherence JSON verdict
   - Set `preview_label` to staged-spine mock-safe wording (no live literature claims)

3. **Follow-up UI compatibility:**
   - `/atlas-preview` `QueuedFollowUps` shows only `status === 'queued'`
   - Staged atlas hook seeds `status: active` — **map to `queued` in curated preview JSON** (preferred) or minimally extend UI to treat `active` as queued; do **not** change research_queue DB semantics

4. **Safety gates before commit:**
   - `validate_atlas_snapshot(snapshot)`
   - `assert_no_private_fields(snapshot)` (no paths, prompts, raw source text, secrets)
   - `python -m rge.modules.safety_auditor --audit full` must pass after JSON update

5. **Tests:**
   - Add `tests/unit/test_public_atlas_preview_fixture.py`:
     - Loads committed preview JSON
     - Asserts `validate_atlas_snapshot`, private-field scan, `clusters.length >= 2`, `follow_up_questions.length >= 1`
     - Asserts staged run id prefix `run_staged_fixture_mode_spine` present in `runs[]` or `clusters[].run_id`
   - Existing GT12 atlas-preview static tests must remain green

6. **Optional thin helper (if needed):** `rge/modules/atlas_preview_curator.py` or script under `scripts/` to
   transform operator export → preview JSON (deterministic; no network). Keep scope minimal.

### Out of scope

- `export-public` or changes to `public_export_policy` beyond existing scans
- New Next.js API routes, fetches, or `process.env` secrets in build
- README-only documentation ticket
- Live OpenAlex layer-3 proof (`live_network`)
- Schema migrations
- Changing core `atlas_snapshot_builder` hooks (319 already closed follow-up/cluster paths)
- Card slug expansion on public site (preview may show atlas-only card ids without `/cards/[id]` links)

## Safety checklist

| Risk | Control |
|------|---------|
| Private DB paths in JSON | `assert_no_private_fields` + safety auditor secrets scan |
| Raw prompts / source text | Atlas contract + export policy (no `raw_text`, `chunk_id` leaks) |
| Accidental `export-public` | Operator workflow uses `export-atlas-snapshot` only; no `data/exports` commit |
| Overclaiming live research | `preview_label` + page copy must state mock/staged fixture provenance |

## Acceptance mapping

| Ticket criterion | Audit decision |
|------------------|----------------|
| Preview renders staged snapshot with clusters + follow-ups | **GO** — with `active`→`queued` curation for UI |
| `validate_atlas_snapshot` + private-field scan | **GO** — mandatory pre-commit |
| Public-site build; no write routes | **GO** |
| Pre-ticket audit | **Satisfied** — this report |

## Test plan (implementation)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_public_atlas_preview_fixture.py -q
python -m pytest tests/golden/test_12_public_site_static_render.py -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

## Recommendation

**GO** — smallest product-facing proof step: refresh committed atlas preview JSON from mock staged spine export.
Rollback = revert two JSON files + optional unit test only.
