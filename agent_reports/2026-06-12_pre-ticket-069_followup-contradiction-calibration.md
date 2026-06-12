---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-069 Followup Contradiction Calibration Audit

- Audit type: focused pre-ticket readiness (live Ollama calibration)
- Date: 2026-06-12
- Baseline HEAD: `b43e965` (ticket-068 on main)
- Human direction: close 3/4 suite gap for followup fixture contradiction stage

## 1. Executive verdict

**GO — report-only prompt + hybrid handoff calibration**

Ticket-067/068 diagnostics show `creativity_ai_diversity_followup_short.txt` passes
stages 1–3 but contradiction stage is **0/1** in hybrid overlay mode. Artifact
`probe_mini_run_2026-06-12T220753Z.json` shows rejection `same_claim_pair`:
the extracted claim contains only the opposing fragment (`reduced semantic diversity`)
but hybrid overlay treated it as the qualifying source claim, so claim-id resolution
collapsed both roles to the same id.

Fix without validator weakening: opposing-only hybrid overlay replaces the bundle
opposing claim slot while preserving bundle qualifying source claims; tighten
Ollama contradiction prompt to require distinct qualifying/opposing claim ids when
fragments are present.

## 2. Root cause classification

| Factor | Assessment |
| ------ | ------------ |
| Prompt wording | Partial — model omits claim ids; needs explicit fragment→id rules |
| Fixture ambiguity | Partial — followup text is opposing-only by design (replication finding) |
| Handoff logic | **Primary** — opposing claim incorrectly overlaid as qualifying |
| Validator behavior | Correct — `same_claim_pair` is intentional |

## 3. Safety checklist

| Control | Status |
| ------- | ------ |
| Validator unchanged | **Confirmed** |
| Floors unchanged | **Confirmed** |
| No DB writes | **Confirmed** |
| No public export | **Confirmed** |
| No OpenAI/cloud | **Confirmed** — ticket-059 deferred |
| Scratch DB untouched | **Confirmed** |
| Qwen ticket authority | **Denied** |

## 4. Expected file changes

- `rge/modules/live_probe.py` — opposing-only hybrid overlay handoff
- `rge/llm/ollama_client.py` — contradiction prompt claim-id guidance
- `tests/unit/test_live_probe_mini_run_cli.py` — hybrid handoff unit test
- `tests/unit/test_ollama_contradiction_prompt.py` — prompt assertion updates
- `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` — note followup fix
- `tickets/ticket-069.json`, `TICKET_QUEUE.md`

## 5. Required tests

- Unit: opposing-only overlay keeps distinct qualifying/opposing claim ids
- Unit: contradiction prompt includes claim-id assignment rules
- Mock mini-run on followup fixture reaches contradiction accepted_count >= 1
- Regression: existing 3 passing suite fixtures still pass (mock + live if available)
- Golden, full pytest, safety audit

## 6. Out of scope

- Validator or floor changes
- Skipping followup fixture
- OpenAI / ticket-059
- Scratch DB or accepted graph writes
- Public export changes
- Broad DB or pipeline refactors

## 7. Rollback plan

Revert handoff + prompt + tests + docs; re-run mock gates. Live suite returns to 3/4.

## 8. Recommendation

Seed ticket-069 and implement on branch
`phase-2/ticket-069-followup-contradiction-calibration`.
