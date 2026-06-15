---
template_id: operator_audit_brief
status: current
date: 2026-06-15
source: terminal/33.txt (operator live_network session)
audience: parallel audit / improvement agent
---

# Operator Live Staged Fetch Failure — Parallel Audit Brief

## Executive summary

**Operator live_network session: discover succeeded; fetch failed with HTTP 403 Forbidden on rank-1 candidate. Report spine test failed (`assert 1 == 0` on `fetch-candidate`). This is an environment/catalog fragility finding, not a mock CI regression.**

| Stage | Observed | Assessment |
|-------|----------|------------|
| `discover-sources` (OpenAlex) | **PASS** — 10 candidates enqueued | Live network + mailto working |
| `fetch-candidate` (rank-1) | **FAIL** — `fetch_failed` / `Forbidden` | Publisher paywall / bot block |
| Downstream spine (ingest → report) | **Not reached** | Blocked at fetch |
| Default `pytest` / golden | **Unaffected** | `live_network` excluded from CI |

**Verdict for operator proof:** **NO-GO for full rank-1 reconcile/report spine on this run** — failure is upstream of deterministic reconcile/report (expected product behavior when fetch fails).

---

## Evidence from terminal log

**Commands run (metadata):**

```powershell
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
python -m pytest tests/unit/test_live_staged_report_mock_spine.py -m live_network -q
```

**Exit code:** `1` (failure on report test; reconcile output not captured in terminal buffer — assume same fetch gate if rank-1 path identical).

**Discover output (truncated tail shows success):**

- `research_question_id`: `rq_live_staged_report_mock_spine`
- `enqueue_status`: `completed`
- `queue_count`: 10
- Real OpenAlex works returned (not fixture sample); top results include AMJ 2023 AI creativity paper, Boden, etc.

**Fetch failure (machine-readable CLI JSON):**

```json
{
  "status": "error",
  "command": "fetch-candidate",
  "reason": "fetch_failed",
  "candidate_id": "disc_openalex_W4394863715",
  "detail": "URL fetch failed: Forbidden"
}
```

**Pytest summary:**

```text
FAILED test_live_openalex_discover_through_report_mock_spine - AssertionError: assert 1 == 0
1 failed, 1 deselected in 1.36s
```

Failure line in test: `fetch-candidate` expected exit `0`, got `1`.

---

## Root-cause analysis

### 1. Dynamic live catalog vs fixture-stable proofs

Live discover uses **real OpenAlex** for query `"human AI creativity"`. Rank-1 candidate at run time was `disc_openalex_W4394863715` (not the checksum-pinned fixture works W2741809807 / W1234567890 used in patched unit tests).

Mock CI proofs patch provider I/O; **operator live proofs depend on whatever OpenAlex ranks #1 today** — titles, URLs, and paywall status drift.

### 2. URL selection prefers landing page over open access

```331:331:rge/modules/research_queue.py
        url = item.get("landing_page_url") or item.get("open_access_url")
```

Enqueue stores **landing_page_url first**. Logged candidates often have `open_access_url: null` and DOI/publisher `landing_page_url`. Publisher sites (e.g. AMJ, Elsevier, Springer) frequently return **403 Forbidden** to bare `urllib` requests without browser cookies or institutional access.

### 3. Fetch client is minimal

```56:64:rge/modules/fetcher.py
def fetch_url_bytes(...):
    request = urllib.request.Request(url, headers={"Accept": "*/*"})
```

No `User-Agent`, no `OPENALEX_MAILTO` on publisher fetch, no retry/fallback to `open_access_url` when landing page fails.

### 4. Test design assumes fetch always succeeds for rank-1

`test_live_staged_report_mock_spine.py` and `test_live_staged_reconcile_mock_spine.py` call `select_rank1_candidate_id` then `fetch-candidate` with hard `assert ... == 0`. No skip/fallback when fetch fails due to external paywall.

---

## What this does **not** indicate

| Not a failure of | Why |
|------------------|-----|
| Deterministic reconcile/report | Never reached |
| Mock golden / CI | Live tests deselected |
| OpenAlex discover API | Returned 10 candidates |
| Env gates | Test ran (not skipped) — gates were set |
| Rank-2 / live Ollama work | Separate milestone |

---

## Parallel audit agent — recommended improvement tickets

### Priority A — Product hardening (medium)

| ID (proposed) | Title | Scope |
|---------------|-------|-------|
| **233** | Staged fetch URL fallback and fail-closed errors | Prefer `open_access_url` when present; on landing 403/401 try OA URL; structured `reason: paywall_blocked` |
| **234** | Fetch User-Agent / polite headers | Add identifiable UA + optional mailto comment on publisher fetch (mirror OpenAlex polite pool) |

### Priority B — Operator proof resilience (low–medium)

| ID (proposed) | Title | Scope |
|---------------|-------|-------|
| **235** | Live staged pytest fetch fallback helper | If rank-1 fetch fails with `fetch_failed`, try rank-2..N with OA URL or skip with explicit `pytest.skip` reason (operator-only) |
| **236** | README operator runbook: live fetch 403 troubleshooting | Document paywall behavior, query pinning, `OPENALEX_API_KEY`, retry on different network |

### Priority C — Audit / observability (low)

| ID (proposed) | Title | Scope |
|---------------|-------|-------|
| **237** | Operator live proof session log template | Standard fields: candidate_id, url attempted, HTTP status, OA vs landing, discover query |

---

## Hardened scope for audit agent (read-only pass)

1. **Confirm** `research_queue.py` URL precedence and document in audit report.
2. **Inventory** live_network tests that hard-require `fetch-candidate == 0` without fallback.
3. **Compare** fixture OpenAlex sample URLs vs live W4394863715 URL fields (operator may re-run discover + SQL inspect).
4. **Assess** whether rank-1 live Ollama proofs (204–217) have same fetch dependency — **yes**, same spine.
5. **Recommend** smallest ticket: **233** (URL fallback) before re-running operator proofs.

---

## Operator retry checklist (immediate, no code)

1. Confirm env: `RGE_ALLOW_SOURCE_NETWORK=1`, `RGE_ALLOW_LIVE_STAGED_REPORT=1` (or `_RECONCILE`), `OPENALEX_MAILTO` set, `RGE_LLM_MODE=mock`.
2. Inspect rank-1 candidate URL in temp DB after discover:
   - `SELECT id, title, url FROM candidate_sources ORDER BY priority_score DESC LIMIT 3`
3. Retry with a query biased toward **open access** works (e.g. include `open_access.is_oa:true` if discover supports filter — audit whether CLI exposes this).
4. Retry from network without corporate proxy / VPN blocking publisher domains.
5. If fetch keeps failing: **expected** until ticket-233; do not treat as reconcile/report regression.

---

## Suggested prompt for parallel audit agent

```text
/rge-principal-audit scoped to operator live staged fetch failures

Read: agent_reports/2026-06-15_operator-live-staged-fetch-403-parallel-audit-brief.md
Audit: rge/modules/research_queue.py URL selection, rge/modules/fetcher.py fetch_url_bytes,
        all tests/unit/test_live_staged_*_mock_spine.py fetch assertions.
Deliver: pre-ticket audit for proposed ticket-233 (URL fallback) with GO/NO-GO and hardened scope.
Do not implement ticket-233 in the audit pass.
```

---

## Assessment for the operator

**You successfully exercised live OpenAlex discover** — that part of the staged spine is working on your machine. The run failed at **publisher fetch**, which is a known fragile boundary for real-world research ingestion (paywalls, bot detection). The engine behaved correctly by returning structured `fetch_failed` JSON rather than silently continuing.

**Re-run after URL-fallback hardening (ticket-233)** or manually verify rank-1 candidate has a fetchable `open_access_url` before expecting reconcile/report live proofs to pass.
