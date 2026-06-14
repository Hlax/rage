---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-115
---

# Pre-Ticket Audit: ticket-115 Domain Pack claim_schema.yaml Loader Proof

## Verdict: **GO** (hardened scope)

Ticket-114 proved `evidence_types.yaml` drives claim validation allowlists. The creativity pack's
`claim_schema.yaml` defines required metadata keys and allowed values for `track`,
`creative_phase`, and `measured_dimension` but is **not loaded at runtime**. `concept_linker.py`
documents pack-backed `domain_metadata` validation but `validate_concept_links()` does not
consult the pack today. Wiring a narrow loader plus concept-link metadata gate is bounded,
deterministic, and does not require schema migrations, live Ollama, or public export changes.

## Current state

### Domain pack loader (`rge/modules/domain_pack_loader.py`)

| Loaded today | Not loaded |
|--------------|------------|
| `ontology.yaml` | `claim_schema.yaml` |
| `aliases.yaml` | `source_preferences.yaml`, `card_templates.yaml`, … |
| `scoring.yaml` (`score_reconciliation`) | |
| `evidence_types.yaml` | |

`DomainPack` fields: `pack_id`, `concepts`, `aliases`, `alias_to_canonical`,
`score_reconciliation`, `evidence_types`.

### Creativity `claim_schema.yaml` (committed)

| Section | Content |
|---------|---------|
| `required_domain_metadata_for_creativity_claims` | `track`, `creative_phase`, `measured_dimension` |
| `allowed_tracks` | `human`, `AI`, `human-AI` |
| `allowed_creative_phases` | 8 phases (`ideation` … `audience_interpretation`) |
| `allowed_measured_dimensions` | 11 values including `diversity`, `semantic diversity`, `quality` |

Matches `docs/agents/06_DOMAIN_PACK_SPEC.md` section 11.

**Not in allowlist:** `idea diversity` — used in contradiction fixtures as a
`measured_dimension` value and as a concept alias (`aliases.yaml` → `semantic diversity`).

### Concept linker (`rge/modules/concept_linker.py`)

- `validate_concept_links()` checks batch diversity and required link fields only.
- **No** `domain_metadata` allowlist enforcement.
- `link_concepts_for_source()` persists `domain_metadata` from accepted links unchanged.
- Docstring claims pack validation — implementation gap ticket-115 closes.

### Claim validator (`rge/modules/claim_validator.py`)

- Does not inspect `domain_metadata` on claim candidates (empty `{}` accepted).
- Ticket-115 **primary consumer** should be `concept_linker`; optional claim-path validation
  is out of hardened scope unless needed for acceptance (not required if concept linker proves pack authority).

### Fixture / golden compatibility matrix

| Fixture / test | `domain_metadata` pattern | Pack compatibility |
|----------------|---------------------------|-------------------|
| GT05 `concept_linking_creativity_diversity.json` | all three keys; `diversity`, `human-AI`, `ideation` | **OK** |
| `concept_linking_manual_synthnote.json` | one link **without** `measured_dimension` | Must not require all keys on every link |
| `concept_linking_creativity_diversity_contradiction.json` | `measured_dimension: idea diversity` | Needs **alias normalization** → `semantic diversity` |
| `claim_extraction_creativity_diversity_contradiction.json` | claim `domain_metadata` with `idea diversity` | Not on concept-link path; defer claim-level gate |
| Claims with `domain_metadata: {}` | manual synthnote, prompt injection | Must pass when metadata empty |

## Hardened scope for ticket-115

### In

1. Add `ClaimSchemaOverlay` frozen dataclass + `parse_claim_schema_yaml()` in
   `domain_pack_loader.py` (hand-rolled parser; no PyYAML).
2. Extend `DomainPack` with `claim_schema: ClaimSchemaOverlay`.
3. `load_domain_pack()` loads `claim_schema.yaml`; fail closed if required sections missing.
4. Helpers:
   - `allowed_domain_metadata_values(pack, key) -> frozenset[str]` (casefold-normalized)
   - `validate_link_domain_metadata(pack, metadata) -> tuple[bool, str | None]` — validates
     **present** keys only; does not require every link to carry all required keys.
5. **Measured_dimension normalization:** before allowlist check, if value is not directly
   allowed, resolve via `resolve_canonical_concept_label(pack, value)` and accept when the
   resolved label is in `allowed_measured_dimensions` (covers `idea diversity` → `semantic diversity`
   without editing committed allowlist or golden fixtures).
6. **Consumer:** extend `validate_concept_links()` (or call helper from it) with optional
   `domain_pack: str` parameter; `link_concepts_for_source()` passes source domain pack and
   rejects links whose present `domain_metadata` values fall outside pack allowlists
   (`weak_concept_mapping` + diagnostic via `link_rejection_diagnostic`).
7. **Proof test** `tests/unit/test_domain_pack_claim_schema_loader.py`:
   - Creativity pack loads expected allowlists (`empirical` path not involved)
   - Temp pack with `allowed_creative_phases: [critique]` only rejects `ideation` on links
   - Temp pack accepts `ideation` when other link validation passes
   - Creativity pack accepts `measured_dimension: idea diversity` after alias normalization
8. Update temp-pack stubs in loader/scoring/evidence_types tests to include minimal
   `claim_schema.yaml` once `load_domain_pack()` requires it.

### Explicitly out (do not broaden)

- Requiring all `required_domain_metadata_for_creativity_claims` keys on every concept link
  (breaks manual synthnote fixture link missing `measured_dimension`)
- Claim-level `domain_metadata` validation in `claim_validator` (future ticket if needed)
- Applying `base_strength` priors from `evidence_types.yaml`
- Loading `source_preferences.yaml`, `card_templates.yaml`, or other pack files
- Adding `idea diversity` to `claim_schema.yaml` allowlist (use alias normalization instead)
- Schema migrations, cloud / live Ollama, public site / export

## Minimal safe implementation path

```
load_domain_pack(pack_id)
  → parse claim_schema.yaml
  → DomainPack(..., claim_schema=ClaimSchemaOverlay(...))

validate_concept_links(links, domain_pack="creativity")
  → for each link with non-empty domain_metadata:
      for each present key in (track, creative_phase, measured_dimension):
        if key == measured_dimension:
          normalize via resolve_canonical_concept_label when direct allowlist miss
        reject if value not in pack allowlist

link_concepts_for_source(...)
  → validate_concept_links(proposed, domain_pack=domain_pack)
```

Injection / weak-mapping batch rules unchanged before metadata gate.

## Mock/golden determinism preservation

- GT05 diversity links: `diversity`, `human-AI`, `ideation` — all in pack.
- GT07 contradiction concept links: `idea diversity` normalized to allowed `semantic diversity`.
- Manual synthnote partial metadata link (no `measured_dimension`) — still accepted.
- Empty claim `domain_metadata` on extraction fixtures — unaffected (concept-link path only).

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| GT07 / contradiction concept linking | Medium | Alias normalization for `measured_dimension` |
| Manual synthnote partial metadata | Medium | Validate present keys only; do not require full triple |
| `DomainPack` dataclass change | Low | Add field; update temp-pack stubs |
| Over-scoping into claim_validator | Medium | Hardened scope: concept_linker only |
| Public export leak | Low | No export/schema changes |

## Expected files to change

| File | Change |
|------|--------|
| `rge/modules/domain_pack_loader.py` | Parse claim_schema; extend `DomainPack` |
| `rge/modules/concept_linker.py` | Pack-backed `domain_metadata` validation |
| `tests/unit/test_domain_pack_claim_schema_loader.py` | New proof tests |
| `tests/unit/test_domain_pack_loader.py` | claim_schema stubs in demo packs |
| `tests/unit/test_domain_pack_scoring_loader.py` | claim_schema stubs |
| `tests/unit/test_domain_pack_evidence_types_loader.py` | claim_schema stubs |
| `agent_reports/2026-06-14_ticket-115_domain-pack-claim-schema-loader.md` | Implementation report |

## Tests to add / run

**New:**

- `test_creativity_pack_loads_claim_schema_overlay`
- `test_temp_pack_restricted_phase_rejects_ideation`
- `test_creativity_normalizes_idea_diversity_measured_dimension`
- `test_partial_domain_metadata_link_still_accepted`

**Regression (ticket test_plan):**

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_domain_pack_claim_schema_loader.py -q
python -m pytest tests/unit/test_domain_pack_evidence_types_loader.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Principal audit gate

Principal cadence satisfied via
`agent_reports/2026-06-14_principal-audit-post-ticket-114.md`.

After this report is committed:

```powershell
python -m rge.modules.principal_audit_gate --next-ticket ticket-115
```

should show `implementation_gate: satisfied` for medium-risk ticket-115.

## NO-GO triggers (none active)

- Would be NO-GO if strict allowlist without alias normalization broke GT07 — **mitigated** by normalization path.
- Would be NO-GO if requiring full metadata triple on every link — **not proposed**.
- Would be NO-GO if schema migration required — **it is not**.

## Recommendation

Proceed with ticket-115 on branch `phase-2/ticket-115-domain-pack-claim-schema-loader` using
the hardened scope above. After implementation, next smallest product move is wiring
`source_preferences.yaml` or applying `base_strength` priors — not another doc cross-link.
