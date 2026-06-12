---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-015 Audit: Public Site Readiness (Tickets 010–014)

- Audit type: principal checkpoint audit (no ticket-015 implementation)
- Date: 2026-06-12
- Agent/model: Cursor principal audit agent (Auto)
- Scope: Git/main state, ticket/report loop for tickets 010–014, executable spine, tests, public export safety, public site safety, ticket-015 readiness

## Summary

The repo is **ready to proceed with ticket-015 (public site card and concept detail pages / Golden Test 12)** after applying the **hardened scope** below. `main` is clean and aligned with `origin/main` at `c8042a1`. Tickets 010–014 are merged, reported, and queue-consistent. All **59** golden tests pass without Ollama; the public site static build succeeds.

The loop advanced four tickets (011–014) since the last full principal audit (pre-ticket-011). No unmerged ticket work or force-push drift was found. `/rge-run-next-ticket` obeyed single-ticket stop rules but **lacked mandatory audit gates** before public export and public-site milestones — the runner command is patched in this audit.

Public export (ticket-014) is **safe for its current scope**: fail-closed validation, no private field leakage in golden tests, and stable golden card IDs. Known limitations are documented (golden card seeding uses exporter constants, not full cluster synthesis; committed `apps/public-site/public/data/public_cards.json` is still the Phase 0 placeholder until a real `export-public` run overwrites it).

**Recommendation:** proceed with hardened ticket-015. No separate pre-015 hardening ticket is required.

## Git / Main Status

| Check | Result | Evidence |
|---|---|---|
| Current branch | `main` | `git branch --show-current` |
| Working tree clean | PASS | `nothing to commit, working tree clean` |
| `main` aligned with `origin/main` | PASS | both at `c8042a1570ecd858296e2dfc88bdb82fba101db4` |
| ticket-010 branch contained in `main` | PASS | `phase-1/ticket-010-score-reconciliation` is ancestor of `HEAD` |
| ticket-011 branch contained in `main` | PASS | merge `4d8e900` |
| ticket-012 branch contained in `main` | PASS | merge `c384cb7` |
| ticket-013 branch contained in `main` | PASS | merge `69befe6` |
| ticket-014 branch contained in `main` | PASS | merge `eb4c3ea`; doc follow-up `c8042a1` |
| Unmerged ticket work | NONE | all phase-1 ticket branches 010–014 are ancestors of `main` |
| Force-push / branch drift signs | NONE | linear merge history; remote matches local |

Recent merge chain (010→014):

```txt
c8042a1 docs: record main merge hash for ticket-014
eb4c3ea Merge branch 'phase-1/ticket-014-public-card-export'
69befe6 Merge branch 'phase-1/ticket-013-research-contract-drift'
c384cb7 Merge branch 'phase-1/ticket-012-mock-research-queue'
4d8e900 Merge branch 'phase-1/ticket-011-mock-contradiction-detection'
011441f Merge branch 'phase-1/ticket-010-score-reconciliation'
```

## Ticket / Report Consistency

| Ticket | Queue status | JSON status | Report | Merge hash in report |
|---|---|---|---|---|
| ticket-010 | done | done | `agent_reports/2026-06-11_phase-1_ticket-010_score-reconciliation.md` | `011441f` |
| ticket-011 | done | done | `agent_reports/2026-06-11_phase-1_ticket-011_mock-contradiction-detection.md` | `4d8e900` |
| ticket-012 | done | done | `agent_reports/2026-06-11_phase-1_ticket-012_mock-research-queue.md` | `c384cb7` |
| ticket-013 | done | done | `agent_reports/2026-06-11_phase-1_ticket-013_research-contract-drift.md` | `69befe6` |
| ticket-014 | done | done | `agent_reports/2026-06-11_phase-1_ticket-014_public-card-export.md` | `eb4c3ea` |
| ticket-015 | proposed | proposed | n/a (not started) | n/a |

Findings:

- All completed tickets 010–014 have agent reports and matching `done` status in queue + JSON.
- **Minor inconsistency:** duplicate ticket JSON files exist for ticket-010 (`tickets/ticket-010.json` and `tickets/ticket-010_score-reconciliation.json`). Both marked `done`; not blocking.
- **Current active ticket** correctly set to `ticket-015 (proposed; awaiting review)`.
- **ticket-015 is the correct next proposed ticket** — it closes Golden Test 12 gap left after ticket-014 (export without detail/concept routes).
- Last principal audit before this run: `agent_reports/2026-06-11_pre-ticket-011_contradiction-readiness-audit.md`. **Four tickets (011–014) shipped without an intervening full audit** — acceptable given passing tests, but the runner should gate future milestones.

## Loop-Runner Behavior Findings

| Check | Result | Notes |
|---|---|---|
| One ticket per invocation | PASS | Separate merge commits for 011, 012, 013, 014 |
| Stop after merge/push | PASS | No evidence of multi-ticket jumps in one run |
| Pre-ticket audit before 011 | PASS | pre-ticket-011 audit existed |
| Pre-ticket audit before 014 (public export) | **MISSING** | ticket-014 merged without principal audit |
| Pre-ticket audit before 015 (public site) | **THIS AUDIT** | performed before implementation |
| Safety auditor on ticket-014 | NOT RUN | `safety_auditor` module still Phase 0 stub; export policy validation used instead |

**Runner patch applied:** `.cursor/commands/rge-run-next-ticket.md` now includes mandatory audit-gate stops before public export, public site changes, schema migrations, and live Ollama tickets.

## Tests / Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden` | PASS | 59/59 in 8.29s (`RGE_LLM_MODE=mock`) |
| `python -m pytest` | PASS | 59/59 in 8.26s |
| `cd apps/public-site && npm run build` | PASS | Next.js 15.5.19 static export; routes: `/`, `/_not-found` only |
| `python -m rge.modules.safety_auditor --audit full` | NOT AVAILABLE | exits 3 by design (Phase 0 stub) |

## Fresh DB Spine Verification

### Minimum spine (audit request)

Run on fresh temp DB with `RGE_LLM_MODE=mock`:

```txt
ingest → extract-claims → link-concepts → build-relationships → reconcile-scores → export-public
```

| Step | Result |
|---|---|
| ingest `creativity_ai_diversity_short.txt` | PASS |
| extract-claims | PASS (2 accepted) |
| link-concepts | PASS |
| build-relationships | PASS (1 active relationship) |
| reconcile-scores | PASS (`no_score_changes` — expected; confidence 0.7 < 0.8 threshold) |
| export-public `--limit 10` | PASS (2 golden cards seeded; no forbidden leaks) |

Export safety checks on output JSON:

| Check | Result |
|---|---|
| `claim_ids` absent | PASS |
| `private_fields` absent | PASS |
| evaluator notes absent | PASS |
| Windows local paths absent | PASS |

### Extended spine (011–013 commands)

Additional steps exercised on the same fresh DB:

| Step | Result | Notes |
|---|---|---|
| ingest + extract follow-up source | PASS extract / mixed rejections | Expected fixture behavior |
| reconcile-scores on follow-up | **FAIL** (exit 1) | No accepted claims on follow-up source unless Golden Test 8 fixture path used |
| ingest + extract contradiction source (default fixtures) | PASS extract | 0 accepted without `--fixture` |
| detect-contradictions (default) | **FAIL** (exit 1) | Requires contradiction `--fixture` chain per Golden Test 7 |
| queue-sources | PASS | 4 queued + marketing rejected |
| validate-contract (out-of-scope + in-scope) | PASS | drift gating works |
| export-public after extended spine | PASS | 2 cards, 6 queue rows |

**Interpretation:** Golden tests cover extended commands with explicit `--fixture` flags. The **minimum spine is intact**. Extended CLI chaining without fixtures is not a ticket-015 blocker but should remain documented in operator notes.

## Public Export Safety Findings

| Requirement | Status | Evidence |
|---|---|---|
| No raw source text exported | PASS | `public_export_policy` + GT11 assertions |
| No raw prompts exported | PASS | private `prompt_template` stored in DB `private_fields_json` only |
| No local paths exported | PASS | GT11 + policy path patterns; golden private path not in export JSON |
| No secrets / key-like strings | PASS | policy patterns; GT11 |
| No private DB fields exported | PASS | `curated_public_card()` whitelist; no `claim_ids_json` in export |
| Fail closed on unsafe fields | PASS | GT11 `<script>` test blocks write |
| Only allowed card fields | PASS | GT11 + `test_00_public_site_static.py` |
| Stable card IDs | PASS | `card_golden_diversity_001`, `card_golden_originality_002` deterministic |
| Derived from accepted graph | **PARTIAL** | Seeding gated on accepted-claim count; card **content** is golden constants keyed by fixture graph presence, not live cluster synthesis |
| Golden Test 11 coverage | **SUFFICIENT** for export boundary | 4 tests: write, field whitelist, fail-closed, limit |

Non-blocking gaps:

1. **`safety_auditor` module not implemented** — export relies on `public_export_policy`, not full audit report persistence.
2. **Optional card fields** (`public_caveats`, etc.) come from exporter constants, not DB columns (ticket-014 documented deviation).
3. **Concepts in export are string labels**, not `cpt_*` IDs — affects ticket-015 concept routing design.

## Public Site Safety Findings

| Requirement | Status | Evidence |
|---|---|---|
| Static JSON only | PASS | `page.tsx` imports JSON; `next.config.js` `output: 'export'` |
| No public write routes | PASS | no `app/api`; `test_00_public_site_static.py` |
| No public ingestion routes | PASS | same |
| No public agent execution routes | PASS | same |
| No unsafe HTML rendering | PASS | React text escaping; no `dangerouslySetInnerHTML` |
| No local DB at build time | PASS | build succeeds without SQLite |
| No local FastAPI at build time | PASS | static export only |
| Card detail route exists | **MISSING** | only `/` and `/_not-found` — ticket-015 scope |
| Concept detail route exists | **MISSING** | ticket-015 scope |
| Committed static JSON matches export pipeline | **DRIFT** | `public_cards.json` still Phase 0 placeholder (`card_placeholder_0001`); golden export IDs not in committed site data |

`test_00_public_site_static.py` validates placeholder JSON safety but does **not** assert Golden Test 12 routes (detail/concept pages).

## Ticket-015 Readiness

| Criterion | Ready? | Notes |
|---|---|---|
| Safe static JSON inputs | YES with hardening | Use exported golden cards in tests; optionally refresh committed `public/data/` from export |
| Clear routing/page scope | YES | add `app/cards/[id]/page.tsx`, `app/concepts/[id]/page.tsx`; update list links |
| No server/write behavior | YES | stay on static export + JSON imports |
| No DB dependency at build | YES | current pattern |
| Clear tests for static pages | NEEDS ADDITION | `test_12_public_site_static_render.py` as proposed |
| No privacy/safety gaps | YES if pages escape text and avoid new routes/API |

**Decision:** ticket-015 may proceed **with hardened scope** (below). No blocking issues.

## Blocking Issues

None for ticket-015 start.

## Recommended Next Action

1. Run `/rge-run-next-ticket` for **ticket-015** using hardened scope below.
2. Before or during ticket-015, optionally run `python -m rge.cli export-public --limit 100` on a dev DB to refresh committed `apps/public-site/public/data/*.json` so the public site list matches golden card IDs (non-blocking but improves GT12 fidelity).
3. Schedule next principal audit before **ticket-016+** if it touches safety auditor implementation, schema migrations, or live Ollama.

## Hardened Ticket-015 Scope

Implement only:

1. **`app/cards/[id]/page.tsx`** — static detail page from `public_cards.json`; `generateStaticParams` from card IDs; link related cards by ID; escape all text fields.
2. **`app/concepts/[slug]/page.tsx`** (or `[id]` with slug = normalized concept label) — aggregate cards mentioning concept string; **do not assume `cpt_*` IDs in export JSON**.
3. **Update `app/page.tsx`** — link each card title to `/cards/[id]`; link concept strings to concept pages; keep build-info footer (already renders `generated_at`).
4. **`tests/golden/test_12_public_site_static_render.py`** — assert route files exist; assert forbidden patterns absent; optionally parse `apps/public-site/out/` HTML for card titles after `npm run build` (or verify `generateStaticParams` sources without full npm in pytest).
5. **Golden test setup** — either commit representative post-export JSON (2 golden cards) or document test precondition running `export-public` into `public/data/` before build assertions.

Non-goals (unchanged):

- No API routes, forms, fetches to local engine, or SQLite.
- No `dangerouslySetInnerHTML`.
- No scope expansion into safety auditor or memo pages.

## Runner Command Patch

Applied to `.cursor/commands/rge-run-next-ticket.md`:

- New **§3.5 Audit gate (mandatory stop)** before selecting/implementing tickets that touch public export, public site, schema migrations, or live Ollama.
- Requires a current `agent_reports/*pre-ticket-*` audit for the target milestone when no audit exists since the last milestone.
- Lists milestone categories and instructs the agent to **stop and request audit** rather than implement when gate is unmet.

## Can the Loop Continue?

**Yes.** Proceed with hardened ticket-015 after this audit. Public export boundaries are acceptable for static site work; the primary gap is missing detail/concept routes and GT12 test coverage — exactly ticket-015 scope.
