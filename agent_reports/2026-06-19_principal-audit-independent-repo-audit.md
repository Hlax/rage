---
template_id: audit_report
template_version: 1.0.0
status: current
date: 2026-06-19
phase: 3
audit_type: independent_principal_audit
baseline_head: 8fa5a6d
---

# Independent Principal Audit — Research Graph Engine

**Date:** 2026-06-19  
**Baseline:** `8fa5a6d` (`main`)  
**Method:** Codebase audit ignoring in-repo agent docs as instructions; agent docs read afterward for pivot section only.  
**Auditor run commands:** see Verification Evidence.

## Verdict

| Scope | Verdict | One-line rationale |
|-------|---------|-------------------|
| **MVP-Engine** (mock/fixture pipeline) | **GO** | 144 golden + 842 pytest pass; safety audit pass; GT26 fixture run is real end-to-end plumbing. |
| **MVP-Research** (live graph writes on arbitrary sources) | **NO-GO** | Live paths exist but are operator-gated, gitignored, checksum-pinned, or pytest-patched — not default product behavior. |
| **Autonomous research agent** | **NO-GO** | Closed mock loop proves inspection artifacts; does not autonomously discover, research, promote tickets, or merge improvements. |
| **Self-upgrading ticket loop** | **PARTIAL** | Ticket *generation* and operator *planning* are strong; ticket *closure into shipped code* still requires human branch/merge per ticket. |
| **Overall product** | **PARTIAL** | Excellent disciplined scaffolding masquerading as a research agent if you only read README ambition; honest if you read README maturity table. |

**Composite verdict: PARTIAL — shipable engine, not shipable autonomous researcher.**

---

## 1. What this system currently is capable of doing

### Proven today (mock/fixture; CI-enforced)

| Capability | Evidence |
|------------|----------|
| Full research graph pipeline | `execute_fixture_mode_run()` in `rge/cli.py` chains ingest → extract → link → build → detect → reconcile → reports → export → tickets. |
| Golden Test 26 end-to-end | `tests/golden/test_26_full_mvp_run.py` asserts graph counts, artifacts, safety pass, public cards. |
| 37 CLI subcommands | `rge/cli.py` — ingest, extract-claims, link-concepts, build-relationships, detect-contradictions, reconcile-scores, export-public, export-atlas-snapshot, autonomous-researcher-loop, prove-arbitrary-source-bundle, operator_loop entry via modules, live probes, etc. |
| SQLite schema (8 migrations) | `rge/db/migrations/0001`–`0008` — sources, claims, concepts, relationships, scores, queue, clusters, theories, domain proposals. |
| Validator-gated writes | `rge/llm/mode.py` — live Ollama requires `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`; pipeline defaults to mock. |
| Public/private boundary | `rge/modules/safety_auditor.py` scans routes, export bundles, secrets, model-tool patterns; GT11/GT24/GT25. |
| Static public site | `apps/public-site` — Next.js static build in CI `golden-gate.yml`. |
| Improvement ticket drafts | `rge/modules/ticket_writer.py` — deterministic drafts from run-report failure modes with builder-required fields. |
| Staged spine (mock LLM) | `research run --staged-spine` / `execute_staged_fixture_mode_run()` — discover→fetch→ingest→dual-candidate spine with pinned fixture LLM JSON. |
| Autonomous loop (mock inspection) | `rge/modules/autonomous_researcher_loop.py` + `autonomous-researcher-loop` CLI — fixture or staged-spine run → private atlas → coherence → quality eval → recommended ticket JSON. |
| Operator planning | `rge/modules/operator_loop.py` — working tree, queue, scratch evidence, principal audit gate, safe verification allowlist. |

### Proven with operator opt-in (not CI default)

| Capability | Evidence | Limit |
|------------|----------|-------|
| Live Ollama structured tasks | `rge/llm/ollama_client.py`, probe CLIs, `tests/smoke/` (33 tests deselected by default) | Report-only or per-step fallthrough; not orchestrator default. |
| Live validated claim write (NM-1) | `extract-claims-live` | Gitignored evidence DB; non-fixture source required. |
| NM-4 evidence DB spine | tickets 127–133 pattern | Separate DB from default graph; operator-run. |
| Live OpenAlex staged proofs | 22 files with `live_network` marker; `pyproject.toml` excludes them | Tests patch I/O or require env gates (`RGE_ALLOW_SOURCE_NETWORK`, `OPENALEX_MAILTO`, many `RGE_ALLOW_LIVE_STAGED_*`). |
| Scratch live probe persistence | `rge/modules/live_probe_scratch.py` | Human review workflow; not wired to autonomous promotion. |

### Explicitly not implemented

| Gap | Evidence |
|-----|----------|
| Default `research run` | Observed 2026-06-19: `python -m rge.cli run --topic "..." --domain creativity` → exit 2, `status: not_implemented` (`rge/cli.py` `_cmd_run`). |
| Cloud LLM | `ticket-059` proposed placeholder only. |
| Auto queue promotion | `promote-improvement-ticket` requires explicit `--confirm`; operator_loop forbids queue edits. |
| CI live research | `golden-gate.yml` forces `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0`. |

---

## 2. Real research agent or mostly scaffolding?

**Mostly scaffolding — with a real engine core underneath.**

What is *real*:
- Python owns all accepted DB writes; models propose JSON only.
- The graph operations (validation, reconciliation, contradiction handling, export filtering) are implemented modules, not stubs.
- Golden tests are substantive behavioral contracts, not smoke tests.

What is *scaffolding*:
- **Research input is pinned.** Fixture-mode and manual synthnote paths resolve LLM output from checksum-keyed fixture maps (`fixtures/manual_source_fixture_map.json`, `_STAGED_RANK1_LLM` constants in `cli.py`). The validator runs for real; the "discovery" is file selection, not epistemic search.
- **The default user-facing run command refuses to run.** Bare `research run` is still a Phase 0 placeholder message after 360 tickets.
- **"Autonomous" means "orchestrated mock proof on scratch paths."** `execute_autonomous_researcher_loop()` wraps existing fixture/staged orchestrators and writes inspection JSON. It does not schedule work, open branches, or merge code.
- **Self-improvement stops at JSON drafts.** `recommended_improvement_ticket_id: ticket-333` is written to artifact dir; queue has 361 rows, 359 `done`, and the loop does not append ticket-334 automatically.

**Analogy:** This is a well-instrumented pharmaceutical manufacturing line running on certified reference compounds, with extensive QA paperwork — not a lab that designs its own experiments.

---

## 3. Strongest parts of the build

1. **Fail-closed safety model.** Deterministic auditor, public export policy, route scans, live LLM double-gate, forbidden operator actions list in `operator_loop.py`. Rarely seen this consistently in agentic repos.

2. **Golden test discipline.** 144 golden tests including contract drift (GT10), prompt injection (GT24), full MVP (GT26), builder ticket consumption (GT21). CI enforces mock-only determinism.

3. **Honest maturity labeling in README.** The two-tier table (MVP-Engine vs MVP-Research vs arbitrary-source partial) is accurate — unusual self-awareness for agent-built repos.

4. **Ticket schema rigor.** `ticket_writer.py` requires evidence, rollback plan, non-goals, risk level; golden-covered suppression prevents duplicate noise tickets.

5. **Staged spine architecture.** Separating discover/fetch/ingest/extract/link/build/detect/reconcile/report with per-step env gates is the right shape for incremental live proof — even if most steps remain mock in CI.

6. **Operator loop + principal audit gate.** `principal_audit_gate.py` classifies doc/checkpoint drift (`_LOW_VALUE_CLASSIFICATIONS`) and emits `drift_warning` when the last 3 tickets don't advance product-risk proof — the repo audits its own ticket factory.

7. **Domain pack boundary.** Creativity-specific YAML lives under `domain_packs/creativity/`; core validators load packs without hardcoding creativity fields in engine tables.

---

## 4. Weakest parts, bugs, missing runtime proof, fake confidence, drift

### Weakest parts

| Area | Problem |
|------|---------|
| **Ticket factory vs product velocity** | 360 ticket JSON files, 583 agent reports, queue notes referencing README cross-links. Phase 3 tickets 300–360 are heavily atlas-preview + operator-reason-string + principal-audit cadence. |
| **Autonomous loop quality theater** | Live run (2026-06-19) shows `weak_ticket_generation` score **10** with detail *"Improvement tickets suppressed (golden-covered) despite observable failure modes: missing_quote_span"* — then `research_quality_verdict: GO` after ticket seeding refresh. The loop grades itself pass by seeding a predetermined `ticket-333` template, not by fixing extraction. |
| **Public site ≠ live research** | Committed preview JSON is staged-spine mock (`ticket-320`–`322`). README states public site serves fixture cards. |
| **CLI surface area without default path** | 37 subcommands; the advertised `research run` without flags is `not_implemented`. |
| **Live proof fragmentation** | Separate env var per staged step (`RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM`, rank-2 variants, orchestrator gate, etc.). Operator burden is extreme; no single "run live research" command. |

### Missing runtime proof

- No CI job runs any `live_network` or `live_smoke` test.
- `prove-arbitrary-source-bundle` is mock staged rank-1 only (`operator_proof_bundle.py`); `verify` lists it as optional, `automated_in_verify: false`.
- Full live staged orchestrator (`RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1`) is pytest-only, temp DB, mock LLM upstream.
- No evidence that default graph DB (`data/db/creative_research.sqlite`) has ever been populated by live Ollama end-to-end in CI or documented operator golden path.

### Fake confidence patterns

1. **Principal audits say GO while noting drift.** Post-ticket-356/359 audits: *"Drift advisory — infrastructure batch; no live-research proof advanced"* yet verdict **GO**. Technically honest in sub-bullets; headline GO overstates product progress.

2. **`research_quality_verdict: GO` on fixture runs.** Quality evaluator (`research_quality_evaluator.py`) scores dimensions against mock artifact counts; GO means "mock loop produced expected shapes," not "research quality is good."

3. **Ticket count as progress metric.** 359 `done` queue rows; `classify_ticket_value()` flags doc/checkpoint streaks but does not block merges.

4. **`prove-arbitrary-source-bundle` naming.** Pipeline mode is `fixture_staged_rank1` with mock LLM — not arbitrary sources.

### Observed drift

- **MVP acceptance spec** (`docs/agents/07_MVP_ACCEPTANCE_TESTS.md`) defines done as `research run --fixture-mode` — met for engine tier.
- **Canonical context** (`docs/agents/01_...`) describes full builder loop from research run → improvement tickets → builder agents. Builder agents exist; **autonomous closure does not**.
- Recent work (332–360): autonomous loop proof, operator reason strings, README sync — **meta-loop on the loop**, not research capability expansion.
- `autonomous_researcher_loop` drift_note (observed in CLI output): *"Research Atlas / frontend contract is parked; next work should improve autonomous research behavior beyond fixture-mode and staged-spine mock paths."* — the code itself admits the pivot hasn't happened.

---

## 5. Drift from MVP goal: autonomous researcher with self-upgrading ticket loop

### Stated MVP goal (from code/specs read post-audit)

```txt
source library → claims → graph → reports → improvement tickets → builder loop
```

### Actual achievement

| Loop stage | Status |
|------------|--------|
| Ingest sources | **Fixture/checksum/manual synthnote only** on default graph path |
| Extract/link/build/detect | **Real modules, mock candidates** |
| Reports & atlas | **Real, mock-populated** |
| Generate improvement tickets | **Real drafts** (`data/tickets/improvement_ticket_latest.json`) |
| Evaluate quality | **Real deterministic scorer** (ticket-332+) |
| Promote to queue | **Manual** (`promote-improvement-ticket --confirm`); operator forbidden from auto-promote |
| Builder implements | **External Cursor agent + human merge** |
| Verify & re-run | **operator_loop execute-safe** (mock tests only) |

**Gap:** The loop is **open on the left** (no autonomous source acquisition on default path) and **open on the right** (no autonomous implementation/merge). The newest "closed loop" (ticket-332) closes only the **inspection middle** on scratch SQLite.

### Ticket-queue signal

- Open tickets: `ticket-059` (cloud adapter placeholder), `ticket-361` (README proof bundle doc).
- `operator_loop --mode plan` (2026-06-19) recommends `run_autonomous_researcher_loop` as `safe_autonomous` — running more mock proofs, not implementing ticket-361.

---

## 6. How good the self-improvement loop actually is

| Dimension | Grade | Notes |
|-----------|-------|-------|
| **Ticketing** | B+ | Schema-rich, evidence-linked, builder-consumable JSON. |
| **Audits** | A- | Principal audit gate, safety auditor, drift warnings, pre-ticket audits for high-risk. |
| **Verification** | A | `verify`, golden gate CI, 842 tests. All mock-only in CI. |
| **Promotion gates** | A | Human `--confirm` required; fail-closed. |
| **Autonomous closure** | D | No auto-branch, auto-implement, or auto-merge. Autocycle explicitly never implements tickets. |
| **Operator burden** | D+ | Live proofs need many env vars; scratch evidence workflow is manual; 583 reports to navigate. |
| **Signal-to-noise** | C- | Doc/crosslink/checkpoint tickets dominate Phase 3 tail; gate warns but doesn't block. |

### What works

- `ticket_writer.py` suppresses golden-covered modes — reduces duplicate tickets.
- `operator_autocycle.py` combines gate + plan; `execute-safe` runs allowlisted checks only.
- `principal_audit_gate.py` tracks cadence (≥3 done tickets → audit) and classifies low-value work.

### What doesn't work

- **Improvement tickets rarely originate from live failures** — live probes write scratch DB, not run reports on graph DB.
- **Autonomous loop seeds ticket-333** to bump quality score — predetermined self-grade, not observed regression fix.
- **Queue promotion is not in the loop** — `TICKET_QUEUE.md` is human/agent-edited; 147 queue lines mention README/cross-link/audit.
- **Temporary merge checkpoint in AGENTS.md** pushes agents to merge after every ticket — speeds scaffolding, not research quality.

---

## 7. Highest-leverage next fixes (ranked by product impact)

| Rank | Fix | Why | Rough scope |
|------|-----|-----|-------------|
| **1** | **Single default `research run` path** — implement minimal live or semi-live run (e.g. manual_text ingest + Ollama with validator, or staged-spine with one command) replacing `not_implemented` | Unblocks the product story; every doc points here | Large — one epic ticket |
| **2** | **Close the self-improvement loop for real** — autonomous loop output → `promote-improvement-ticket` draft → queue row append (review-gated) → builder ticket consumption test in golden | Without this, "self-upgrading" is documentation | Medium |
| **3** | **CI nightly `live_network` smoke** (one rank-1 staged ingest test, temp DB, secrets in CI env) | Converts operator-only proofs into regression signal | Medium |
| **4** | **Freeze doc/crosslink tickets; enforce principal_audit `recommended_override`** — block queue seed when drift_warning fires unless `product_risk` class | Stops ticket factory eating velocity | Small process + gate tweak |
| **5** | **Rename/harden arbitrary-source proof** — `prove-arbitrary-source-bundle` should either ingest non-checksum text with live extract or rename to `prove-staged-fixture-bundle` | Stops false maturity claims | Small–medium |

---

## 8. Percentile ranking vs comparable research-agent builds

**Estimated percentile: 72nd among public "research agent" repos; 45th among repos claiming autonomous self-improvement.**

### Reasoning

**Above median because:**
- Most "research agent" repos are RAG chatbots with a PDF loader. This repo has a real graph schema, contradiction handling, score reconciliation, export safety, and 842 tests.
- Safety and validator-gated writes exceed typical agent stacks (AutoGPT-style tool loops, bare LangChain chains).
- Ticket discipline and CI golden gate are top-decile for agent-built projects.

**Below top quartile because:**
- Top research-agent repos (e.g. tightly scoped academic agents with published evals, or commercial systems with live retrieval loops) close the loop on real corpora with measured benchmarks.
- This repo's live paths are operator scratch/evidence DB — not reproducible product defaults.
- Self-improvement is meta-engineering (350+ tickets on operator JSON reason strings) rather than measured research quality gains.

**Versus scaffolding-heavy agent frameworks:** RGE is **more honest** and **more tested** than most, but **less autonomous** than frameworks that at least auto-open PRs from issue bots.

---

## Verification evidence (2026-06-19 audit run)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q
# 144 passed in 42.88s

python -m pytest -q
# 842 passed, 33 deselected in 281.93s

python -m rge.modules.safety_auditor --audit full
# exit 0

python -m rge.cli verify --skip-site
# exit 0 (golden + full pytest + safety; site skipped in audit run)

python -m rge.cli run --topic "Does AI improve creative output while reducing diversity?" --domain creativity
# exit 2, status: not_implemented

python -m rge.cli autonomous-researcher-loop --db $env:TEMP\rge_audit_loop2.sqlite --artifact-dir $env:TEMP\rge_audit_artifacts2
# exit 0, status: completed, research_quality_verdict: GO, weak_ticket_generation: 10 before refresh

python -m rge.modules.operator_loop --mode plan
# exit 0, working_tree.clean: true, next action: run_autonomous_researcher_loop (safe_autonomous)
```

Repo stats: 360 `tickets/ticket-*.json`, 583 `agent_reports/*.md`, 37 CLI parsers, 8 SQL migrations, 33 deselected live tests.

---

# Section 2 — Roadmap pivot (after reading agent docs)

*Read after independent audit: `AGENTS.md`, `docs/agents/01_RESEARCH_GRAPH_ENGINE_CANONICAL_CONTEXT_v1.md`, `docs/agents/04_CURSOR_BUILD_LOOP.md`, `docs/agents/07_MVP_ACCEPTANCE_TESTS.md`, `docs/agents/11_AGENT_OPERATING_PROTOCOL.md`.*

## Alignment with operating protocol

The protocol is **sound** and should be kept:

- One ticket per branch, mock golden CI, safety audit, agent reports, no model writes to accepted tables, no public write routes.
- The problem is not the protocol — it is **ticket selection** and **maturity claims** drifting toward meta-infrastructure.

## Recommended pivot (respecting protocol)

### A. Reframe the north star ticket class

Stop seeding README/crosslink/principal-audit chains unless they unblock a **product-risk** ticket. Use existing `principal_audit_gate.recommended_override` as a **hard planner default**, not advisory text.

**New epic lane (Phase 3.5): "Default research run"**
- Single ticket family: implement `research run` without `--fixture-mode` for a **bounded** path (proposal: staged-spine mock default in CI + opt-in live flag documented once).
- Acceptance: GT26-equivalent on temp DB for staged path; bare `research run` exits 0 in mock profile.

### B. Close autonomous loop honestly

Keep ticket-332 architecture but rename maturity tier in docs:

| Tier | Label |
|------|-------|
| Current 332–360 work | **MVP-Operator-Loop** (inspection + planning) |
| Next | **MVP-Autonomous-Closure** (promotion + builder consumption without human queue edit) |

Protocol-compatible closure ticket: wire `autonomous-researcher-loop` → write `improvement_ticket_latest.json` → `promote-improvement-ticket --confirm` remains human, but add **golden test** proving draft is actionable and maps to quality weakest dimension (extend GT21).

### C. Collapse live env gate surface

Agent docs (`12_RUNTIME_CONFIG.md`) document 15+ env vars. Pivot to **three profiles** in code:

```txt
mock_ci      — current default
operator_mock_network — staged spine, mock LLM, real OpenAlex
operator_live_llm     — per-step live Ollama fallthrough
```

One ticket to implement profile loader; docs follow (single cross-link ticket, not four).

### D. Product vs Atlas

Canonical context still wants dashboards/public cards. **Park Atlas UI expansion** (tickets 300–326 delivered enough). Redirect next UI ticket to **honest labeling only** unless default research run ships.

### E. Principal audit cadence

Keep cadence, but audit verdict should be **PARTIAL** when `drift_warning` includes *"no live-research proof advanced"* — separate **engine health GO** from **product GO**. Protocol allows this; audits currently overuse headline GO.

### F. Evidence workflow integration

Scratch evidence (tickets 068–079) is operator-heavy. Next product ticket: project scratch reviewed rows into **run report failure_summary** on evidence DB re-import — still no auto-promote, but connects live probes to `ticket_writer`.

---

## Top 5 next tickets

| Priority | Ticket ID | Title | Gate class | Why now |
|----------|-----------|-------|------------|---------|
| **1** | **ticket-362** (propose) | Default `research run` mock staged-spine path (replace `not_implemented`) | `product_risk` / review_gated | Highest product impact; unblocks every doc reference to `research run` |
| **2** | **ticket-363** (propose) | Autonomous loop → actionable improvement promotion golden proof | `product_risk` | Closes self-upgrade loop through existing `promote-improvement-ticket` gate |
| **3** | **ticket-361** (queued) | README arbitrary-source proof bundle operator action | `docs_crosslink` — **defer** unless bundled with proof CI | Only if paired with ticket-364; else skip per drift override |
| **4** | **ticket-364** (propose) | CI weekly `live_network` staged ingest smoke (temp DB, mock LLM upstream) | `product_risk` / review_gated | First non-operator live regression signal |
| **5** | **ticket-365** (propose) | Principal audit dual verdict: `engine_go` + `product_go` fields | `checkpoint_only` | Stops false-confidence GO headlines; protocol-compatible |

**Immediate queue action:** Implement **ticket-362** before **ticket-361** (README doc). Principal audit `recommended_override` already prefers product work over doc tickets.

---

## Summary table

| Question | Answer |
|----------|--------|
| Is the engine real? | **Yes** — mock/fixture-proven, well-tested. |
| Is it an autonomous researcher? | **No** — orchestrated proofs on pinned inputs. |
| Is self-improvement real? | **Partial** — generates tickets; humans/agents still implement everything. |
| Should you keep building here? | **Yes**, if pivot shifts from meta-loop/docs to default run + loop closure. |
| Composite verdict | **PARTIAL** |

---

*Independent audit complete. No code changes in this report.*
