# PDF / TEI Milestone

**Date:** 2026-06-20  
**Packet:** PDF / TEI Milestone  
**Cycle:** Operator loop cycle 3 — after web adapter / Scrapling proof  
**Verdict:** **GO**

## Fixture run summary (2026-06-20 — cycle 3)

| Signal | Result |
| --- | ---: |
| TEI fixture | `fixtures/source_documents/manual_oa_tei.xml` |
| TEI parser | `tei_xml` — clean_text_ready |
| TEI accepted / trace | 1 claim / 1 trace row |
| PDF fixture spine | 1 accepted claim (plain_text path) |
| Dirty PDF gate | **Blocked** pre-LLM |
| Local PDF byte parse | `pdf_unavailable` in this env |
| GROBID | Not enabled |

TEI is the primary proof path. PDF spine succeeds via fixture full-text acquisition; dirty PDF bytes blocked before extraction. Non-fatal pypdf stderr warnings on exit 0 (expected on minimal/dirty fixture bytes).

## Artifacts

- Public: `apps/public-site/public/data/atlas_pdf_tei_milestone_latest.json`
- Operator export: `data/exports/pdf_tei_milestone/`

## Operator command

```powershell
$env:RGE_ALLOW_PDF_TEI_MILESTONE = "1"
$env:RGE_LLM_MODE = "mock"
python scripts/run_pdf_tei_milestone.py --sync-public
```

## Verification

| Command | Status |
| --- | --- |
| Fixture operator run `--sync-public` | **PASS** (GO) |
| `pytest tests/unit/test_pdf_tei_milestone.py -q` | **PASS** (8 passed) |
| `python -m rge.modules.safety_auditor --audit full` | **PASS** |
| `cd apps/public-site && npm run build` | **PASS** |

## Next recommended packet

**Demo Loop Polish** (`demo-loop-polish`) — closes fixture spine before full-atlas refresh.

```powershell
$env:RGE_ALLOW_DEMO_LOOP_POLISH = "1"
$env:RGE_LLM_MODE = "mock"
python scripts/run_demo_loop_polish.py --persist-claims --sync-public
```
