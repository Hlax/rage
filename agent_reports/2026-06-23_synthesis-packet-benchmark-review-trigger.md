# Synthesis Packet Benchmark + Review-Trigger Dry Run

- Date: 2026-06-23
- Branch: `phase-3/cloud-synthesis-packet-cli-throughput`
- Verdict: **PASS** (mock-first; no live OpenAI calls)

## Summary

Added a repeatable mock-first benchmark for the synthesis packet CLI to measure reports/hour and verify local vs OpenAI big-review threshold wiring without live OpenAI HTTP. Fixed orphaned `_scalar_count` helper in `synthesis_packet_runner.py` (required for `--db` throughput snapshots).

Prior cloud synthesis packet CLI work was already committed (`b5aa04f`). This run adds benchmark module, script, tests, and docs note only.

No live OpenAI calls were made. No `.env.local` contents or API keys were read, printed, or serialized. No synthesis ledger rows were mutated (`evaluate_governor=False` in benchmark loop).

## Benchmark command

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_synthesis_packet_benchmark.py --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json --runs 25
```

## Observed benchmark results (25 runs, mock_cloud)

| Metric | Value |
|--------|-------|
| Runs completed | 25 |
| Total elapsed (wall clock) | 0.052 s |
| Average seconds per report | 0.002 s |
| Estimated reports/hour | ~1,742,444 (mock; not representative of live OpenAI latency) |
| Total claims produced | 50 (2 per run × 25) |
| Provider | `mock_cloud` |
| Mode | `mock` |
| Cloud call made (any run) | **No** |
| Estimated cost USD total | 0.0 |

**Note:** Mock synthesis completes in sub-millisecond time per run, so reports/hour is an instrumentation ceiling, not a production SLA. Use the same benchmark shape with a gated live provider once operator gates pass to estimate real OpenAI cadence.

## Local review threshold status

- **Triggered:** yes (`local_review_recommended: true`)
- **Reason:** `reports_completed=25` reached default local interval (every 25 reports)
- **Tier:** `local`
- Claims after 25 runs: 50 — below the default local claim interval (100)

## OpenAI big-review threshold status

- **Triggered:** no (`openai_big_review_recommended: false`)
- **Tier:** `none` at cumulative 25 reports / 50 claims
- **Live call blocked:** n/a (no big-review recommendation at this volume)
- Policy defaults remain: every **100 reports** or **500 claims** for OpenAI big review

## Recommended OpenAI review cadence (from observed throughput)

| Policy interval | Reports | Claims | At mock 0.002 s/report (illustrative only) |
|-----------------|---------|--------|---------------------------------------------|
| Local review | 25 | 100 | ~0.05 s / ~0.2 s |
| OpenAI big review | 100 | 500 | ~0.2 s / ~1.0 s |

**Operator guidance:** Keep default count-based cadence (100 reports / 500 claims) for OpenAI big review. After the first gated live OpenAI single-run timing (`research synthesize --provider openai --confirm` with all env gates), multiply average seconds per report by 100 to estimate wall-clock time between big reviews. Example: 30 s/report → ~50 minutes between big reviews at the report interval.

Immediate review still applies on drift, contradiction, quality, or grounding signals regardless of count.

## Deliverables

| Path | Purpose |
|------|---------|
| `rge/modules/synthesis_packet_benchmark.py` | Benchmark aggregation, reports/hour, review-threshold dry run |
| `scripts/run_synthesis_packet_benchmark.py` | Operator CLI wrapper |
| `tests/unit/test_synthesis_packet_benchmark.py` | Mock default, deterministic throughput math, threshold + secret tests |
| `rge/modules/synthesis_packet_runner.py` | Fix `_scalar_count` for DB throughput snapshots |
| `docs/agents/12_RUNTIME_CONFIG.md` | Benchmark command reference |

## Verification

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_synthesis_packet_benchmark.py tests/unit/test_synthesis_packet_runner.py -q` | 16 passed |
| `python -m pytest -q` | 1323 passed, 49 deselected |
| `python -m rge.cli verify --skip-site` | exit 0 |
| `python -m rge.modules.safety_auditor --audit full` | pass |
| `python -m rge.modules.operator_loop --mode plan` | exit 0 |
| `python scripts/run_release_governor.py --inspect` | completed |

## Safety properties

- Benchmark refuses `--provider openai` (ValueError before any client call)
- `cloud_call_made_any` remains false under default `mock_cloud`
- OpenAI big-review evaluation is recommendation-only; `openai_live_call_blocked` true when gates missing
- Summary JSON scanned via `_private_value_violations` before emit
- No accepted graph writes; candidate output only

## Next smallest ticket

Wire benchmark summary export to a gitignored operator artifact path (e.g. `data/reports/synthesis_packet_benchmark_latest.json`) and surface `reports_per_hour_estimate` in operator_loop plan mode when synthesis packet CLI is on the active branch.
