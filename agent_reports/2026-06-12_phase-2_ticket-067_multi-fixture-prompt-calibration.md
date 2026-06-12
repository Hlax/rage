---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Phase 2 — ticket-067: Multi-fixture prompt calibration for local live mini-run suite

- Date: 2026-06-12
- Branch: `phase-2/ticket-067-multi-fixture-prompt-calibration`
- Baseline HEAD: `f7b730c` (ticket-066 on main)
- Risk level: low-medium

## Summary

Calibrated local Qwen prompts and suite fixtures after ticket-066 exposed three
failure modes: relationship drafts using labels outside linked concepts, mini-run
relationship handoff accepting only one claim id, and claim scopes too long on
the contradiction passage. Added GT02 and contradiction calibration sources for
the suite. Live suite now passes floors on **3/4** fixtures (exceeds ≥2 acceptance).

## Root causes (ticket-066 diagnostics)

| Issue | Fix |
| ----- | --- |
| Relationship used `idea quality` / claim subject phrases | Ollama relationship prompt: copy labels exactly from allowed list |
| Multi-claim stage 1 but single claim id in stage 3 validation | Mini-run `accepted_claim_ids` includes all probe claim ids |
| Contradiction source scopes too long for verbatim embedding | New `live_probe_contradiction_calibration_short.txt` |
| Full GT02 passage scope embedding unreliable | New `live_probe_diversity_calibration_short.txt` in suite |

Validators unchanged.

## Files changed

| File | Change |
| ---- | ------ |
| `rge/llm/ollama_client.py` | Claim + relationship prompt calibration |
| `rge/modules/live_probe.py` | Multi-claim handoff; suite fixture list |
| `fixtures/sources/live_probe_diversity_calibration_short.txt` | GT02 suite calibration |
| `fixtures/sources/live_probe_contradiction_calibration_short.txt` | Contradiction suite calibration |
| `tests/unit/test_ollama_*_prompt.py` | Prompt assertion updates |
| `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` | Suite fixture table |
| `rge/cli.py` | Suite help text |
| `tickets/ticket-067.json`, `TICKET_QUEUE.md` | Done status |

## Live suite result (post-calibration)

| Fixture | Floors met | Notes |
| ------- | ---------- | ----- |
| `live_probe_claim_calibration_short.txt` | **yes** | 2/0, 4/0, 1/0, 1/0 hybrid |
| `live_probe_diversity_calibration_short.txt` | **yes** | 2/0, 4/0, 1/0, 1/0 hybrid |
| `creativity_ai_diversity_followup_short.txt` | **no** | stages 1–3 ok; contradiction 0/1 |
| `live_probe_contradiction_calibration_short.txt` | **yes** | 1/1, 2/0, 1/0, 1/0 hybrid |

Suite: `fixtures_passed: 3`, `fixtures_failed: 1`, `status: partial`
Artifact: `data/reports/live_probes/probe_mini_run_suite_2026-06-12T220829Z.json`

## Mock verification

| Check | Result |
| ----- | ------ |
| pytest | **273 passed**, 6 deselected |
| verify --skip-site | **pass** |

## Safety confirmations

- No default DB writes
- No public export / cloud keys
- No ticket authority for Qwen
- Live artifacts gitignored

## Principal audit cadence

Post-ticket-064 checkpoint: **3 done tickets** (065–067). Threshold 3 — **due** before
next medium-risk ticket; optional focused audit if seeding scratch DB next.

## Merge

- Merge commit SHA: `1fcce3d`
- Main push SHA: `1fcce3d`
- Golden Gate run: **27445901235** — **success** at `1fcce3d`

## Recommended next move

1. Optional followup contradiction prompt calibration (single remaining suite gap).
2. **Scratch DB persistence ticket** now reasonable (≥2 consistent suite passes).
3. Keep ticket-059 OpenAI deferred.
