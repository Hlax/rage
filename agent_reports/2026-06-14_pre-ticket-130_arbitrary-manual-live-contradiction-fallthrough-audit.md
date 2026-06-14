---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-130
category: product-risk reduction / NM-4 pipeline continuation
---

# Pre-Ticket Audit: ticket-130 Arbitrary Manual Live Contradiction Fall-Through

## Verdict: **GO**

ticket-129 proved live relationship drafting for arbitrary `manual_text`. ticket-130
extends NM-4 with live contradiction detection using the same explicit opt-in gates.
Mock must fail-closed for unmapped manual sources (no silent diversity fixture).

## Principal audit cadence

Post-ticket-127 principal audit (`agent_reports/2026-06-14_principal-audit-post-ticket-127.md`).
Two consecutive done tickets since (128, 129) — **cadence satisfied** for ticket-130;
principal audit due after ticket-130 completes (before ticket-131).

## Current contradiction fixture path

| Location | Role |
|----------|------|
| `fixtures/manual_source_fixture_map.json` | Checksum → `detect_contradictions` fixture + optional `contradiction_claim_hints` |
| `rge/modules/manual_source_fixtures.py` | `contradiction_fixture_for_manual_source()` |
| `rge/modules/contradiction_detector.py` | Mock path falls back to `contradiction_detection_creativity_diversity.json` when no map entry (**bug — same class as tickets 112/128/129**) |

## Live write boundary (tickets 127–129)

| Location | Role |
|----------|------|
| `rge/modules/live_extraction_write.py` | Evidence DB default, shared checksum helpers |
| `rge/modules/live_probe.py` | `assert_live_probe_env`, `assert_ollama_health` |
| `rge/modules/relationship_builder.py` | `build_relationships_manual_live_fallthrough()` |
| Evidence DB | `data/db/live_research_evidence.sqlite` (gitignored) |

Contradictions persist via `RelationshipEvidenceRepository.insert` with
`stance=qualifies` and `RelationshipRepository.merge_domain_metadata` after
`validate_contradiction_candidates`. Empty validated batch yields
`status: no_qualifications` (explicit no-contradiction result).

## Command path

```
# After ticket-127 extract + ticket-128 link + ticket-129 build-relationships:

detect-contradictions --source <source_id> --db data/db/live_research_evidence.sqlite --live-manual-contradiction-fallthrough
  (requires RGE_LLM_MODE=ollama, RGE_ALLOW_LIVE_LLM=1)
```

Prerequisite: accepted claims and active domain relationships must exist.
Live proof may legitimately return `no_qualifications` when the graph lacks a
qualifying base/new relationship pair (e.g. single live-drafted edge).

## Mock/golden determinism

- Synthnote checksum-pinned path unchanged (`contradiction_detection_manual_synthnote.json`).
- Unknown `manual_text` in mock without map: **explicit error** (new fail-closed).
- Golden tests stay mock-only.

## Live mode gating (all required)

1. `RGE_LLM_MODE=ollama`
2. `RGE_ALLOW_LIVE_LLM=1`
3. `--live-manual-contradiction-fallthrough` on `detect-contradictions`
4. Explicit gitignored `--db`
5. `assert_ollama_health()` before inference
6. Source absent from fixture map `detect_contradictions` entry

## Ollama calibration

Extend `_contradiction_detection_prompt` with optional `manual_text_arbitrary_live`
block: base/new triples must match active relationship triples exactly; return
empty `items` when no valid qualification pair exists; use claim ids from input
when proposing links.

## Tests to add

| Test | Purpose |
|------|---------|
| Mock fail-closed for unknown manual_text contradictions | Regression |
| Live flag gate tests | Opt-in + DB guard |
| Stub Ollama completes with `no_qualifications` or qualification | Persistence path |
| Synthnote mock spine through detect-contradictions | Determinism |

## Expected file changes

| File | Change |
|------|--------|
| `rge/modules/manual_source_fixtures.py` | `manual_text_lacks_contradiction_fixture()` |
| `rge/modules/contradiction_detector.py` | Fail-closed mock; live fall-through |
| `rge/llm/ollama_client.py` | Manual arbitrary contradiction prompt calibration |
| `rge/cli.py` | `--live-manual-contradiction-fallthrough` |
| `tests/unit/test_manual_live_fallthrough.py` | Contradiction fall-through tests |

## Out of scope

Score reconciliation live fall-through, validator weakening, public export/site,
cloud, source discovery, docs chain.

## Recommendation

| Action | Verdict |
|--------|---------|
| Implement ticket-130 | **GO** |

## Next command

```text
/rge-run-next-ticket
```
