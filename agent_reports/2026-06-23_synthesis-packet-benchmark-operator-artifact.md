# Synthesis Packet Benchmark Operator Artifact + Plan Surfacing

- Date: 2026-06-23
- Branch: `phase-3/cloud-synthesis-packet-cli-throughput`
- Verdict: **PASS** (mock-first; no live OpenAI calls)

## Summary

Wired synthesis packet benchmark summary export to gitignored `data/reports/synthesis_packet_benchmark_latest.json` and surfaced `reports_per_hour_estimate` in `operator_loop --mode plan` when the active branch matches synthesis packet CLI work.

## Benchmark command (writes artifact)

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/run_synthesis_packet_benchmark.py --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json --runs 25
```

Artifact path: `data/reports/synthesis_packet_benchmark_latest.json` (under gitignored `data/`).

## Operator plan surfacing

On branch `phase-3/cloud-synthesis-packet-cli-throughput`, plan mode now includes:

```json
"synthesis_packet_benchmark_status": {
  "status": "available",
  "reports_per_hour_estimate": 1920381.004,
  "runs_completed": 25,
  "artifact_path": "data/reports/synthesis_packet_benchmark_latest.json"
}
```

Off synthesis-packet CLI branches: `status: not_applicable`, `reports_per_hour_estimate: null`.

Missing artifact on synthesis branch: `status: missing`, `benchmark_recommended: true`.

## Deliverables

| Path | Change |
|------|--------|
| `rge/modules/synthesis_packet_benchmark.py` | Artifact write/load, branch detection, `inspect_synthesis_packet_benchmark_plan_status` |
| `rge/modules/operator_loop.py` | Plan field `synthesis_packet_benchmark_status` |
| `scripts/run_synthesis_packet_benchmark.py` | Writes artifact by default; `--no-write-artifact` opt-out |
| `tests/unit/test_synthesis_packet_benchmark_operator_plan.py` | Artifact + plan integration tests |
| `docs/agents/12_RUNTIME_CONFIG.md` | Artifact + plan note |

## Verification

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_synthesis_packet_benchmark_operator_plan.py tests/unit/test_synthesis_packet_benchmark.py -q` | 15 passed |
| `python scripts/run_synthesis_packet_benchmark.py ... --runs 25` | exit 0; artifact written |
| `python -m rge.modules.operator_loop --mode plan` | `synthesis_packet_benchmark_status.status=available` |
| `python -m rge.cli verify --skip-site` | exit 0 |

## Safety

- No live OpenAI calls
- Artifact scanned via `_private_value_violations` before write
- Plan inspect is read-only; no ledger mutation

## Next smallest ticket

Promote `synthesis_packet_benchmark_status.benchmark_recommended` into `_action_from_state` as a `safe_autonomous` dry-run action when artifact is missing on the synthesis CLI branch.
