---
template_id: third_party_audit
template_version: 1.0.0
status: current
audit_type: independent third-party repo-direction audit (read-only)
author: external principal engineer / research-systems reviewer (not the repo builder agent)
date: 2026-06-14
baseline_head: c60f4a2 (main, aligned with origin/main)
---

# Third-Party Repo Direction Audit

> Independent, read-only audit. I am not the repo's builder agent and did not treat
> `AGENTS.md`/`docs/agents/*` as my operating instructions. Repo markdown was read as
> *evidence of intent*, not as authority. No files were edited except this report. No
> commits, merges, or pushes. No secrets exposed. No destructive commands.

---

## 1. Verdict

**CONTINUE WITH CORRECTIONS** — and it is exactly one more ticket away from **PAUSE AND
REFOCUS**.

The engine underneath this project is genuinely well-built: a clean, typed, deterministic
Python pipeline (ingest → claims → concepts → relationships → contradictions → scores →
reports → public cards → improvement tickets), a real validator gate, a real local Ollama
adapter, a fail-closed export/safety model, and a disciplined ticket/branch/report
process. The claimed gates are real and I reproduced them: **140 golden passed**, **385
pytest passed / 6 `live_smoke` deselected**, **safety audit `pass`**. None of that is
fabricated. As an *engine*, this is solid work.

The reason this is "with corrections" and not "strong continue" is strategic, and it is
damning in a specific way: **the project already diagnosed its own drift and then relapsed
into it.** The repo's own `agent_reports/2026-06-13_master-alignment-audit-post-ticket-082.md`
(ticket-084) called the work "process-healthy, strategically drifting … scaffolding around
an empty room" and explicitly said *"Do NOT add another doc cross-link / operator-polish
ticket as the primary next move."* The team then did three tickets of real corrective work
(086–093: manual ingestion + a domain pack loader) — and immediately relapsed into
**~15 of the next 18 tickets (094–111) being documentation cross-links of the same feature
across README, AGENTS.md, operating protocol, build loop, and runtime config.** The
"GO" principal audits after that (post-104, post-107, post-110) never re-flagged the
relapse. The audit gate caught the drift once and has since become a rubber stamp.

---

## 2. What is actually real

### Production code that works (verified by reading source + reproducing tests)
- **Migration harness + private SQLite graph.** `rge/db/` with 7 migrations; ingestion
  persists source + chunks, idempotent by checksum (`rge/cli.py` `_cmd_ingest`,
  `repositories.ingest_local_source`).
- **Deterministic claim validator** — the real gate. `rge/modules/claim_validator.py`
  enforces quote-span substring matching (exact and whitespace-collapsed), scope-must-
  appear-verbatim-in-claim, overgeneralization patterns, required SPO fields, prompt-
  injection rejection. Rejections are stored with reasons, not discarded. This is the
  strongest single piece of the codebase.
- **Real local Ollama adapter.** `rge/llm/ollama_client.py` makes real HTTP calls,
  wraps untrusted source text in an injection-resistant preamble, parses JSON, validates
  against versioned Pydantic schemas, and returns typed candidates only. It never writes
  to the DB.
- **Fail-closed public export + static site.** `card_exporter.py`, `safety/` (route,
  secrets, export-policy, prompt-injection auditors). `apps/public-site/` is a real
  Next.js static app that imports committed JSON only (no fetches, no routes).
- **Deterministic reporting/queue/ticket modules** (cluster, theory, ontology pressure,
  domain proposal, run report, improvement tickets) with golden coverage GT01–GT26.
- **Operator tooling**: bounded `operator_loop.py`, `principal_audit_gate.py`, `verify`
  runner, live-probe CLIs.

### Tests that prove real behavior
- Golden GT01–GT26 and the unit suite genuinely exercise the validator, export safety,
  prompt injection, and the full mock spine. The validator and safety tests are meaningful
  (they assert real accept/reject behavior and forbidden-field absence), not just
  snapshots.
- `test_manual_source_pipeline_e2e.py` / `_idempotency.py` prove the manual spine runs
  end-to-end and is re-run stable.

### Mock / fixture-only behavior (the important caveat)
- **All "model" output in the tested path is canned.** `MockModelClient` reads fixture
  JSON from `fixtures/llm_outputs/`.
- **The "real manual source" pipeline is canned too.** `manual_source_fixtures.py` +
  `fixtures/manual_source_fixture_map.json` resolve extraction/linking/relationship/
  contradiction outputs **by the SHA-256 checksum of the exact source file bytes**. So
  ingesting the committed `manual_synthnote.txt` returns a hand-authored fixture (e.g.
  "2 accepted, 1 rejected `missing_quote_span`") — the *text is really ingested and the
  validator really runs*, but the candidate claims are a lookup keyed to one specific
  file, not inference over its content. Any other real file returns nothing.
- The public site renders exactly **2 cards**, both literally `"source_type": "fixture"`
  (`apps/public-site/public/data/public_cards.json`). It is a proof artifact, not a
  research surface.

### Docs-only / aspirational claims
- `docs/agents/02_ARCHITECTURE.md` describes **LangGraph orchestration, a local FastAPI
  app, an embedding model (for drift/dedup/clustering), and a graph/ layer (NetworkX)**.
  None exist in code (grep: no `langgraph`, `fastapi`, `networkx`, `sentence_transformers`
  imports anywhere). The pipeline is CLI-step chaining in `cli.py::execute_fixture_mode_run`.
- The creativity domain pack ships 10 YAML files; only `ontology.yaml` + `aliases.yaml`
  are consumed (`domain_pack_loader.py`). `scoring/evidence_types/claim_schema/
  source_preferences/card_templates/search_templates/safety_notes` are declarative docs
  the engine does not load.

### Deferred / live-only
- `source_discovery.py`, `fetcher.fetch_source`, `candidate_ranker.py` are
  `NotImplementedError` ("Phase 3"). `research run` without `--fixture-mode` returns
  `not_implemented`.
- Live Ollama extraction is real but **report-only** (`db_writes: False` at 6 sites in
  `live_probe.py`), opt-in (`RGE_ALLOW_LIVE_LLM=1`), and historically flaky (tickets
  066–069: suite went 1/4 → 3/4 → 4/4 floors with calibration).
- Cloud providers (OpenAI/OpenRouter/etc.): not wired; ticket-059 placeholder.

---

## 3. Biggest strengths (top 5)

1. **The validator is real and rigorous.** `claim_validator.py` is the load-bearing
   "Python decides, model only proposes" boundary, and it genuinely enforces it
   (quote-span substring, scope-in-claim, overgeneralization, injection). This is the
   thing most "AI research" repos fake; here it's real.
2. **Safety boundary is real and fail-closed.** No public write/ingestion/agent routes;
   export allowlist with `FORBIDDEN_VALUE_PATTERNS`; deterministic auditor that I ran to
   `pass`; static site imports JSON only. The model never writes accepted rows.
3. **The model boundary is honest.** Both mock and Ollama clients return typed candidates
   only and never touch the DB; live extraction is quarantined to report-only probes.
   Golden tests are forced mock — no Ollama dependency. This is the correct architecture.
4. **Reproducible green gates.** The checkpoint's numbers are accurate (140 golden, 385
   pytest, safety pass). Determinism work (ticket-034) keeps fixture runs git-clean.
5. **Process discipline that actually self-diagnosed.** The ticket-084 master alignment
   audit is one of the most honest internal documents I've seen in a repo of this kind. The
   *capacity* for brutal self-assessment exists — it just isn't being acted on lately.

---

## 4. Biggest concerns (top 10)

1. **Relapse into doc-ceremony after self-diagnosing it.** Tickets 094–111 are ~15 doc
   cross-links of one feature across 5 files, after ticket-084 explicitly forbade exactly
   this. This is the single most important finding.
2. **"MVP-Research largely proven" is overstated.** The post-ticket-110 audit calls the
   manual pipeline "largely proven." It is proven *for one checksum-pinned file with
   hand-authored candidate JSON.* No real arbitrary source has produced an accepted claim
   from actual inference written to the graph. The honest status is the one ticket-084
   used: **MVP-Research NOT done.**
3. **The principal-audit gate has degraded into a rubber stamp.** Post-104/107/110 audits
   all say "GO" and recount the same mock gates; none re-raised the drift that 084 raised.
   A gate that cannot fire twice on the same problem is not a control.
4. **Cadence is measured in ticket *count*, not value.** `principal_audit_gate` fires
   every 3 `done` tickets regardless of whether those tickets moved product risk. Three
   doc cross-links trigger an audit that blesses three more doc cross-links.
5. **Checksum-keyed fixtures masquerade as "real source" research.** A reviewer skimming
   README would reasonably believe the engine extracts claims from manual sources. It
   looks up canned output by file hash. This is the highest risk of false confidence.
6. **Architecture doc oversells.** LangGraph, FastAPI, embeddings, NetworkX graph layer
   are presented as the architecture but are absent. A new contributor would expect a
   system that isn't there.
7. **Domain pack is 80% inert.** Eight of ten pack files are unused. "Domain-general
   engine + domain packs" is the headline design principle, but the pack is mostly
   decoration; the abstraction is unproven beyond ontology labels + aliases.
8. **Live extraction quality is unproven and untracked at HEAD.** The only real-inference
   path (Ollama probes) is report-only, was flaky during calibration, and there is no
   committed, current evidence of its accuracy. Scratch DB is empty.
9. **Improvement-ticket loop has never consumed a real failure.** GT20–22 prove the
   *mechanism*; every generated ticket so far is fixture-driven. The "self-improvement"
   claim is mechanism-only.
10. **Single-domain, single-fixture overfitting.** Validator overgeneralization patterns
    and prompts are hardcoded to the AI/creativity/diversity example
    (`_OVERGENERALIZED_CLAIM_PATTERNS = "ai reduces creativity", …`). The system is tuned
    to its one demo question.

---

## 5. Mock-complete vs reality-complete (1–5; 5 = reality-complete)

| Dimension | Score | Rationale |
|---|---:|---|
| Fixture/mock research pipeline | **5** | Genuinely end-to-end, deterministic, green (GT26). Best part of the repo. |
| Live LLM extraction | **2** | Real Ollama adapter + calibrated prompts exist, but report-only, opt-in, historically flaky, no current committed accuracy evidence, never writes to graph. |
| Manual source workflow | **3** | Real ingestion/chunking/idempotency + real validator; but candidate generation is checksum-keyed canned fixtures, so it's "real plumbing, canned content." |
| Automated research workflow | **1** | `source_discovery`/`fetcher`/`candidate_ranker` are `NotImplementedError`; live `run` is `not_implemented`. Does not exist. |
| Public export / site | **4** | Export + static site are production-shaped and safety-gated; but serve 2 fixture cards. Real surface, placeholder content. |
| Safety boundaries | **4** | Real, deterministic, fail-closed, reproduced to `pass`. Slight gold-plating (scratch-policy checks for an empty scratch DB). |
| Agent improvement loop | **2** | Generation/validation/promotion mechanisms real (GT20–22); never driven by a real failure. |
| Operator ergonomics | **4** | operator_loop, verify, model-health, Windows-encoding fixes are real and thorough — arguably over-built relative to product. |
| Third-party usability | **2** | An outsider can run mock verify and read code, but cannot point it at their own sources and get real claims. |
| Product clarity | **2** | Docs blur mock vs real ("MVP-Research largely proven"); checksum fixtures look like real extraction; architecture doc describes an unbuilt system. |

---

## 6. Is the ticket loop helping?

**Partially — and recently, no.** The loop was clearly valuable through ~ticket-060: it
built a real engine in small, safe, well-tested increments, with honest reports. The
machinery (one-ticket-per-branch, mandatory reports, mock-only golden gate, safety audit,
cadence checkpoints) is sound.

But since ~ticket-068 the loop has been compounding **process value, not product value**.
Evidence, straight from `tickets/TICKET_QUEUE.md` and `git log`:

- Tickets 094–098: cross-link the "manual synthnote spine" into 5 docs.
- Tickets 100–104: cross-link "reconcile-scores" into the same 5 docs.
- Tickets 107–111: cross-link "pipeline proof tests" into the same 5 docs.
- Interleaved "docs: record main merge hash" and "principal audit checkpoint" commits.

That is the same feature documented three times across the same five files. The cadence
gate then fires every 3 tickets and produces a "GO" audit that authorizes the next three.
This is a **local maximum**: each ticket is individually safe, reversible, green, and
"done," so the loop keeps choosing the lowest-risk lane. The loop optimizes for *not
breaking the build*, and doc cross-links never break the build.

The tell is structural: the cadence trigger counts tickets, and the audit it triggers
re-verifies the same mock gates. Nothing in the loop measures "did product risk decrease?"
So the loop cannot distinguish ticket-086 (real ingestion, high value) from ticket-109
(one doc link, ~zero value) — both are "1 done ticket."

---

## 7. Strategic drift check

Original goal: *ingest evidence → extract scoped claims → link concepts → build
relationships → reconcile scores → produce public-safe cards/reports → generate useful
improvement tickets.*

**Aligned:**
- The *shape* of the pipeline matches the goal exactly, end-to-end, in mock mode.
- Safety/export/model boundaries match the canonical intent precisely.
- Claim scoping, rejection preservation, score-event history, qualify-don't-delete
  contradiction handling are all faithful to the design.

**Drifting:**
- The goal says **"ingest evidence"** — real evidence. The system ingests *bytes* but
  *extracts* from a checksum→fixture table. The "evidence → claim" link is simulated.
- **"generate useful improvement tickets"** from real runs has never happened.
- The last ~18 tickets advanced *documentation of* the pipeline, not the pipeline.
- The architecture is drifting from its own spec (no LangGraph/FastAPI/embeddings), and
  the domain-pack abstraction is mostly unexercised.

Net: the repo is *aligned in architecture and boundaries* but *drifting in mission* — it
keeps proving and re-documenting the machine instead of running real research through it.
This is precisely what ticket-084 said, and it remains true 27 tickets later.

---

## 8. Safety and trustworthiness assessment

- **Public write safety:** Strong. No write routes; static site only; verified by route
  auditor and by reading `apps/public-site` (imports JSON, no API).
- **Source ingestion safety:** Strong. Ingestion is local/private; no public ingestion;
  all source text treated as untrusted.
- **Model tool boundaries:** Strong. Mock and Ollama clients return typed candidates only;
  `db_writes: False` enforced on probes; Python is the only writer to accepted tables.
- **Export safety:** Strong. Allowlist + `FORBIDDEN_VALUE_PATTERNS` + fail-closed auditor;
  reproduced `pass`. No raw text/paths/secrets in the 2 committed cards.
- **Prompt-injection posture:** Good. Untrusted-source preamble in live prompts; injection
  rejection in the validator; GT24 covers it.
- **Risk of false confidence from mocks:** **High and under-managed.** "385 passing /
  safety pass / MVP-Research largely proven" reads as product readiness. In reality every
  tested claim is canned and the only real-inference path is report-only. The docs do not
  consistently foreground this; the checksum-fixture trick actively obscures it.
- **Risk of agents following docs instead of reality:** **High.** `AGENTS.md` instructs
  builder agents to obey the queue and cadence; the queue's path of least resistance is
  more doc cross-links. An agent faithfully following the protocol will keep producing
  low-value tickets and "GO" audits — which is what has happened.

---

## 9. Product usefulness today

**What a real outside user/engineer can do today:**
- Clone, `pip install -e .[dev]`, set `RGE_LLM_MODE=mock`, run `python -m rge.cli verify`
  and get a green deterministic suite.
- Run `research run --fixture-mode` and watch a full claim-graph pipeline execute on the
  built-in fixtures, producing reports, 2 public cards, and a static site.
- Read a clean, well-documented reference implementation of a "model proposes / Python
  validates and writes" research-graph architecture with a real safety model.
- With local Ollama, run report-only live probes to see Qwen produce (sometimes valid)
  scoped claims that the validator accepts/rejects — without any DB writes.

**What they cannot do yet:**
- Point it at *their own* documents and get real extracted claims into the graph (manual
  pipeline only "works" for the two checksum-pinned committed files; everything else
  returns no fixture).
- Run any automated/live research end-to-end to the graph or public site.
- Trust the public site as a research output — it shows fixtures.
- Use any cloud model, discovery, fetching, or ranking.
- Rely on the "self-improvement" loop to surface real issues.

So: **useful as a reference architecture and a mock demo; not yet useful as a research
tool outside the author's fixtures.**

---

## 10. Recommended next moves

> I am explicitly **not** defaulting to the queue. Ticket-111 (README cross-link) is the
> weakest possible next move and should not be the headline. Do it in 5 minutes if you
> want the doc complete, but it must not consume an audit cycle.

### NM-1 — Prove real (non-checksum) extraction writes one real accepted claim
- **Why it matters:** This is *the* missing proof. It converts MVP-Engine into the first
  inch of MVP-Research and ends the "canned content" critique.
- **Scope:** Take one *new* real creativity source (not in the fixture map). Run live
  Ollama extraction → validator → **write accepted/rejected claims to a real (gitignored)
  DB**. Capture a committed evidence report (counts, the accepted claim, rejections w/
  reasons). No public export required.
- **Acceptance:** ≥1 accepted scoped claim from genuine inference on a source with **no**
  fixture-map entry; ≥1 reasoned rejection preserved; validator unchanged; safety pass;
  evidence report committed.
- **Risk:** Medium (first model→graph write path; needs care that only validated output
  writes).
- **Order:** **Before** ticket-111. This is the real next ticket.

### NM-2 — Relabel maturity honestly in README + status docs
- **Why:** Remove the false-confidence surface. Distinguish "real plumbing / canned
  content (checksum fixtures)" from "real inference." Replace "MVP-Research largely
  proven" with ticket-084's accurate two-tier framing.
- **Scope:** Docs-only, but *corrective*, not ceremonial: one honest status block; mark the
  manual synthnote pipeline as fixture-content; mark architecture doc items
  (LangGraph/FastAPI/embeddings) as "planned, not implemented."
- **Acceptance:** No doc claims a docs-only or fixture-only capability as real.
- **Risk:** Low. **Order:** Can run alongside NM-1; supersedes ticket-111.

### NM-3 — Reform the cadence gate to value, not count
- **Why:** Stop the loop from authorizing low-value lanes. Make audits fire on *risk/value*
  and require each audit to explicitly answer "did the last N tickets reduce product risk?
  If no for 2 audits running, escalate."
- **Scope:** Extend `principal_audit_gate` with a "value classification" per closed ticket
  (product / infra / docs) and a drift alarm when ≥K consecutive docs/infra tickets occur.
- **Acceptance:** Gate emits `drift_warning` for the 094–111 pattern on historical data.
- **Risk:** Low–Medium. **Order:** After NM-1.

### NM-4 — Make the manual pipeline work for *arbitrary* real text (retire checksum coupling)
- **Why:** A research tool that only handles two pre-hashed files is a demo. This is the
  generalization of NM-1.
- **Scope:** Allow the manual pipeline to run live extraction for any `manual_text` source
  with no fixture-map entry (fall through to Ollama), keeping fixtures only for tests.
- **Acceptance:** A fresh `.md` ingested + extracted live yields validator-gated claims;
  golden tests still mock-only and green.
- **Risk:** Medium. **Order:** After NM-1/NM-3.

### NM-5 — Wire one more domain-pack file end-to-end (e.g. `scoring.yaml` or `evidence_types.yaml`)
- **Why:** Prove the domain-pack abstraction is real beyond ontology labels, before
  claiming domain-generality.
- **Scope:** Load one additional pack file and use it in scoring or validation; delegate
  `domain_metadata` allowed-values to the pack.
- **Acceptance:** Behavior demonstrably changes with the pack file; core hardcodes nothing
  creativity-specific.
- **Risk:** Medium. **Order:** After MVP-Research has one real claim (NM-1).

---

## 11. Stop-doing list

- **Stop documentation cross-link tickets as primary work.** The doc chain is complete and
  over-maintained. Ticket-111 is the last acceptable one and only as a quick chore.
- **Stop "principal audit checkpoint" tickets that only recount mock gates.** Audits that
  cannot detect the drift they're standing in are theater. Fold verification into NM-3.
- **Stop expanding operator/scratch/probe tooling** until the scratch DB has real rows to
  operate on (it's empty; the persist→summary→review→plan chain has nothing to chew).
- **Stop calling the manual pipeline "real source research"** in docs until NM-1/NM-4 land.
- **Stop the every-3-tickets cadence ritual** in its current count-based form.
- **Do not** start OpenAI/cloud (ticket-059) — correctly deferred; would add cost/authority
  risk while the real-extraction proof is still missing.

---

## 12. Brutal final assessment

**Are we building the right thing?** The *architecture* is right — genuinely. The
model/Python boundary, the validator, the fail-closed safety model, and the export design
are what a serious research-graph engine should look like, and they're real. But the
*work* has stopped building the right thing. For roughly the last 18 tickets the project
has been documenting and re-documenting a machine instead of running research through it.

**Are we proving the right things?** No. We are proving, repeatedly, that the mock pipeline
is green and that five docs all mention the same feature. We are *not* proving the one thing
the whole project exists to prove: that real evidence becomes a real, validated claim
graph. The checksum-keyed fixture map lets "real manual source" demos pass without ever
performing real extraction — that is proving the wrong thing convincingly.

**Biggest hidden risk:** **False confidence laundering.** Green tests + a safety pass +
"MVP-Research largely proven" + a production-shaped public site together read as
readiness, while every tested claim is canned and the only real-inference path is
report-only. A stakeholder (or a future builder agent obeying `AGENTS.md`) can run the
loop indefinitely, see green, and never notice the engine has not done its actual job.
The repo's *own* ticket-084 audit saw this clearly and was then out-voted by the cadence.

**What I would do if I owned this repo (next 1–2 weeks):**
1. Freeze the doc/cross-link/checkpoint lane today. Ship ticket-111 in 5 minutes or drop it.
2. Do **NM-1**: one real source, live Ollama, validator-gated, written to a real local DB,
   with a committed evidence report. That single ticket is worth the last 18 combined.
3. Do **NM-2**: rewrite the status docs to ticket-084's honest two-tier framing and stop
   the checksum fixture from being presented as real extraction.
4. Reform the cadence gate (**NM-3**) so it measures product-risk reduction, then let it
   re-authorize work.
5. Only after a real claim exists end-to-end, generalize (NM-4) and prove the domain-pack
   abstraction (NM-5). Keep cloud deferred.

The good news: the hard, scary parts (validator, safety, model boundary) are already real
and trustworthy. The correction here is not an architectural reset — it's discipline.
Point the excellent machine you've built at one real source and let it do its job.

---

### Appendix — commands run this pass (PowerShell, mock mode)

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
git status --short / git branch --show-current / git log --oneline -60   # main @ c60f4a2, clean except 2 untracked reports
python -m pytest -q                                  # 385 passed, 6 deselected (54.6s)
python -m pytest tests/golden -q                     # 140 passed (36.9s)
python -m rge.modules.safety_auditor --audit full    # status: pass
```

Reads (not exhaustive): `rge/cli.py`, `rge/llm/{mock_client,ollama_client}.py`,
`rge/modules/{claim_extractor,claim_validator,manual_source_fixtures,domain_pack_loader,
source_discovery,fetcher,live_probe}.py`, `fixtures/manual_source_fixture_map.json`,
`apps/public-site/app/page.tsx`, `apps/public-site/lib/publicCards.ts`,
`apps/public-site/public/data/public_cards.json`, `README.md`, `AGENTS.md`,
`docs/agents/{02_ARCHITECTURE,11_AGENT_OPERATING_PROTOCOL}.md`, `tickets/TICKET_QUEUE.md`,
`agent_reports/2026-06-13_master-alignment-audit-post-ticket-082.md`,
`agent_reports/2026-06-14_principal-audit-post-ticket-110.md`.

### Commands not run / skipped (honest disclosure)
- `cd apps/public-site && npm run build` — **skipped** (did not invoke Node toolchain in
  this read-only pass to avoid environment churn; build status is trusted from the
  post-ticket-110 checkpoint and the static site source was read directly). Not a failure;
  not independently re-verified this pass.
- Live Ollama probes (`probe-*`, `model-health` against a running service) — **skipped**
  (no live model invoked in a read-only audit; live-extraction quality therefore
  remains unverified at HEAD, which is itself a finding — see §4.8).
- `git log --oneline -40 | cat` initially failed (PowerShell has no pipeable `cat`);
  re-run without the pipe succeeded.
