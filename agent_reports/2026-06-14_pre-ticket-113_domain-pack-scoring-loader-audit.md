---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-113
---

# Pre-Ticket Audit: ticket-113 Domain Pack scoring.yaml Loader Proof

## Verdict: **GO** (hardened scope)

The creativity pack's `scoring.yaml` exists but is **not loaded at runtime**.
Score reconciliation today uses **hardcoded module constants** (`STRONGER_SOURCE_BOOST = 0.12`,
`STRONGER_CLAIM_CONFIDENCE_THRESHOLD = 0.8`) in `score_reconciler.py`. Wiring a narrow
`score_reconciliation` overlay from the pack is bounded, deterministic, and does not
require schema migrations, live Ollama, or public export changes.

## Current state

### Domain pack loader (`rge/modules/domain_pack_loader.py`)

| Loaded today | Not loaded |
|--------------|------------|
| `ontology.yaml` | `scoring.yaml` |
| `aliases.yaml` | `evidence_types.yaml`, `claim_schema.yaml`, … (7 other files) |

`DomainPack` dataclass: `pack_id`, `concepts`, `aliases`, `alias_to_canonical` only.

Consumers: `concept_linker.py`, `repositories.py` (ontology seeding). **`score_reconciler.py` does not call `load_domain_pack`.**

### Creativity `scoring.yaml` (committed)

Contains `claim_scoring_overlay` with domain_match penalties, scope_clarity flags,
`evidence_bonus` values, and contradiction_handling — **none of which are consumed by code today**.

**Gap:** the values actually driving reconcile-scores are **not in scoring.yaml**:

| Constant (hardcoded) | Value | Used by |
|----------------------|------:|---------|
| `STRONGER_SOURCE_BOOST` | 0.12 | GT08 (0.52→0.64), manual synthnote (0.5→0.62) |
| `STRONGER_CLAIM_CONFIDENCE_THRESHOLD` | 0.8 | stronger-evidence gate |
| `STRONGER_SOURCE_REASON` | string | `score_events.reason` |
| `FORMULA_VERSION` | `golden_v0.1.0` | `score_events.formula_version` |

### Score reconciler (`rge/modules/score_reconciler.py`)

- `reconcile_scores_for_source(conn, source_id)` — production CLI path
- `claim_supports_relationship()` uses **creativity-specific** subject/object/predicate
  strings (`AI assistance`, `semantic diversity`, `may_reduce`) for relationship matching
- Matching logic is **not** scoring-overlay math; defer moving matchers to pack in this ticket

### Tests that lock current behavior

| Test | Expected score change |
|------|----------------------|
| `tests/golden/test_08_score_reconciliation.py` | 0.52 → 0.64 |
| `tests/unit/test_manual_source_pipeline_e2e.py` | 0.5 → 0.62 |
| `tests/unit/test_manual_source_pipeline_idempotency.py` | 0.5 → 0.62 |
| `tests/unit/test_manual_score_reconciliation.py` | imports `STRONGER_SOURCE_BOOST` |

All must remain green when creativity pack values stay **0.12 / 0.8**.

## Hardened scope for ticket-113

### In

1. **Extend** `domain_packs/creativity/scoring.yaml` with a explicit reconcile block
   (preserve existing `claim_scoring_overlay`; add sibling section):

   ```yaml
   score_reconciliation:
     formula_version: golden_v0.1.0
     stronger_evidence_boost: 0.12
     stronger_claim_confidence_threshold: 0.8
     stronger_source_reason: >-
       New supporting empirical claim from higher-credibility source.
   ```

2. Add `parse_scoring_yaml()` + `ScoreReconciliationOverlay` (frozen dataclass) in
   `domain_pack_loader.py`; extend `DomainPack` with `score_reconciliation` field.

3. `load_domain_pack()` loads `scoring.yaml`; fail closed if reconcile section missing
   required keys for creativity (or define minimal required subset).

4. `score_reconciler.py`:
   - Resolve domain from relationship `domain` field (or source domain via claims)
   - Load pack overlay via `load_domain_pack(domain)`
   - Replace uses of module-level `STRONGER_*` constants with overlay values
   - Keep `STRONGER_*` as **deprecated aliases** re-exporting creativity defaults only
     for backward-compatible test imports, OR update tests to read from pack

5. **Proof test** `tests/unit/test_domain_pack_scoring_loader.py`:
   - Creativity pack loads boost 0.12 / threshold 0.8
   - Temp pack with `stronger_evidence_boost: 0.20` yields demonstrably different
     `compute_relationship_score` / reconcile output (0.5 → 0.70)

6. No changes to golden fixtures, public export, or live paths.

### Explicitly out (do not broaden)

- Moving `GOLDEN_SUBJECT` / `GOLDEN_OBJECT` / `GOLDEN_PREDICATE` relationship matchers into pack
- Loading `evidence_types.yaml`, `claim_schema.yaml`, or other pack files
- Applying `claim_scoring_overlay.domain_match` penalties in reconciler (future ticket)
- Schema migrations
- Cloud / live Ollama
- Public site / export

## Minimal safe implementation path

```
load_domain_pack(pack_id)
  → parse scoring.yaml
  → DomainPack(..., score_reconciliation=ScoreReconciliationOverlay(...))

reconcile_scores_for_source(conn, source_id)
  → for each matching relationship:
      overlay = load_domain_pack(relationship["domain"]).score_reconciliation
      gate: claim.confidence >= overlay.stronger_claim_confidence_threshold
      new_score = min(1.0, old + overlay.stronger_evidence_boost)
      score_events.reason = overlay.stronger_source_reason
      score_events.formula_version = overlay.formula_version
```

Cache pack per reconcile call (single domain per creativity run); no global mutable cache required.

## Mock/golden determinism preservation

- Creativity `scoring.yaml` reconcile values **must match current constants** (0.12, 0.8)
  so GT08 and manual synthnote expectations unchanged.
- Proof of pack authority comes from **temp-pack unit test** with different boost value.
- Golden tests stay mock-only; no new Ollama dependency.

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| GT08 / manual e2e score drift | Medium | Keep creativity values identical; run full test plan |
| `DomainPack` dataclass change | Low | Add field; frozen dataclass; update constructors only |
| Over-scoping into claim_scoring_overlay | Medium | Hardened scope: reconcile block only |
| Public export leak | Low | No export/schema changes |

## Expected files to change

| File | Change |
|------|--------|
| `domain_packs/creativity/scoring.yaml` | Add `score_reconciliation` section |
| `rge/modules/domain_pack_loader.py` | Parse scoring; extend `DomainPack` |
| `rge/modules/score_reconciler.py` | Consume pack overlay |
| `tests/unit/test_domain_pack_scoring_loader.py` | New proof tests |
| `tests/unit/test_domain_pack_loader.py` | Optional: assert scoring loaded |
| `agent_reports/2026-06-14_ticket-113_domain-pack-scoring-loader.md` | Implementation report |

## Tests to add / run

**New:**

- `test_parse_scoring_yaml_reads_reconcile_block`
- `test_load_creativity_pack_includes_score_reconciliation`
- `test_different_pack_boost_changes_reconcile_output` (temp pack, mock DB)

**Regression (ticket test_plan):**

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_domain_pack_scoring_loader.py -q
python -m pytest tests/unit/test_manual_source_pipeline_e2e.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Principal audit gate

After this report is committed, `python -m rge.modules.principal_audit_gate --next-ticket ticket-113`
should show `implementation_gate: satisfied` for medium-risk ticket-113.

Cadence: satisfied (0 done tickets since post-ticket-110 checkpoint; ticket-112 merge not yet
in queue as `done` row — queue update on ticket-113 completion will address cadence).

## NO-GO triggers (none active)

- Would be NO-GO if creativity pack could not express 0.12/0.8 without breaking spec — **it can**, via new reconcile section.
- Would be NO-GO if reconcile required schema migration — **it does not**.
- Would be NO-GO if only path was weakening GT08 thresholds — **not proposed**.

## Recommendation

Proceed with ticket-113 on branch `phase-2/ticket-113-domain-pack-scoring-loader` using
the hardened scope above. After implementation, next smallest product move is wiring one
additional pack file (e.g. `evidence_types.yaml`) or live-extraction calibration — not
another doc cross-link.
