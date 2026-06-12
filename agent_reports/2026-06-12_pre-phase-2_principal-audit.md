---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Phase-2 Principal Audit Checkpoint (ticket-033)

- Audit type: principal audit — full repo, Phase 1 completion, safety boundaries, public-site product review, Phase 2 planning
- Date: 2026-06-12
- Agent/model: Cursor principal audit agent
- Scope: read-only audit and planning. No runtime, schema, frontend, or export changes were made. Generated fixture-run artifacts were cleaned (documented below).

## Executive Summary

Phase 1 is **real and verified**. The fixture-mode MVP spine (`research run --fixture-mode`) executes the full pipeline — contract, queue, three-source ingest/extract/link/relationship/contradiction/score, cluster report, theory candidates, public export, run report, improvement tickets, safety audit — deterministically in mock mode. All 119 golden tests pass, the full pytest suite passes, the full safety audit passes, and the public site builds 11 static pages and renders cleanly.

**Go decision: GO for Phase 2**, with three caveats that should be fixed first:

1. **Fixture-run artifact hygiene (must-fix):** `research run --fixture-mode` dirties the working tree. It rewrites the two committed public-data snapshots with non-deterministic key ordering, live timestamps, and a `source_count` drift (committed snapshot says `1`, regenerated export says `3`), and drops untracked `data/` and `tickets/improvement_ticket_latest.json`. This silently violates the build loop's clean-tree precondition after every demo run.
2. **README is dangerously stale (must-fix):** the root README still says "Phase 0 / 0.5 scaffold (ticket-001) … Pipeline behavior … intentionally not implemented yet." A new engineer or external reviewer would conclude the MVP does not exist.
3. **No CI enforcement:** the builder merge gate (GT22) is convention-enforced via agent protocol only. There is no CI workflow; nothing mechanical blocks a merge that skips `pytest tests/golden`.

Recommended first Phase 2 ticket: **ticket-034 fixture-run artifact hygiene** (deterministic export serialization + gitignore generated artifacts), followed by README/docs refresh, then a small presentation-only public-site polish ticket, then Ollama live structured-task work.

## Current Repo / Main Status

| Check | Result |
|---|---|
| Branch | `main`, aligned with `origin/main` (`## main...origin/main`) |
| Working tree | clean at audit start and after artifact cleanup |
| Main tip | `502c5c2` (docs: record main merge hash for ticket-032) |
| ticket-032 merge commit | `95041c9` — matches reported state |
| Unmerged branches | `git branch --all --no-merged main` → **none** |
| Tickets 028–032 | all `done`, merged, pushed; merge hashes in reports match `git log` (`5d0c214`, `9c90123`, `48fd6ba`, `b859fda`, `95041c9`) |
| ticket-033 | `proposed`, correct next checkpoint; this report satisfies its expected file |

No dangling unmerged work affects Phase 2.

## Phase 1 Completion Verification

Report claims vs repo reality — all verified:

| Claim (reports 028–032) | Verified |
|---|---|
| ticket-028: `execute_fixture_mode_run()` in `rge/cli.py`, GT26 added | YES — code present, GT26 has 4 tests |
| ticket-029/030/031: GT22 `REQUIRED_GOLDEN_AREAS` extended with `full_mvp_run`, `safety_audit_gate`, `prompt_injection`, `public_site_debug` | YES — all entries present |
| ticket-032: GT07/GT09/GT12 added; 9 optional modules documented; inventory test added | YES — `INTENTIONALLY_OPTIONAL_GOLDEN_TESTS` and `test_phase1_optional_golden_tests_are_documented` present |
| 119 golden / 119 total tests pass | YES — re-run this audit: 119 passed (both) |
| Safety audit passes | YES — `status: pass`, exit 0 |
| Public site builds 11 static pages | YES — re-run this audit: 11/11 pages, exit 0 |

Ticket statuses in `TICKET_QUEUE.md` and ticket JSONs are consistent. No stale or overstated report claims found.

### What the MVP actually is

- **Real and executable:** SQLite migration harness (7 migrations); ingest → claim extraction → concept linking → relationship building → contradiction detection → score reconciliation (all deterministic Python validation over mock-LLM candidate JSON); research contract drift gating; queue ranking; cluster/theory/ontology/domain/run reports; improvement ticket generation + builder-consumption validation; fail-closed public card export; static Next.js public site; deterministic safety auditor; prompt-injection rejection; full fixture-mode orchestration.
- **Mock/fixture-only:** every LLM step. Pipeline modules hard-force `RGE_LLM_MODE=mock`; `OllamaModelClient` structured tasks raise `OllamaNotAvailableInPhase0`; only `health_check()` may touch the network when explicitly invoked.
- **Intentionally out of scope:** live discovery (`research run` without `--fixture-mode` returns `not_implemented`), `research verify` (placeholder), embeddings, LangGraph, any cloud provider (OpenAI/OpenRouter/Anthropic/Gemini/Vertex — zero code references), public write/ingestion/agent routes.
- **What a new engineer would misunderstand:** the README (see Docs section). Also `.env.example` defaults `RGE_LLM_MODE=ollama`, which suggests live inference works; it does not (it fails closed, but the failure mode is a runtime exception, not a doc-visible limitation).

## Golden Test / Builder Gate Assessment

`tests/golden/test_22_builder_golden_gate.py` defines:

- `BUILDER_MERGE_GATE_COMMAND = "pytest tests/golden"`.
- 16 `REQUIRED_GOLDEN_AREAS` covering ingestion, claim extraction/validation, concept linking, relationships, contradiction detection, scoring history, research queue, public export, public-site static render, cluster report, ticket generation (GT20+GT21), safety audit gate, prompt injection, public-site debug, full MVP run.
- 9 `INTENTIONALLY_OPTIONAL_GOLDEN_TESTS` with written omission reasons (scaffold smoke, model runtime smoke, static JSON policy, contract drift, theory, questions, ontology pressure, domain proposal, run report — all still executed by the full suite).
- `META_GOLDEN_TEST_FILES` tracks the gate file itself.
- An inventory completeness test fails if any new `tests/golden/test_*.py` is neither required, optional-documented, nor meta — this is a strong self-sealing property.

**Assessment:** every golden file is accounted for; required areas are sensible for Phase 1; the optional list does not weaken the gate because `pytest tests/golden` runs everything regardless — the required/optional split only governs which areas count as named merge-blocker capabilities. GT3/GT4 (quote-span and overgeneralization rejection) live inside `test_02_claim_extraction.py` and are covered by the `claim_validation` area; GT14 (balanced evidence packet) lives inside `test_13_cluster_report.py`.

**Gaps before Phase 2:**

1. **No CI workflow.** The gate exists as a convention plus meta-tests; nothing mechanically runs `pytest tests/golden` on push/merge. A minimal GitHub Actions workflow (mock mode, no Ollama) would make the gate real rather than honor-system.
2. **No required area for export determinism.** Nothing asserts that re-running export yields byte-identical committed snapshots (the root cause of the artifact-hygiene finding).
3. `/rge-principal-audit` is referenced by handoffs but **does not exist** in `.cursor/commands/` (only `rge-handoff`, `rge-next-ticket`, `rge-phase0-scaffold`, `rge-run-next-ticket`, `rge-verify`). The audit cadence rule in `rge-run-next-ticket.md` step 3.5 references it implicitly; the command file should be added.

## MVP Fixture Run Assessment

Command run (exact):

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
```

Result: exit 0, `status: completed`, all 12 orchestration steps completed, post-run safety audit `pass` enforced inside the orchestrator. The run is real: it produces accepted and rejected claims, active relationships, score events, qualifies+supports evidence, ≥2 public cards, cluster/theory/run reports, and improvement tickets, with hard validation thresholds that raise on shortfall.

**Repo dirtiness (documented exactly):** after the run, `git status --short` showed:

```txt
 M apps/public-site/public/data/build_info.json    (generated_at timestamp churn)
 M apps/public-site/public/data/public_cards.json  (key reordering, updated_at churn, source_count 1 -> 3)
?? data/                                           (db + reports, untracked)
?? tickets/improvement_ticket_latest.json          (untracked)
```

Cleanup used: `git restore` on the two tracked JSON files; deleted `data/` and `tickets/improvement_ticket_latest.json`. Tree verified clean afterwards.

Three distinct problems:

1. **Non-deterministic serialization** — exporter writes dict-ordered keys that differ from the committed snapshot's ordering.
2. **Timestamp churn** — `generated_at` / `updated_at` use wall-clock time, so every run diffs.
3. **Snapshot drift** — committed cards say `source_count: 1` but the pipeline now ingests 3 sources, so regenerated cards say `3`. Either the committed snapshot is stale or the exporter's source counting changed after the snapshot was committed. This should be reconciled deliberately, not by accident on the next unrelated commit.
4. `tickets/improvement_ticket_latest.json` is written into the **real ticket queue directory** by default and is untracked/un-ignored — easy to commit accidentally.

## Safety / Public-Data Assessment

`python -m rge.modules.safety_auditor --audit full` → `status: pass`, exit 0.

**Exact checks performed by the full audit:**

| Check | Mechanism |
|---|---|
| Route permissions | Scans all public-site `.ts/.tsx/.js/.jsx` for POST/PUT/PATCH/DELETE handlers, method literals, `/ingest`, `/agent`, `/local/*`, `127.0.0.1:port`, `localhost:port/local`; asserts policy kinds (no write / ingestion / agent-execution / private-API routes) |
| Public export | Loads `public_cards.json` / `public_memos.json` / `build_info.json`; whitelist of 14 allowed card fields; 9 required fields; forbidden key substrings (`private`, `prompt`, `secret`, `evaluator`, `claim_id`, `local_path`, `raw_text`, `body_markdown`, `chunk_id`, `source_id`, `api_key`); forbidden value patterns (Windows drive paths, `/home|/Users` paths, `sk-…` keys, `api_key`, `<script`, `IGNORE ALL PREVIOUS INSTRUCTIONS`) |
| Secrets | Same forbidden value patterns over raw export file text |
| Raw HTML | `dangerouslySetInnerHTML` ban across public-site sources |
| Model tool permissions | `rge/llm/*.py` scanned for `subprocess`, `os.system`, `Popen`, `shell=True`, `git push` |
| Prompt injection | Evidence files exist (policy module, GT24 fixtures, GT24 test) |
| Public-site debug | Evidence files exist (card detail page, `publicCards.ts`, GT25 test) |
| Full MVP run | `rge/cli.py` contains `execute_fixture_mode_run`; GT26 test exists |

**Boundary verification (all hold):** no public write routes (static export, no API routes in `apps/public-site/app/`); no raw source text (cards carry only title/summary/concepts/caveats/source metadata); no raw prompts; no secrets; no local paths; no private evaluator notes; no hidden reasoning; the GT24 injected-instruction fixture is rejected with `unsafe_or_injected_content` and its markers are blocked from exports by value pattern; internal IDs (`claim_id`, `source_id`, `chunk_id`) are forbidden key substrings — only the public `card.id` is exposed, which is intentional and required; draft theory/ontology/domain internals stay in `data/reports/` and SQLite, never in the export bundle. Debug details are curated to exactly two fields (`evidence_type`, `public_run_timestamp`) plus already-public `updated_at`.

**Honest weaknesses (not failures):**

- Route and model-tool checks are regex-over-source; they are bypassable by an adversarial builder, acceptable for Phase 1 given the protocol layer above them.
- Prompt-injection/GT25/GT26 checks are **existence checks** (files present), not behavioral re-verification — the behavior lives in the golden tests, which is fine while the gate runs them.
- The auditor scans only `apps/public-site/public/data/`; `data/exports/` (same content, second write target) is unscanned. Low risk since both come from the same validated bundle, but worth closing when exports grow.
- `route_audit.py` allows `GET /about`, which doesn't exist yet — allowed-but-unimplemented, no risk.

## Public-Facing UI / Product Assessment

`npm run build`: **pass** — 11 static pages (/, _not-found, 2 cards, 5 concepts, static export). The built site was served locally and reviewed in a browser (home + card detail screenshots taken; not committed, per repo convention).

**What works:**

- Honest framing: "Read-only public export surface" kicker, explicit no-write/no-ingestion/no-agent statement, fixture caveats on every card. Trust messaging is genuinely good for an MVP.
- Clean dark theme, readable type, consistent card containers, working concept cross-links, related-card links, breadcrumbs, build provenance footer (schema version, phase, generated-at).
- Card detail page has clear hierarchy: title → meta line → summary → concepts → caveats → source metadata → related cards → debug details.
- No client JS beyond Next runtime, no fetches, no forms — the safety story is visible in the UX itself.

**What reads as a test artifact rather than a product:**

| Issue | Severity |
|---|---|
| Raw enum strings in UI: `cluster_card`, `empirical`, `standard`, raw ISO timestamps (`2026-06-12T00:00:00Z`) | High — first thing a viewer sees |
| Only 2 cards, both labeled "fixture" — fine for now, but the homepage doesn't explain *why* (no "this is a deterministic pipeline demo" note) | Medium |
| No `/about` page: methodology, safety model, what "confidence: medium" means | Medium — biggest credibility gap |
| All styles are inline `style={{}}` objects; no global stylesheet/design tokens; harder to evolve consistently | Medium (engineering debt, invisible to users) |
| Empty state: zero cards renders "Public cards (0)" with nothing else | Low (can't happen while snapshot is committed) |
| Default Next 404 page (unstyled vs site theme) | Low |
| No favicon / OG metadata beyond title+description | Low |
| Mobile: single-column 760px max-width with padding — acceptable; debug `<dl>` grid may crowd on narrow screens | Low |

**Verdict:** structurally a real public MVP, presentationally ~70% there. One small, presentation-only polish ticket would make it externally shareable. Nothing requires export-policy changes if it only formats existing fields.

## Docs / README Assessment

| Doc | State |
|---|---|
| Root `README.md` | **Stale and misleading.** "Current Status" says Phase 0/0.5 scaffold, "Pipeline behavior … intentionally not implemented yet." Missing: fixture-run quickstart, mock-vs-live explanation, artifact paths, public-site deployment, self-improvement loop. This is the #1 doc fix before any external handoff. |
| `docs/agents/12_RUNTIME_CONFIG.md` | Excellent — accurate env table, mock-forcing reality, local file layout, smoke checklist. Minor: "Ticket-028 / Golden Test 26" section is now historical. |
| `.env.example` | Accurate but defaults `RGE_LLM_MODE=ollama`, inviting confusion since live structured tasks fail closed. Consider defaulting the example to `mock` until live inference exists. |
| `.env.smoke.example` | Good; honest "Phase 1 reality check" header. |
| `docs/agents/*` specs | Internally consistent; `04_CURSOR_BUILD_LOOP.md` / `AGENTS.md` temporary merge checkpoint still active (safety evaluator agent not yet live). |
| `.cursor/commands/` | `rge-run-next-ticket.md` is thorough (audit gate table is in place). **Missing `rge-principal-audit.md`** even though handoffs suggest `/rge-principal-audit`. |
| Roadmap docs | None exist; this audit's roadmap file is the first. |

Operator answers: a new contributor **cannot** currently understand the system from README alone (must read docs/agents/). An operator **can** run the fixture MVP only if they find report 028 or GT26. Env vars are clear in doc 12. Safety boundaries are clear in doc 10 + README boundaries section. Public-site deployment is **not** explained anywhere. The self-improvement loop is explained in specs but not surfaced in README.

## Live Provider Readiness

| Question | Answer |
|---|---|
| OpenAI / OpenRouter / Anthropic / Gemini / Vertex wired? | **No.** Zero code references; config validates only `mock`/`ollama`. |
| Ollama usable? | **Intentionally blocked** for structured tasks (`OllamaNotAvailableInPhase0`); only `health_check()` is live, and only when explicitly called. Pipeline modules force `RGE_LLM_MODE=mock` regardless of env. |
| Live smoke tests possible today? | **No.** Two blockers: forced mock in 4 pipeline modules, and unimplemented Ollama structured tasks. |
| Provider adapter layer in Phase 2? | The adapter boundary already exists (`rge/llm/base.py` + registry). Phase 2 should *implement* the Ollama client first, not add a multi-provider abstraction. Cloud providers can be a later thin addition behind the same `ModelClient` interface. |
| Which provider first? | **Ollama (qwen2.5:7b)** — it is the canonical core rule ("Qwen/Ollama proposes candidate JSON"), local-first, zero API cost, no secrets. |
| Safe gating for live smoke | (a) replace forced-mock with an explicit opt-in (e.g. `RGE_ALLOW_LIVE_LLM=1` + `RGE_LLM_MODE=ollama`, fail closed otherwise); (b) live tests behind a pytest marker (`-m live_smoke`) excluded from `pytest tests/golden` and default `pytest`; (c) keep golden fixtures mock-only forever; (d) timeout/budget caps in config (timeout exists; add max-call counters for cloud providers later). |
| Preventing live runs mutating public exports | Already structurally protected: export passes `validate_public_export_bundle` fail-closed, and the orchestrator runs the full safety audit post-export. Add: live-mode runs should default `--export-dir` to a scratch path (never `apps/public-site/public/data/`) unless an explicit `--publish` review flag is set, and committed snapshots should only change in deliberate snapshot-refresh commits (ties into artifact hygiene ticket). |

No API keys were added; no secrets printed; no `.env.local` created.

## Phase 2 Risks

1. **Silent snapshot mutation** — the highest-probability incident: a fixture run before an unrelated commit pushes regenerated public JSON to main without review (artifact hygiene ticket closes this).
2. **Live LLM nondeterminism leaking into the golden surface** — forced-mock removal must be opt-in and never reachable from golden tests.
3. **Documentation debt compounding** — Phase 2 features on top of a Phase-0-era README makes onboarding worse with every ticket.
4. **Merge gate erosion** — without CI, the gate depends entirely on agent protocol compliance; a single sloppy merge breaks the inductive guarantee.
5. **UI scope creep** — public-site work can balloon; keep tickets presentation-only and audit-gated per the existing rule table.
6. **Improvement-ticket collision** — generated `tickets/improvement_ticket_latest.json` shares a directory with real queue tickets.

## Recommended Phase 2 Ticket Roadmap (ranked)

Full details (problem / acceptance criteria / test plan / risk) in `agent_reports/2026-06-12_phase-2_ticket-roadmap.md`. Categories per audit instruction:

**1. Must-fix before external MVP demo**

- ticket-034: Fixture-run artifact hygiene — deterministic export serialization, stable timestamps for fixture mode, gitignore `data/` + generated ticket artifact (or relocate to `data/tickets/`), reconcile `source_count` snapshot drift deliberately. Low risk. Pre-ticket audit: not required (this audit covers it).
- ticket-035: README + operator setup refresh — Phase 1 reality, fixture-run quickstart, mock-vs-live, artifact map, safety boundaries pointer. Low risk. No pre-audit.

**2. Should-fix for credible product/UI**

- ticket-036: Public-site presentation polish — humanize enums/timestamps, `/about` (methodology + trust), styled 404, empty state, favicon/meta; presentation-only, no export schema changes. Low-medium risk. **Pre-ticket audit required** (public-site rule), but this audit's UI section can serve as it if scope stays presentation-only.

**3. Needed for real provider smoke tests**

- ticket-037: Ollama live structured-task implementation behind explicit env opt-in (remove forced mock; fail closed by default). Medium-high risk. **Pre-ticket audit required** (live Ollama rule).
- ticket-038: Live smoke-test gating — `live_smoke` pytest marker, scratch export dirs for live runs, `model-health` CLI surfacing `health_check()`. Medium risk. Pre-audit folded into ticket-037's.

**4. Needed for agent-loop self-improvement**

- ticket-039: Self-improvement loop validation — round-trip a generated improvement ticket through the builder ticket format into the real queue with explicit human/audit promotion step. Medium risk. Pre-audit recommended.
- ticket-040: Add `.cursor/commands/rge-principal-audit.md` + CI workflow running `pytest tests/golden` (mock) + safety audit on PR/push. Low risk. No pre-audit.

**5. Needed for public deployment**

- ticket-041: Deployment-readiness pass — static hosting docs (the site is already a static export), build provenance in footer, deploy checklist incl. safety audit as pre-deploy gate. Low risk pre-audit not required if docs-only; required if site config changes.

**6. Nice-to-have after Phase 2**

- Cloud provider adapter (OpenAI/OpenRouter) behind `ModelClient`; embeddings; concept graph visualization; export snapshot versioning/history; `research verify` implementation.

## Recommended Immediate Next Ticket

**ticket-034 (fixture-run artifact hygiene).** It is the smallest ticket, closes the highest-probability incident, and makes every subsequent demo/dev loop clean. Then 035 (README), then 036 (UI polish).

## UI Work Placement (explicit answer)

The stated preference — include the UI pass in this audit, implement nothing, propose small UI tickets after — is **validated and correct**. UI work should land **immediately after artifact hygiene + README** (it does not need to wait for live-provider hardening; it touches only presentation and is independent of the LLM runtime). Smallest safe UI ticket: presentation-only polish (label formatting, date formatting, `/about`, 404, empty state) — safe because it reads existing whitelisted fields and renders no new data. Any UI change that wants **new data fields** (e.g. claim counts, run metrics, contradiction badges) requires an export-policy update + safety audit extension + GT25-style golden coverage, and must be a separate audited ticket. Of the candidate framings, "public-site product polish" is the right first ticket; "homepage narrative" and "card detail UX" fit inside it; "deployment-readiness" is separate (category 5).

## Blockers

None for Phase 2 start. Caveats:

- The temporary agent-merge-to-main checkpoint (AGENTS.md step 9) remains active until a safety evaluator agent owns merge gating.
- `/rge-principal-audit` slash command referenced by handoffs does not exist as a command file yet (this audit was run from an inline prompt).

## Commands Run and Exact Results

| Command | Result |
|---|---|
| `git status --short --branch` | `## main...origin/main` — clean |
| `git log --oneline --decorate -30` | tip `502c5c2`; merges `95041c9`/`b859fda`/`48fd6ba`/`9c90123`/`5d0c214` all present |
| `git branch --all --no-merged main` | empty — no unmerged branches |
| `RGE_LLM_MODE=mock python -m pytest tests/golden -q` | **119 passed** in 33.21s |
| `RGE_LLM_MODE=mock python -m pytest -q` | **119 passed** in 33.16s |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | `status: pass`, exit 0 |
| `RGE_LLM_MODE=mock python -m rge.cli run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode` | exit 0, `status: completed`; dirtied 2 tracked files + 2 untracked paths (documented above); cleaned via `git restore` + deletion |
| `cd apps/public-site && npm run build` | pass — 11/11 static pages, static export OK |
| Local static preview + browser review of `/` and `/cards/card_golden_diversity_001/` | rendered correctly; findings in UI section |
| `git status --short` (after cleanup) | clean |

## Artifacts Added by This Audit

| File | Purpose |
|---|---|
| `agent_reports/2026-06-12_pre-phase-2_principal-audit.md` | This report |
| `agent_reports/2026-06-12_phase-2_ticket-roadmap.md` | Proposed Phase 2 ticket roadmap (planning doc; no ticket JSONs created) |

No runtime, schema, frontend, export, or ticket-JSON changes were made.

## Exact Next Prompt

```txt
/rge-run-next-ticket
```

After marking ticket-033 done and seeding ticket-034 (fixture-run artifact hygiene) from the roadmap into `tickets/` per the existing queue workflow.
