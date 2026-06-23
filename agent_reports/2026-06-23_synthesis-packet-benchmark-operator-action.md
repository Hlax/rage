# Synthesis Packet Benchmark → Operator Loop Action

- Date: 2026-06-23
- Branch: `phase-3/cloud-synthesis-packet-cli-throughput`
- Verdict: **PASS**

## Summary

Promoted `synthesis_packet_benchmark_status.benchmark_recommended` into `_action_from_state` as `run_synthesis_packet_benchmark` (`safe_autonomous`) when the synthesis packet CLI branch is active and the gitignored benchmark artifact is missing. `execute-safe` runs the mock benchmark hook after verification when that action is recommended.

## Behavior

| Condition | `next_recommended_action` |
|-----------|---------------------------|
| Synthesis CLI branch + missing artifact | `run_synthesis_packet_benchmark` (`safe_autonomous`) |
| Synthesis CLI branch + artifact present | Falls through to `run_autonomous_researcher_loop` |
| Other branches | Unchanged (benchmark `not_applicable`) |

## Verification

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_synthesis_packet_benchmark_operator_plan.py -q` | 11 passed |
| `pytest tests/unit/test_synthesis_packet_benchmark*.py -q` | 18 passed |

## Deliverables

- `rge/modules/operator_loop.py` — `_action_from_state` + execute-safe hook
- `rge/modules/synthesis_packet_benchmark.py` — `run_synthesis_packet_benchmark_execute_safe_hook`
- `tests/unit/test_synthesis_packet_benchmark_operator_plan.py` — action + hook tests
- `docs/agents/12_RUNTIME_CONFIG.md` — plan action note

## Next smallest ticket

Add `synthesis_packet_benchmark_status` to `self_improvement_status` snapshot when on synthesis CLI branch.
