---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-117
---

# Pre-Ticket Audit: ticket-117 Domain Pack card_templates.yaml Loader Proof

## Verdict: **GO** (hardened scope)

Ticket-116 proved `source_preferences.yaml` drives research-queue credibility priors. The
creativity pack's `card_templates.yaml` defines per-card-type `required_fields` but is
**not loaded at runtime**. Export validation today uses a single global
`REQUIRED_PUBLIC_CARD_FIELDS` tuple in `public_export_policy.py` and duplicate constants
in GT11. Wiring pack templates into export validation is bounded, touches the public
export boundary (medium risk), and must **not** require fields outside the public allowlist
or change committed site JSON.

## Current state

### Domain pack loader (`rge/modules/domain_pack_loader.py`)

| Loaded today | Not loaded |
|--------------|------------|
| `ontology.yaml` | `card_templates.yaml` |
| `aliases.yaml` | `search_templates.yaml`, `safety_notes.yaml`, `domain.yaml` |
| `scoring.yaml` | |
| `evidence_types.yaml` | |
| `claim_schema.yaml` | |
| `source_preferences.yaml` | |

`DomainPack` fields: concepts, aliases, alias_to_canonical, score_reconciliation,
evidence_types, claim_schema, source_preferences.

### Creativity `card_templates.yaml` (committed)

| Card type | Pack `required_fields` |
| --------- | ---------------------- |
| `claim_card` | title, summary, confidence, concepts, source_count, public_caveats |
| `cluster_card` | title, summary, confidence, concepts, source_count, strongest_support, strongest_qualification, open_gaps |
| `theory_card` | title, summary, confidence, supporting_claim_count, weakening_evidence, boundary_conditions, status |

Matches `docs/agents/06_DOMAIN_PACK_SPEC.md` section 12.

### Public export policy (`rge/safety/public_export_policy.py`)

Global `REQUIRED_PUBLIC_CARD_FIELDS`:

```txt
id, type, title, summary, confidence, concepts, source_count, public_detail_level, updated_at
```

`ALLOWED_PUBLIC_CARD_FIELDS` (14 keys) — **does not include** cluster-only pack fields
(`strongest_support`, `strongest_qualification`, `open_gaps`) or theory-only fields.

`validate_public_card()` applies global required list only; no per-type template logic.

### Card exporter (`rge/modules/card_exporter.py`)

- Golden seeded cards use `card_type: cluster_card`.
- `EXPORT_CARD_FIELD_ORDER` and `GOLDEN_CARD_EXTRAS` supply `public_caveats` for golden IDs.
- `export_public_cards()` calls `curated_public_card()` then `validate_public_export_bundle()`.
- No domain pack load today; no `domain` parameter on export path.

### Golden Test 11 (`tests/golden/test_11_public_card_export.py`)

- `REQUIRED_CARD_FIELDS` mirrors global policy (9 fields).
- `ALLOWED_CARD_FIELDS` mirrors allowlist (14 fields).
- Asserts ≥2 cards, no forbidden keys/values, fail-closed on unsafe card.
- **Does not** assert cluster-specific pack fields.

### Golden Test 12 (public site)

Consumes committed `apps/public-site/public/data/public_cards.json` — ticket non-goal:
no site routing or committed JSON changes. Export output shape must remain GT11/GT12 compatible.

## Risk analysis

| Risk | Mitigation |
| ---- | ---------- |
| Requiring pack fields outside allowlist breaks export | Only enforce intersection of pack `required_fields` ∩ `ALLOWED_PUBLIC_CARD_FIELDS` |
| Cluster pack requires non-exportable fields | Skip or ignore pack-only keys not in allowlist for validation |
| Changing golden fixture JSON | Non-goal; golden cards already include `public_caveats` via extras |
| Public site committed JSON drift | No `--publish` or site file edits in ticket |
| Model writes to DB | No model use in exporter; Python validates only |

## Hardened scope for ticket-117

### In

1. Add `CardTemplatesOverlay` frozen dataclass + `parse_card_templates_yaml()` in
   `domain_pack_loader.py` (parse `cards:` map → card_type → `required_fields` tuple).
2. Extend `DomainPack` with `card_templates: CardTemplatesOverlay`.
3. `load_domain_pack()` loads `card_templates.yaml`; fail closed if `cards` missing or empty.
4. Helper `template_required_fields(pack, card_type) -> tuple[str, ...]` returning normalized
   field names for a card type (empty tuple if type unknown).
5. **Consumer:** extend `validate_public_card()` (or a thin wrapper used by exporter) to
   accept optional `card_templates` overlay and, when `card["type"]` is known:
   - Compute `enforce = template_fields ∩ ALLOWED_PUBLIC_CARD_FIELDS`
   - Append violations for missing `enforce` fields
   - **Do not** require fields in pack template that are not in the allowlist
6. **Exporter wiring:** `export_public_cards()` loads creativity pack (or resolves domain from
   caller) and passes overlay into bundle validation. Prefer `load_domain_pack("creativity")`
   for fixture/MVP path; optional `domain_pack` parameter if repo pattern supports it.
7. Unit tests `tests/unit/test_domain_pack_card_templates_loader.py`:
   - Parse creativity pack; assert three card types and field lists
   - Temp-pack monkeypatch: add `public_caveats` to `cluster_card` required_fields → validation
     fails when card lacks `public_caveats`; passes when present
   - Temp-pack: remove `title` from `claim_card` in temp pack does not break cluster export
     (type-specific enforcement)
8. Update temp-pack stubs in prior `test_domain_pack_*.py` files with minimal
   `card_templates.yaml` (three card types matching creativity shape).

### Out (non-goals — enforce)

- No `search_templates.yaml`, `safety_notes.yaml`, or `domain.yaml` loading.
- No public site file or routing changes.
- No schema migrations or new DB columns for cluster/theory-only fields.
- No changing `ALLOWED_PUBLIC_CARD_FIELDS` surface for this ticket.
- No live Ollama or cloud changes.

### GT11 / GT12 safety

| Field | Global required | Pack cluster required | In allowlist | Safe to enforce |
| ----- | --------------- | --------------------- | ------------ | --------------- |
| title | yes | yes | yes | yes |
| summary | yes | yes | yes | yes |
| confidence | yes | yes | yes | yes |
| concepts | yes | yes | yes | yes |
| source_count | yes | yes | yes | yes |
| public_caveats | no | no (cluster) | yes | optional via claim_card only |
| strongest_support | no | yes | **no** | **must not enforce** |
| public_detail_level | yes | no | yes | keep global required |

Golden cluster cards receive `public_caveats` via `GOLDEN_CARD_EXTRAS` — GT11-safe.

## Test plan (ticket-aligned)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_domain_pack_card_templates_loader.py -q
python -m pytest tests/unit/test_domain_pack_source_preferences_loader.py -q
python -m pytest tests/golden/test_11_public_card_export.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Rollback

Revert `card_templates` loader and exporter validation wiring; restore global-only
`REQUIRED_PUBLIC_CARD_FIELDS` validation path.

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-117 per hardened scope | **GO** |
| Principal cadence | Satisfied (post-ticket-116 checkpoint + this pre-ticket report resets window) |

## Suggested implementation prompt

```
/rge-run-next-ticket
```

Pre-ticket audit: `agent_reports/2026-06-14_pre-ticket-117_domain-pack-card-templates-loader-audit.md`
Principal checkpoint: `agent_reports/2026-06-14_principal-audit-post-ticket-116.md`
