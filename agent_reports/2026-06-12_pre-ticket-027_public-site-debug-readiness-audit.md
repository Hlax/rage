---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-027 Audit: Public-Site Debug Details Readiness

- Audit type: pre-implementation readiness audit (no ticket-027 code changes)
- Date: 2026-06-12
- Agent/model: Cursor builder agent (GPT-5.5)
- Scope: Git/main state after ticket-026, queue order, ticket-026 report consistency, public export policy, public-site display boundaries, Golden Test 25 readiness

## Summary

The repo is ready to begin ticket-027. `main` is clean and aligned with `origin/main` at `b004f48`; ticket-026 is merged, pushed, and marked `done`; ticket-027 is the lowest-order `proposed` ticket. All 110 golden tests pass; full safety audit returns `pass`. Current public export and public-site card detail pages are safe but incomplete for Golden Test 25: they lack explicit `evidence_type` and `public_run_timestamp` debug fields and a dedicated public debug section.

**Recommendation: proceed with ticket-027.**

## Git/Main Status

| Check | Result |
|---|---|
| Current branch | `main` |
| Main tip | `b004f48` |
| `origin/main` | `b004f48` |
| `main` vs `origin/main` | aligned |
| Working tree | clean (`## main...origin/main`) |
| ticket-026 merge commit | `c015d3e51bd2fe214693bc094afc3e44c6be2327` present in history |

Recent history confirms ticket-026 merged and documented:

- `c015d3e` merge ticket-026
- `07c0d7f` implement ticket-026
- `f109dbf` pre-ticket-026 audit
- `b004f48` docs: record main merge hash for ticket-026

## Ticket/Queue Consistency

| Check | Result |
|---|---|
| ticket-026 status | `done` in `TICKET_QUEUE.md` and `tickets/ticket-026.json` |
| ticket-027 status | `proposed` — lowest-order proposed ticket |
| ticket-027 risk level | `medium` |
| Pre-ticket audit gate | **applies** (medium risk; public export + public-site display surface) |

Ticket-027 is clear and builder-consumable:

- Title: Add public-site debug details without private data exposure (Golden Test 25)
- Expected files: card detail page, `publicCards.ts`, `card_exporter.py`, `tests/golden/test_25_public_site_debug_details.py`
- Non-goals: no public write routes, no local API exposure, no raw HTML rendering, no prompt-injection changes

## Ticket-026 Report Consistency

| Claim | Verified |
|---|---|
| All claimed implementation files exist | PASS |
| Golden Test 24 exists (`tests/golden/test_24_prompt_injection.py`) | PASS |
| Prompt-injection safety audit evidence | PASS — full audit checks GT24 files |
| Merge commit `c015d3e` | PASS |
| 110 golden tests | PASS (re-run this audit) |
| Full safety audit `pass` | PASS (re-run this audit) |

Verified ticket-026 files:

- `fixtures/sources/prompt_injection_creativity_short.txt`
- `fixtures/llm_outputs/claim_extraction_prompt_injection.json`
- `rge/safety/prompt_injection.py`
- `tests/golden/test_24_prompt_injection.py`

## Commands/Tests Run

| Command | Result |
|---|---|
| `git status --short --branch` | `## main...origin/main` (clean) |
| `git log --oneline --decorate -20` | ticket-026 merge at `c015d3e`; HEAD `b004f48` |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | 110 passed |
| `RGE_LLM_MODE=mock python -m pytest` | 110 passed |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | exit 0; `status: pass`; no blocked reasons |

## Public Debug Fields: Allowed vs Blocked

### Allowed on public card detail (per GT25 + `10_SAFETY_MODEL.md` §7–8)

| Field | Current state | GT25 requirement |
|---|---|---|
| claim summary (`summary`) | rendered | required |
| concepts | rendered | required |
| confidence | rendered | required |
| source count | rendered | required |
| evidence type | **missing** | required |
| public caveats | rendered when present | required |
| public source metadata | rendered when present | required |
| related cards | rendered when present | required |
| public run timestamp | partial (`updated_at` only) | required as explicit public run timestamp |

Additional allowed curated export fields already whitelisted: `id`, `type`, `title`, `public_detail_level`, `updated_at`.

### Must never appear in export or public UI

- Raw prompt text / prompt templates
- Private evaluator notes
- Local filesystem paths (`C:\...`, `/home/...`, `/Users/...`)
- Full copyrighted/private source text / raw source excerpts
- API keys / secret-like strings
- Hidden internal chain/reasoning
- Unreviewed draft claims (unless explicitly marked public-safe)
- Injected source instructions (GT24 markers)
- Internal IDs: `claim_id`, `source_id`, `chunk_id` (blocked by key substring policy)
- `private_fields_json` contents from DB
- Internal run reports, theory/ontology/domain draft internals
- Raw HTML/script from card JSON

Policy enforcement locations:

- `rge/safety/public_export_policy.py` — field whitelist, forbidden key substrings, value patterns
- `rge/modules/card_exporter.py` — `curated_public_card()` strips non-whitelisted fields; `GOLDEN_PRIVATE_FIELDS` stored in DB but must not export
- `rge/modules/safety_auditor.py` — route, export, secrets, raw-html scans

## Current Public Export Safety

Inspected `apps/public-site/public/data/public_cards.json`:

- Contains only whitelisted fields for two golden cards
- No forbidden key substrings (`private`, `prompt`, `evaluator`, `claim_id`, etc.)
- No local paths, API keys, prompt text, or injected instructions in values
- `build_info.json` is minimal and safe (`export_schema_version`, `generated_at`, `phase`, counts)

**Verdict: current public export is safe; it is not yet GT25-complete.**

## Current Public Site Rendering

Inspected `apps/public-site/app/cards/[id]/page.tsx`:

- Renders summary, concepts, confidence, source_count, public_detail_level, caveats, source metadata, related cards, card id, `updated_at`
- Uses React text escaping; no `dangerouslySetInnerHTML`
- No fetch/API routes; static JSON import only
- Does **not** render `evidence_type` or a labeled `public_run_timestamp` debug section

**Verdict: current public site is safe; debug detail section is incomplete for GT25.**

## Implementation Scope Recommendation

| Layer | Modify? | Rationale |
|---|---|---|
| Public export (`card_exporter.py`, `public_export_policy.py`) | **Yes** | GT25 requires `evidence_type` and `public_run_timestamp` in curated export JSON |
| Public-site display (`page.tsx`, `publicCards.ts`) | **Yes** | GT25 requires UI to show the new debug fields |
| Safety audit | **Extend lightly** | Add GT25 evidence file check in full audit (mirror GT24 pattern) |
| DB schema | **No** | Derive debug fields at export time from existing card/claim data and golden extras |

Both export and display layers must change; export alone is insufficient because GT25 validates UI rendering.

## Safety Audit Extension

Recommend extending `_audit_public_export` or adding a GT25 evidence check in full audit:

- Verify `tests/golden/test_25_public_site_debug_details.py` exists after implementation
- Existing export/secrets/raw-html checks already cover forbidden content; new allowed fields must be added to `ALLOWED_PUBLIC_CARD_FIELDS` and GT11 `ALLOWED_CARD_FIELDS` must stay synchronized

## Golden Test 25 Assertions (exact)

Add `tests/golden/test_25_public_site_debug_details.py` with at least:

1. **Export includes debug fields** — after `export-public`, each golden card has `evidence_type` and `public_run_timestamp`; fields remain within updated allowed set; no forbidden value patterns.
2. **Private DB fields do not leak** — `GOLDEN_PRIVATE_FIELDS` keys/values (`evaluator_notes`, `local_path`, `prompt_template`, `raw_source_excerpt`) absent from export JSON.
3. **Card detail source renders debug section** — `page.tsx` contains labels for evidence type and public run timestamp; no `dangerouslySetInnerHTML`; no references to private field names.
4. **Static JSON snapshot aligned** — committed `apps/public-site/public/data/public_cards.json` includes new debug fields for golden cards.

Optional (if `npm run build` available in CI): static HTML contains debug labels without forbidden substrings.

## Is Ticket-027 Safe to Begin?

**Yes.** Preconditions satisfied:

- Clean `main` aligned with `origin`
- ticket-026 complete with verified artifacts
- 110/110 tests green
- Full safety audit pass
- Public export and site currently safe (no leaks found)
- Scope is bounded to curated export fields + read-only UI display

## Blockers

None.

## Next Step

Proceed with `/rge-run-next-ticket` for ticket-027 on branch `phase-1/ticket-027-public-site-debug-details`.
