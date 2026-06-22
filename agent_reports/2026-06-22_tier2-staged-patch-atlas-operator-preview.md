# Tier 2 Staged Patch Atlas Operator Preview

**Date:** 2026-06-22  
**Verdict:** GO  
**Phase:** Autonomy / Tier 2 operator visibility

## Summary

Exposed the latest Tier 2 patch staging bundle and diff-quality verdict in Atlas via a public-safe operator artifact and `/atlas-preview` panel. Operators can inspect validation verdict, risk class, line stats, safety audit requirement, next action, and top validation reasons without raw diffs or file contents.

## Artifact

**Path:** `apps/public-site/public/data/atlas_tier2_patch_staging_latest.json`  
**Schema:** `atlas_tier2_patch_staging_v0.1.0`

| Field | Description |
|-------|-------------|
| `bundle_schema_version` | Source bundle schema (`tier2_patch_bundle_v0.1.0`) |
| `draft_ticket_label` / `draft_ticket_path_summary` | Scrubbed draft reference (basename + relative path) |
| `instruction_packet_label` / `instruction_packet_path_summary` | Scrubbed packet reference |
| `branch_name` | Intended Tier 2 branch |
| `validation_verdict` | GO / PARTIAL / NO-GO / PENDING / UNKNOWN |
| `risk_class` | low / medium / high |
| `changed_file_count` | File count from diff summary |
| `lines_added` / `lines_removed` | Aggregate line stats |
| `safety_audit_required` | Public-surface touch flag |
| `test_plan_count` | Number of draft test commands |
| `validation_reasons` | Capped (5), scrubbed gate messages |
| `next_recommended_action` | Operator next step label |
| `apply_ready` / `stop_state` | GO apply vs PARTIAL/NO-GO fix flags |
| `preview_freshness` | fresh / stale / missing |
| `generated_at` | Bundle timestamp |
| `updated_at` | Preview sync timestamp |

## Scrubbed / private boundary

**Not exposed:** raw diff, raw file contents, secrets, `.env.local`, raw prompts, absolute paths, private notes, operator ledger content.

Validation reasons are redacted for Windows/Unix absolute paths, secret-like tokens, and private-field key names. Full artifact passes `assert_no_private_fields` before write.

## CLI

```powershell
python scripts/refresh_tier2_patch_staging_preview.py --latest --sync-public
python scripts/refresh_tier2_patch_staging_preview.py --bundle PATH --sync-public
python scripts/refresh_tier2_patch_staging_preview.py --latest --dry-run
```

Fails closed when no bundle exists or bundle schema is invalid.

## Atlas preview panel

`/atlas-preview` section **Tier 2 patch staging (operator panel)** (`#tier2-patch-staging-panel`) shows:

- Validation verdict, risk class, changed file count
- Lines added/removed, safety audit requirement
- Preview freshness, next recommended action
- Draft/branch/packet summaries and top validation reasons
- Apply-ready vs stop/fix state for GO vs PARTIAL/NO-GO bundles

## Operator loop behavior

When latest bundle mtime is newer than the public preview artifact:

- `tier2_patch_staging_preview_refresh_recommended` → `refresh_tier2_patch_staging_preview` (safe_autonomous)
- Priority: after validation, before apply/commit recommendations

PARTIAL/NO-GO bundles surface `stop_state: true` and `fix_staged_patch*` next actions in Atlas.

## Tests run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_tier2_patch_staging_preview.py -q
python -m pytest tests/unit/test_safety_auditor_atlas_preview.py -q
python -m pytest tests/golden/test_12_public_site_static_render.py -q
```

**Result:** 29 tests passed (11 new preview tests).

## Safety audit

```powershell
python -m rge.modules.safety_auditor --audit full
```

**Result:** pass (2026-06-22T18:59:43Z). `atlas_tier2_patch_staging_latest.json` included in secrets scan list.

## Public-site build

```powershell
cd apps/public-site && npm run build
```

**Result:** pass (Next.js 15 static export).

## What remains blocked

- Push, merge, publish, canonical promotion (unchanged)
- Raw diff / file contents in public artifact (by design)
- Auto-apply/commit from Atlas preview (read-only panel)

## Next recommended packets

1. **Autocycle execute-safe patch staging hook** — optional stage+validate+preview refresh in execute-safe
2. **Auto-sync preview after patch bundle write** — refresh Atlas preview when staging completes with GO/PARTIAL/NO-GO
3. **Instruction packet auto expected_files inference** — reduce path-scope PARTIAL verdicts upstream

## Files touched

- `rge/modules/tier2_patch_staging_preview.py` (new)
- `rge/modules/tier2_patch_staging.py` (`discover_latest_patch_bundle`)
- `scripts/refresh_tier2_patch_staging_preview.py` (new)
- `apps/public-site/public/data/atlas_tier2_patch_staging_latest.json` (new)
- `apps/public-site/lib/atlasPreview.ts`
- `apps/public-site/app/atlas-preview/page.tsx`
- `rge/modules/safety_auditor.py`
- `rge/modules/operator_loop.py`
- `rge/modules/operator_autocycle.py`
- `rge/modules/release_governor.py`
- `tests/unit/test_tier2_patch_staging_preview.py` (new)
- `tests/unit/test_safety_auditor_atlas_preview.py`
- `tests/golden/test_12_public_site_static_render.py`
