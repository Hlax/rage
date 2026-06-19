# MVP-P5/P6/P7 Research Demo — Packet Closeout

**Date:** 2026-06-19  
**Branch:** `phase/mvp-p5-p6-p7-research-demo`  
**Verdict:** **GO** (mock/fixture scope)

## Checklist

| Packet | Verdict |
|--------|---------|
| P5 selective full-text | **GO** — fixture TEI/PDF paths, thin-abstract policy, non-fatal failures |
| P6 PDF/TEI parser | **GO** — no raw PDF UTF-8 decode; quality gates; pypdf integration |
| P7 demo loop | **GO** — `research-run --fixture-mode` produces full bundle |
| Full verify | **PASS** — 920 pytest, 156 golden, safety audit |

## MVP product loop status

One fixture-mode command now delivers the north-star loop at mock maturity:

```text
resolve → rank → abstract evidence → selective full text → field report → improvement packet
```

## Honest limits

- Not merged into staged orchestrator / SQLite ingest spine
- No live OpenAlex field-map + selective fetch operator proof
- PDF parser is pypdf-only; dirty publisher PDFs may still need GROBID/PyMuPDF tier
- Public export unchanged

## Next work (post-MVP packets)

1. Wire `research-run` outputs into DB ingest + extract-claims spine  
2. Operator live proof: resolve → selective fetch → parse → extract on temp DB  
3. Upgrade PDF tier (PyMuPDF/GROBID) when pypdf quality gates fail on real corpus samples
