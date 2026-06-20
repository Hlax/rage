# Tiny Atlas Connection Preview

- Date: 2026-06-20
- Verdict: **GO**
- Route: `/atlas-preview`
- Scope: smallest read-only, fixture-backed public-safe Atlas connection preview; no broad frontend refactor and no new automation.

## Summary

Added a text-first Tiny Atlas connection preview to the existing public-site Atlas route. The preview shows the path from research question and purpose tags through source health, evidence atoms, typed relationships, cluster metrics, trace details, readiness warnings, and the next recommended packet.

The data source is the new static JSON fixture `apps/public-site/public/data/tiny_atlas_connection_preview.json`, derived from the committed creativity Atlas fixture and acquisition audit report. It intentionally uses public-safe summaries/counts/reasons only.

## Changed Files

- `apps/public-site/app/atlas-preview/page.tsx`
- `apps/public-site/lib/atlasPreview.ts`
- `apps/public-site/public/data/tiny_atlas_connection_preview.json`
- `.gitignore`
- `rge/modules/safety_auditor.py`
- `tests/unit/test_tiny_atlas_connection_preview.py`
- `tests/unit/test_safety_auditor_atlas_preview.py`
- `tests/golden/test_12_public_site_static_render.py`

## UI Coverage

- Research question header: topic, purpose, asset affordance tags, readiness verdict.
- Source health panel: status counts, acquisition/parser notes, quality gate outcomes, blocked/dirty/failed reasons.
- Evidence cluster panel: maturity, synthesis readiness, relationship density, source diversity, orphan counts.
- Evidence atom cards: canonical atom text, maturity, stance counts, source count, purpose status, asset tags, why clustered/weak.
- Relationship view: supports, contradicts, qualifies, defines, and scope-difference edges with concept links and explanations.
- Evidence trace detail panel: public-safe source status, claim summary, atom/concept/relationship/cluster links, and connection explanation.
- Gaps / next move panel: blockers, graph warnings, readiness statuses, next recommended packet and reason.

## Public / Private Boundary

The preview remains static and read-only. It imports committed JSON and does not fetch from a local API, database, or agent service. The fixture excludes raw quote text, local paths, private row IDs, prompt fields, hidden notes, and unsafe evaluator detail.

The safety auditor now scans `tiny_atlas_connection_preview.json` alongside the existing Atlas preview JSON files.

## Readiness Findings

- Frontend readiness: **PARTIAL**. The route now makes the graph understandable from fixture data and build output is green.
- Graph observability: **GO for fixture debug**. A human can follow source/claim/atom/concept/relationship/cluster readiness without a graph visualization.
- Local model readiness: **PARTIAL**. Purpose gates and typed fixture traces are visible, but arbitrary live Ollama source runs remain unproven.
- Paid API readiness: **NO-GO**. No paid provider or escalation path exists.
- Automation readiness: **NO-GO**. Acquisition/parser and live-purpose enforcement blockers remain.

## Verification

- `npm run build` in `apps/public-site` -> pass.
- `python -m pytest tests/unit/test_tiny_atlas_connection_preview.py tests/unit/test_safety_auditor_atlas_preview.py tests/golden/test_12_public_site_static_render.py -q` -> pass, `21 passed`.
- `python -m rge.modules.safety_auditor --audit full` -> pass, `blocked_reasons=[]`; checked secrets includes `tiny_atlas_connection_preview.json`.

Manual inspection notes: static build generated `/atlas-preview`; targeted golden test verified the exported HTML contains the Tiny Atlas sections and next recommended packet. No screenshot was taken.

## Top Blockers

1. Relationship density is fixture-proven, not arbitrary live research proof.
2. Purpose gates are not yet enforced across every future live arbitrary-source path.
3. Acquisition/parser status is still partially report-derived rather than consistently persisted into source metadata.
4. Paid API and automation readiness remain NO-GO.

## Next 3 Recommended Packets

1. Live/Arbitrary Source Purpose Gate Enforcement.
2. Relationship Type Contract Formalization.
3. Source Health Persistence for Atlas Preview.

