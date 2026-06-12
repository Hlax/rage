---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-026 Audit: Prompt-Injection Readiness

- Audit type: pre-implementation readiness audit (no ticket-026 code changes)
- Date: 2026-06-12
- Agent/model: Cursor builder agent (GPT-5.5)
- Scope: Git/main state after ticket-025, report consistency for tickets 021-025, deterministic chain, safety audit gate, prompt-injection readiness, ticket-026 scope

## Summary

The repo is functionally ready for ticket-026 in terms of branch position, queue order, reports, tests, and safety gate behavior. `main` is aligned with `origin/main` at `7ae393969a7f35bbb73e9ba7f49b6d1a9a171cca`; ticket-021 through ticket-025 are merged and pushed; ticket-026 is the lowest-order proposed ticket and is safety-sensitive because it touches prompt injection and source/model input handling.

However, this audit run did not start ticket-026 because the working tree is not clean. The dirty files are generated export artifacts (`apps/public-site/public/data/build_info.json`, `apps/public-site/public/data/public_cards.json`, and untracked `data/exports/*`) and must not be merged into an audit or ticket branch unless intentionally refreshed by the relevant ticket.

Recommendation: do not proceed; resolve blockers first.

## Git/Main Status

| Check | Result |
|---|---|
| Current branch | `main` |
| Main tip | `7ae393969a7f35bbb73e9ba7f49b6d1a9a171cca` |
| `origin/main` | `7ae393969a7f35bbb73e9ba7f49b6d1a9a171cca` |
| `main` vs `origin/main` | aligned |
| Branches containing HEAD | `main` |
| Unmerged branches into main | none reported |
| Working tree | dirty generated artifacts |

Dirty artifacts observed:

- `apps/public-site/public/data/build_info.json` modified generated timestamp.
- `apps/public-site/public/data/public_cards.json` modified ordering/timestamps.
- `data/exports/build_info.json`, `data/exports/public_cards.json`, `data/exports/public_memos.json` untracked generated exports.

Recent history confirms tickets 021-025 were merged and pushed:

- `ac1c11e` merge ticket-021
- `8b7375a` merge ticket-022
- `551cf5a` merge ticket-023
- `3185684` merge ticket-024
- `30d054b` merge ticket-025
- `7ae3939` docs commit recording ticket-025 main merge hash

## Ticket/Queue Consistency

Tickets 021-025 are consistently marked `done` in both `tickets/TICKET_QUEUE.md` and their JSON files. Ticket-026 is the lowest-order `proposed` ticket and is also listed as the current active ticket awaiting review.

Ticket-026 is clear and builder-consumable:

- Title: `Add prompt-injection golden fixture handling (Golden Test 24)`
- Risk level: `medium`
- Expected files: prompt-injection source fixture, LLM output fixture, `rge/safety/prompt_injection.py`, and `tests/golden/test_24_prompt_injection.py`
- Acceptance criteria: malicious instructions do not alter extraction behavior/source credibility; only actual research claim is extracted; GT24 passes; existing golden suite remains green
- Non-goals: no Ollama, no public write routes, no full runtime sandbox beyond fixture-mode validation

Because ticket-026 touches prompt injection, source text handling, claim validation, and model input boundaries, it is safety-sensitive even aside from the stated medium risk. The runner protocol requires this pre-ticket audit.

## Report-Claim Consistency For 021-025

Reports for tickets 021-025 match repo reality.

| Ticket | Report Claim | Repo Reality |
|---|---|---|
| ticket-021 | `generate-run-report`, run repositories, GT19, 89 passing | CLI command exists; run-report repositories/functions exist; `tests/golden/test_19_run_report.py` exists; current suite includes GT19 |
| ticket-022 | `generate-improvement-tickets`, `ticket_writer.py`, GT20, 93 passing | CLI command exists; `ticket_writer.py` exists; GT20 exists; current suite includes GT20 |
| ticket-023 | `validate_builder_ticket()`, GT21, 97 passing | `validate_builder_ticket()` exists; GT21 exists; current suite includes GT21 |
| ticket-024 | builder golden merge gate, GT22, 101 passing | `tests/golden/test_22_builder_golden_gate.py` exists with `BUILDER_MERGE_GATE_COMMAND`; current suite includes GT22 |
| ticket-025 | `run_safety_audit()`, GT23, full safety audit, 106 passing | `run_safety_audit()` exists; GT23 exists with 5 tests; full audit returns machine-readable `status: pass`; current suite has 106 tests |

No missing report files were found among the requested reports. Command counts claimed by earlier reports are plausible against the current 106-test suite: each ticket added its reported increment, and all prior golden tests remain collected.

## Commands/Tests Run

| Command | Result |
|---|---|
| `git status --short --branch` | `## main...origin/main` with dirty generated artifacts |
| `git log --oneline --decorate -30` | ticket-021 through ticket-025 merge history present; HEAD `7ae3939` |
| `git branch --contains HEAD` | `* main` |
| `git fetch --prune origin` + rev comparison | `main` and `origin/main` both `7ae393969a7f35bbb73e9ba7f49b6d1a9a171cca` |
| `git branch --all --no-merged main` | no output |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | exit 0; JSON `status: pass`; no blocked reasons |
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_23_safety_audit_gate.py` | 5 passed |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | 106 passed |
| `RGE_LLM_MODE=mock python -m pytest` | 106 passed |

Safety audit JSON status:

```json
{
  "report_type": "safety_audit_report",
  "audit_type": "full",
  "status": "pass",
  "blocked_reasons": []
}
```

## Recent System-Chain Verification

The deterministic chain expected after recent tickets is present:

- Core commands are registered in `rge/cli.py`: `ingest`, `extract-claims`, `link-concepts`, `build-relationships`, `detect-contradictions`, `reconcile-scores`, `generate-cluster-report`, `generate-theory-candidates`, `generate-followup-questions`, `generate-ontology-pressure`, `generate-domain-proposal`.
- Self-improvement commands are registered: `generate-run-report`, `generate-improvement-tickets`.
- Builder ticket validation exists in `rge/modules/ticket_writer.py`.
- Builder golden merge gate tests exist in `tests/golden/test_22_builder_golden_gate.py`.
- Safety audit exists in `rge/modules/safety_auditor.py` and passes as JSON.

No Ollama or live web discovery was used.

## Safety Audit Verification

`run_safety_audit()` returns machine-readable JSON and CLI exit behavior is fail-closed: exit 0 on pass, exit 1 on fail. Golden Test 23 verifies the clean-repo pass, JSON shape, CLI JSON output, forbidden public write route patterns, and model shell execution patterns.

Coverage verified:

- Route/public-site scan is limited to `apps/public-site/app`, `apps/public-site/lib`, and `next.config.js`, excluding noisy generated folders such as `node_modules`, `out`, and `.next`.
- Public export validation reuses `validate_public_export_bundle`.
- Secret scanning checks public export JSON using forbidden value patterns.
- Raw HTML checks reject `dangerouslySetInnerHTML`.
- Model tool checks scan `rge/llm/*.py` for subprocess/shell/Git-push patterns.
- Prompt-injection audit currently checks policy presence; runtime fixture behavior is explicitly GT24 scope.

Public-site routes under `apps/public-site/app` are static/read-only pages. No POST/write, ingestion, local-agent, or raw HTML rendering route was found.

## Prompt-Injection Readiness

Golden Test 24 is specified in `docs/agents/00_GOLDEN_TESTS.md`: malicious source text includes instructions to ignore prior instructions, mark the source credible, delete claims, and export private notes; the system must extract only the actual research claim and must not modify credibility, delete claims, export private data, or modify system behavior.

Prompt-injection requirements are also present in `docs/agents/10_SAFETY_MODEL.md`: source text is untrusted data, prompt wording alone is insufficient, unsafe injected content should be rejected with `unsafe_or_injected_content`, and deterministic checks override model commentary. `docs/agents/09_RESEARCH_RUN_CONTRACT.md` already lists `fixtures/sources/prompt_injection_source.txt` among fixture-mode source strategy examples.

Audit answers:

- Does a prompt-injection fixture already exist? A seed fixture exists at `fixtures/sources/prompt_injection_source.txt`. The ticket-026 expected fixture name `fixtures/sources/prompt_injection_creativity_short.txt` does not yet exist.
- Is there already a prompt-injection detector, sanitizer, validator, policy object, or rejection reason? There is a policy constants module at `rge/safety/prompt_injection.py` with `FORBIDDEN_INJECTION_EFFECTS` and `REJECTION_REASON_INJECTED_CONTENT = "unsafe_or_injected_content"`. There is no runtime detector/sanitizer yet. `claim_validator.py` mentions the rejection reason in its docstring but does not enforce prompt-injection rejection.
- Which module should own prompt-injection handling? `rge/safety/prompt_injection.py` should own deterministic pattern/policy helpers and constants; `rge/modules/claim_validator.py` should apply them at the candidate-claim boundary before accepted-graph writes; `claim_extractor.py` should select the deterministic prompt-injection fixture in mock mode.
- Where should handling happen? Multiple layers: source text remains untrusted at ingestion; candidate extraction must not turn injected instructions into accepted claims; claim validation should reject instruction-like candidate claims; public export must continue blocking injected text; safety audit should surface policy/fixture evidence after GT24.
- What must Golden Test 24 prove? Malicious instructions are ignored as instructions, source credibility does not change, claims are not deleted, private notes are not exported, only the actual research claim is accepted, injected instruction candidates are rejected or ignored with machine-readable reasons, and normal source text still passes.
- What machine-readable fields/reasons should appear? Use `unsafe_or_injected_content` for rejected injected instruction candidates. Include stable evidence such as rejected claim IDs/reasons where claims are persisted.
- What must not happen? Prompt-injection text must not become an accepted claim, relationship, theory candidate, public card, domain proposal, ontology proposal, improvement ticket instruction, or builder action. It must not alter source credibility, trigger deletes, export private notes, call Ollama, access shell/Git/network tools, or broaden public routes.
- Does the safety audit need GT24 fixture evidence after ticket-026? Yes. After ticket-026, `run_safety_audit("full")` should do more than policy-presence checking: it should include prompt-injection fixture/protection evidence without running Ollama or relying on generated noisy folders.

## Expected Ticket-026 Scope

The proposed scope is correct and should be implemented as one ticket only:

- Add deterministic prompt-injection fixture(s), either by adopting the existing `fixtures/sources/prompt_injection_source.txt` or adding the ticket-expected `fixtures/sources/prompt_injection_creativity_short.txt`.
- Add `fixtures/llm_outputs/claim_extraction_prompt_injection.json`.
- Extend `rge/safety/prompt_injection.py` with deterministic validators/patterns and the stable rejection reason.
- Apply prompt-injection checks in `claim_validator.py` so instruction-like candidates are rejected with `unsafe_or_injected_content`.
- Update `claim_extractor.py` mock fixture selection for the prompt-injection fixture.
- Add `tests/golden/test_24_prompt_injection.py`.
- Add targeted tests proving malicious source instructions are rejected or safely quarantined and normal source claims still pass.
- Consider extending `run_safety_audit()` to report prompt-injection fixture protection status after GT24.

Non-goals remain correct:

- No Ollama.
- No LangGraph.
- No live web discovery.
- No public write routes.
- No public export of injected text.
- No broad rewrite of the pipeline.
- No implementation of multiple tickets.

## Safety Boundaries

All source text and fixtures are untrusted data. The prompt-injection fixture must not be interpreted as instructions by the builder or by RGE runtime components. Qwen/Ollama remains a candidate JSON proposer only; Python validators decide accepted/rejected records. Golden tests must continue forcing `RGE_LLM_MODE=mock`.

## Blocking Issues

| ID | Issue | Impact | Resolution |
|---|---|---|---|
| B1 | Working tree is dirty with generated export artifacts | Violates the user's requirement to continue only if the repo is clean; risks accidental inclusion in ticket-026 branch/commit | Clean, stash, or otherwise resolve generated artifacts under human direction before running `/rge-run-next-ticket` |

## Recommendation

Recommendation: do not proceed; resolve blockers first.

Once the generated artifacts are resolved and the working tree is clean, ticket-026 is the correct next smallest safe ticket.
