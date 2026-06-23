# Cloud Synthesis Packet CLI + Throughput Instrumentation

- Date: 2026-06-23
- Branch: `phase-3/cloud-synthesis-packet-cli-throughput`
- Verdict: **PASS** (mock-first; no live OpenAI calls)

## Summary

Wired the ticket-059 cloud synthesis adapter into the research CLI via `research synthesize --packet`. Default provider remains `mock_cloud`. Live OpenAI requires `--provider openai --confirm` plus all existing env gates. Added throughput metrics on each synthesis run and review-threshold policy defaults for local vs OpenAI big-review cadence.

No live OpenAI HTTP calls were made. No `.env.local` contents or API keys were read, printed, or serialized.

## Synthesis packet command

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli synthesize --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json
```

Optional flags:

- `--provider mock_cloud|openai` (default: `mock_cloud` from env/config)
- `--confirm` (required for OpenAI)
- `--db PATH` (read-only throughput counters from SQLite)
- `--output-dir PATH` (default: `data/exports/synthesis_packets/`)
- `--load-operator-env` (apply `.env`/`.env.local` via `operator_env_loader`)

Live OpenAI was **not** called in this packet.

## Deliverables

| Module | Purpose |
|--------|---------|
| `rge/modules/synthesis_packet_runner.py` | Packet validation → `get_cloud_synthesis_client()` → candidate output + throughput |
| `rge/modules/synthesis_review_threshold_policy.py` | Local/OpenAI review cadence + immediate quality triggers |
| `rge/cli.py` | `synthesize` subcommand |
| `fixtures/synthesis/grounded_evidence_packet_dry_run.json` | Grounded v0.2.0 dry-run packet (referenced by governor/UI) |
| `tests/unit/test_synthesis_packet_runner.py` | Mock synthesis, gate, throughput, secret-redaction tests |
| `docs/agents/12_RUNTIME_CONFIG.md` | CLI + benchmark + threshold env table |
| `docs/agents/13_MODEL_ESCALATION_POLICY.md` | Packet CLI policy note |
| `.env.example` | Review threshold env placeholders |

## Throughput fields (`throughput` object)

Each synthesis run records:

- `started_at`, `completed_at`, `elapsed_seconds`
- `sources_processed`, `reports_completed`, `claim_count`
- `concept_link_count`, `relationship_count`, `qualification_count`, `card_count`
- `provider`, `mode`, `model`
- `cloud_call_made` (boolean)
- `estimated_cost_usd` (null for mock)

DB counters populate when `--db` is passed; otherwise packet-local fallbacks are used.

## Review threshold defaults

| Tier | Reports interval | Claims interval |
|------|------------------|-----------------|
| Local / mock / Ollama | every 25 | every 100 |
| OpenAI big review | every 100 | every 500 |

Immediate review also triggers on `drift_warning_active`, `contradiction_threshold_exceeded`, `quality_threshold_failed`, or `grounding_failed` quality signals.

OpenAI big-review recommendations set `openai_live_call_blocked: true` unless all live HTTP gates pass. Threshold evaluation never initiates live HTTP by itself.

Env overrides: `RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_REPORTS`, `RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_CLAIMS`, `RGE_SYNTHESIS_OPENAI_REVIEW_EVERY_REPORTS`, `RGE_SYNTHESIS_OPENAI_REVIEW_EVERY_CLAIMS`.

## Reports/hour benchmark (operator)

```powershell
$env:RGE_LLM_MODE = "mock"
Measure-Command {
  python -m rge.cli synthesize --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json
}
# reports_per_hour ≈ 3600 / elapsed_seconds from throughput.elapsed_seconds
```

## Safety properties

- Packet validated before client call (`validate_synthesis_evidence_packet` + operator-safe checks; grounded schema required for OpenAI).
- Governor evaluated with `write_ledger=False` (no ledger mutation).
- `no_accepted_graph_writes: true` on every run artifact.
- Value-level secret/path scan on result payload (no API keys in JSON).

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_synthesis_packet_runner.py tests/unit/test_openai_synthesis_adapter_contract.py -q
python -m pytest -q
python -m rge.cli verify --skip-site
python -m rge.modules.safety_auditor --audit full
python -m rge.cli synthesize --packet fixtures/synthesis/grounded_evidence_packet_dry_run.json
python -m rge.modules.operator_loop --mode plan
python scripts/run_release_governor.py --inspect
```

| Command | Result |
|---------|--------|
| Targeted synthesis tests | 17 passed |
| Full pytest | 1315 passed, 49 deselected |
| `verify --skip-site` | pass |
| Safety audit full | pass |
| `synthesize` CLI smoke | `mock_cloud`, `cloud_call_made: false` |
| `operator_loop --mode plan` | exit 0 |
| `run_release_governor.py --inspect` | exit 0 |

## Live call status

**No live OpenAI HTTP calls were made.**
