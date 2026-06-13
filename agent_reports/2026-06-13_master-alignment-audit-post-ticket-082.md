---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Master Repo Alignment Audit (post-ticket-082)

- Audit type: **master repo-wide alignment audit** (read-only, strategic)
- Ticket: **ticket-084 — Master repo alignment audit**
- Date: 2026-06-13
- Base tip: `b5328b1` (main, after ticket-083 checkpoint merge `efea1a7`)
- Prior healthy SHA (pre-checkpoint): `77a54cf`
- Scope: docs-only / audit-only. No product features. No domain seed. No validators or tests changed.

---

## 0. TL;DR (brutally honest)

The repo is **green and disciplined**, but it is **strategically drifting**. We have spent
tickets ~060–082 building an increasingly elaborate **operator/scratch-evidence/doc
cross-link apparatus** around a research engine that **has never ingested a real source
or accumulated a single real accepted claim**. The Golden MVP is genuinely complete in
**mock/fixture mode**, and the live Qwen probe spine works **report-only**. But the
defining promise of the project — *turn real sources into a traceable claim graph in the
creativity domain* — is **not started**. `source_discovery`, `fetcher`, and
`candidate_ranker` still raise `NotImplementedError` ("arrives with Phase 3"). The
creativity domain pack is **declarative scaffold**: only `ontology.yaml` labels are read
by code; `aliases/scoring/evidence_types/claim_schema/source_preferences/card_templates/
search_templates/safety_notes` are not loaded by the engine.

We are still in the **General Research Graph Engine MVP** (mock-proven), drifting into
**operator infrastructure**, and **not** yet in domain-specific research. The next high-
value move is to **stop polishing operator/doc scaffolding** and either (a) define the
domain-entry gate and prove real source ingestion, or (b) consolidate before doing so.
**Do not** start OpenAI/cloud, and **do not** let scratch evidence become graph authority.

---

## 1. Where are we in the build?

**Answer: General Research Graph Engine MVP (mock/fixture-complete), now over-extended into Operator Infrastructure. NOT domain-specific research. NOT a real public showcase.**

Evidence:

| Signal | Reading |
| ------ | ------- |
| `README` "Current Status" | "Phase 1 MVP is complete" in deterministic mock/fixture mode |
| `canonical context` build phases | Phase 1 = general engine; Phase 2 = creativity domain pack; Phase 3 = local research MVP |
| `source_discovery.py` / `fetcher.py` / `candidate_ranker.py` | all `raise NotImplementedError(... "Phase 3")` |
| `research run` without `--fixture-mode` | returns `not_implemented` |
| domain pack consumption | only `concept_linker._parse_ontology_concepts(ontology.yaml)` reads pack files |
| tickets 060–082 | live probe spine (report-only) + scratch DB + summary + evidence review + operator-loop hooks + 6 doc cross-links |
| scratch DB | empty locally; never populated by CI or fixtures |

The repo *labels* itself Phase 2 (creativity domain pack). In reality, **Phase 2 has barely
begun**: the domain pack exists as YAML documentation, but the engine does not load most of
it, and no real creativity research has been run. Most recent work is Phase-3-adjacent
**operator tooling** built before Phase 3's ingestion spine exists.

---

## 2. What is real and verified?

Verified this pass on `b5328b1` (mock-only): **140 golden passed**, **safety audit pass**.
(Full pytest 328 / 6 `live_smoke` deselected, public-site build, and Golden Gate
`27473374772` are confirmed in the post-082 checkpoint; not all re-run here.)

| Capability | Status | Proof |
| ---------- | ------ | ----- |
| Mock/golden full MVP spine (ingest → claims → concepts → relationships → contradictions → scores → reports → cards → site → improvement tickets) | **REAL (mock)** | 140 golden tests, GT01–GT26, `test_26_full_mvp_run.py` |
| Deterministic fixture-mode `research run --fixture-mode` | **REAL (mock)** | GT26; repo-clean after run (ticket-034) |
| Public card export with fail-closed safety filtering | **REAL (mock data)** | GT11, `card_exporter.py`, safety auditor export checks |
| Static public site (Next.js, read-only) | **REAL (mock data)** | `npm run build` 12 pages; safety audit routes pass |
| Deterministic safety auditor (routes/exports/secrets/prompt-injection) | **REAL** | `status: pass` this pass; GT23–GT25 |
| Local live probe spine (Qwen/Ollama), report-only | **REAL but non-authoritative** | tickets 060–069; `db_writes: false`; live floors documented (env-dependent) |
| Scratch evidence persistence (sanitized metadata) | **REAL but UNUSED** | `live_probe_scratch.py`, GT/unit tests; scratch DB empty locally |
| Scratch evidence summaries + deterministic evidence review | **REAL but ZERO-STATE** | `probe-scratch-summary`, `probe-scratch-evidence-review`; probe artifact shows 0 rows |
| Operator loop (plan / execute-safe) | **REAL** | `operator_loop.py`, `test_operator_loop.py`; never merges/pushes/promotes |
| Principal audit cadence gate | **REAL** | `principal_audit_gate.py`; satisfied for ticket-084 |
| CI Golden Gate (mock-only) | **REAL** | `.github/workflows/golden-gate.yml`; run 27473374772 green |

The honest qualifier: **every "real" capability above operates on fixtures or report-only
worker output.** Nothing has processed a real external source into an accepted graph row.

---

## 3. What is still scaffold or not proven?

| Area | Status | Why |
| ---- | ------ | --- |
| Domain research workflow (real sources → claims) | **NOT PROVEN** | `source_discovery`/`fetcher`/`candidate_ranker` = `NotImplementedError`; live `research run` = `not_implemented` |
| Domain pack ingestion / wiring | **MOSTLY SCAFFOLD** | only `ontology.yaml` labels consumed; aliases/scoring/evidence_types/claim_schema/source_prefs/card_templates/search_templates/safety_notes are YAML docs not loaded by code; no `import yaml` (custom mini-parser) |
| Human-creativity-vs-AI-creativity ontology in practice | **DOC-ONLY** | rich concept list in spec + `ontology.yaml`; `domain_metadata` (track/creative_phase/measured_dimension) validated as generic JSON only, not against pack-allowed values |
| Real evidence accumulation | **ZERO** | no accepted claims from real sources; scratch DB empty; live probes write nothing |
| Public-facing research output | **PLACEHOLDER** | public site renders golden fixture cards (`card_golden_*`), not real findings |
| OpenAI / cloud path | **DEFERRED (intentional)** | ticket-059 placeholder; no adapter, no keys wired |
| Autonomous improvement loop | **HALF-REAL** | improvement-ticket *generation/validation/promotion* exist (GT20–GT22), but driven by fixtures; no real run has produced a real improvement ticket; promotion is human-gated by design |

---

## 4. Are we drifting? (the uncomfortable section)

**Yes — process-healthy, strategically drifting.**

| Drift question | Verdict | Detail |
| -------------- | ------- | ------ |
| Over-investing in operator/scratch infra? | **YES** | 068–073 build persist→summary→review→loop hooks for a scratch DB that is still empty; 074–082 are Windows-encoding + six doc cross-links for that same unused workflow. ~15 consecutive tickets of meta-tooling. |
| Docs and CLI aligned? | **YES (well-aligned)** | README/AGENTS/11/04/12/14 all cross-link the runbook checklist; CLI commands match documented probe/scratch surface. Alignment is, if anything, *over*-maintained. |
| Public site ahead of real research content? | **YES** | site + export pipeline are production-shaped but serve golden fixture cards. Presentation maturity >> research maturity. |
| Safety complexity proportional? | **MOSTLY YES** | safety auditor scope (routes/exports/secrets/injection/live-LLM/scratch policy) is justified by the public-export + untrusted-source threat model. Slight risk of gold-plating (scratch policy checks for an empty scratch DB), but defensible. |
| Avoiding the actual domain too long? | **YES** | the central deliverable (real creativity research) has not started after 80+ tickets. The path of least resistance (docs, operator polish, Windows fixes) has repeatedly won over the hard path (real ingestion). |
| Duplicate / stale docs? | **MINOR** | `docs/agents/` has both forward- and back-slash duplicate listings (OS artifact, not real dupes). `000_init.md` is explicitly historical. Phase-2 roadmap report is the de facto roadmap. No urgent consolidation, but a single "current state" pointer would help. |

The drift is not laziness — it is **disciplined motion in a low-risk lane**. The cadence
gate, operator loop, and doc cross-links are good engineering. But they are **scaffolding
around an empty room**. The strongest signal: the scratch-evidence apparatus has a full
persist→summarize→review→plan pipeline and **zero rows of evidence** to operate on.

---

## 5. Updated MVP definition (plain language)

The canonical "Golden MVP Proof" (mock fixture E2E + golden + safety + 1 improvement
ticket) is **already met**. That bar proved the *machine*. It did not prove the *research*.

**Updated MVP definition (the bar that now matters):**

> The Research Graph Engine MVP is real when, starting from a small set of **real,
> manually-supplied creativity sources** (PDFs/URLs/notes), it can — on the operator's
> local machine, with deterministic Python validation — ingest those sources, extract
> **scoped, source-anchored creativity claims**, link them to the creativity ontology,
> build at least one support/contradiction/qualification relationship, reconcile scores
> with history, emit a run + cluster report, export **public-safe cards reflecting real
> findings (not fixtures)**, render them on the static site, generate at least one
> improvement ticket from a **real** failure, and pass the full safety audit — all
> without any model output writing directly to the accepted graph.

Two tiers, stated honestly:

- **MVP-Engine (DONE):** deterministic mock fixture spine, green and safe.
- **MVP-Research (NOT DONE):** the same spine driven by ≥1 real source set with real
  accepted claims and a real (non-fixture) public card. This is the gap.

---

## 6. Domain-entry gates (minimum criteria before the first real domain pack)

Do **not** start real domain research until all of these are true:

1. **G1 — Manual ingestion path is real.** `research ingest` (or a Phase-3 ingest CLI)
   accepts a real local source file (PDF/text/URL-saved-text), chunks it, and persists
   source + chunks to the private SQLite graph — deterministically, no live LLM required.
   (`fetcher`/`source_discovery` may stay stubbed; manual Level-1 ingestion must work.)
2. **G2 — Validator floor holds on real text.** Claim validation (quote span,
   scope, overgeneralization, injection) is proven against at least one **non-fixture**
   real source, with rejections preserved and reasoned. No validator weakening.
3. **G3 — Domain pack is loadable, not just declarative.** A domain pack loader reads
   `ontology.yaml` + `aliases.yaml` (minimum) and exposes concepts/aliases to the
   concept linker. `domain_metadata` allowed-value checks delegate to the pack.
4. **G4 — Determinism + safety preserved.** A real-source run leaves `git status` clean
   except intended `data/` (gitignored) artifacts; safety audit passes; no secrets/raw
   text/local paths in any export.
5. **G5 — Human-gated promotion intact.** Any improvement ticket from a real run is a
   draft requiring `--confirm` promotion + human queue row. No model/Qwen authority.
6. **G6 — A pre-ticket audit exists** for the first ingestion-touching ticket (medium
   risk: schema/ingestion surface).

G1–G2 are the **hard, missing** gates. G3 is partial (ontology only). G4–G6 are already
culturally enforced.

---

## 7. What should the first real domain pack be?

**Recommendation: keep `creativity`, but scope the first real run to the narrowest
controlled slice — "AI-assisted ideation vs. semantic diversity" — using a tiny set of
real manual sources.**

Rationale:

- The entire repo, fixtures, golden tests, ontology, and example topic
  ("Does AI improve creative output while reducing diversity?") are already built around
  creativity. Switching domains now would waste that and *increase* drift.
- "Human creativity vs AI creativity" as a whole is **too broad** for a first real run —
  it invites the same over-scoping the claim model warns against.
- "Design/film/art research" are **future overlap domains**, explicitly proposal-only in
  the spec; starting there violates the domain lifecycle.
- A **smaller controlled domain** outside creativity would abandon sunk, aligned work.

So: **same domain pack (`creativity`), minimal real-source slice** (the
AI-assistance → may_reduce → semantic-diversity tension), 3–5 real manual sources. This
is the smallest thing that converts MVP-Engine into MVP-Research without scope creep.

---

## 8. What is the next best move? (option comparison)

| Option | What | Value | Risk | Verdict |
| ------ | ---- | ----- | ---- | ------- |
| **A** — canonical context scratch workflow pointer doc patch | one more doc cross-link in `01_...CONTEXT_v1.md` | very low | very low | **Defer.** Pure scaffolding; deepens drift. Optional cleanup only. |
| **B** — run runbook scratch checklist with a live probe session | operator populates scratch DB locally, validates evidence review on real rows | medium (validates unused pipeline) | low (local, report-only, env-dependent on Ollama) | **Useful as operator action, not a code ticket.** Good to *prove* the scratch apparatus isn't dead, but does not advance MVP-Research. |
| **C** — deterministic evidence review report over scratch summaries | already implemented (ticket-071); re-running adds nothing without rows | low | low | **No.** Capability exists; gated on B producing rows. |
| **D** — first real domain pack seed (real ingestion) | build G1/G3: real manual ingestion + domain pack loader | **high (the actual mission)** | medium (schema/ingestion surface; needs pre-ticket audit) | **Yes — the strategic move,** but only after a domain-entry gate spec + readiness audit. |
| **E** — ticket-059 / OpenAI | cloud adapter | low now | **high** (cost, keys, authority creep, explicitly out of scope) | **No. Forbidden this pass.** |
| **F** — cleanup / stale-doc consolidation | one "current state" pointer; note OS-dup doc listings | low-medium | very low | **Light yes,** fold into A as a tiny optional pass; do not let it become another 5-ticket lane. |

**Chosen next move:** prepare for **Option D** by first writing a **domain-entry gate
spec + Phase-3 ingestion readiness audit** (ticket-085), then implement **real manual
ingestion** (ticket-086), then a **minimal domain pack loader** (ticket-087). Option B
(operator live probe session) is recommended **in parallel by the operator**, off the
critical path. Option A/F are optional low-priority cleanup.

---

## 9. What should NOT happen next (explicit)

- **Do NOT** start ticket-059 / OpenAI or wire any cloud/API call. No keys, no adapter.
- **Do NOT** add another doc cross-link / operator-polish ticket as the *primary* next
  move. The doc chain is complete; more of it is drift.
- **Do NOT** let live probe / scratch evidence write to the accepted graph DB or become
  graph authority. Scratch stays isolated, metadata-only, report-only.
- **Do NOT** public-export scratch or live-probe artifacts. Do not commit
  `data/reports/live_probes/*` or the local probe markdown artifact.
- **Do NOT** give Qwen/model output ticket, queue, Git, or DB authority.
- **Do NOT** weaken validators, delete failure records, or relax golden tests to make a
  real source "pass." Real-source rejections are evidence, not bugs.
- **Do NOT** broaden the domain to film/design/music or "all of human vs AI creativity."
- **Do NOT** auto-activate domains/concepts from model output.
- **Do NOT** start real ingestion (ticket-086) before the ticket-085 readiness audit GO.

---

## 10. Next 3-ticket sequence

### ticket-085 — Domain-entry gate spec + Phase-3 ingestion readiness audit
- **Goal:** Add a short `docs/agents/` section (or report) defining the domain-entry gates
  G1–G6 above and audit current readiness for real manual ingestion (what exists in
  `parser`/`repositories`/`ingest` vs. what `fetcher`/`source_discovery` stub). Produce a
  GO/NO-GO for ticket-086 with the smallest missing proof named.
- **Risk:** low (docs/audit only; no code).
- **Acceptance criteria:**
  - Domain-entry gates documented with current status per gate.
  - Explicit inventory: which ingestion code paths are real vs. `NotImplementedError`.
  - GO/NO-GO recommendation for ticket-086 with named smallest missing proof.
  - No runtime/schema/validator/test changes.
- **Pre-ticket audit required?** No (this *is* the readiness audit; this principal pass
  covers cadence).

### ticket-086 — Real manual source ingestion (Level-1) into the private graph
- **Goal:** Implement deterministic manual ingestion of a real local source
  (text/markdown first; PDF optional behind a clear path) into source + chunk tables via
  the existing migration harness — no live LLM, no `fetcher`/`source_discovery`. Add one
  real (non-fixture) creativity source under an operator-local path and prove ingestion +
  validator floor on it.
- **Risk:** medium (touches ingestion surface, possibly schema/migration).
- **Acceptance criteria:**
  - `research ingest` (or Phase-3 ingest CLI) persists a real local text source + chunks
    deterministically; repeated runs leave git clean (artifacts under gitignored `data/`).
  - At least one real source processed; claim extraction (mock-validated) yields ≥1
    accepted scoped claim and preserves ≥1 reasoned rejection.
  - Safety audit passes; no raw text/secrets/local paths in any export.
  - Golden tests unchanged and still 140 green; new unit tests for ingestion path.
- **Pre-ticket audit required?** **Yes** (medium risk, ingestion/schema surface; gated by
  ticket-085 GO).

### ticket-087 — Minimal domain pack loader (ontology + aliases) wired to concept linking
- **Goal:** Add a real domain pack loader that parses `ontology.yaml` + `aliases.yaml`
  (introduce `pyyaml` or a hardened parser) and feeds concepts/aliases to `concept_linker`,
  replacing the ad-hoc ontology mini-parser; delegate `domain_metadata` allowed-value
  checks to the pack. Keep creativity-specific logic in the pack only.
- **Risk:** medium (concept-linking behavior; dependency addition).
- **Acceptance criteria:**
  - Loader reads `ontology.yaml` + `aliases.yaml`; concept linker uses loaded
    concepts/aliases; alias → canonical mapping proven (e.g. "AI-assisted brainstorming"
    → "AI assistance").
  - Core engine still hardcodes no creativity fields; `domain_metadata` allowed values
    delegated to pack per DOMAIN_PACK_SPEC §11.
  - All golden tests pass (update only fixtures/expectations that legitimately reflect
    loader wiring, with justification); safety audit passes; new unit tests for loader.
- **Pre-ticket audit required?** **Yes** (medium risk; behavior + dependency change).

Sequencing note: 086 and 087 can be reordered, but **085 must come first**, and each of
086/087 requires its own pre-ticket audit GO before implementation.

---

## 11. Safety boundary confirmation (this pass)

| Boundary | Held? |
| -------- | ----- |
| No ticket-059 / OpenAI started | **yes** |
| No cloud/API calls added | **yes** |
| No writes to accepted graph DB from live runs | **yes** (none run) |
| Scratch evidence kept non-authoritative | **yes** |
| No private scratch/probe artifact exported or committed | **yes** (left untracked) |
| No model/Qwen ticket authority | **yes** |
| No broad refactors during audit | **yes** |
| Validators unchanged | **yes** |
| Tests not weakened | **yes** |
| No domain work seeded (only proposed tickets documented) | **yes** |

---

## 12. Commands run (this audit pass)

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m rge.modules.principal_audit_gate --next-ticket ticket-083   # overdue→ (report present) satisfied
python -m rge.modules.safety_auditor --audit full                     # status: pass
python -m pytest tests/golden -q                                      # 140 passed
python -m rge.modules.principal_audit_gate --next-ticket ticket-084   # satisfied
# git: branch + commit + --no-ff merge of ticket-083 checkpoint to main
```

Not re-run this pass (trusted from post-082 checkpoint at `77a54cf`): full `pytest -q`
(328/6 deselected), `npm run build`, Golden Gate `27473374772`.

## Merge

- Implementation SHA: (ticket-084 branch commit on `phase-2/ticket-084-master-alignment-audit`)
- Merge commit SHA: `7078342`
- Pushed: `77a54cf..7078342  main -> main`
- Golden Gate run: (pending push CI)

## 13. Stop

Read-only master alignment audit complete. No product features implemented, no domain
work seeded, no validators or tests changed. Next action is **operator decision**: approve
ticket-085 (domain-entry gate spec + readiness audit) as the move that ends the drift, or
explicitly choose to continue operator/doc consolidation (Option A/F) with eyes open.
