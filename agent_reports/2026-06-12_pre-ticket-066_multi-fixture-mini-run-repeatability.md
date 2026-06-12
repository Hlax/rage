---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-066 Multi-Fixture Mini-Run Repeatability Audit

- Audit type: focused pre-ticket readiness (live Ollama batch probe)
- Date: 2026-06-12
- Scope: read-only design audit. Ticket seed only; implementation follows on branch.
- Baseline HEAD: `0dc709c` (live probe operator runbook)
- Prior work: ticket-065 mini-run chain; evidence review recommends option A
- Human approval: operator approved seeding ticket-066 from live-probe evidence review

## 1. Executive verdict

**GO — proceed with report-only multi-fixture suite**

Ticket-065 proved the hybrid mini-run on one calibration source. The spine is
stable enough to batch the same report-only chain across **four committed
creativity sources** without DB, export, or cloud surfaces. Add a suite command
that runs default hybrid mini-run per fixture, writes individual mini-run reports
plus one suite summary with per-fixture floor checks.

**Do not** weaken stage validators, add persistence, or grant Qwen ticket authority.

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` | at audit |
| Runbook | **committed** | `0dc709c` — `14_LIVE_PROBE_OPERATOR_RUNBOOK.md` |
| ticket-065 | **done** | mini-run hybrid chain on `main` |
| Evidence review | **written** | `agent_reports/2026-06-12_live-probe-evidence-review.md` |
| ticket-059 OpenAI | **deferred** | placeholder only |
| Principal cadence | **not due** | 1 done ticket since post-ticket-064 checkpoint |

## 3. Proposed design

### CLI

```powershell
python -m rge.cli probe-mini-run-suite
python -m rge.cli probe-mini-run-suite --strict-chain
```

Optional `--fixture-source` repeatable to override the default four-fixture set.

### Default fixture set (committed, creativity domain)

| # | Fixture | Rationale |
| - | ------- | --------- |
| 1 | `fixtures/sources/live_probe_claim_calibration_short.txt` | ticket-061 calibration baseline |
| 2 | `fixtures/sources/creativity_ai_diversity_short.txt` | golden GT02-style passage |
| 3 | `fixtures/sources/creativity_ai_diversity_followup_short.txt` | replication-style short source |
| 4 | `fixtures/sources/creativity_ai_diversity_contradiction.txt` | divergent-condition / tension source |

Exclude prompt-injection fixtures from the default suite (safety / out-of-scope for repeatability).

### Outputs

- One `probe_mini_run_<UTC>.json` per fixture (existing format)
- One `probe_mini_run_suite_<UTC>.json` summary with:
  - per-fixture status, stage counts, `contradiction_input_mode`, `floors_met`
  - suite-level `fixtures_passed` / `fixtures_failed`
  - `db_writes: false`, `public_export: false`, `cloud_calls: false`

### Stage floors (same as runbook)

Stages 1–3: `accepted_count >= 1` each. Stage 4 default hybrid: `accepted_count >= 1`.
Strict-chain: stage 4 skip is expected; suite marks fixture `partial` not failure when
stages 1–3 pass.

### Non-goals

- No scratch DB import
- No public export
- No OpenAI / ticket-059
- No Qwen ticket drafting or queue edits
- No new committed live probe artifacts in git

## 4. Safety checklist

| Control | Status |
| ------- | ------ |
| Report-only | **Confirmed** — reuse `run_probe_mini_run` |
| Default DB untouched | **Confirmed** — no new persistence paths |
| CI mock-only | **Confirmed** — unit tests with MockModelClient |
| Qwen ticket authority | **Denied** — out of scope |
| Live smoke | **Optional** — suite live smoke may be omitted (4× mini-run latency) |

## 5. Acceptance criteria

- `probe-mini-run-suite` requires live opt-in env gates.
- Default run executes four committed fixtures sequentially.
- Suite summary records per-fixture floors and links to individual reports.
- Mock pytest + verify remain green without Ollama.
- Docs: runbook + `12_RUNTIME_CONFIG.md` updated.
- Live suite run documented in agent report (operator environment).

## 6. Recommendation

**Seed ticket-066 and implement on branch `phase-2/ticket-066-multi-fixture-mini-run-repeatability`.**
