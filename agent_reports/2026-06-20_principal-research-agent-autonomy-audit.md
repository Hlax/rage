# Principal Research Agent Autonomy Audit

**Date:** 2026-06-20  
**Baseline commit:** `3708e9c` (Add live abstract evidence quality smoke and checkpoint reports.)  
**Auditor:** Principal agentic systems auditor (read-only inspection + verification runs)  
**JSON companion:** `agent_reports/2026-06-20_principal-research-agent-autonomy-audit-latest.json`

---

## Verdict

| Scope | Verdict | Rationale |
|-------|---------|-----------|
| **Overall** | **PARTIAL** | Real engine + new live-abstract proofs; not an autonomous researcher. |
| MVP-Engine (mock/fixture CI) | **GO** | 164 golden pass; safety audit pass; public-site build pass. |
| MVP-Research (live arbitrary writes) | **PARTIAL** | Live OpenAlex/arXiv abstract path proven with operator gates; extraction still mock-default in smokes. |
| Autonomous research agent | **NO-GO** | No self-directed discovery→synthesis→ship loop; mock orchestration + human tickets. |
| Self-improvement ticket loop | **PARTIAL** | Strong draft generation and planning; closure requires human branch/merge. |
| Atlas research cockpit | **PARTIAL** | Excellent operator debug surface; mixed fixture/live JSON; not live-connected. |

**Composite: PARTIAL — a disciplined research *engine* with growing live-abstract *proofs*, not a product autonomous agent.**

---

## Executive Summary

RGE has materially advanced since the 2026-06-19 independent principal audit. The repo now proves **live OpenAlex + arXiv abstract resolution**, **purpose-gated acceptance**, **quote-backed claims** (with mock extraction), **evidence atoms**, **trace summaries**, and **Atlas panels** wired from run artifacts. Multi-question live runs (5 questions, 19 aggregate accepted claims) show purpose routing that honestly fails strict agency/style questions instead of shallow universal GO.

What has **not** changed at the product level: the system is still a **semi-manual operator harness** around excellent Python validation plumbing. CI remains mock-only. `execute-safe` is blocked on the current dirty tree. Full pytest fails on **operator_loop plan drift** (uncommitted `full_atlas_refresh_checklist` priority). Local Ollama on the same live abstracts is **thinner than mock** (2 vs 5 accepted). OpenAI/paid synthesis is **zero code** (ticket-059 placeholder). Graph relationships recently improved via **concept-seed upgrade**, not semantic discovery at scale. Atlas `/atlas-preview` is a **static JSON debugger**, not a live cockpit.

**Brutal honesty:** If you demo RGE today, you are demoing **operator-gated live metadata + mock extraction + static Atlas JSON**, not an agent that reads papers and upgrades itself.

---

## Scores (0–1)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Research data quality | **0.55** | Live abstracts real; claims quote-backed under mock extract; strict questions thin; atoms weak. |
| Atlas / frontend readiness | **0.62** | Many debug panels; staged-fixture snapshot vs live health/trace split; build passes. |
| Graph maturity | **0.48** | Orphan claims fixed by seeding; 0 multi-claim atoms; 0 synthesis-ready clusters. |
| Local model readiness | **0.52** | Ollama wired, probes exist; live abstract comparison GO but quality thinner than mock. |
| Paid / OpenAI API readiness | **0.15** | Policy only; no adapter, no key loading, no dry-run client. |
| Automation readiness | **0.58** | Mock autonomous loop + operator plan; no live auto-research or auto-merge. |
| Safety / public-private | **0.88** | Safety audit pass; public_safe flags; fail-closed LLM/network gates. |

---

## Verification Evidence (this audit)

### Git

```text
git status --short  → DIRTY (60+ modified/untracked; operator packet wave in progress)
git log --oneline -n 12 → 3708e9c … 5e1a312 (live abstract, atlas panels, source health)
```

### `python -m rge.cli verify --skip-site` (mock)

| Check | Result |
|-------|--------|
| golden_tests | **PASS** — 164 passed |
| full_pytest | **FAIL** — 1117 passed, **1 failed** |
| safety_audit | **PASS** |

**Failure (classified, not hidden):**

`tests/unit/test_operator_loop_plan.py::test_atlas_refresh_recommended_action_when_missing_source_health_artifact`

- Expected `action_id`: `refresh_atlas_public_previews`
- Actual: `run_full_atlas_refresh_checklist`
- **Classification:** Uncommitted operator_loop behavior change + incomplete test update during full-atlas packet work. Product regression risk: plan mode now prioritizes live checklist over staged refresh script.

### Targeted tests

| Suite | Result |
|-------|--------|
| `test_live_abstract_evidence_quality.py` + `test_multi_question_live_abstract.py` | **11 passed** |
| `test_operator_loop_plan` (atlas refresh case) | **1 failed** (same drift) |

### Safety audit

`python -m rge.modules.safety_auditor --audit full` → **PASS**

### Public site

`cd apps/public-site && npm run build` → **PASS** (static `/atlas-preview` included)

### Operator loop plan (dirty tree)

- `execute_safe_eligible`: **false**
- `next_recommended_action`: `resolve_documentation_git_drift` (**blocked**)
- Working tree dirty paths include atlas-preview TS, atlas JSON, operator modules, untracked packet scripts.

---

## What Is Real vs Fixture / Mock

### CI-enforced (real plumbing, mock epistemics)

| Layer | Mode | Evidence |
|-------|------|----------|
| Golden tests | mock LLM | 164 tests; GT26 full MVP fixture run |
| Default verification | mock | `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0` |
| Staged-spine orchestrator | mock LLM after optional live fetch | Checksum-pinned fixture JSON for extract/link/build/detect |
| `research run` default | staged_spine mock | ticket-362; **no longer** bare `not_implemented` |
| `research run --fixture-mode` | creativity fixture graph | Golden MVP topic pipeline |
| `atlas_snapshot_preview.json` | staged-fixture graph | `snap_staged_fixture_preview_v0_001`, mode `fixture` |
| Public cards | golden export | `card_golden_diversity_001`, etc. |
| Autonomous-researcher-loop | mock inspection | Fixture or staged-spine → atlas/coherence/quality/ticket JSON |

### Operator opt-in live (real network/metadata; extraction usually still mock)

| Layer | Mode | Evidence |
|-------|------|----------|
| OpenAlex discover/fetch | live HTTP | `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO` |
| arXiv resolver | live | `atlas_source_health_run_latest`: 5 arxiv + 1 openalex |
| Unpaywall enrich | optional live | live-source-expansion packet; `enrich_unpaywall` flag |
| Live abstract evidence smoke | live metadata + **mock extract** | `test_live_network_abstract_evidence_quality_smoke.py` |
| Multi-question live abstract | live + mock extract | 5 questions; aggregate 19 accepted / 6 rejected |
| Local model comparison | live abstracts + **live Ollama** | 2 accepted vs mock 5 — thinner |
| Graph maturity upgrade | live ingest subset + seed upgrade | 11 accepted claims; relationships 8; PARTIAL verdict |
| `atlas_source_health_run_latest.json` | **live run artifact** | Question: "How does AI affect human creativity?" |
| `atlas_multi_question_live_abstract_latest.json` | **live run aggregate** | 5 question runs with per-question verdicts |
| `tiny_atlas_connection_preview.json` | **fixture audit snapshot** | Explicit `readiness_verdict: PARTIAL - fixture-backed` |

### Not implemented

| Gap | Status |
|-----|--------|
| OpenAI / cloud adapters | ticket-059 proposed placeholder only |
| Default live LLM orchestrator | Explicitly forbidden; per-step fallthrough only |
| Auto queue promotion / merge | Forbidden in operator_loop |
| Live research in CI | `live_network` marker excluded from default pytest |

---

## Research-Agent Function (specific questions)

### Can the agent take a real question and produce useful, quote-grounded evidence?

**Partially — with operator setup and mock extraction.**

- **Yes (bounded):** Live abstract path resolves real OpenAlex/arXiv records, purpose-fits metadata, accepts quote-backed claims under mock extraction, promotes atoms, builds trace summaries visible in Atlas.
- **Evidence:** `agent_reports/2026-06-20_live-abstract-evidence-quality-latest.json` — 5 live sources, 5 accepted, 5 atoms, 5 relationships, trace_count 5, `evidence_quality_verdict: GO`.
- **No (full agent):** No automatic question→literature→synthesis without operator env scripts, temp DB paths, and mock LLM for extraction in documented smokes.

### Live vs mock vs fixture-backed?

| Step | Default CI | Operator live abstract smokes | Full fixture graph |
|------|------------|--------------------------------|-------------------|
| Discover/fetch | stub/mock | **Live** OpenAlex/arXiv | Fixture files |
| Ingest/parse | fixture | Live abstract_record parser | Manual + fixture TEI/PDF |
| Extract claims | **mock** | **mock** (unless live LLM gates) | mock/checksum |
| Link/build/detect | mock | mock in smokes | mock |
| Reconcile/report | deterministic | deterministic | deterministic |
| Atlas public JSON | mixed | live health + fixture snapshot | fixture |

### Are live abstract results genuinely useful or shallow tests?

**Mixed — better than pure fixture theater, not yet research-grade synthesis input.**

- **Genuine:** Real metadata diversity, purpose gating on strict questions (agency: 1 accepted / 4 rejected; style: partial match), trace summaries with quote flags, public_safe scanning.
- **Shallow:** ~5 sources per question, mock extraction inflates acceptance vs live Ollama, relationships often 1:1 with claims, `concept_count: 0` on several trace rows, `why_clustered` empty.
- Multi-question GO is **not** "five deep literature reviews" — it is "five bounded resolver runs with acceptance gates."

### Is the graph producing meaningful relationships or thin atoms/cards?

**Mostly thin atoms; relationships recently densified by upgrade seeding.**

- Graph maturity packet: **8 single-claim atoms**, **0 multi-claim**, **0 synthesis-ready clusters**, **8 weak atoms**, relationship_density 1.0 after concept-seed (orphan claims 8→0).
- Relationships include support/contradiction/qualification types in health artifact, but **multi_claim_atom_count: 0**, **clustered_atom_count: 0**.
- Public cards remain **two golden cards** — not driven by live abstract runs.

### Scale: 10 questions, 100 sources, 1,000 sources?

| Scale | Predicted behavior | Confidence |
|-------|-------------------|------------|
| **10 questions** | Operator scripts could run sequentially; no unified orchestrator; Atlas JSON manual sync; SQLite single DB; **no proven batch command** | Medium — 5Q proven |
| **100 sources** | Per-source extract/link LLM calls (mock or Ollama) **linear cost**; no pagination proof in repo; queue/rank exists but not stress-tested | Low |
| **1,000 sources** | **Not viable** without acquisition batching, incremental ingest, cost caps, and synthesis gating — **no architecture proof** | Very low |

---

## Operator Loop

### Where is the human still running commands manually?

| Activity | Manual today |
|----------|----------------|
| Live network env setup | `RGE_ALLOW_SOURCE_NETWORK`, `OPENALEX_MAILTO`, per-smoke `RGE_ALLOW_LIVE_*` |
| Atlas public JSON refresh | `scripts/run_full_atlas_refresh_checklist.py` or per-script refresh + `npm run build` |
| Live pytest smokes | `pytest -m live_network` per packet |
| Live Ollama per-step staged spine | Separate gates per extract/link/build/detect (rank-1 closed at detect) |
| Scratch live probe review | `probe-scratch-evidence-review` + human sign-off |
| Ticket implementation | Human branch per ticket; merge per AGENTS.md checkpoint |
| Improvement promotion | `promote-improvement-ticket --confirm` (forbidden in execute-safe) |

### What can be safely chained now?

| Chain | Command / path | Gates |
|-------|----------------|-------|
| Mock verification | `python -m rge.cli verify` | clean tree, mock |
| Mock autonomous inspection | `autonomous-researcher-loop --db scratch` | execute-safe when clean |
| Mock staged spine | `research run --topic ... --domain ...` | default staged mock |
| Full atlas refresh (operator) | `run_full_atlas_refresh_checklist.py` | review_gated; live env for non-fixture-only |
| Prove arbitrary bundle | `prove-arbitrary-source-bundle` | review_gated; mock |

### What still requires human approval?

- All **live network** and **live LLM** work (review_gated or manual)
- **Full atlas refresh** with live abstract smoke
- **Scratch evidence** promotion to improvement tickets
- **Queue edits**, merges, pushes, public publish
- **ticket-059** / any paid API (not started)

### Minimum viable one-button research run (proposed)

See **Proposed One-Button Research Run** section below.

### Operator loop: automatic vs recommend-only

| Automatic (execute-safe, clean tree) | Recommend only |
|--------------------------------------|----------------|
| golden + pytest + safety + site build | live smokes |
| mock autonomous-researcher-loop scratch proof | full atlas refresh checklist |
| | scratch evidence review |
| | arbitrary source proof bundle |
| | staged-spine with live fetch |

**Assessment:** The operator loop is **real planning infrastructure**, not documentation cosplay — but it **recommends** more than it **runs** for anything live or product-facing.

---

## Atlas / Frontend

### Does `/atlas-preview` show the right information for debugging?

**Yes for operator packet debugging; split-brain for graph structure.**

Present panels (from `atlasPreview.ts` + page):

| Panel | Backing |
|-------|---------|
| Snapshot graph (nodes/edges/cards/follow-ups) | **Fixture** `atlas_snapshot_preview.json` (staged spine) |
| Coherence | **Fixture** `atlas_coherence_preview.json` |
| Tiny connection preview | **Fixture audit** `tiny_atlas_connection_preview.json` |
| Source health / purpose / readiness / trace / graph summary | **Live run** `atlas_source_health_run_latest.json` |
| Multi-question live abstract | **Live aggregate** artifact |
| Local model comparison | **Operator packet** artifact |
| Graph maturity upgrade | **Operator packet** artifact |
| Live source expansion | **Operator packet** artifact |
| Web adapter / Scrapling proof | **Operator packet** artifact |
| PDF/TEI milestone | **Operator packet** artifact |
| Demo loop polish | **Operator packet** artifact |
| Full atlas refresh checklist | **Operator packet** artifact |
| Gaps / next move | Derived from above |

Page comment: *"Static fixture JSON only; no fetches"* — partially outdated; several panels are live-run backed but still **build-time static imports**.

### What would make Atlas a research cockpit?

1. Single **live DB export** driving snapshot + health (eliminate fixture/live split)
2. Run selector (question, run_id, timestamp) without rebuild
3. Drill-down from trace → claim → source ref → acquisition status
4. Synthesis readiness dashboard (multi-claim atoms, cluster maturity, purpose mismatch rate)
5. Live vs mock / LLM mode badge per run
6. Operator action panel surfacing `operator_loop --mode plan` next step (read-only JSON feed)

### Missing before polished frontend

- Unified data contract version across panels
- No runtime API (static export only by design — safety win)
- No graph visualization (text-first tables)
- Public cards not connected to live runs
- No auth/deploy story for private operator cockpit

**Atlas frontend readiness: debug cockpit GO; product UI NO-GO.**

---

## Evidence Graph

### Are evidence atoms reusable?

**Partially.** Atoms exist with maturity (`weak`/`promising`), training_suitability (`not_ready`), trace refs, and public_safe flags. Reuse for synthesis requires **multi-claim, cross-source, clustered** atoms — **not present** (0 multi-claim atoms in live maturity upgrade).

### Are relationship edges meaningful?

**Operationally typed but often mechanically seeded.** Support/contradiction/qualification edges appear in trace summaries. Graph maturity upgrade added **14 seeded concept links** to eliminate orphans — useful for density metrics, not discovery insight.

### Are trace summaries sufficient for local or paid synthesis?

**For debugging: yes. For synthesis: no.**

Trace rows explain `why_connected` with template strings; `why_clustered` often empty; `concept_count: 0` on live traces. Paid synthesis should consume **packetized atom clusters + claim refs**, not raw traces alone.

### Metrics that should gate synthesis readiness

| Metric | Current live health artifact | Suggested gate |
|--------|------------------------------|----------------|
| `multi_claim_atom_count` | 0 | ≥ N per cluster |
| `synthesis_ready_cluster_count` | 0 | ≥ 1 |
| `weak_atom_count` | 5–8 | < 30% of atoms |
| `purpose_mismatch_count` | 0 on open Q; high on strict | per question intent |
| `quote_backed_accepted_count` | 5 per open Q | 100% of accepted |
| `source_diverse_atom_count` | 0 | ≥ 2 sources per cluster |
| `training_suitability` | not_ready | ready_for_synthesis subset |

### Missing graph objects

- Cross-run lineage at Atlas snapshot level (fixture snapshot has rank2; live health is single-question)
- Hypothesis/theory nodes in live panels
- Acquisition failure → improvement ticket auto-link in Atlas
- Synthesis packet export (evidence-only bundle for LLM)

---

## API / Model Readiness

### Local Ollama / Qwen extraction

| Item | Status |
|------|--------|
| Registry | mock + ollama only; fail-closed |
| Live gate | `RGE_ALLOW_LIVE_LLM=1` required |
| model-health CLI | exists |
| Live abstract comparison | **GO** but **thinner than mock** |
| Staged per-step live fallthrough | rank-1 closed at detect; rank-2 closed at detect |
| CI | never live |

**Score rationale:** Infrastructure GO; quality NO-GO for default local research.

### OpenAI API synthesis

**Not implemented.** ticket-059 placeholder. Policy in `docs/agents/13_MODEL_ESCALATION_POLICY.md` defers cloud.

### Paid API escalation

No cost caps, no budget env vars, no adapter — policy text only.

### Multi-model comparison

Local vs mock comparison packet exists (`atlas_local_model_extraction_comparison_latest.json`). No cloud comparison path.

---

## Proposed OpenAI API / Paid Synthesis Integration Plan

Safe integration **when ticket-059 is promoted** (not implemented in this audit):

1. **Env-key loading only** — `OPENAI_API_KEY` / `RGE_OPENAI_API_KEY`; never log, never commit, never in artifacts.
2. **Fail-closed default** — `RGE_CLOUD_LLM_ENABLED=0`; registry raises if cloud mode without key + enable flag.
3. **Mock/dry-run default** — `MockCloudClient` returns fixture synthesis JSON for CI; `--dry-run` logs packet hash only.
4. **Cost caps** — `RGE_CLOUD_MAX_USD_PER_RUN`, `RGE_CLOUD_MAX_TOKENS_PER_CALL`; hard stop mid-run with partial artifact.
5. **Packetized evidence input only** — Input schema: `{atoms[], claims[], source_refs[], trace_refs[], purpose}` — **no raw PDF/HTML**.
6. **Output cites refs** — Every synthesis sentence carries `claim_ids[]`, `atom_ids[]`, `source_refs[]`; validator rejects orphan prose.
7. **Human confirmation gate** — `research synthesize --confirm` separate from extract; operator_loop forbidden list includes cloud calls in execute-safe.
8. **No CI** — Cloud tests use mock client only.
9. **Escalation policy tie-in** — Require `synthesis_ready_cluster_count ≥ 1` from graph metrics before cloud mode is offered in plan mode.

---

## Automation / Self-Improvement

### Is the recommender choosing the right next packet?

**Mostly yes for engineering velocity; mixed for product risk.**

Recent operator packet chain: live abstract → full atlas checklist → multi-question → live source expansion → local model comparison → graph maturity → web adapter → pdf tei → demo polish — **logical acquisition→quality→graph→acquisition hardening arc.**

Drift: improvement tickets from **fixture failure modes** (blocked_by_quality_gate, pdf_parser_unavailable) still surface; packet recommender can mis-route `missing_quote_span` to demo-loop (documented in 2026-06-19 data-quality audit).

### Improvement tickets: real metrics or test scaffolding?

**Both.** `research_quality_evaluator.py` scores observable dimensions from run artifacts; templates like `ticket-333` seed from `weak_ticket_generation`. Autonomous loop can **GO** while observing golden-covered rejection modes — grading theater if interpreted as product quality.

### Automation safe now

- `verify` / execute-safe on **clean** tree
- Mock autonomous-researcher-loop scratch proof
- Improvement **draft** JSON generation
- Principal audit gate + autocycle **plan** mode
- Deterministic reconcile/report on staged spine

### Automation premature

- Auto-merge ticket branches
- Live network in CI (ticket-364 proposed — still review)
- Cloud synthesis
- Auto-promote improvement tickets
- 10+ question unattended live runs without cost/quality caps

### Next autonomous loop milestone

**Milestone:** *Closed mock research run with live-fetch option, unified Atlas export, green pytest, and one actionable non-golden improvement draft — still no merge.*

Concrete: fix operator_loop drift → commit packet wave → `one-button-research-run-v1` on scratch DB → gate ticket-059 spec on `synthesis_ready_cluster_count`.

---

## Safety / Public-Private Boundaries

| Finding | Status |
|---------|--------|
| Safety auditor full | **PASS** |
| No public write routes | Confirmed in auditor patterns |
| Live artifacts `public_safe` / `atlas_artifact_public_safe` | Present on live JSON |
| export-public publish gated | execute-safe forbids |
| LLM fail-closed | Unknown mode → error |
| Network fail-closed | `RGE_ALLOW_SOURCE_NETWORK` required |
| Scratch DB gitignored | Operator evidence not graph authority |

**No critical safety regressions observed.** Main risk is **semantic overclaim** in marketing if live abstract GO is read as fully live research.

---

## Top 10 Blockers

1. **Pytest red** — operator_loop plan vs `run_full_atlas_refresh_checklist` action_id drift.
2. **Dirty tree** — blocks execute-safe; hides CI truth.
3. **Mock extraction in live abstract GO path** — not end-to-end live epistemics.
4. **Local Ollama thinner than mock** on same abstracts.
5. **Zero multi-claim / synthesis-ready clusters** on live graph.
6. **Atlas snapshot fixture vs live health split** — confusing graph truth.
7. **Operator env gate fragmentation** — unsustainable for humans.
8. **No paid/cloud synthesis path** — ticket-059 deferred.
9. **Scale unproven** beyond ~5 sources × 5 questions.
10. **Self-improvement does not ship code** — tickets stop at drafts + human branches.

---

## Top 10 Highest-ROI Improvements

1. Fix operator_loop test drift; restore green full pytest.
2. Commit or split operator packet wave into reviewable tickets.
3. **One-button research run** — question → staged spine → private atlas → quality JSON.
4. Live Ollama abstract extract with **quote-validity ≥ mock baseline** gate.
5. Multi-claim atom clustering across abstracts/sources.
6. Unify Atlas snapshot source to live DB export when health artifact exists.
7. Synthesis readiness metrics panel with explicit NO-GO until thresholds met.
8. Consolidated operator env profile doc + single `source-health-smoke` script.
9. 10-source live abstract batch proof (temp DB).
10. ticket-059 spec + mock cloud client (no real key in CI).

---

## Recommended Next 5 Packets

| # | Packet | Why |
|---|--------|-----|
| 1 | operator-loop-plan-drift-fix | Restore CI truth; unblock execute-safe |
| 2 | one-button-research-run-v1 | Reduce manual command chains |
| 3 | live-ollama-abstract-extract-gate | Close mock/live gap on real abstracts |
| 4 | multi-claim-atom-clustering | Graph maturity for synthesis |
| 5 | openai-synthesis-adapter-spec | Safe paid path design before code |

---

## Proposed One-Button Research Run Design

```powershell
# Mock default (CI-parity, scratch DB only)
python -m rge.cli research run `
  --topic "How does AI affect human creativity?" `
  --domain creativity `
  --db data/db/scratch_research.sqlite `
  --output-dir data/reports/scratch_research `
  --export-atlas-snapshot data/reports/scratch_research/atlas_snapshot.json `
  --quality-report data/reports/scratch_research/research_quality.json

# Optional live network (still mock LLM unless --live-llm-extract)
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m rge.cli research run ... --live-network --source-limit 10

# Optional live extract (operator explicit)
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
python -m rge.cli research run ... --live-network --live-llm-extract
```

**Outputs:** SQLite DB, run report, private atlas snapshot, coherence report, research quality eval, recommended improvement draft JSON (not queue append).

**Must not:** auto `export-public --publish`, auto merge, cloud calls without separate gate.

**Operator_loop:** recommend `research run` when tree clean and no active ticket; execute-safe runs mock variant only.

---

## What Not to Build Yet

- Polished public research UI / graph viz product
- Auto ticket queue promotion and auto-merge
- OpenAI calls in CI or execute-safe
- Sending raw PDFs/HTML to paid models
- 1000-source batch orchestration without 10-source proof
- Marketing "autonomous agent" claims without live LLM + synthesis gates
- Replacing human ticket review with agent merge

---

## Agent Report Index Consulted

Latest JSON packets under `agent_reports/*latest.json`:

- `2026-06-20_live-abstract-evidence-quality-latest.json` — GO
- `2026-06-20_multi-question-live-abstract-runs-latest.json` — GO (19 accepted)
- `2026-06-20_operator-full-atlas-refresh-checklist-latest.json` — GO 7/7
- `2026-06-20_local-model-extraction-comparison-latest.json` — GO, thinner local
- `2026-06-20_graph-maturity-evidence-atom-upgrade-latest.json` — PARTIAL
- `2026-06-20_live-source-expansion-latest.json` — GO
- `2026-06-19_data-quality-evidence-atoms-acquisition-audit-latest.json` — PARTIAL

Prior principal baseline: `agent_reports/2026-06-19_principal-audit-independent-repo-audit.md`

---

## Closing

RGE is **not** becoming a fully autonomous research agent yet. It **is** becoming a **credible local-first research engine** with **honest live-abstract proofs**, **purpose gating**, and an **operator-grade Atlas debugger** — provided you read PARTIAL/NO-GO verdicts literally and fix pytest drift before claiming green.

**Next honest milestone:** one-button mock research run + green CI + live Ollama matching mock quote-validity on 10 abstracts — then revisit ticket-059.
