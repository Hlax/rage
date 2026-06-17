---
template_id: audit_report
template_version: 1.0.0
status: current
date: 2026-06-17
phase: 3
checkpoint_before: ticket-300
---

# Pre-Ticket-300 Audit: Research Atlas Read-Only Public Preview v0

- Audit type: pre-ticket audit (public-site + public-facing data presentation)
- Date: 2026-06-17
- Baseline HEAD: `f3e8ad4` (`main`, synced with `origin/main`)
- Prior checkpoint: `agent_reports/2026-06-17_principal-audit-post-ticket-298.md`
- Trigger: ticket-300 (`risk_level: medium`; public-site milestone)

## Executive summary

**GO — implement ticket-300 with hardened scope below.**

Evidence DB atlas population is closed (294–298). A static, fixture-backed Atlas
preview page is the smallest product-facing step to evaluate whether the
`atlas_snapshot_v0.1.0` contract feels frontend-ready before wiring live operator
exports or graph visualization.

## Gate output

```json
{
  "status": "go",
  "implementation_gate": "satisfied",
  "pre_ticket_audit_required": true,
  "pre_ticket_audit_written": true,
  "principal_audit_cadence": "satisfied",
  "next_ticket_id": "ticket-300"
}
```

## Repo health (audit-time)

| Check | Verdict |
|-------|---------|
| `main` aligned with `origin/main` | **PASS** |
| Mock golden gate | **PASS** — 142 golden, 757 pytest (per post-ticket-298 audit) |
| Safety audit | **PASS** |
| Public site build | **PASS** |
| Cadence since principal audit | **PASS** — ticket-299 only since post-ticket-298 |

## Safety boundary checklist

| Area | Finding | Ticket-300 posture |
|------|---------|-------------------|
| Public write routes | None today | **No new write/ingest/agent routes** |
| API routes | None (`app/api` absent) | **No API routes** |
| Dynamic DB reads | Site uses static JSON imports | **Static JSON imports only** |
| Operator-private atlas | Gitignored `data/atlas/` | **Do not consume operator exports** |
| `export-public` semantics | Golden GT11 proven | **No changes to `export-public` or `card_exporter`** |
| Atlas private-field scan | `assert_no_private_fields` on export | **Use committed fixture already passing scan** |
| Live LLM | Mock in CI | **No live LLM** |
| Raw HTML / forms | GT00/GT12 forbid patterns | **Text-only React; no `dangerouslySetInnerHTML`, no forms** |

## Data source decision (hardened)

| Source | Approved? | Notes |
|--------|-----------|-------|
| `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` | **YES** | Byte-stable fixture-mode snapshot; `safety.public_safe: true`; used in ticket-292 pipeline |
| Derived coherence summary JSON | **YES** | Trimmed subset: `overall_coherence_verdict`, `population` counts, `preview_label` only |
| Operator gitignored atlas exports | **NO** | ticket-293 v298 paths stay operator-only |
| Live DB `export-atlas-snapshot` at build time | **NO** | No dynamic generation in public-site build |

Copy fixture → `apps/public-site/public/data/atlas_snapshot_preview.json` and commit a
matching `atlas_coherence_preview.json` derived from `build_atlas_coherence_report` on
that fixture. Document provenance in page copy (“fixture-mode preview”).

## Hardened implementation scope

**In:**

- New static route: `/atlas-preview` (`apps/public-site/app/atlas-preview/page.tsx`)
- `lib/atlasPreview.ts` — types + static import helpers (mirror `publicCards.ts` pattern)
- Committed preview JSON under `apps/public-site/public/data/` (fixture copy + coherence summary)
- Text-first sections:
  1. Research run summary (`root`, `runs[]`)
  2. Domains (`domains[]`)
  3. Cards (`cards[]`; optional link to existing `/cards/[id]` when IDs match public export)
  4. Nodes/edges summary (counts + concise list; no graph viz)
  5. Reports (`reports[]`)
  6. Follow-up questions (`follow_up_questions[]`; distinguish queued vs parked)
  7. Lineage / research trail (`runs[]` question lineage fields)
  8. Coherence status badge (`atlas_coherence_preview.json`)
- Footer link from home page to preview (read-only navigation only)
- Agent report with product verdict and section description

**Out:**

- `export-public` / `card_exporter` / `public_export_policy` changes
- Schema migrations
- `app/api/**` routes
- Auth, client fetches, server actions, forms
- 3D/graph visualization libraries
- Image/media assets
- Operator DB wiring or CI live_network proofs
- `review_batch` persistence
- AGENTS.md unless explicitly added in ticket JSON (not required)

## Golden / safety test posture

Existing GT00/GT12 scan all `app/**/*.tsx` for forbidden patterns — new page must comply.
No golden test changes required unless GT12 should assert `/atlas-preview` HTML exists;
optional follow-on only (not blocking ticket-300).

Run ticket test plan:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

## Product evaluation framing (for final report)

The implementation agent must answer in the ticket-300 report:

1. Does the text-first preview feel like the right direction for Research Atlas UI?
2. Which atlas fields are awkward or missing for frontend use?
3. What is the smallest next product-facing ticket after v0?

## Recommendation

| Action | Verdict |
|--------|---------|
| `/rge-run-next-ticket` for ticket-300 | **GO** |
| Hardened scope | This audit |
| `export-public` changes | **NO-GO** |
| Operator live atlas on public site | **NO-GO** |

## Suggested next prompt

```txt
/rge-run-next-ticket for ticket-300
```
