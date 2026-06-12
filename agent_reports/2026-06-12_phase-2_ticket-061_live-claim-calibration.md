---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-061: Live claim extraction calibration for local Qwen

- Date: 2026-06-12
- Branch: `phase-2/ticket-061-live-claim-calibration`
- Baseline HEAD: `894f1f6023e31710c719072efbf20f76a9fb8d87`
- Risk level: low-medium

## Summary

Calibrated local Qwen claim extraction so `probe-extract-claims` produces at least
one accepted scoped claim on the default calibration fixture. Root cause of
ticket-060's 0 accepts was **prompt/schema mismatch**, not validator weakness:
Qwen omitted subject/predicate/object and did not embed `scope` verbatim in
`claim_text`. Tightened the Ollama extraction prompt (SPO fields, scope-in-claim
rules, positive/negative examples), added a controlled calibration fixture as
the default probe source, and added `validation_diagnostic` on rejected rows.
Validator strictness unchanged.

## Root cause (ticket-060 live failure)

Both live candidates were rejected as `overgeneralized_scope` because:

1. **Scope not embedded in claim_text** — validator requires
   `scope.lower()` to appear inside `claim_text` (see `claim_validator.py`).
   Qwen set `scope` to a long population/task string but `claim_text` used
   "across submitted ideas" without the scope phrase.
2. **Missing SPO fields** — the pre-061 Ollama prompt JSON schema omitted
   `subject`, `predicate`, and `object`; Qwen returned nulls (would also fail
   `unsupported_claim` if scope check passed).

The validator behaved correctly; calibration targeted model guidance, not rules.

## Files changed

| File | Change |
| ---- | ------ |
| `rge/llm/ollama_client.py` | Calibrated claim extraction prompt |
| `rge/modules/claim_validator.py` | `rejection_diagnostic()` for probe reports |
| `rge/modules/live_probe.py` | Default calibration fixture; diagnostics on rejections |
| `fixtures/sources/live_probe_claim_calibration_short.txt` | New controlled probe source |
| `rge/cli.py` | `--fixture` alias; updated default help |
| `tests/unit/test_claim_rejection_diagnostics.py` | Validator strictness tests |
| `tests/unit/test_ollama_claim_prompt.py` | Prompt content tests |
| `tests/unit/test_live_probe_cli.py` | Updated default fixture path |
| `docs/agents/12_RUNTIME_CONFIG.md` | Calibration fixture docs |
| `tickets/ticket-061.json`, `TICKET_QUEUE.md` | Ticket seed/queue |

## Live probe command

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
python -m rge.cli probe-extract-claims
```

## model-health result

- `reachable: true`, `model_available: true`, `effective_llm_mode: ollama`

## Live probe result

| Field | Value |
| ----- | ----- |
| accepted_count | **1** |
| rejected_count | **1** |
| db_writes | **false** |
| fixture | `fixtures/sources/live_probe_claim_calibration_short.txt` |

**Accepted (summary):** AI-assisted brainstorming increased average idea quality **in short-form writing tasks** (scoped empirical claim with SPO fields).

**Rejected (summary):** diversity-reduction claim used scope phrase "short-form writing tasks" in the `scope` field but phrased claim_text as "…same short-form writing task setting" — correctly rejected with diagnostic noting scope must appear verbatim in claim_text.

## Report artifact path

`data/reports/live_probes/probe_extract_claims_2026-06-12T185110Z.json`

## Mock verification

| Check | Result |
| ----- | ------ |
| pytest | **219 passed**, 2 live_smoke deselected |
| safety audit | **pass** |
| verify --skip-site | **pass** |

## Confirmations

- **No default DB writes** — mtime unchanged
- **No public export / committed JSON churn**
- **No cloud/API keys**
- **Validator strictness preserved** — GT02 overgeneralized tests pass; live still rejects 1 mis-scoped claim
- **CI/golden mock-only**

## Principal audit cadence

`principal_audit_gate` reports **overdue** after ticket-061: **3 done tickets**
since post-ticket-056 checkpoint (057, 058, 060); threshold is 3. Run
`/rge-principal-audit` or a focused pre-ticket audit before the next
implementation ticket beyond routine low-risk calibration.

## Merge

- Ticket commit SHA: _(filled after commit)_
- Main push SHA: _(filled after push)_
- Golden Gate run: _(filled after push)_

## Recommended next move

1. Optional: second calibration pass so both fixture findings accept (prompt tuning only).
2. **probe-link-concepts** ticket once operator confirms repeatable claim accepts.
3. Keep ticket-059 OpenAI deferred until local structured path is stable.
