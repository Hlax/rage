---
template_id: pre_ticket_audit
status: NO-GO
date: 2026-06-15
risk_level: medium
ticket: N/A (no follow-on implementation ticket)
category: Phase 3 / live LLM / staged spine product-risk
---

# Pre-Ticket Audit: Live Staged Generate-Run-Report on Staged Spine (Per-Step Live LLM)

## Verdict: **NO-GO** (`generate-run-report` is deterministic Python; `draft_run_summary` LLM task is Phase 0 stub and not wired to staged spine CLI)

## Context

Per-step live staged LLM fallthrough proofs cover **model-assisted pipeline tasks**
(extract, link, build, detect) where Ollama proposes candidate JSON and Python validates
before persistence (tickets 204/208/212/217).

ticket-187 proved **live OpenAlex + mock LLM through reconcile + deterministic
generate-run-report** on temp DB (`RGE_ALLOW_LIVE_STAGED_REPORT=1` is a **network spine
gate**, not an LLM gate). ticket-221 audited reconcile as **NO-GO** for live LLM for the
same architectural reasons.

This audit closes the staged-spine review for **report generation**.

---

## Audit answers

### 1. What does “live staged report” mean in this repo today?

| Interpretation | Scope | Verdict |
|----------------|-------|---------|
| Live OpenAlex spine through `generate-run-report` (ticket-187) | Network + mock LLM upstream; deterministic report | **Already proven** |
| Per-step live Ollama `generate-run-report` fallthrough | New env gate + CLI on staged spine | **NO-GO** |
| Live Ollama `draft_run_summary` narrative layer | Separate future task; not in CLI today | **NO-GO** (defer; not staged spine) |
| Full orchestrator live LLM report | Changes `execute_staged_fixture_mode_run` | **NO-GO** |

### 2. Does `generate-run-report` use an LLM?

**No.** `rge/modules/run_evaluator.py` module docstring:

```text
Build run reports and failure summaries. Deterministic; no model use.
```

- **CLI:** `python -m rge.cli generate-run-report [--run-id] [--topic] [--db] [--output-dir]`
- **Entry:** `generate_run_report()` → `build_run_report()` → `aggregate_run_metrics()` +
  `aggregate_top_failure_modes()` from SQLite counts.
- **Persistence:** `run_reports` table + optional `run_report_latest.json` on disk.
- **No** `get_model_client`, fixture routing, or Ollama call in the report path.

### 3. What is `draft_run_summary` and how does it relate?

| Surface | Status |
|---------|--------|
| `MockModelClient.draft_run_summary()` | Reads mock fixture for contract tests |
| `OllamaClient.draft_run_summary()` | Raises `OllamaNotAvailableInPhase0("run_summary")` |
| `generate-run-report` CLI | **Does not invoke** `draft_run_summary` |

A future **narrative run summary** LLM task would be a **new milestone** (likely tied to
reporting spec §6+ and ticket generation), not a per-step staged-spine fallthrough mirror
of extract/link/build/detect. It must not bypass deterministic metric aggregation in
`build_run_report()`.

### 4. What is `RGE_ALLOW_LIVE_STAGED_REPORT`?

Opt-in env for **live_network pytest** proving discover→…→reconcile→generate-run-report
(`tests/unit/test_live_staged_report_mock_spine.py`). Gates **OpenAlex network** spine
execution only. There is **no** `RGE_ALLOW_LIVE_STAGED_REPORT_LIVE_LLM` and none should be
added without a new LLM task spec, validator, and reporting contract update.

### 5. Should a live LLM report fallthrough be added to staged spine?

**NO-GO:**

1. **Architecture:** Run reports are JSON-first metric snapshots for operator review and
   ticket generation inputs; counters must be reproducible from DB state.
2. **Existing proof:** ticket-187 + golden GT19 prove deterministic report generation.
3. **Separation of concerns:** LLM narrative summaries (when implemented) should augment,
   not replace, deterministic `run_report` JSON — separate pre-ticket audit required.
4. **Orchestrator:** staged orchestrator remains mock LLM for model-assisted steps; report
   stays Python-only.

### 6. Orchestrator mock-only boundary

**Unchanged.** `execute_staged_fixture_mode_run` forces mock LLM for extract/link/build/detect;
reconcile and generate-run-report remain deterministic in orchestrator chains (tickets 184/187/193).

### 7. Staged spine LLM surface — complete inventory (post ticket-217/221/222)

| Stage | Model-assisted? | Per-step live Ollama opt-in |
|-------|-----------------|----------------------------|
| discover → fetch → ingest-staged | No (network) | live OpenAlex (existing gates) |
| extract-claims | Yes | ticket-204 ✓ |
| link-concepts | Yes | ticket-208 ✓ |
| build-relationships | Yes | ticket-212 ✓ |
| detect-contradictions | Yes | ticket-217 ✓ |
| reconcile-scores | **No** (deterministic) | **NO-GO** (ticket-221) |
| generate-run-report | **No** (deterministic) | **NO-GO** (this audit) |

No further per-step live LLM fallthrough tickets are warranted on the staged rank-1 spine
unless product scope explicitly adds new LLM tasks (e.g. narrative summary, theory generation).

---

## Hardened scope — follow-on implementation

**None.** Do **not** seed live report LLM fallthrough implementation.

## Recommended next tickets

| Priority | Ticket idea | Risk | Rationale |
|----------|-------------|------|-----------|
| 1 | **Principal audit** post-ticket-222 staged spine LLM surface closure | low | Cadence overdue (218–221 since ticket-219); document complete LLM boundary table |
| 2 | Pre-ticket audit: narrative `draft_run_summary` live path (if product wants prose reports) | medium | Separate from staged spine; requires reporting spec + validator |
| 3 | Rank-2 / orchestrator / theory milestones | varies | Existing queue deferrals |

## Safety

- No new model write paths proposed.
- Deterministic report persists metrics only; no raw prompts or secrets in public export path.

## Operator reference (existing deterministic report spine)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_REPORT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_report_mock_spine.py -m live_network -q
```

Requires `seed_domain_opposing_context(temp_db)` before live discover.

## Recommendation

**NO-GO** for live Ollama staged `generate-run-report` fallthrough. Run **principal audit
(ticket-223)** to reset cadence and publish the closed staged-spine LLM inventory. Do not
implement `--live-staged-report-fallthrough` or `RGE_ALLOW_LIVE_STAGED_REPORT_LIVE_LLM`.
