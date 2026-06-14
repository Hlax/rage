---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-129
category: product-risk reduction / NM-4 pipeline continuation
---

# Pre-Ticket Audit: ticket-129 Arbitrary Manual Live Relationship Fall-Through

## Verdict: **GO**

ticket-128 proved live concept linking for arbitrary `manual_text`. ticket-129
extends NM-4 with live relationship drafting using the same explicit opt-in gates.
Mock must fail-closed for unmapped manual sources (no silent diversity fixture).

## Current relationship fixture path

| Location | Role |
|----------|------|
| `fixtures/manual_source_fixture_map.json` | Checksum → `build_relationships` fixture filename |
| `rge/modules/manual_source_fixtures.py` | `relationship_fixture_for_manual_source()` |
| `rge/modules/relationship_builder.py` | Mock path falls back to `relationship_drafting_creativity_diversity.json` when no map entry (**bug — same class as tickets 112/128**) |

## Live write boundary (tickets 127–128)

| Location | Role |
|----------|------|
| `rge/modules/live_extraction_write.py` | Evidence DB default, shared checksum helpers |
| `rge/modules/live_probe.py` | `assert_live_probe_env`, `assert_ollama_health` |
| `rge/modules/concept_linker.py` | `link_concepts_manual_live_fallthrough()` |
| Evidence DB | `data/db/live_research_evidence.sqlite` (gitignored) |

Relationships persist via `RelationshipRepository.insert` + `RelationshipEvidenceRepository.insert` after `validate_relationship_candidates`.

## Command path

```
# After ticket-127 extract + ticket-128 link on arbitrary source:

build-relationships --source <source_id> --db data/db/live_research_evidence.sqlite --live-manual-relationship-fallthrough
  (requires RGE_LLM_MODE=ollama, RGE_ALLOW_LIVE_LLM=1)
```

Prerequisite: accepted claims and concept links must exist for the source.

## Mock/golden determinism

- Synthnote checksum-pinned path unchanged (`relationship_drafting_manual_synthnote.json`).
- Unknown `manual_text` in mock without map: **explicit error** (new fail-closed).
- Golden tests stay mock-only.

## Live mode gating (all required)

1. `RGE_LLM_MODE=ollama`
2. `RGE_ALLOW_LIVE_LLM=1`
3. `--live-manual-relationship-fallthrough` on `build-relationships`
4. Explicit gitignored `--db`
5. `assert_ollama_health()` before inference
6. Source absent from fixture map `build_relationships` entry

## Ollama calibration

Extend `_relationship_drafting_prompt` with optional `manual_text_arbitrary_live`
block: use linked concept labels exactly (e.g. `AI assistance`, `originality`),
claim scope in relationship scope, valid `supporting_claim_ids`.

## Tests to add

| Test | Purpose |
|------|---------|
| Mock fail-closed for unknown manual_text relationships | Regression |
| Live flag gate tests | Opt-in + DB guard |
| Stub Ollama persists ≥1 active relationship | Persistence path |
| Synthnote mock spine through build-relationships | Determinism |

## Expected file changes

| File | Change |
|------|--------|
| `rge/modules/manual_source_fixtures.py` | `manual_text_lacks_relationship_fixture()` |
| `rge/modules/relationship_builder.py` | Fail-closed mock; live fall-through |
| `rge/llm/ollama_client.py` | Manual arbitrary relationship prompt calibration |
| `rge/cli.py` | `--live-manual-relationship-fallthrough` |
| `tests/unit/test_manual_live_fallthrough.py` | Relationship fall-through tests |

## Out of scope

Contradiction live fall-through, validator weakening, public export/site, cloud,
source discovery, docs chain.

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-129 | **GO** |

## Next command

```text
/rge-run-next-ticket
```
