# MVP-P1 Source Resolver — Evidence Report

**Date:** 2026-06-19  
**Branch:** `phase/mvp-p1-source-resolver`  
**Packet:** MVP-P1 — Source resolver foundation  
**Status:** implemented (mock/fixture proven)

## What changed

Added a unified source resolver layer that sits above existing OpenAlex discovery and returns explicit acquisition status before any LLM extraction.

| Area | Change |
|------|--------|
| `rge/modules/source_resolver/` | Status vocabulary, unified record schema, evidence summaries, multi-backend resolver |
| `rge/modules/source_providers/arxiv.py` | arXiv Atom metadata discovery provider |
| `rge/modules/source_providers/unpaywall.py` | DOI OA enrichment (non-fatal; preserves `metadata_only` when closed) |
| `rge/modules/source_providers/__init__.py` | Registers `arxiv` alongside `openalex` |
| `rge/config.py` | `UNPAYWALL_EMAIL` (falls back to `OPENALEX_MAILTO`) |
| `rge/cli.py` | New `resolve-sources` command |
| `fixtures/source_providers/` | Manual resolver fixtures, Unpaywall sample, arXiv Atom sample |
| `tests/unit/test_source_resolver.py` | 15 focused unit tests |
| `tests/golden/test_27_source_resolver.py` | 5 golden fixture-mode tests |
| `tests/golden/test_22_builder_golden_gate.py` | Documents new optional golden module |
| `.env.example` | Documents `UNPAYWALL_EMAIL` |

## Behavior delivered

- **OpenAlex:** existing `abstract_inverted_index` reconstruction preserved; mapped into unified records with `source_status`.
- **Unpaywall:** optional `--enrich-unpaywall` enriches DOI-backed records; missing OA does not fail the run.
- **arXiv:** first-class metadata + abstract + PDF URL via Atom API provider.
- **Manual fixtures:** `--fixture-mode` resolves deterministic records without network.
- **Evidence explanation:** each record gets `extraction_recommendation` (`abstract_quote_first`, `skip_llm_extraction`, etc.) before LLM work.
- **Status vocabulary:** `metadata_only`, `abstract_available`, `oa_pdf_available`, `oa_tei_available`, plus post-acquisition statuses reserved for fetch/parse pipeline.

## What already existed (not duplicated)

- OpenAlex discovery provider (`ticket-139`)
- OpenAlex URL candidate ordering (`ticket-233`)
- Quote validation / claim extraction spine (unchanged)
- `discover-sources` CLI (unchanged; resolver is additive)

## Verification run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_source_resolver.py tests/golden/test_27_source_resolver.py -q
# 20 passed

python -m pytest tests/golden/test_22_builder_golden_gate.py -q
# 5 passed (after documenting test_27)
```

**Not run in this session:** full `python -m rge.cli verify --skip-site` re-run after golden-gate fix (prior run failed only on undocumented golden inventory; safety audit passed).

**Not run:** live OpenAlex/Unpaywall/arXiv network proof (`RGE_ALLOW_SOURCE_NETWORK=1`) — operator opt-in per repo policy.

## Example command

```powershell
# Mock / no network
python -m rge.cli resolve-sources --fixture-mode

# Live (operator opt-in)
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m rge.cli resolve-sources --query "AI creativity diversity" --sources openalex,arxiv --enrich-unpaywall
```

## Remaining gaps (honest)

- Resolver output is **not yet wired** into staged ingest, fetch-candidate, or extract-claims.
- `oa_tei_available` status is modeled but OpenAlex TEI URL detection is not implemented yet.
- No persistence table for resolved records (JSON CLI output only).
- Live multi-backend resolver proof not executed in this packet.

## Recommended next packet

MVP-P2 — Abstract-first evidence cards (quote-first extraction from abstract text using resolver evidence summaries).
