---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-117
---

# ticket-117: Domain Pack card_templates.yaml Loader Proof (NM-5 Continuation)

## Summary

Extended the domain pack loader to parse `card_templates.yaml` and expose
`CardTemplatesOverlay` on `DomainPack`. Public export validation now enforces
per-card-type `required_fields` from the pack (intersection with the public
allowlist only). `export_public_cards()` loads the creativity pack and passes
templates into `validate_public_export_bundle()`. GT11/GT12 unchanged.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-117 |
| Branch | `phase-2/ticket-117-domain-pack-card-templates-loader` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-117_domain-pack-card-templates-loader-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-116.md` |
| Main tip before branch | `0c7b55a` |

## Scope

### In

- `parse_card_templates_yaml()` + `CardTemplatesOverlay`
- `template_required_fields()` helper
- `validate_public_card()` / `validate_public_export_bundle()` optional template enforcement
- `export_public_cards()` loads pack templates with repo-root fallback for temp export tests
- Proof tests in `tests/unit/test_domain_pack_card_templates_loader.py`

### Out

- Pack fields outside `ALLOWED_PUBLIC_CARD_FIELDS` (e.g. `strongest_support`)
- Public site or committed JSON changes
- Other pack files, schema migrations, live Ollama

## Changed files

| File | Change |
|------|--------|
| `rge/modules/domain_pack_loader.py` | Parse card_templates; extend `DomainPack` |
| `rge/safety/public_export_policy.py` | Template-aware card validation |
| `rge/modules/card_exporter.py` | Load pack templates at export validation |
| `tests/unit/test_domain_pack_card_templates_loader.py` | New (7 tests) |
| `tests/unit/test_domain_pack_*.py` | card_templates stubs |
| `tickets/ticket-117.json` | status done |
| `tickets/ticket-118.json` | seeded next ticket |
| `tickets/TICKET_QUEUE.md` | ticket-117 done; ticket-118 proposed |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `card_templates.yaml` loaded for creativity at runtime | **PASS** |
| 2 | Consumer reads pack template metadata | **PASS** (export validation) |
| 3 | Temp-pack test proves template config changes validation | **PASS** |
| 4 | Golden GT11/GT12 and manual synthnote green | **PASS** |
| 5 | Safety audit passes | **PASS** |
| 6 | No public export/site changes beyond exporter metadata read | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_domain_pack_card_templates_loader.py -q   # 7 passed
python -m pytest tests/unit/test_domain_pack_source_preferences_loader.py -q   # 7 passed
python -m pytest tests/golden/test_11_public_card_export.py -q               # 4 passed
python -m pytest tests/golden -q                                            # 140 passed
python -m pytest -q                                                         # 432 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                           # pass
```

## Manual CLI verification

Not required — export path covered by GT11 golden tests.

## Spec deviations

None. Cluster pack fields outside the public allowlist are not enforced at export.

## Merge to main

Merged to `main` at `9c2a723` and pushed to `origin/main`.

## Recommended next ticket

**ticket-118** — Domain pack `search_templates.yaml` loader proof (NM-5 continuation).

## Suggested next prompt

```
/rge-principal-audit
```

Then pre-ticket audit + `/rge-run-next-ticket` for ticket-118.
