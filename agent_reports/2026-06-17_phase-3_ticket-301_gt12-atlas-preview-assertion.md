# Agent Report: ticket-301 — GT12 atlas-preview static export assertion

**Date:** 2026-06-17  
**Ticket:** ticket-301  
**Branch:** `phase-3/ticket-301-gt12-atlas-preview-assertion`  
**Main tip before branch:** `b6864ff`  
**Audit gate:** Not required — low-risk golden test only; no public export, site, schema, or live Ollama changes.

## Summary

Extended Golden Test 12 with atlas-preview coverage: source-level static fixture checks,
home-page link assertion, and static export HTML assertions for primary question and
coherence badge after `npm run build`.

## Scope

**In:** `tests/golden/test_12_public_site_static_render.py` only.

**Out:** Production code, public-site UI, `export-public`, new routes.

## Changed files

| File | Change |
|------|--------|
| `tests/golden/test_12_public_site_static_render.py` | +2 tests; atlas-preview assertions in GT12 |
| `tickets/ticket-301.json` | Status `done` |
| `tickets/ticket-302.json` | Seeded safety auditor follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## New GT12 assertions

| Test | Asserts |
|------|---------|
| `test_list_page_links_to_atlas_preview` | Home page links `/atlas-preview` |
| `test_atlas_preview_page_is_static_fixture_only` | Route exists; static JSON imports; no `fetch(` |
| `test_static_export_atlas_preview_page_exists` | `atlas-preview.html` exists; primary question, `Coherence:`, `Pass`, `Research Atlas` in HTML |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| GT12 asserts `atlas-preview.html` after build | **PASS** |
| GT12 asserts primary question + coherence badge | **PASS** |
| No production or export-public changes | **PASS** |
| Golden + full pytest green | **PASS** — 144 golden (+2), 759 full (+2) |

## Verification

```powershell
cd apps/public-site && npm run build
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden/test_12_public_site_static_render.py -q   # 11 passed
python -m pytest tests/golden -q                                        # 144 passed
python -m pytest -q                                                     # 759 passed, 33 deselected
```

Safety audit not required — test-only ticket.

## Manual CLI verification

Not applicable.

## Spec deviations

None.

## Cadence note

Three done tickets since post-ticket-298 principal audit (299, 300, 301). Recommend
`/rge-principal-audit` before next medium-risk public-site or export work.

## Recommended next ticket

**ticket-302** — Extend safety auditor to scan committed atlas preview JSON under
`apps/public-site/public/data/` (closes gap noted in ticket-300 safety run).

## Suggested next prompt

```txt
/rge-principal-audit
```

or

```txt
/rge-run-next-ticket
```

## Merge to main

Merge commit: _(pending)_
