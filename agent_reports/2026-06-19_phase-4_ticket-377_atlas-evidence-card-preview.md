# Packet 5 Follow-on: Atlas Evidence Card Preview + Safety Audit

Date: 2026-06-19
Branch: `phase-4/packets-002-004-evidence-quality-extraction`
Decision: **GO**

## Delivered

- `evidence_cards_preview[]` on `atlas_snapshot_v0.1.0` (contract field in `atlas_snapshot_v0.py`)
- `build_atlas_evidence_cards_preview()` projects atlas-safe previews from accepted quote-backed claims
- `audit_atlas_evidence_cards_preview()` / `audit_snapshot_evidence_cards_preview()` fail closed on quote/claim/private keys
- `build_atlas_snapshot_from_db()` embeds previews and runs existing `assert_no_private_fields` scan
- `safety_auditor` secrets audit scans `atlas_snapshot_preview.json` evidence card previews
- `atlas_preview_curator.validate_public_preview_snapshot()` audits evidence card previews
- Updated committed fixture `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json`
- Tests: `tests/unit/test_atlas_evidence_cards_preview.py`

## Safety boundary

- **No change** to `export-public` allowlist or `public_cards.json` shape
- Previews contain: summary, badges (source_type, evidence_type, stance, maturity, asset_tags, confidence), concepts, scope — **no quote, no claim_id, no raw text**
- Operator-private `evidence_cards` with full quotes remain in `export-evidence-cards` only

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_evidence_cards_preview.py tests/unit/test_atlas_snapshot_builder.py tests/golden/test_23_safety_audit_gate.py
python -m rge.cli verify --skip-site
```

**Result (2026-06-19):** `verify --skip-site` **PASS** — 158 golden, 954 pytest, safety audit full.

## Closeout fixes

- `list_top_evidence_cards` now uses `ORDER BY id ASC` so `evidence_cards_preview` order is stable across fixture runs (wall-clock second boundaries during ingest no longer reorder previews).
- Regenerated `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` via `scripts/regenerate_atlas_creativity_fixture.py` (byte-stable with `export-atlas-snapshot --fixture-mode`).

## Next slice

Packet 6: `ingest-webpage` CLI wiring `web_source_adapter` → chunk ingest → quote-first extract.
