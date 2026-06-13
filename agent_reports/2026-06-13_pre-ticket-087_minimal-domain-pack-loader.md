---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-087 Minimal Domain Pack Loader Audit

- Audit type: focused pre-ticket readiness (domain pack loading + concept linking)
- Date: 2026-06-13
- Scope: read-only design audit. No implementation in this report.
- Baseline HEAD: `1f0c967e` (main; ticket-086 landed)
- Prior checkpoint: `agent_reports/2026-06-13_principal-audit-post-ticket-085.md`
- Principal gate (`--next-ticket ticket-087`): **satisfied** (cadence + implementation gate not blocked)

## Executive verdict

**GO — seed ticket-087**

Ticket-086 proved manual ingestion. Before real claim extraction (ticket-088), concept
linking must resolve domain vocabulary from pack files, not hardcoded core logic. The
smallest safe step is a reusable loader for `ontology.yaml` + `aliases.yaml` and alias
→ canonical resolution in the concept linker persistence path.

## Repo state

| Check | Result |
| ----- | ------ |
| Branch | `main` at `1f0c967e` |
| Working tree | untracked probe artifact only |
| Golden (pre-impl) | 140 passed at ticket-086 tip |
| Safety audit | pass at ticket-086 tip |
| Manual ingest | unchanged; `src_fc40fea5f4169dd8` in private DB |

## What code reads today

| File | Read by code? | Mechanism |
| ---- | ------------- | --------- |
| `ontology.yaml` | **yes** | `_parse_ontology_concepts` regex parser in `concept_linker.py` |
| `aliases.yaml` | **no** | Declarative only |
| `domain.yaml` | **no** | Scaffold |
| `scoring.yaml`, `evidence_types.yaml`, etc. | **no** | Scaffold |

**Core hardcoding to remove:** `SUPPLEMENTAL_CREATIVITY_CONCEPTS` and
`if domain_pack != "creativity"` in `load_domain_pack_concepts`. Move
`brainstorming`, `ideation`, `creativity` into `domain_packs/creativity/ontology.yaml`
(candidate status) so GT05 labels remain available without core creativity logic.

## Parser strategy

| Option | Verdict |
| ------ | ------- |
| PyYAML | **Not required.** `pyproject.toml` has no PyYAML dep; adding one expands supply-chain surface for two small stub files. |
| Hand-rolled parser | **Recommended.** Existing ontology regex parser is proven in production paths; extend with a focused `aliases:` block parser matching current YAML layout. |
| Fail closed | Missing pack dir, missing `ontology.yaml`/`aliases.yaml`, empty ontology, or malformed `aliases:` → `DomainPackError` with clear message. |

## Alias wiring plan

1. `load_domain_pack(pack_id)` returns concepts + `canonical → [aliases]` map.
2. Build normalized `alias_phrase → canonical_label` reverse map at load time.
3. `resolve_concept_label(pack_id, label)` maps aliases before `ConceptRepository.get_by_label`.
4. Call normalization in `link_concepts_for_source` after model propose, before validate/persist.
5. `ontology_labels_for_pack` stays **canonical-only** (model prompt surface).
6. `link_rejection_diagnostic` expands allowed set to include alias phrases that map to ontology.

Example mapping (from `aliases.yaml`):

- `"AI-assisted brainstorming"` → `"AI assistance"`
- `"idea diversity"` → `"semantic diversity"`

## Golden preservation

GT05 uses mock fixture with canonical labels (`AI assistance`, `brainstorming`, etc.).
No golden change expected if supplemental concepts move to ontology.yaml and alias
resolution is additive (canonical labels pass through unchanged).

Tests to add: `tests/unit/test_domain_pack_loader.py`, `tests/unit/test_concept_link_aliases.py`.

## Avoid creativity hardcoding in core

- Loader is pack-id driven: `domain_packs/<pack_id>/`.
- No creativity-specific alias maps in `rge/modules/concept_linker.py`.
- Supplemental concepts belong in `domain_packs/creativity/ontology.yaml`, not Python tuples.
- `ontology_pressure.py` golden aliases remain fixture-test constants (out of scope).

## Out of scope

- scoring, evidence_types, claim_schema, search_templates loading
- source discovery, URL/PDF fetch
- OpenAI/cloud, live LLM extraction
- validator changes, schema migrations, export changes
- scratch → accepted graph promotion

## Rollback plan

Revert `domain_pack_loader.py`, concept_linker alias wiring, ontology.yaml additions,
and unit tests. `load_domain_pack_concepts` API restored from git. Golden GT05 must
pass before merge.

## GO / NO-GO

**GO for ticket-087** with hand-rolled parser, supplemental concepts moved to pack YAML,
and alias resolution in concept linker only.
