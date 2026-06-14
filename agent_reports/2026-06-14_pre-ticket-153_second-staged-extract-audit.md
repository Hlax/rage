---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-153
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-153 Extract Claims from Second Staged-Ingested Source

## Verdict: **GO**

ticket-152 leaves rank #2 ingested with chunk text from mock HTML. ticket-153 may prove
**extract-claims** on that source using a **new mock LLM fixture** whose `quote_span` values
match the rank #2 staged chunk — no live LLM, no link/build spine.

## Principal / cadence gate

| Field | Value |
| ----- | ----- |
| Main tip | `8dbd290` (post ticket-152) |
| Pre-ticket required | yes — **this report** |
| Principal cadence | **at threshold** — 3 done tickets since post-ticket-149 checkpoint (`ticket-150`–`ticket-152`); `/rge-principal-audit` recommended after ticket-153 or next product-risk batch |
| Milestone triggers | none — mock extract only; no public export/migrations/live Ollama |

Pre-ticket audit **unblocks** ticket-153 implementation. Principal cadence does not block this
scoped test-forward ticket but should not be deferred past the next 1–2 done tickets.

## 1. Upstream state (ticket-152)

| Field | Value |
| ----- | ----- |
| candidate id | `disc_openalex_W1234567890` |
| title | Constraint management in AI-assisted creative teams |
| mock HTML body text | `Constraint management improves AI-assisted creative team workflows.` |
| inferred source_type | `unknown` |
| post-ingest | `sources=1`, `claims=0` |

Reuse helpers from `tests/unit/test_staged_second_candidate_spine.py` (discover → fetch #2 → ingest-staged).

## 2. Why a new fixture is required

Rank #1 auto-select in `claim_extractor._default_fixture_for_chunk()` matches only:

```python
"human-ai co-creativity" in chunk and "songwriting" in chunk
→ staged_fetch_extract_claims.json
```

Rank #2 chunk text does **not** match that heuristic. Without a new fixture, mock mode falls
through to `claim_extraction_valid_and_missing_quote.json` (wrong quotes → nondeterministic
rejections).

**Required:** `fixtures/llm_outputs/staged_fetch_second_candidate_extract_claims.json`

## 3. Fixture contract (minimal)

Mirror rank #1 pattern (`staged_fetch_extract_claims.json`): **1 accepted + 1 rejected**.

| # | claim (summary) | quote_span | expected status |
| - | --------------- | ---------- | --------------- |
| 1 | Constraint management improves AI-assisted creative team workflows. | exact substring from chunk | `accepted` |
| 2 | Broad/overclaim variant (e.g. always increases creativity) | `null` | `rejected` / `missing_quote_span` |

Placeholders `src_placeholder` / `chk_placeholder` are fine; mock client binds real ids at runtime.

Suggested accepted row:

```json
{
  "claim_text": "Constraint management improves AI-assisted creative team workflows.",
  "quote_span": "Constraint management improves AI-assisted creative team workflows.",
  "subject": "Constraint management",
  "predicate": "improves",
  "object": "AI-assisted creative team workflows",
  "scope": "AI-assisted creative teams",
  "evidence_type": "empirical",
  "confidence": 0.7,
  "limitations": ["Staged fetch artifact; operator must verify source provenance."],
  "domain": "creativity"
}
```

## 4. Fixture selection strategy (hardened scope)

Ticket JSON lists `affected_modules: []`. **Prefer test-only binding:**

```text
extract-claims --source <rank_2_source_id> --fixture staged_fetch_second_candidate_extract_claims.json
```

Optional parity with ticket-144 (small `claim_extractor.py` addition):

- Add `_is_second_staged_fetch_spine_chunk()` matching `"constraint management"` + `"creative team"` (or `"workflows"`)
- Return `staged_fetch_second_candidate_extract_claims.json` from `_default_fixture_for_chunk()`
- Add unit test `test_default_fixture_for_second_staged_fetch_spine_chunk`

Either path satisfies acceptance; **do not** do both unless the auto-select test is included.

## 5. Minimal test file

`tests/unit/test_staged_second_candidate_extract_spine.py`

1. Run ticket-152 spine through ingest-staged (reuse `_discover_and_enqueue`, fetch #2, ingest)
2. Resolve rank #2 `source_id` by title `LIKE '%Constraint management%'`
3. `extract-claims` with `--fixture staged_fetch_second_candidate_extract_claims.json`
4. Assert `accepted_count == 1`, `rejected_count == 1`
5. Optional: re-run extract → `already_extracted` (idempotent)
6. Optional: CLI JSON asserts `status`, `command`, counts

**Out of scope:** link-concepts, build-relationships, detect, reconcile (ticket non_goals).

## 6. Tables touched (read/write)

| Table | Write on extract |
| ----- | ---------------- |
| `claims` | accepted + rejected rows |
| `sources` | no new rows |

No schema migration. No public export.

## 7. Test proof

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_extract_spine.py -q
python -m pytest tests/unit/test_staged_second_candidate_spine.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## 8. Out of scope

- Live Ollama / live OpenAlex
- Link/build/detect for second source
- Schema migrations, public export/site
- Reusing rank #1 fixture for rank #2 chunk text

## Recommendation

| Action | Verdict |
| ------ | ------- |
| Implement ticket-153 | **GO** |
| Next follow-on | ticket-154 — link-concepts on second staged source (propose when seeding queue) |

## Suggested builder prompt

```text
/rge-run-next-ticket
```

Follow this audit: new fixture + extract test; use explicit `--fixture` unless adding the optional auto-select heuristic from section 4.
