---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: medium
ticket: ticket-267
category: Phase 3 / arbitrary-source pipeline / product-risk reduction
---

# Pre-Ticket Audit: ticket-267 End-to-End Arbitrary-Source Operator Proof Bundle

## Verdict: **GO** (hardened scope — mock staged spine + proof artifact only)

ticket-267 reprioritizes away from the superseded AGENTS.md candidate-id cross-link
(tickets 263–265 closed that thread). Implementation must deliver a **single
operator-inspectable proof bundle** for the mock arbitrary-source product path — not
more documentation.

## Recenter context

| Signal | Finding |
|--------|---------|
| Principal audit post-ticket-265 | `drift_warning`: no product-risk work in last 3 tickets |
| Staged rank candidate-id thread | **Closed** (261 JSON, 262/264 tests, 265 README) |
| Superseded ticket-267 scope | AGENTS.md cross-link — **do not implement** |
| Maturity tier (AGENTS.md) | Arbitrary-source pipeline **partial** — staged mock spine proven; export/card bundle missing |

## What already exists?

| Path | Coverage | Gap |
|------|----------|-----|
| `execute_staged_fixture_mode_run` | discover→fetch→ingest→extract→link→build→detect→reconcile→report for rank #1 and #2; returns count summary + `artifacts.rank1_run_report` | No `export-public`; no unified proof bundle schema; dual-rank summary not operator-first |
| `tests/unit/test_manual_source_pipeline_e2e.py` | manual_text ingest→detect (+ reconcile variant) on temp DB | Checksum-pinned synthnote only; no report/export; no proof artifact |
| `tests/unit/test_staged_fixture_mode_run_spine.py` | Patched-network orchestrator counts + idempotency | Asserts orchestrator JSON counts, not export/card paths |
| `export-public` | `rge/modules/card_exporter.py`; golden tests use `--fixture-mode` | Not chained after staged orchestrator |
| `generate-run-report` | Deterministic; staged spine already calls it | Report path not surfaced in operator proof bundle |

## Recommended hardened scope

### Primary pipeline mode: `fixture_staged_rank1`

Reuse **`execute_staged_fixture_mode_run`** internals (or call it, then extend) on a
**temp `--db`**, **temp `--output-dir`**, and **temp `--staging-dir`**. Patched OpenAlex
I/O in unit tests (same pattern as `test_staged_fixture_mode_run_spine.py`); no
`live_network` in default CI.

After rank-1 `generate-run-report` completes (rank-2 spine may continue unchanged for
orchestrator parity, but proof bundle focuses on **rank-1 primary source** as the
operator lens for “usable research output”):

1. Run `export-public --fixture-mode --limit 100` to a **temp export directory** (not
   `apps/public-site/data/` unless tests use isolated paths).
2. Build and write **`operator_proof_bundle.json`** via new module
   `rge/modules/operator_proof_bundle.py`.

### Proof bundle schema (minimum)

```json
{
  "status": "completed",
  "pipeline_mode": "fixture_staged_rank1",
  "source_id": "<uuid>",
  "claim_count": 2,
  "concept_link_count": 4,
  "relationship_count": 2,
  "qualification_count": 1,
  "reconcile": {
    "status": "completed",
    "score_events_created": 1
  },
  "report_path": "<temp>/run_report_latest.json",
  "export_path": "<temp>/public_cards.json",
  "card_count": 12,
  "database_path": "<temp>.sqlite",
  "steps_completed": ["..."],
  "usable_output": true
}
```

On failure: `status: "error"`, `failed_step`, `detail`, partial counts when safe.

`usable_output` should be deterministic boolean logic, e.g. rank-1 accepted claims ≥ 1,
relationships ≥ 1, report file exists, export validation passed.

### CLI surface (proposed)

Add subcommand:

```txt
python -m rge.cli prove-arbitrary-source-bundle
  --topic "..." --domain creativity
  --db <temp.sqlite> --output-dir <temp> --staging-dir <temp> --export-dir <temp>
  --bundle-out <temp>/operator_proof_bundle.json
```

Implementation may alternatively add `--proof-bundle-out` to `research run
--fixture-mode --staged-spine` if that keeps orchestrator wiring DRY — prefer **one
entry point** documented in the agent report.

### Mock / safety constraints

| Constraint | Enforcement |
|------------|-------------|
| Mock LLM only | Force `RGE_LLM_MODE=mock`; no `RGE_ALLOW_LIVE_LLM` |
| Temp DB | Required `--db`; default graph path rejected or overridden to temp in tests |
| No live_network in CI | Unit tests patch network; marker not added to default collection |
| Public safety | `export-public` uses existing `validate_public_export_bundle`; fixture-mode to temp dir only |
| No model writes to accepted tables | Unchanged — Python validates all candidates |
| Reconcile/report deterministic | No live LLM hooks |

## What files are expected to change?

| File | Change |
|------|--------|
| `rge/modules/operator_proof_bundle.py` | **New** — assemble proof bundle from DB + step payloads |
| `rge/cli.py` | CLI subcommand or staged-run hook; wire export + bundle write |
| `tests/unit/test_operator_proof_bundle.py` | **New** — schema, happy path, failure clarity |
| `agent_reports/2026-06-16_phase-3_ticket-267_*.md` | Implementation report |

**Out of scope:** AGENTS.md, README, detect-seed docs, candidate-id docs.

## Tests to add

| Test | Purpose |
|------|---------|
| `test_proof_bundle_happy_path_fixture_staged` | Patched orchestrator → bundle JSON; counts match ticket-162 rank-1 expectations |
| `test_proof_bundle_schema_required_fields` | Required keys present; types sane |
| `test_proof_bundle_failure_reports_failed_step` | Inject failing step; assert `status=error` + `failed_step` |
| `test_proof_bundle_export_path_exists_when_completed` | `export_path` points to validated JSON |

Do **not** add Ollama, OpenAlex live_network, or golden fixture changes unless export
paths require stable timestamps (reuse existing `FIXTURE_EXPORT_TIMESTAMP`).

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Accidental default DB mutation | Medium | Require explicit `--db`; tests use `tmp_path` only |
| Public export writing repo paths | Medium | Default `--export-dir` under temp; never `--publish` in proof command |
| Scope creep into live orchestrator | Medium | Non-goal; mock-only gate in module |
| Duplicating staged spine logic | Low | Call existing `execute_staged_fixture_mode_run` then extend |
| Broadening to manual_text arbitrary live | High | **Out of scope** — NM-1/live fallthrough unchanged |

Overall: **medium** — product-facing CLI + export touchpoint; bounded by mock-only and temp paths.

## Acceptance mapping

| User criterion | Audit answer |
|----------------|--------------|
| Golden + pytest + safety | Required in test_plan |
| Operator inspects one bundle | `operator_proof_bundle.json` + stdout JSON echo |
| Public site build | Only if export/site files change |
| No live LLM / live_network CI | Enforced in module + tests |
| No more detect-seed / candidate-id docs | Explicit non-goal |

## Recommendation

**GO** — implement ticket-267 on branch
`phase-3/ticket-267-arbitrary-source-operator-proof-bundle`. Start with
`operator_proof_bundle.py` and unit tests; wire CLI second. Do not resurrect the
superseded AGENTS.md cross-link.
