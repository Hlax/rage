---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-131
category: product-risk reduction / NM-4 pipeline continuation
---

# Pre-Ticket Audit: ticket-131 NM-4 Evidence DB Score Reconciliation Operator Proof

## Verdict: **GO**

Principal audit post-ticket-130 retargeted ticket-131 away from a non-existent live
Ollama reconcile path. Score reconciliation is **deterministic Python** driven by
domain-pack overlays and accepted claims — mirror ticket-099 synthnote proof on the
gitignored evidence DB instead.

## Scope correction (from post-ticket-130)

| Incorrect (prior JSON) | Correct (retargeted) |
|---|---|
| Live Ollama score reconciliation fall-through | Deterministic `reconcile-scores` operator proof |
| Mock fixture map task for reconcile | No fixture map entry; follow-up uses extract fixtures / live extract |
| `--live-manual-*` on reconcile-scores | Explicit `--db data/db/live_research_evidence.sqlite` only |

## Current score reconciliation path

| Location | Role |
|----------|------|
| `rge/modules/score_reconciler.py` | Deterministic matcher + domain-pack overlay boost |
| `domain_packs/creativity/scoring.yaml` | `score_reconciliation.formula_version`, boost, threshold |
| `tests/unit/test_manual_score_reconciliation.py` | Synthnote + follow-up mock proof (ticket-099) |
| Evidence DB | `data/db/live_research_evidence.sqlite` (gitignored) |

Persistence: `score_events` append-only rows + optional `relationship_evidence`
via `persist_relationship_score_update`.

## Evidence DB baseline (post ticket-130)

| Field | Value |
|-------|-------|
| Primary source | `src_1b8354e5f2203f82` (ticket-127 NM-4 live proof) |
| Active relationships | 1 (`AI assistance` → `constraint`, `supports`, conf 0.5) |
| Contradiction result | `no_qualifications` (expected — single edge) |
| Score events | none yet |

**Gap:** `claim_supports_relationship()` today only matches the golden
`may_reduce` + `semantic diversity` triple. Live-drafted edges (e.g.
`supports` / `constraint`) will not reconcile without matcher hardening.

## Hardened implementation scope

### In

1. Extend `claim_supports_relationship` (or adjacent helper) so follow-up claims
   can match **active relationships on the evidence DB graph** — e.g. claims whose
   text supports an existing edge subject/object/predicate family, with confidence
   ≥ overlay threshold.
2. Add committed follow-up fixture `fixtures/sources/ticket131_nm4_evidence_followup.txt`
   (operator copy under gitignored `data/sources/manual/creativity/` optional).
3. Unit/integration test `tests/unit/test_nm4_evidence_score_reconciliation.py`:
   stub/live spine on temp `--db` mirroring evidence DB shape → follow-up ingest →
   extract (mock stub or live fallthrough) → `reconcile-scores` → assert ≥1
   `score_events` row and confidence bump.
4. Operator CLI proof on evidence DB (document in agent report):
   ingest follow-up → extract (live fallthrough if unmapped) → reconcile-scores.
5. Optional CLI guard: clear error when reconciling against default graph DB without
   explicit intent (mirror evidence DB patterns from tickets 127–130 if useful).

### Out

- Ollama calls inside `score_reconciler`
- New live reconcile flags
- Validator weakening
- Public export/site/schema changes
- Docs cross-link chain

## Mock/golden determinism

- `test_manual_score_reconciliation.py` must remain green (synthnote path unchanged).
- Golden tests stay mock-only; no Ollama in CI.

## Live mode (extract only)

Follow-up extract on unmapped `manual_text` may reuse existing
`--live-manual-fallthrough` (ticket-127). **Reconcile-scores itself stays
deterministic** — no `RGE_ALLOW_LIVE_LLM` requirement for the reconcile step.

## Tests to add

| Test | Purpose |
|------|---------|
| Evidence-shaped graph + follow-up reconcile | ≥1 score_events |
| Synthnote reconcile regression | ticket-099 unchanged |
| Idempotent reconcile re-run | no duplicate score_events |
| Matcher rejects insufficient confidence | skip reason surfaced |

## Expected file changes

| File | Change |
|------|--------|
| `rge/modules/score_reconciler.py` | Evidence-graph matcher hardening |
| `rge/cli.py` | Optional evidence DB guard / JSON clarity |
| `fixtures/sources/ticket131_nm4_evidence_followup.txt` | Follow-up operator text |
| `tests/unit/test_nm4_evidence_score_reconciliation.py` | NM-4 evidence proof tests |

## Principal audit gate

| Gate | Status |
|------|--------|
| Cadence (post-ticket-130) | **satisfied** |
| Pre-ticket audit (this report) | **GO** |
| Milestone (live Ollama constraint) | **not triggered** — reconcile is deterministic |

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement retargeted ticket-131 | **GO** |

## Next command

```text
/rge-run-next-ticket
```
