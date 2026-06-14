---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-140
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-140 Research Queue Candidate Ranking from Discovered Sources

## Verdict: **GO**

ticket-139 delivers OpenAlex candidate metadata JSON only. ticket-140 may add **deterministic
ranking overlays** using domain-pack `source_preferences.yaml` and the existing queue-priority
formula — **JSON-first via `--rank-only`**, with optional staging enqueue behind an explicit
flag. No fetch, ingest, claim extraction, schema migrations, or accepted-table writes.

## Principal / cadence gate

| Field | Value |
|-------|-------|
| Main tip verified | `80cb883` (post ticket-139 merge) |
| Latest principal checkpoint | `agent_reports/2026-06-14_ticket-137_principal-audit-post-ticket-136.md` |
| Done since checkpoint | ticket-137, ticket-138, ticket-139 (**3** — cadence threshold met) |
| `principal_audit_gate --next-ticket ticket-140` | `cadence_status: overdue`; `implementation_gate: blocked_missing_pre_ticket_audit` |
| Milestone triggers (140) | none — no public export, site, migrations, theory, or live-smoke changes |
| Pre-ticket required | yes (medium risk) — **this report** |
| Cadence note | Cadence is **overdue** by automated counter. ticket-139 was real product work (OpenAlex provider). This focused pre-ticket audit satisfies the **medium-risk implementation gate** for ticket-140; a separate `/rge-principal-audit` is optional hygiene, not a blocker to ticket-140 once this report is on file. |

## Repo verification (2026-06-14)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_SOURCE_NETWORK = "0"

python -m pytest tests/golden -q          # 142 passed
python -m pytest -q                       # 499 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full   # pass
```

Working tree clean at audit time. Golden gate remains mock-only; no Ollama in default collection.

## Problem statement (gap analysis)

| Layer | ticket-139 state | ticket-140 need |
|-------|------------------|-----------------|
| Discovery output | Flat `candidates[]` with provider metadata | Ranked view with credibility/recency signals |
| `source_preferences.yaml` | Loaded for fixture ranking (`rank_fixture_candidates`) | Apply to **discovered** candidates |
| `research_queue.py` | `rank_fixture_candidates()` keyed on hardcoded `FIXTURE_CANDIDATE_PROFILES` | New path for provider-shaped candidates |
| `candidate_ranker.py` | `NotImplementedError` | **Do not implement here** — keep stub; wire ranking in `research_queue.py` per ticket JSON |
| `queue-sources` CLI | Persists **fixture** JSON to `candidate_sources` + `research_queue` | Optional extension for discovered candidates (explicit flag only) |
| Network gate | `RGE_ALLOW_SOURCE_NETWORK=1` for provider HTTP | **Unchanged** — ranking is pure Python on in-memory candidates |

ticket-139 candidate shape (no ranking fields, no `source_type`):

```json
{
  "provider": "openalex",
  "provider_id": "W2741809807",
  "title": "...",
  "authors": ["..."],
  "year": 2023,
  "doi": "https://doi.org/...",
  "open_access_url": "...",
  "landing_page_url": "...",
  "abstract": "...",
  "domain_pack": "creativity",
  "discovered_at": "2026-06-14T12:00:00Z"
}
```

## Audit questions

### What signals are required on ranked output?

Minimum v1 ranked record (extends each discovered candidate or parallel `ranked_candidates[]`):

| Field | Source |
|-------|--------|
| `provider`, `provider_id`, `title`, `year`, … | Preserve ticket-139 candidate fields |
| `source_type` | Inferred (deterministic rules — see below) |
| `credibility_prior` | `source_type_credibility_prior(pack, source_type)` from pack |
| `recency_score` | Deterministic function of `year` and fixed reference year in tests |
| `relevance_score` | Deterministic token overlap: `--query` vs normalized `title` + `abstract` |
| `gap_fill_score`, `novelty_score`, `source_diversity_score`, `drift_risk` | Documented constants or simple heuristics (no LLM) |
| `priority_score` | Existing `compute_priority_score()` — formula `golden_v0.1.0` |
| `reason` | Machine-readable string citing inferred type + top signals |
| `status` | `queued` default; `rejected` only when inferred `marketing_page` |
| `formula_version` | `"golden_v0.1.0"` |

Ranking **influences queue priority; it does not determine truth** (per domain pack spec §8).

### How is `source_type` inferred without LLM?

Deterministic rules on discovered metadata only (implement in `research_queue.py`):

| Condition | Inferred `source_type` |
|-----------|------------------------|
| Title matches marketing patterns (e.g. contains `"only tool you"`, `"supercharge"`, `"#1"`) | `marketing_page` → `status: rejected` |
| `doi` present and `year` within last 10 years of reference year | `peer_reviewed_empirical` |
| `doi` present and older | `theory_essay` |
| No `doi`, non-empty `abstract` | `case_study` |
| Otherwise | `unknown` → credibility prior **0.40** (`UNKNOWN_SOURCE_TYPE_CREDIBILITY_DEFAULT`) |

Optional small enrichment: if implementer adds `work_type` from OpenAlex `work["type"]` in
`map_openalex_work`, map `article` → `peer_reviewed_empirical`, `book` → `theory_essay`.
**Not required** for GO if fixture-based unit tests use ticket-139 candidate shape only.

### Schema / DB writes now or JSON enough?

**Primary acceptance path: JSON only.**

- `discover-sources ... --rank-only` returns `ranked_candidates` sorted by `priority_score` descending.
- **No DB writes** on the default `--rank-only` path.

**Optional secondary path (explicit opt-in):**

- `discover-sources ... --rank-only --enqueue --db <path> --question <rq_id>` may persist to
  **`candidate_sources` + `research_queue`** (staging tables per data model §4.12–4.13).
- Must **not** write to `sources`, `claims`, or other accepted graph tables.
- Idempotent per `(research_question_id, provider_id)` like fixture `queue_sources_from_fixture`.
- If enqueue adds too much scope in one ticket, **defer enqueue to ticket-141** and ship
  `--rank-only` only — still satisfies acceptance criterion 1.

### Network opt-in?

- Ranking runs on in-memory candidates — **no additional network**.
- Discovery still requires ticket-139 gate when `--provider` is used without mocked tests.
- Unit tests patch `get_provider` / provider `discover()` — same pattern as ticket-139.

### Tests deterministic?

- Patch provider HTTP; freeze reference year (e.g. `2026`) for recency scoring in tests.
- Fixture: reuse `fixtures/source_providers/openalex_works_sample.json` + expected rank order.
- Assert credibility priors match creativity pack weights for inferred types.
- Assert marketing-like fixture titles (if added) rank last or `rejected`.
- GT09 fixture path **must not regress** — `rank_fixture_candidates()` unchanged in behavior.

### Connection to NM-4 / ingest?

| Path | ticket-140 | Later |
|------|------------|-------|
| NM-4 evidence DB ingest | **out of scope** | operator selects ranked candidate → manual ingest or fetcher ticket |
| Automatic ingest | **forbidden** | — |
| `research run` live path | unchanged (`not_implemented`) | — |

### Safety boundaries

| Boundary | ticket-140 |
|----------|------------|
| Public write / ingestion routes | none |
| Model → accepted DB | none |
| Staging queue tables | optional `--enqueue` only |
| Credibility as final decision | **no** — signals + `reason` only |
| Secrets in stdout | none |

## Hardened implementation scope

### In

1. **`research_queue.py`**
   - `infer_source_type_for_discovered_candidate(candidate) -> str`
   - `score_discovered_candidate(candidate, *, query, domain_pack, reference_year) -> dict`
   - `rank_discovered_candidates(candidates, *, query, domain_pack, reference_year) -> list[dict]`
   - Reuse `compute_priority_score()` and `source_type_credibility_prior()`.
   - Optional: `enqueue_discovered_candidates(conn, ranked, ...)` mirroring fixture idempotency.

2. **`source_discovery.py`**
   - After successful provider discover, if `--rank-only`: attach `ranked_candidates` to payload.
   - Preserve existing exit codes (stub 2, blocked 1, ok 0).

3. **`rge/cli.py`**
   - Add `--rank-only` to `discover-sources`.
   - Optional: `--enqueue`, `--db`, `--question` when `--rank-only` and operator explicitly queues.

4. **Tests:** `tests/unit/test_discovered_source_queue_ranking.py`
   - Mocked discover + rank-only JSON shape and sort order.
   - Pack credibility prior assertions.
   - Blocked/network/stub paths unchanged.
   - Marketing rejection case.

5. **Agent report** per ticket JSON.

### Out

- PDF/HTML fetch, Playwright, Scrapfly, browser automation
- Claim extraction, accepted-table writes, schema migrations
- Public export / site changes
- LLM relevance scoring
- Automatic ingest or automatic credibility finalization
- `candidate_ranker.py` full implementation (may add one-line delegate later; not required)
- Changing GT09 golden fixture ranking order

## Contract sketch (`--rank-only`)

```json
{
  "command": "discover-sources",
  "status": "ok",
  "provider": "openalex",
  "query": "human AI creativity",
  "domain_pack": "creativity",
  "limit": 10,
  "candidate_count": 2,
  "candidates": [ "... unranked ticket-139 shape ..." ],
  "ranked_candidates": [
    {
      "provider": "openalex",
      "provider_id": "W2741809807",
      "title": "...",
      "source_type": "peer_reviewed_empirical",
      "credibility_prior": 0.9,
      "recency_score": 0.88,
      "relevance_score": 0.75,
      "priority_score": 0.7123,
      "reason": "Inferred peer_reviewed_empirical; DOI present; relevance 0.75 from query overlap.",
      "status": "queued",
      "formula_version": "golden_v0.1.0"
    }
  ]
}
```

## Risk assessment

| Risk | Mitigation |
|------|------------|
| Heuristic `source_type` wrong | Machine-readable `reason`; operator review before ingest; no auto-accept |
| Regress GT09 fixture ranking | Separate code path; do not alter `FIXTURE_CANDIDATE_PROFILES` |
| Accidental network in tests | Mock provider; no `RGE_ALLOW_SOURCE_NETWORK` in CI |
| Staging DB scope creep | `--enqueue` optional; defer if tight |

## Recommendation

| Action | Verdict |
|--------|---------|
| Repo / merge gate health | **GO** |
| Pre-ticket audit (140) | **GO** — this report |
| Cadence | **overdue** (informational); optional principal audit; not blocking 140 |
| Implement ticket-140 | **GO** |
| Next after 140 | ticket-141 — staging enqueue from discovery or fetcher entry (product) |
| Docs/checkpoint loop | **stop** — no docs-only ticket before fetch/enqueue product work |

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-140**.
