# Agent Report: ticket-315 — Evidence DB Atlas re-export proof refresh v0

**Date:** 2026-06-18  
**Ticket:** ticket-315  
**Branch:** `phase-3/ticket-315-evidence-db-atlas-reexport-proof-refresh-v0`  
**Main tip before branch:** `main` @ synced with `origin/main`  
**Supersedes:** proposed README-only ticket-315 runbook scope (deferred)

## Summary

Refreshed operator-private evidence DB atlas export + coherence proof on a freshly
bootstrapped gitignored DB. **Coherence pass** on export mechanics; **product verdict
PARTIAL** — pipeline populates all atlas sections but graph richness remains too thin
for a compelling Research Atlas frontend without staged-spine or richer live evidence.

**Drift advisory (center):** This ticket breaks the six-ticket infra/docs streak (309–314)
with operator product proof, not another README. It does **not** close the underlying
live-research cadence gap: Ollama was unreachable and ticket-293 live NM-1 DB was absent
on this machine, so refresh used stub-live NM-4 spine (same regression path as pytest).

## Scope

**In:** Operator re-export on gitignored evidence DB; nine-question product assessment;
regression pytest; full verify.

**Out:** README runbook (superseded), production code, public routes/site, CI live tests,
schema migrations, review_batch persistence.

## Blockers and fallback path

| Blocker | Detail |
|---------|--------|
| ticket-293 live NM-1 DB | `data/db/ticket293_live_nm1_quality_proof.sqlite` **not present** on operator machine |
| Live Ollama | `model-health`: reachable=false; WinError 10061 on :11434 |
| Fallback | Ingest ticket127 source → stub-live extract+link (patched client, same as unit tests) → `export-atlas-snapshot` hooks populate runs/cards/reports/clusters/edges |

Honest framing: this proves **export/coherence mechanics** on the evidence DB path; it
does **not** re-validate live Ollama NM-1 quality from ticket-293.

## Operator artifacts (gitignored)

| Path | Purpose |
|------|---------|
| `data/db/ticket315_evidence_atlas_refresh.sqlite` | Bootstrapped evidence DB |
| `data/atlas/ticket315/atlas_snapshot_v315.json` | Private atlas export |
| `data/atlas/ticket315/atlas_coherence_report_v315.json` | Coherence JSON |
| `data/atlas/ticket315/atlas_coherence_report_v315.md` | Coherence markdown |

## Operator commands

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
$DB = "data/db/ticket315_evidence_atlas_refresh.sqlite"
$TOPIC = "Does AI-assisted songwriting reduce creative diversity in workshop drafts?"

# ingest (see report for stub-live extract+link bootstrap when Ollama unavailable)
python -m rge.cli ingest fixtures/sources/ticket127_arbitrary_manual_live.txt `
  --domain creativity --source-type manual_text `
  --source-title "Ticket-315 evidence atlas refresh" --db $DB

python -m rge.cli export-atlas-snapshot --db $DB `
  --out data/atlas/ticket315/atlas_snapshot_v315.json `
  --topic $TOPIC --domain creativity
# overall_coherence_verdict: pass

python -m rge.cli atlas-coherence-report `
  --snapshot data/atlas/ticket315/atlas_snapshot_v315.json `
  --out-json data/atlas/ticket315/atlas_coherence_report_v315.json `
  --out-md data/atlas/ticket315/atlas_coherence_report_v315.md
```

## Product assessment (nine questions)

| # | Question | Answer |
|---|----------|--------|
| 1 | Does evidence DB export produce populated `runs[]`? | **Yes** — 1 run (`run_evidence_e5702e75029cf509`, mode `live_evidence`, `research_question_id` present) |
| 2 | Meaningful `nodes[]` and `edges[]`? | **Partial** — 24 nodes (domain ontology catalog; only 2 concepts research-linked); 1 projected relationship edge (`AI assistance` → `ideation`, `may_influence`) |
| 3 | Cards/claims connected to sources and domains? | **Yes** — `card_claim_922897d244ce2be9` with concepts, `public_source_metadata`, creativity domain |
| 4 | Reports represented clearly? | **Yes** — 1 run_report with `run_id`, informational status, public_summary |
| 5 | Follow-up questions when expected? | **Yes** — 1 active question tied to `rq_evidence_*`, full contract fields |
| 6 | Lineage understandable for Research Atlas frontend? | **Partial** — `research_question_id` on run; no `parent_question_id`, spawn fields, or multi-run lineage |
| 7 | Coherence report pass or fail? | **Pass** — all sub-verdicts pass; `missing_fields_create_refactor_risk.notes` empty |
| 8 | If fail, root cause? | **N/A (pass)** — weakness is **data quality / graph richness**, not export mechanics or missing projection fields |
| 9 | Next product improvement ticket? | **ticket-316** — live staged-spine operator proof refresh (recommended over more docs) |

## Population snapshot

| Field | ticket-298 (ticket-293 DB) | ticket-315 refresh |
|-------|---------------------------:|-------------------:|
| `overall_coherence_verdict` | pass | pass |
| runs | 1 | 1 |
| cards | 1 (claim-backed) | 1 (claim-backed) |
| reports | 1 | 1 |
| follow_up_questions | 1 | 1 |
| clusters | 1 | 1 |
| edges | 1 | 1 |
| nodes | 24 | 24 |

Parity with ticket-298 on counts confirms export hooks remain stable; neither path yet
delivers multi-claim, multi-source atlas richness.

## Product verdict

**PARTIAL**

- **GO on mechanics:** evidence DB export path produces contract-valid snapshot; coherence pass; claim-backed card (not golden placeholder); all atlas sections populated.
- **Weak on product usefulness:** single claim, single edge, ontology-heavy node list — insufficient for Research Atlas UX beyond smoke/demo.
- **Not NO-GO:** export does populate the atlas product model meaningfully at v0 schema level.

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Private atlas export from evidence DB path | **PASS** |
| atlas-coherence-report on snapshot | **PASS** — overall **pass** |
| Human report with GO/PARTIAL/NO-GO | **PASS** — **PARTIAL** |
| Supersedes README-only ticket-315 | **PASS** |
| Golden + pytest + safety + site build | **PASS** — see below |
| Next product move stated | **PASS** — staged-spine operator proof |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_evidence_db_atlas_projection.py `
  tests/unit/test_evidence_db_run_report_projection.py `
  tests/unit/test_evidence_db_cluster_projection.py `
  tests/unit/test_evidence_db_relationship_projection.py -q
# 12 passed

python -m rge.cli verify --skip-site
# 144 golden, 789 pytest, safety audit pass

cd apps/public-site && npm run build
# success; /atlas-preview exported
```

## Drift advisory

| Signal | Status |
|--------|--------|
| Infra/docs streak since ticket-309 | **Broken** by this operator proof (not README) |
| Live-research cadence since ticket-298 | **Still stale** — no live Ollama NM-1 re-run; no staged-spine advance |
| ticket-315 original README runbook | **Deferred** — commands already in README from ticket-298 family; duplicating adds no product signal |

**Next move should be:** **live staged-spine operator proof** (ticket-316), not extraction
quality repair (mechanics pass), not Atlas projection field repair (coherence pass), and
not public preview UI iteration until richer private atlas data exists.

Secondary path when Ollama returns: re-run ticket-293 NM-1 DB on operator machine and
compare live vs stub-live card/edge quality.

## Changed files

| File | Change |
|------|--------|
| `agent_reports/2026-06-18_phase-3_ticket-315_evidence-db-atlas-reexport-proof-refresh-v0.md` | This report |
| `tickets/ticket-315.json` | Repurposed from README runbook → product proof; status `done` |
| `tickets/ticket-316.json` | Seeded staged-spine follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

## Recommended next ticket

**ticket-316** — Live staged-spine operator proof refresh v0 (`pytest -m live_network`
opt-in when network gates set; mock layer-2 fallback with honest blocker if gates absent).

## Merge to main

Merge commit: `303082c`

## Suggested next prompt

```txt
/rge-run-next-ticket
```
