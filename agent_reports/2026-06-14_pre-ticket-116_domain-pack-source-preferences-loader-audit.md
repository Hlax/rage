---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-116
---

# Pre-Ticket Audit: ticket-116 Domain Pack source_preferences.yaml Loader Proof

## Verdict: **GO** (hardened scope)

Ticket-115 proved `claim_schema.yaml` drives concept-link `domain_metadata` validation. The
creativity pack's `source_preferences.yaml` defines `source_type_weights` and source lists
but is **not loaded at runtime**. Queue ranking today uses hardcoded `SOURCE_TYPE_CREDIBILITY`
in `research_queue.py`. Wiring pack weights into `rank_fixture_candidates()` is bounded,
deterministic, and does not require schema migrations, live Ollama, or public export changes.

## Current state

### Domain pack loader (`rge/modules/domain_pack_loader.py`)

| Loaded today | Not loaded |
|--------------|------------|
| `ontology.yaml` | `source_preferences.yaml` |
| `aliases.yaml` | `card_templates.yaml`, `search_templates.yaml`, … |
| `scoring.yaml` | `domain.yaml` |
| `evidence_types.yaml` | |
| `claim_schema.yaml` | |

`DomainPack` fields: concepts, aliases, alias_to_canonical, score_reconciliation,
evidence_types, claim_schema.

### Creativity `source_preferences.yaml` (committed)

| Section | Content |
|---------|---------|
| `source_type_weights` | 8 types (`meta_analysis` 0.95 … `marketing_page` 0.20) |
| `preferred_sources` | Semantic Scholar, OpenAlex, Crossref, arXiv, manual PDFs, expert interviews |
| `avoid_as_primary` | marketing landing pages, uncited hot takes, SEO summaries |

Matches `docs/agents/06_DOMAIN_PACK_SPEC.md` section 8.

### Research queue (`rge/modules/research_queue.py`)

Hardcoded `SOURCE_TYPE_CREDIBILITY` (7 entries):

| `source_type` | Hardcoded | Pack `source_type_weights` |
|---------------|----------:|----------------------------|
| `peer_reviewed_empirical` | 0.90 | 0.90 |
| `benchmark_paper` | 0.80 | 0.80 |
| `expert_interview` | 0.70 | 0.70 |
| `theory_essay` | 0.60 | 0.60 |
| `product_docs` | 0.45 | 0.45 |
| `marketing_page` | 0.20 | 0.20 |
| `blog_post` | 0.35 | **not in pack** |
| `meta_analysis` | — (fallback 0.40) | 0.95 |
| `case_study` | — (fallback 0.40) | 0.65 |

`rank_fixture_candidates()` reads `SOURCE_TYPE_CREDIBILITY`; unknown types default to **0.40**.
`queue_sources_from_fixture()` does not pass a domain pack id.

Marketing rejection remains **code-driven** (`source_type == "marketing_page"` →
`status: rejected`), not loaded from `avoid_as_primary` (defer list consumption).

### Golden Test 9 (`tests/golden/test_09_research_queue.py`)

Fixture `fixtures/candidate_sources/source_ranking_fixture.json` — five candidates:

| ID | `source_type` | Credibility today |
|----|---------------|-------------------|
| `cand_empirical_paper` | `peer_reviewed_empirical` | 0.90 |
| `cand_marketing_page` | `marketing_page` | 0.20 (rejected) |
| `cand_expert_interview` | `expert_interview` | 0.70 |
| `cand_theory_paper` | `theory_essay` | 0.60 |
| `cand_generic_blog` | `blog_post` | 0.35 |

Assertions: empirical **top** queued item; empirical > marketing and expert; marketing
`rejected`; 4 queue rows. **No assertion** on blog vs theory ordering.

**GT09-safe wiring:** pack weights match hardcoded values for all fixture types except
`blog_post` (pack missing → fallback 0.40 vs 0.35). Shift is small and does not affect
asserted ordering.

Manual synthnote pipeline does not call `queue-sources`; no manual e2e regression risk.

## Hardened scope for ticket-116

### In

1. Add `SourcePreferencesOverlay` frozen dataclass + `parse_source_preferences_yaml()` in
   `domain_pack_loader.py` (parse `source_type_weights` map + list sections for future use).
2. Extend `DomainPack` with `source_preferences: SourcePreferencesOverlay`.
3. `load_domain_pack()` loads `source_preferences.yaml`; fail closed if `source_type_weights`
   missing or empty.
4. Helper `source_type_credibility_prior(pack, source_type) -> float`:
   - Lookup normalized key in pack weights
   - Engine fallback **0.40** for unknown types (preserves GT09 stability; documents deviation
     for `blog_post` 0.35 → 0.40)
5. **Consumer:** `research_queue.rank_fixture_candidates()` — add optional `domain_pack`
   parameter (default `"creativity"`); replace `SOURCE_TYPE_CREDIBILITY` reads with pack helper.
   Keep `SOURCE_TYPE_CREDIBILITY` as **deprecated re-export** from creativity pack for any
   unit imports, or remove after updating tests.
6. `queue_sources_from_fixture()` passes `domain_pack="creativity"` (or load from research
   question domain when available — not required for GT09 fixture path).
7. **Proof test** `tests/unit/test_domain_pack_source_preferences_loader.py`:
   - Creativity pack loads weights (`peer_reviewed_empirical` 0.90)
   - Temp pack with `expert_interview: 0.95`, `peer_reviewed_empirical: 0.10` flips
     credibility priors and changes `rank_fixture_candidates()` ordering for those two fixture ids
   - Marketing still `rejected` when weight raised (status logic unchanged)
8. Update temp-pack stubs in existing domain-pack loader tests to include minimal
   `source_preferences.yaml`.

### Explicitly out (do not broaden)

- Consuming `preferred_sources` / `avoid_as_primary` lists in ranking or ingestion
- Changing marketing rejection to pack-driven `avoid_as_primary` matching
- Adding `blog_post` to creativity pack YAML (use engine fallback 0.40)
- Applying `base_strength` from evidence_types
- Loading remaining pack files (`card_templates.yaml`, etc.)
- Schema migrations, cloud / live Ollama, public site / export

## Minimal safe implementation path

```
load_domain_pack(pack_id)
  → parse source_preferences.yaml
  → DomainPack(..., source_preferences=SourcePreferencesOverlay(...))

rank_fixture_candidates(candidates, domain_pack="creativity")
  → pack = load_domain_pack(domain_pack)
  → credibility_prior = source_type_credibility_prior(pack, source_type)
  → compute_priority_score(..., credibility_prior=credibility_prior)
```

Marketing `status: rejected` branch stays in `research_queue.py` (not pack-driven).

## Mock/golden determinism preservation

- GT09 fixture types use pack weights identical to current hardcoded values (except
  `blog_post` fallback 0.40 vs 0.35 — immaterial to assertions).
- Empirical remains top queued candidate; marketing remains rejected.
- Proof of pack authority via temp-pack weight inversion unit test.

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| GT09 ordering drift | Medium | Pack values match hardcoded; run GT09 + full golden |
| `blog_post` credibility 0.35 → 0.40 | Low | Not asserted in GT09; document in report |
| `DomainPack` dataclass change | Low | Add field; update temp-pack stubs |
| Over-scoping into preferred/avoid lists | Medium | Hardened scope: weights only |
| Public export leak | Low | No export/schema changes |

## Expected files to change

| File | Change |
|------|--------|
| `rge/modules/domain_pack_loader.py` | Parse source_preferences; extend `DomainPack` |
| `rge/modules/research_queue.py` | Pack-driven credibility priors |
| `tests/unit/test_domain_pack_source_preferences_loader.py` | New proof tests |
| `tests/unit/test_domain_pack_*.py` | source_preferences stubs in demo packs |
| `agent_reports/2026-06-14_ticket-116_domain-pack-source-preferences-loader.md` | Implementation report |

## Tests to add / run

**New:**

- `test_creativity_pack_loads_source_type_weights`
- `test_temp_pack_weight_inversion_changes_rank_order`
- `test_marketing_still_rejected_despite_high_pack_weight`

**Regression (ticket test_plan):**

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_domain_pack_source_preferences_loader.py -q
python -m pytest tests/unit/test_domain_pack_claim_schema_loader.py -q
python -m pytest tests/golden/test_09_research_queue.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Principal audit gate

Cadence satisfied (`agent_reports/2026-06-14_principal-audit-post-ticket-114.md`; 1 done
since checkpoint).

After this report is committed:

```powershell
python -m rge.modules.principal_audit_gate --next-ticket ticket-116
```

should show `implementation_gate: satisfied` for medium-risk ticket-116.

## NO-GO triggers (none active)

- Would be NO-GO if pack weights diverged from hardcoded GT09 values — **they align** for
  asserted candidates.
- Would be NO-GO if marketing rejection depended on pack lists in this ticket — **not proposed**.
- Would be NO-GO if schema migration required — **it is not**.

## Recommendation

Proceed with ticket-116 on branch `phase-2/ticket-116-domain-pack-source-preferences-loader`
using the hardened scope above. After implementation, next smallest product move is wiring
`card_templates.yaml` or applying `evidence_types` `base_strength` priors — not another doc
cross-link.
