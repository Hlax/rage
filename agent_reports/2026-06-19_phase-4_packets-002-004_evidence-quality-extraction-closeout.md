# Packets 002–004 Closeout: Atom Promotion, Quality Gates, Quote-First Extraction

Date: 2026-06-19
Branch: `phase-4/packets-002-004-evidence-quality-extraction`
Decision: GO (mock verification PASS; live Ollama shape proof PASS)

## Outcome

Implemented the next three packets from
`agent_reports/rge_next_features_data_quality_evidence_atoms.md`:

1. **Packet 2 — Evidence atom promotion + cluster integration**
2. **Packet 3 — Source acquisition/text quality gates before extraction**
3. **Packet 4 — Quote-first extraction hardening**

Also switched the default local model to `qwen3.5:9b-q4_K_M` and proved live
structured claim extraction shape with Ollama (not mock wiring).

## Packet 2 — Evidence Atom Promotion + Cluster Integration

Delivered:

- `promote_accepted_claims_for_domain()` and `promote_cluster_evidence_atoms()`
  in `rge/modules/evidence_atoms.py` with idempotent merge on same `atom_id`.
- `atom_maturity_for_stance()` for deterministic maturity assignment.
- Cluster reporter auto-promotes atoms before building evidence packets
  (`top_evidence_atoms` populated in cluster reports).
- CLI command `promote-evidence-atoms` for operator batch promotion.
- Golden cluster report tests assert non-empty `top_evidence_atoms` with `atom_` IDs.

## Packet 3 — Source Acquisition / Text Quality Gates

Delivered:

- `rge/modules/text_quality_gate.py`:
  - `discover_quoteable_spans()`
  - `assess_chunk_extractability()`
  - `gate_source_for_extraction()` — blocks `dirty_text`, `parse_failed`,
    `download_failed`, and sources with zero extractable chunks.
- `extract_claims_for_source()` applies source-level gate for non-mock,
  non-live-fallthrough paths; returns `blocked_by_quality_gate`.
- Unit tests in `tests/unit/test_text_quality_gate.py`.

## Packet 4 — Quote-First Extraction Hardening

Delivered:

- Pre-LLM quoteability gate in `extract_and_validate_for_chunk()` returning
  `zero_quoteable_spans` when no quoteable spans exist (live / unknown chunks).
- Pinned mock fixture profiles bypass gate (creativity diversity, staged rank-1/2,
  manual checksum map, prompt-injection fixture).
- Live fallthrough paths bypass source-level and chunk-level gates (operator opt-in).
- `quoteable_span_hints` passed into Ollama claim-extraction prompt.
- Scope entailment validation in `claim_validator.py`:
  - scope supported by quote, sentence context, preamble, or grounded claim text
    that also appears in chunk.
- `REJECTION_ZERO_QUOTEABLE = "zero_quoteable_spans"` rejection reason.
- Unit tests in `tests/unit/test_quote_first_extraction.py`.

## Model Runtime — Qwen 3.5 Q4_K_M Live Shape Proof

Changed defaults:

- `rge/config.py` → `RGE_LOCAL_LLM=qwen3.5:9b-q4_K_M`
- `.env.example` updated with quantized model example.

Ollama compatibility fix:

- `rge/llm/ollama_client.py` sets `"think": false` on `/api/generate` so Qwen 3.5
  returns JSON in `response` instead of empty `response` + `thinking` channel.

Live proof (operator machine, local Ollama):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_TIMEOUT_SECONDS = "180"
python -m rge.cli model-health
python -m rge.cli probe-extract-claims
python -m pytest tests/smoke/test_live_ollama_smoke.py::test_live_probe_extract_claims_on_fixture_chunk -m live_smoke -q
```

Results:

- `model-health`: PASS — `qwen3.5:9b-q4_K_M` available.
- `probe-extract-claims`: PASS — 2 accepted, 0 rejected, valid
  `claim_extraction` batch shape, report at
  `data/reports/live_probes/probe_extract_claims_2026-06-19T213919Z.json`.
- Live smoke extract test: PASS (~15s).

## GO / PARTIAL / NO-GO

**GO** for packets 002–004 scope with honest live-runtime caveat:

- Mock/fixture verification: PASS (full suite).
- Live claim-extraction shape: PASS on operator Ollama with Qwen 3.5 Q4_K_M.
- Live link/build/detect mini-run: **not re-run in this closeout** (prior smoke
  suite exists; only extract step re-verified after model switch).

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
```

- Golden tests: **157 passed**
- Full pytest: **942 passed**, 35 deselected
- Safety audit: **pass**

New/updated tests:

- `tests/unit/test_text_quality_gate.py`
- `tests/unit/test_quote_first_extraction.py`
- `tests/unit/test_evidence_atoms.py` (domain promotion idempotency)
- `tests/golden/test_13_cluster_report.py` (top evidence atoms)
- `tests/golden/test_00_scaffold.py` (`promote-evidence-atoms` CLI)

## Honest Weakness Notes

- Atom merge is basic (same `atom_id` only); no semantic collapse across claims.
- Quality gate is conservative; live fallthrough and pinned mock profiles bypass it
  by design.
- Scope entailment allows preamble/chunk grounding for fixture compatibility; live
  models may still propose scopes not fully entailed — Python validator remains the
  write gate.
- Qwen 3.5 requires `think: false` for structured JSON via Ollama generate API.
- Default 60s timeout may be tight for larger live prompts; probe used 180s env override.

## Suggested Next Packet

Packet 5 from the feature roadmap: **abstract/PDF quote-first adapters** with
selective fulltext promotion — wire `text_quality_gate` + quote-first extraction
into abstract and PDF ingest paths with operator-private evidence atom cards.
