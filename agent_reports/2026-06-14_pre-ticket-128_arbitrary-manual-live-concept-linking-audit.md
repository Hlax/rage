---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-128
category: product-risk reduction / NM-4 pipeline continuation
---

# Pre-Ticket Audit: ticket-128 Arbitrary Manual Live Concept Linking

## Verdict: **GO**

ticket-127 proved live claim extraction for arbitrary `manual_text`. ticket-128
extends NM-4 with live concept linking using the same explicit opt-in gates.
Mock must fail-closed for unmapped manual sources (no silent diversity fixture).

## Current link fixture path

| Location | Role |
|----------|------|
| `fixtures/manual_source_fixture_map.json` | Checksum → `link_concepts` fixture filename |
| `rge/modules/manual_source_fixtures.py` | `link_fixture_for_manual_source()` |
| `rge/modules/concept_linker.py` | Mock path falls back to `concept_linking_creativity_diversity.json` when no map entry (**bug — same class as pre-ticket-112 extract**) |

## NM-1 / ticket-127 live write boundary

| Location | Role |
|----------|------|
| `rge/modules/live_extraction_write.py` | Evidence DB default, checksum guards, live env gates |
| `rge/modules/live_probe.py` | `assert_live_probe_env`, `assert_ollama_health` |
| Evidence DB | `data/db/live_research_evidence.sqlite` (gitignored) |

Concept links persist via `ClaimConceptRepository.insert` after `validate_concept_links`.

## Command path

```
# After ticket-127 extract on arbitrary source (or fresh ingest + extract --live-manual-fallthrough)

link-concepts --source <source_id> --db data/db/live_research_evidence.sqlite --live-manual-link-fallthrough
  (requires RGE_LLM_MODE=ollama, RGE_ALLOW_LIVE_LLM=1)
```

## Mock/golden determinism

- Synthnote checksum-pinned paths unchanged (`concept_linking_manual_synthnote.json`).
- Unknown `manual_text` in mock without map: **explicit error** (new fail-closed).
- Golden tests stay mock-only; no live flag in golden spine.

## Live mode gating (all required)

1. `RGE_LLM_MODE=ollama`
2. `RGE_ALLOW_LIVE_LLM=1`
3. `--live-manual-link-fallthrough` on `link-concepts`
4. Explicit gitignored `--db` (not default graph DB)
5. `assert_ollama_health()` before inference
6. Source absent from fixture map `link_concepts` entry

## Avoid silent wrong mock content

Replace generic diversity fixture fallback for unmapped `manual_text` with
`ValueError` in mock mode. Live + flag runs Ollama `link_concepts`.

## Prove source absent from fixture map

Reuse `resolve_manual_source_fixture(checksum, "link_concepts") is None` and
include checksum in CLI JSON output.

## Ollama calibration

Extend `_concept_linking_prompt` with optional `manual_text_arbitrary_live`
calibration block (workshop/songwriting claim shape from ticket-127 source).
Validator unchanged: batch needs ≥2 distinct specific ontology labels.

## Tests to add

| Test | Purpose |
|------|---------|
| Mock fail-closed for unknown manual_text link | Regression |
| Live flag blocked without opt-in / default DB | Gate regression |
| Stub Ollama client persists ≥1 accepted link | Persistence path |
| Synthnote mock spine unchanged | Determinism |

## Expected file changes

| File | Change |
|------|--------|
| `rge/modules/manual_source_fixtures.py` | `manual_text_lacks_link_fixture()` |
| `rge/modules/concept_linker.py` | Fail-closed mock; live fall-through orchestration |
| `rge/llm/ollama_client.py` | Manual arbitrary link prompt calibration |
| `rge/cli.py` | `--live-manual-link-fallthrough` |
| `tests/unit/test_manual_live_fallthrough.py` | Link fall-through tests |

## Out of scope

Relationship/contradiction live fall-through, validator weakening, public
export/site, cloud, source discovery, docs chain.

## Ollama environment

Assumed available from ticket-127 proof (`qwen2.5:7b`, model-health ok). Live
proof in ticket report only; CI stays mock-only.

## Hardened scope

### In

1. `--live-manual-link-fallthrough` on `link-concepts`.
2. Mock fail-closed for unmapped `manual_text`.
3. Live Ollama link + validate + persist ≥1 accepted link in evidence DB.
4. Unit tests with stub client; golden unchanged.

### Out

- Relationship/contradiction fall-through
- New modules beyond concept_linker/cli unless minimal shared import from live_extraction_write

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-128 | **GO** |
| Broaden scope | **NO-GO** |

## Next command

```text
/rge-run-next-ticket
```
