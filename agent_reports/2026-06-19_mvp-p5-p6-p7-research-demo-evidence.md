# MVP-P5/P6/P7 Research Demo — Evidence Report

**Date:** 2026-06-19  
**Branch:** `phase/mvp-p5-p6-p7-research-demo`  
**Packets:** selective full-text (P5), PDF/TEI parser (P6), demo loop (P7)  
**Status:** implemented (mock/fixture proven)

## MVP-P5 — Selective full-text acquisition

| Deliverable | Location |
|-------------|----------|
| Acquisition policy + fixture manifest | `rge/modules/selective_fulltext.py`, `fixtures/source_documents/manifest.json` |
| TEI/PDF fixture documents | `fixtures/source_documents/*` |

Behavior:
- Prefers TEI → OA PDF → arXiv PDF location resolution
- Only requests full text when abstract evidence is thin (or `--mode full-text-augmented`)
- Explicit acquisition statuses (`full_text_not_needed`, `full_text_clean_text_ready`, `full_text_parse_failed`, …)
- Failures do not abort the research run

## MVP-P6 — PDF/TEI parser milestone

| Deliverable | Location |
|-------------|----------|
| Parser + quality gates | `rge/modules/document_parser.py` |
| Fetcher integration | `rge/modules/fetcher.py` (`artifact_bytes_to_text`) |
| Dependency | `pypdf>=4` in `pyproject.toml` |

Behavior:
- TEI/XML paragraph extraction (stdlib)
- PDF via `pypdf` — **never raw UTF-8 decode of `%PDF` bytes**
- Quality gates: readable char ratio, sentence count, quoteable spans
- Classifies `clean_text_ready` vs `dirty_text` vs `parse_failed`

## MVP-P7 — Single-command demo loop

| Deliverable | Location |
|-------------|----------|
| Orchestrator | `rge/modules/research_run.py` |
| CLI | `research-run` |

```powershell
python -m rge.cli research-run `
  --fixture-mode `
  --topic "AI assisted creativity and idea diversity" `
  --top-sources 5 `
  --full-text-top-n 3 `
  --out data/reports/research_runs
```

Output bundle includes:
- source status table
- ranked sources
- abstract evidence cards
- selective full-text acquisitions
- field-map report
- improvement packet recommendation

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_document_parser.py tests/unit/test_selective_fulltext.py tests/unit/test_research_run.py tests/golden/test_29_mvp_research_demo.py -q
python -m rge.cli verify --skip-site
# 920 pytest, 156 golden, safety audit PASS
```

## Remaining gaps

- Live network selective fetch not operator-proven in this session
- GROBID / PyMuPDF not integrated (pypdf only)
- Full-text quote extraction not wired to DB ingest spine
- `evaluate_fetch_artifact_quality` still uses byte-count heuristic for PDF pre-download checks
