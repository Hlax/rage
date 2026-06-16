# Agent Report: ticket-293 — Live NM-1 extraction + Atlas coherence quality proof v0

**Date:** 2026-06-16  
**Ticket:** ticket-293  
**Branch:** `phase-3/ticket-293-live-nm1-atlas-quality-proof-v0`  
**Main tip before branch:** `82d8e4d`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-293_live-nm1-atlas-quality-proof-audit.md` (GO)

## Summary

Executed opt-in live Ollama NM-1 extraction on a gitignored evidence DB, expanded with
NM-4 live link/build fallthrough, exported a private atlas snapshot, and generated a
coherence report. Live research **does** produce validated claims, concept links, and
relationship edges — but the Atlas snapshot is **not yet frontend-ready** because
`runs[]` is empty and `cards[]` are golden fixture placeholders rather than live-derived
summaries.

**Human quality verdict: PARTIAL**

## Scope

**In:** Operator live run, private atlas export + coherence report, quality assessment agent report.

**Out:** Production code, default pytest live tests, public routes/site, schema migrations,
review_batch persistence, staged network proofs.

## Changed files

| File | Change |
|------|--------|
| `agent_reports/2026-06-16_pre-ticket-293_live-nm1-atlas-quality-proof-audit.md` | Pre-ticket GO (on main) |
| `agent_reports/2026-06-16_phase-3_ticket-293_live-nm1-atlas-quality-proof-v0.md` | This report |
| `tickets/ticket-293.json` | Status `done` |
| `tickets/ticket-294.json` | Seeded follow-on |
| `tickets/TICKET_QUEUE.md` | Queue update |

**Operator artifacts (gitignored under `data/`):**

| Path | Purpose |
|------|---------|
| `data/db/ticket293_live_nm1_quality_proof.sqlite` | Live-derived evidence DB |
| `data/atlas/ticket293/atlas_snapshot.json` | Private atlas export |
| `data/atlas/ticket293/atlas_coherence_report.json` | Coherence verdict JSON |
| `data/atlas/ticket293/atlas_coherence_report.md` | Coherence markdown |
| `data/atlas/ticket293/01_ingest.json` … `06_*.json` | Step stdout captures |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Opt-in live research run executed | **PASS** — Ollama qwen2.5:7b; no gate blocker |
| Private atlas_snapshot.json exported | **PASS** — `data/atlas/ticket293/atlas_snapshot.json` |
| Coherence report via CLI | **PASS** — JSON + MD written |
| Human-readable GO/PARTIAL/NO-GO with evidence | **PASS** — **PARTIAL** (see below) |
| Recommends concrete next improvement | **PASS** — ticket-294 seeded |
| Mock golden/full pytest green | **PASS** — 142 golden, 745 full |

## Live operator run

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health   # status: ok

$DB = "data/db/ticket293_live_nm1_quality_proof.sqlite"

python -m rge.cli ingest fixtures/sources/ticket127_arbitrary_manual_live.txt `
  --domain creativity --source-type manual_text `
  --source-title "Ticket-293 NM-1 quality proof" --db $DB
# source_id: src_1b8354e5f2203f82

python -m rge.cli extract-claims-live --source src_1b8354e5f2203f82 --db $DB
# accepted_count: 1, rejected_count: 1

python -m rge.cli link-concepts --source src_1b8354e5f2203f82 --db $DB `
  --live-manual-link-fallthrough
# link_count: 2 (AI assistance, ideation)

python -m rge.cli build-relationships --source src_1b8354e5f2203f82 --db $DB `
  --live-manual-relationship-fallthrough
# relationship_count: 1 (AI assistance supports constraint)

python -m rge.cli export-atlas-snapshot --db $DB `
  --out data/atlas/ticket293/atlas_snapshot.json `
  --topic "Does AI-assisted songwriting reduce creative diversity in workshop drafts?" `
  --domain creativity

python -m rge.cli atlas-coherence-report `
  --snapshot data/atlas/ticket293/atlas_snapshot.json `
  --out-json data/atlas/ticket293/atlas_coherence_report.json `
  --out-md data/atlas/ticket293/atlas_coherence_report.md
```

## Quality assessment (human-readable)

### Overall verdict: **PARTIAL**

Pipeline mechanics and live extraction quality are proven; Atlas population gaps block
a GO for frontend expansion.

| Question | Finding |
|----------|---------|
| 1. Did live extraction produce useful claims? | **Yes** — 1 accepted claim with scoped workshop language, quote span, and char ranges; 1 rejected (`unsupported_claim`) showing validator gate works |
| 2. Are claims linked to sources? | **Yes** — claim tied to `src_1b8354e5f2203f82` and chunk with quote evidence |
| 3. Are claims linked to concepts/domains? | **Yes** — 2 concept links (`AI assistance`, `ideation`) on accepted claim; creativity domain on relationship |
| 4. Meaningful edges, not isolated cards? | **Partial** — 1 active relationship edge with evidence row; graph is minimal but not empty |
| 5. Did follow-up questions appear? | **No** — `follow_up_questions[]` empty (no research_queue population on NM-1 spine) |
| 6. Did lineage fields make the trail understandable? | **No** — `runs[]` empty; no `research_question_id` lineage on evidence DB spine |
| 7. Frontend-ready for Research Atlas? | **No** — cards are golden fixture placeholders (`card_golden_diversity_001`) seeded by `ensure_golden_public_cards`, not live-derived summaries; coherence `overall_coherence_verdict: fail` |
| 8. Next improvement? | Wire evidence DB spine to `research_runs` + `generate-run-report`, and project **live-derived** public cards into atlas export instead of golden seed fallbacks |

### Coherence report summary

| Field | Count |
|-------|------:|
| runs | 0 |
| nodes | 24 |
| edges | 1 |
| cards | 2 |
| reports | 0 |
| follow_up_questions | 0 |

- `overall_coherence_verdict`: **fail** (missing runs — fails meaningful_atlas_data)
- `claims_linked_to_sources_and_concepts`: **pass**
- Private-field scan: **clean**
- Contract validation: **pass**

### Stability

Atlas export from live DB is **structurally stable** (schema-valid, deterministic given DB
state) but **not byte-stable** across runs (timestamps, snapshot_id). Coherence report is
**structurally stable** given snapshot input.

### Private-field scanning before write

**Yes** — export-atlas-snapshot runs validation + private-field scan before write;
coherence report confirms `private_field_violations: []`.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 745 passed, 33 deselected
```

Safety audit not required — gitignored operator paths only; no public surface changes.

## Spec deviations

NM-4 live link/build fallthrough included per pre-ticket-293 hardened scope (expansion
beyond bare NM-1 extract for linkage/edge quality assessment). No production code added.

## Drift note

Ticket-293 completes the product-centered pivot from Atlas pipeline mechanics (289–292).
Next work must address **live-derived atlas population** (runs, cards, follow-ups) — not
another operator-tooling-only ticket.

## Recommended next ticket

**ticket-294** — Evidence DB research_run lineage + live-derived atlas card projection v0

## Suggested next prompt

```txt
/rge-principal-audit
```

## Merge to main

Merge commit: _(pending)_
