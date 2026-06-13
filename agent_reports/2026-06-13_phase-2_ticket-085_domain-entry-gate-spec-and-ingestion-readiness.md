---
template_id: audit_report
template_version: 1.0.0
status: current
---

# ticket-085 — Domain-entry Gate Spec + Phase-3 Ingestion Readiness Audit

- Audit type: **focused readiness audit** (read-only). Not another master audit.
- Date: 2026-06-13
- Base tip: `49052ee` (main, clean except untracked local probe artifact)
- One question: **Are we ready to implement deterministic manual ingestion of a real local creativity source into the private graph?**
- Scope: docs/audit-only. No ingestion implemented. No validators changed. No OpenAI/cloud.

---

## Verdict (up front)

**GO for ticket-086.**

The ingestion spine **already exists and is proven by golden tests**. The master audit
(ticket-084) under-stated this: `research ingest` deterministically persists a real local
text source + chunks today (GT01), is idempotent by content checksum, and survives process
restart. The fetcher and parser are real for local text. The only true code gap for *real
manual* ingestion is cosmetic-but-meaningful: every ingested source is labeled
`source_type="fixture"`, and there is no operator convention for where real sources live.

ticket-086 is therefore **small and low-risk**: label real manual sources correctly, add a
title/type option, establish a gitignored manual-sources directory, and prove it on one
real source. **No new schema, no validator change, no export change.**

This report **serves as the focused pre-ticket audit for ticket-086** (G6). No separate
audit is required provided ticket-086 stays within the scope defined in §"ticket-086 plan".

---

## Hard-ordering confirmations

| Step | Result |
| ---- | ------ |
| Repo status inspected | done |
| `main` clean + up to date | **yes** — `49052ee` == `origin/main`; only untracked file is the private probe artifact |
| Master alignment audit exists | **yes** — `agent_reports/2026-06-13_master-alignment-audit-post-ticket-082.md` |
| Required surfaces inspected | yes (see inventory) |
| `principal_audit_gate --next-ticket ticket-085` | **satisfied** (not blocked) — see §Gate |
| ticket-085 seeded | yes — `tickets/ticket-085.json` (status done) |
| Readiness report created | this file |
| Ingestion implemented in 085? | **no** |
| GO → ticket-086 plan written? | **yes** (§ticket-086 plan) |

---

## Gate result (audit cadence)

```json
{
  "status": "satisfied",
  "cadence_status": "satisfied",
  "done_ticket_ids_since_latest_checkpoint": ["ticket-083", "ticket-084"],
  "next_ticket_id": "ticket-085",
  "implementation_gate": "not_applicable"
}
```

Not blocked. `implementation_gate: not_applicable` because ticket-085 had no risk level at
gate time (now seeded as `low`). Cadence is satisfied (2 done since post-082 checkpoint,
below threshold 3).

---

## Real vs stub ingestion inventory (the evidence)

| Component | File | Status | Notes |
| --------- | ---- | ------ | ----- |
| `ingest` CLI command | `rge/cli.py` `_cmd_ingest` + subparser (≈L1406, L1501) | **REAL** | `ingest <path> --domain <d> [--db]`; prints machine-readable JSON |
| Local text fetch | `rge/modules/fetcher.py` `fetch_local_text_file` | **REAL** | UTF-8 read, empty-file guard, returns raw_text/title/local_path; **forces `source_type="fixture"`** |
| Parse / chunk | `rge/modules/parser.py` `parse_source_text` | **REAL, deterministic** | 4000-char chunks, paragraph-aware split, sha256 checksums, stable IDs, token count |
| Persist source+chunks | `rge/db/repositories.py` `ingest_local_source` | **REAL, idempotent** | dedupes by `raw_text_checksum`; returns `ingested` / `already_ingested` |
| Source/chunk tables | `rge/db/migrations/0001_initial.sql` | **REAL** | `sources` (incl. `source_type`, `local_path`, `domain`, `raw_text_checksum`, `status`), `chunks` |
| Source/chunk repos | `rge/db/repositories.py` `SourceRepository`, `ChunkRepository` | **REAL** | `get_by_checksum`, `get_by_id`, `insert`, `insert_many`, `list_for_source` |
| ID derivation | `make_source_id` (`src_<checksum[:16]>`), `make_chunk_id` | **REAL, deterministic** | content-addressed → reproducible across runs/machines |
| GT coverage | `tests/golden/test_01_ingestion.py` | **REAL** | persists source+chunks; idempotent re-ingest (count stays 1); survives restart; JSON output |
| `fetcher.fetch_source` (queue-driven) | `rge/modules/fetcher.py` | **PARTIAL STUB** | local_path only; `NotImplementedError` otherwise — **not needed for manual ingest** |
| `source_discovery.discover_candidate_sources` | `rge/modules/source_discovery.py` | **STUB** | `NotImplementedError` ("Phase 3") — **not needed for manual ingest** |
| `candidate_ranker` | `rge/modules/candidate_ranker.py` | **STUB** | `NotImplementedError` — **not needed for manual ingest** |
| `research run` (live) | `rge/cli.py` `_cmd_run` | **stub by design** | non-fixture run → `not_implemented` — **not in scope** |

**Bottom line:** the manual-ingestion path does **not** depend on any of the stubs.
Discovery/fetch-queue/ranking are Phase-3 automation; manual Level-1 ingestion bypasses
them entirely and already works.

---

## Gate assessment (G1–G6)

### G1 — Manual ingestion path is real

- Can a local `.txt`/`.md` be ingested without fetcher/discovery? **YES, today.**
  `python -m rge.cli ingest <path> --domain creativity` works on any local text file.
  `.md` already works (it is read as UTF-8 text); only the chunker treats it as plain text.
- Which CLI exists? **`ingest`** (real). A dedicated `research-ingest-manual-source` is
  *optional sugar*, not required.
- Tables used: **`sources`** (one row, status `ingested`) and **`chunks`** (≥1 rows).
- Deterministic? **Yes** — content-addressed source/chunk IDs, checksum dedupe, no time/random in IDs.
- Missing: **(1)** `source_type` is hardcoded `"fixture"` (real sources mislabeled);
  **(2)** no `--source-title` / `--source-type` override; **(3)** no operator convention for
  where real sources live (`data/sources/manual/creativity/`).
- **Gate status: PASS (with one small real gap = source_type labeling).**

### G2 — Validator floor on real text

- Can a non-fixture source produce ≥1 accepted scoped claim + ≥1 reasoned rejection?
  **Not in mock mode.** `mock_client.extract_claims` loads a **canned fixture file**
  independent of the source's actual text, so a real source in mock mode yields
  fixture claims unrelated to the real text (false signal).
- So a real validator floor on real text requires **live Qwen** (`RGE_LLM_MODE=ollama` +
  `RGE_ALLOW_LIVE_LLM=1`) **or** a seeded fixture-style expected output matched to the
  real source.
- Safest first proof: **DO NOT attempt G2 in ticket-086.** ticket-086 proves ingestion
  (source+chunks) only. G2 (real claim extraction floor) is a **separate later ticket**
  (operator runs live probe extraction on the ingested real source, report-only, then a
  calibrated fixture or live floor). This keeps ticket-086 deterministic and CI-safe.
- **Gate status: DEFERRED past ticket-086 (intentional; not a blocker for ingestion).**

### G3 — Domain pack loadability

- What is actually loaded by code? **Only `ontology.yaml`**, via
  `concept_linker._parse_ontology_concepts` (a hand-rolled mini-parser; no `pyyaml`).
- `aliases.yaml`, `scoring.yaml`, `evidence_types.yaml`, `claim_schema.yaml`,
  `source_preferences.yaml`, `card_templates.yaml`, `search_templates.yaml`,
  `safety_notes.yaml`: **declarative only — not loaded by engine code.**
- Minimum needed before first real *ingestion*: **none.** Ingestion stores
  `domain="creativity"` as a string and does not consult the pack. Domain pack loading
  (ontology+aliases) is required before real **concept linking**, i.e. ticket-087, not 086.
- **Gate status: NOT REQUIRED for ticket-086; required before ticket-087.**

### G4 — Determinism and safety

- Real sources kept private? **Yes.** Raw text lives in the `chunks`/`sources` rows inside
  the default DB `data/db/creative_research.sqlite`, which is under gitignored `data/`.
- Output artifacts under gitignored `data/`? **Yes** — default DB is `data/db/...`;
  proposed manual-source dir `data/sources/manual/creativity/` is also under `data/`.
- Public export avoids raw text/secrets/local paths/scratch? **Yes** — `card_exporter`
  uses an **allowlist** (`EXPORT_CARD_FIELD_ORDER`) and treats `local_path`,
  `raw_source_excerpt`, `prompt_template`, `evaluator_notes` as `GOLDEN_PRIVATE_FIELDS`
  that must never export; safety auditor scans `data/exports/*` and public-site JSON.
- Does safety auditor cover relevant surfaces? **Yes for exports/routes/secrets.** It does
  **not** scan `data/db` or `data/sources` — correct, those are private and gitignored.
  ingestion produces **no export**, so no new audit surface is added by ticket-086.
- **Gate status: PASS.**

### G5 — Human-gated promotion

- Real-run failures → draft improvement tickets without promotion authority? **Yes** —
  generation writes drafts to gitignored `data/tickets/improvement_ticket_latest.json` +
  `improvement_tickets` rows; pipeline runs never auto-promote.
- Promotion still requires explicit human confirmation? **Yes** —
  `promote-improvement-ticket --confirm`; no `TICKET_QUEUE.md` auto-edit; Qwen/model has
  no ticket/queue/Git/DB authority.
- **Gate status: PASS (unchanged; ingestion does not touch this path).**

### G6 — Pre-ticket audit requirement for ticket-086

- Milestone triggers requiring a focused pre-ticket audit: public export/`card_exporter`
  changes, public site/committed-JSON changes, **schema migrations**, theory/inference
  changes, live Ollama/smoke constraint changes.
- ticket-086 as scoped: additive CLI flags + a new `source_type` **value** (the column
  already exists — **no migration**), a gitignored directory convention, and unit tests.
  It touches **none** of the milestone triggers and does not change validators or exports.
- **Gate status: a separate pre-ticket audit is NOT required.** This ticket-085 report is
  the focused readiness/pre-ticket audit for ticket-086. (If ticket-086 scope expands to a
  migration, PDF parsing, or any export/card_exporter change, a new pre-ticket audit IS
  required.)

---

## GO / NO-GO

**GO for ticket-086.** All blocking gates (G1, G4, G5) pass. G2 is intentionally deferred
(not a blocker for ingestion). G3 is not required until ticket-087. G6 is satisfied by this
report.

**Smallest missing proof to call MVP-Research "started" after 086:** one real,
operator-supplied creativity source persisted as a private `sources` row labeled as a real
manual source (not `fixture`) with deterministic chunks, idempotent re-ingest, and a clean
safety audit — with **no** export and **no** model involvement.

---

## ticket-086 plan (exact implementation target)

**Title:** ticket-086 — Real manual source ingestion (Level-1)

**Goal:** Ingest a local operator-supplied `.txt`/`.md` creativity source into the private
SQLite graph as a **correctly-labeled** source + deterministic chunks, reusing the existing
`ingest_local_source` spine. No discovery, no fetch queue, no PDF/URL, no LLM, no export.

**Recommended approach (least drift): extend the existing `ingest` command** rather than
add a parallel CLI.

- Add `--source-type` (default `fixture` to preserve GT01 back-compat) and `--source-title`
  (default = filename) to the `ingest` subparser.
- Plumb both through `_cmd_ingest` → `ingest_local_source` (already accepts `source_type`;
  add an optional `title` override).
- Stop `fetcher.fetch_local_text_file` from *forcing* `source_type`; let the CLI decide
  (keep default `fixture` when unspecified). Accept `.md` explicitly in help text.
- For real manual sources, operators pass `--source-type manual_text`.
- Optional convenience alias `research-ingest-manual-source` that calls the same code with
  `source_type` defaulting to `manual_text` — only if the operator wants the explicit verb.
  (Do **not** duplicate logic; it must delegate to `ingest_local_source`.)

**Operator source location (gitignored):** `data/sources/manual/creativity/`
(under existing `data/` ignore). ticket-086 may add a tracked `.gitkeep` **or** simply
document the path; it must **not** commit any real source file. (No safe-fixture policy
exists for private sources, so none are committed.)

**Acceptance criteria:**

1. `python -m rge.cli ingest <path.md|path.txt> --domain creativity --source-type manual_text --source-title "<title>"`
   persists exactly one `sources` row with `source_type="manual_text"`, given title,
   `status="ingested"`, `domain="creativity"`, populated `raw_text_checksum`, and ≥1 chunks.
2. **Determinism:** running the same command twice on identical content yields
   `already_ingested`, `sources` count stays 1, and chunk IDs are byte-identical across runs.
3. **`.md` supported** in addition to `.txt`.
4. **Back-compat:** existing `ingest` without `--source-type` still behaves as today;
   **GT01 unchanged and green** (140 golden total stays green).
5. **No export by default:** ingest writes nothing under `data/exports/` or
   `apps/public-site/public/data/`; safety audit passes (`status: pass`).
6. **No export leak:** a unit test asserts the public/source serialization
   (`source_record_to_public_dict`) excludes `local_path` and raw text; `local_path` remains
   a `GOLDEN_PRIVATE_FIELDS` member.
7. **No model authority:** ingestion path imports no LLM client and writes no `claims`,
   `concepts`, or `relationships`; behaves identically regardless of `RGE_LLM_MODE`.
8. **New unit tests** under `tests/unit/` cover: manual `.md` ingest, `source_type`
   persistence, title override, idempotency/chunk-ID stability, and "no rows in
   claims/concepts after ingest".
9. Repeated ingestion leaves `git status` clean (artifacts under gitignored `data/`).

**Test plan:** `python -m rge.cli ingest ... --source-type manual_text` on a tmp/real file;
`python -m pytest tests/unit/test_manual_ingestion*.py -q`; `python -m pytest tests/golden -q`
(140); `python -m rge.modules.safety_auditor --audit full`.

**Non-goals:** no URL fetch, no PDF parse, no `source_discovery`/`candidate_ranker`, no
LLM/OpenAI/cloud, no claim extraction, no concept linking, no export, no schema migration,
no validator change, no scratch DB involvement.

**Risk:** low–medium (touches ingest CLI + fetcher default + repo signature). No migration.
**Pre-ticket audit:** satisfied by this ticket-085 report (no separate audit required at the
above scope).

---

## How ticket-086 proves the three safety claims

| Claim | Proof in ticket-086 |
| ----- | ------------------- |
| Repeated ingestion is deterministic | content-addressed `src_`/`chk_` IDs; second run returns `already_ingested`; unit test asserts count==1 and identical chunk IDs |
| No public export leaks raw text or local paths | ingest produces no export; safety audit pass; unit test asserts `source_record_to_public_dict` omits `local_path`/raw text; `local_path` stays in `GOLDEN_PRIVATE_FIELDS` |
| No model output writes the accepted graph | ingestion uses only deterministic Python (fetch+parse+persist); no LLM import; unit test asserts `claims`/`concepts`/`relationships` empty after ingest |

---

## Safety boundary confirmation (this ticket)

| Boundary | Held? |
| -------- | ----- |
| No OpenAI/cloud/API added | yes |
| No ingestion implemented in 085 | yes |
| No validators changed | yes |
| No broad docs cleanup / second master audit | yes |
| No private local source files committed | yes (none created) |
| Scratch DB kept non-authoritative | yes (untouched) |
| Probe artifact left untracked | yes |

---

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.modules.principal_audit_gate --next-ticket ticket-085   # satisfied (not blocked)
python -m rge.modules.safety_auditor --audit full                     # status: pass
python -m pytest tests/golden -q                                      # 140 passed
```

Full `pytest -q` and public-site build were **not re-run** this pass: ticket-085 changes
are docs/JSON only (no Python/site code touched), and both are confirmed green at the
post-082 checkpoint and Golden Gate `27473374772`. They will be required for ticket-086.

## Merge

- Implementation SHA: `ead6cba`
- Merge commit SHA: `164c2e2`
- Pushed: `main -> main`
- Golden Gate run: (pending push CI)

## Stop

Readiness audit complete. **GO for ticket-086** (real manual Level-1 ingestion) with the
plan above. No ingestion code written here. OpenAI/cloud remains deferred.
