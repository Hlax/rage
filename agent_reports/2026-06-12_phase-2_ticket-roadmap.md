---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Phase 2 Ticket Roadmap (proposed)

- Source: `agent_reports/2026-06-12_pre-phase-2_principal-audit.md` (ticket-033 principal audit)
- Date: 2026-06-12
- Status: **planning document only.** No ticket JSON files were created. The next implementation agent should seed `tickets/ticket-034.json` (and successors) from this roadmap via the normal queue workflow, one ticket at a time.

## Ordering rationale

Hygiene → docs → presentation → live runtime → loop validation → deployment. Each ticket is the smallest mergeable unit; none broadens the public data surface without its own audit.

---

## ticket-034 — Fixture-run artifact hygiene (must-fix)

- **Problem:** `research run --fixture-mode` dirties the working tree: rewrites committed `apps/public-site/public/data/build_info.json` and `public_cards.json` with non-deterministic key ordering and live timestamps, drifts `source_count` (committed `1` vs regenerated `3`), and drops untracked `data/` and `tickets/improvement_ticket_latest.json` into the repo.
- **Why it matters:** every demo run risks committing unreviewed export mutations to main; violates the build loop clean-tree precondition; `tickets/` pollution risks queue confusion.
- **Affected files/modules:** `rge/modules/card_exporter.py` (stable key order via canonical serialization, fixture-mode deterministic timestamps), `rge/cli.py` (default improvement-ticket artifact path → `data/tickets/` or similar), `.gitignore` (`data/`, generated ticket artifact), committed snapshots (one deliberate refresh commit reconciling `source_count`), GT26/GT11 assertions for determinism.
- **Suggested title:** "Make fixture-mode run repo-clean and export serialization deterministic"
- **Acceptance criteria:** running the fixture-mode command twice from a clean tree leaves `git status --short` empty; committed snapshots match regenerated output byte-for-byte; improvement ticket artifact no longer lands in `tickets/`; all golden tests pass.
- **Test plan:** `pytest tests/golden`; manual: fixture run + `git status --short` empty; `python -m rge.modules.safety_auditor --audit full`.
- **Risk:** low. **Pre-ticket audit:** not required (covered by ticket-033 audit).

## ticket-035 — README and operator setup hardening (must-fix)

- **Problem:** root `README.md` still describes Phase 0 scaffold and claims pipeline behavior is unimplemented; no fixture-run quickstart; mock-vs-live limits, artifact paths, and public-site deployment are undocumented at the entry point.
- **Why it matters:** the repo cannot be handed to a new engineer or shown externally without misrepresenting itself.
- **Affected files:** `README.md` (status, quickstart, mock-vs-live, artifact map, verification commands, safety boundary pointers, link to `docs/agents/12_RUNTIME_CONFIG.md`), `.env.example` (consider `RGE_LLM_MODE=mock` default until live inference ships), small historical-note cleanup in `12_RUNTIME_CONFIG.md`.
- **Suggested title:** "Refresh README for Phase 1 reality and operator quickstart"
- **Acceptance criteria:** README accurately states what is real, mock-only, and out of scope; a new operator can run the fixture MVP, tests, safety audit, and site build from README alone; no stale Phase 0 claims remain.
- **Test plan:** `pytest tests/golden` (no code changes expected); follow README quickstart verbatim on a clean checkout.
- **Risk:** low. **Pre-ticket audit:** not required.

## ticket-036 — Public-site product polish (presentation-only)

- **Problem:** UI exposes raw enums (`cluster_card`, `empirical`, `standard`) and raw ISO timestamps; no `/about` (methodology/trust) page; default unstyled 404; no empty state; no favicon/meta; inline styles only.
- **Why it matters:** the site reads as a test artifact; an `/about` page is the biggest external-credibility lever and `GET /about` is already in `ALLOWED_PUBLIC_ROUTES`.
- **Affected files:** `apps/public-site/app/*` (page/layout/card/concept), new `app/about/page.tsx`, `app/not-found.tsx`, optional shared style module; `lib/publicCards.ts` display helpers. **No export schema changes; no new data fields.**
- **Suggested title:** "Public-site presentation polish and about page (no data surface changes)"
- **Acceptance criteria:** humanized labels and dates; `/about` explains the engine, fixture provenance, confidence semantics, and safety boundaries; styled 404 and zero-card empty state; site builds statically; GT12/GT25 pass unchanged; safety audit passes; no new fields read from JSON.
- **Test plan:** `pytest tests/golden`; `cd apps/public-site && npm run build`; `python -m rge.modules.safety_auditor --audit full`; manual render review.
- **Risk:** low-medium (public-site rule). **Pre-ticket audit:** required by the audit-gate table; ticket-033's UI section satisfies it if scope stays presentation-only.

## ticket-037 — Ollama live structured-task adapter (design + implement behind opt-in)

- **Problem:** live inference is impossible: pipeline modules force `RGE_LLM_MODE=mock` and `OllamaModelClient` structured tasks raise `OllamaNotAvailableInPhase0`.
- **Why it matters:** the core product rule ("Qwen/Ollama proposes candidate JSON; Python validates and writes") has never run live; Phase 2 intelligence work needs a real model path.
- **Affected files:** `rge/llm/ollama_client.py` (implement structured tasks: prompt template + JSON parse + Pydantic validation), `rge/modules/{claim_extractor,concept_linker,relationship_builder,contradiction_detector}.py` (replace hard-forced mock with fail-closed opt-in, e.g. require `RGE_ALLOW_LIVE_LLM=1` and `RGE_LLM_MODE=ollama`), `rge/config.py`, `docs/agents/12_RUNTIME_CONFIG.md`, `.env.smoke.example`.
- **Suggested title:** "Implement Ollama structured tasks behind explicit live-mode opt-in"
- **Acceptance criteria:** golden tests remain mock-only and pass unchanged with no Ollama running; default behavior without the opt-in env is identical to today (fail closed); with Ollama running and opt-in set, `extract-claims` produces validated candidates through the existing Python validation path; no model output writes directly to accepted tables.
- **Test plan:** `pytest tests/golden` (no live deps); new unit tests for prompt/parse with canned responses; manual live smoke documented in report.
- **Risk:** medium-high. **Pre-ticket audit:** **required** (live Ollama rule in the audit-gate table).

## ticket-038 — Live smoke-test gating and model-health CLI

- **Problem:** no safe harness exists for live runs: no pytest marker isolation, no `model-health` command, and live runs would write to the same default export dirs as golden runs.
- **Why it matters:** prevents live nondeterminism from ever touching golden fixtures or committed public snapshots.
- **Affected files:** `pyproject.toml`/pytest config (`live_smoke` marker excluded by default), new `tests/smoke/` (env-gated, skipped without opt-in), `rge/cli.py` (`model-health` surfacing `health_check()`; live-mode default `--export-dir` to scratch path unless explicit publish flag), docs.
- **Suggested title:** "Gate live smoke tests behind env opt-in and add model-health command"
- **Acceptance criteria:** `pytest` and `pytest tests/golden` collect zero live tests by default; `research model-health` reports reachability without raising; live-mode runs cannot write `apps/public-site/public/data/` without an explicit flag; safety audit unchanged.
- **Test plan:** `pytest tests/golden`; `pytest -m live_smoke` skips cleanly without env; manual health check.
- **Risk:** medium. **Pre-ticket audit:** folded into ticket-037's audit.

## ticket-039 — Self-improvement loop validation

- **Problem:** improvement tickets are generated and validated for builder consumption (GT20/GT21), but no ticket has ever round-tripped: generated ticket → promoted into `tickets/` queue → implemented → verified. The loop is plumbed, not proven.
- **Why it matters:** the self-improvement loop is the system's core long-term claim; promotion must have an explicit human/audit review step so generated tickets cannot self-insert into the queue.
- **Affected files:** `rge/modules/ticket_writer.py` (promotion helper or documented manual procedure), `tickets/TICKET_QUEUE.md` conventions, possibly a `research promote-ticket` CLI with explicit confirmation; golden test for the promotion format.
- **Suggested title:** "Validate improvement-ticket round-trip into the builder queue with review gate"
- **Acceptance criteria:** a generated improvement ticket can be promoted to a valid queue ticket JSON via an explicit reviewed step; promotion never happens implicitly during runs; format validated by GT21 rules; documented in AGENTS workflow.
- **Test plan:** `pytest tests/golden`; manual round-trip of one generated ticket.
- **Risk:** medium. **Pre-ticket audit:** recommended (agent-loop semantics).

## ticket-040 — Merge-gate enforcement: CI workflow + principal-audit command

- **Problem:** the GT22 merge gate has no mechanical enforcement (no CI), and `/rge-principal-audit` is referenced by handoffs but missing from `.cursor/commands/`.
- **Why it matters:** the inductive safety of main depends on every agent honoring the protocol; CI converts convention to guarantee.
- **Affected files:** `.github/workflows/golden-gate.yml` (mock-mode `pytest tests/golden` + safety audit + public-site build), `.cursor/commands/rge-principal-audit.md` (codify the checkpoint this audit performed).
- **Suggested title:** "Add CI golden gate workflow and rge-principal-audit command doc"
- **Acceptance criteria:** CI runs on push/PR with `RGE_LLM_MODE=mock`, no Ollama, and passes on main; command doc reproduces the ticket-033 audit procedure.
- **Test plan:** CI run green on a no-op branch; `pytest tests/golden` locally.
- **Risk:** low. **Pre-ticket audit:** not required.

## ticket-041 — Deployment-readiness pass (public site)

- **Problem:** the site is a static export but nothing documents how to deploy it, what the pre-deploy checklist is, or how snapshot refreshes reach production safely.
- **Why it matters:** "public-facing" currently means localhost; external sharing needs a deploy path with the safety audit as a hard pre-deploy gate.
- **Affected files:** docs (deploy guide: any static host serving `apps/public-site/out/`), optional `package.json` script, deploy checklist including `safety_auditor --audit full` and snapshot review; no new routes.
- **Suggested title:** "Public-site deployment readiness: static hosting docs and pre-deploy safety checklist"
- **Acceptance criteria:** an operator can deploy the static export following docs alone; checklist requires passing safety audit + reviewed snapshot diff before publish; no server-side surface added.
- **Test plan:** `npm run build`; dry-run deploy to a local static server; safety audit.
- **Risk:** low (docs-only) — becomes medium if site config changes, which would then require a pre-ticket audit.

## ticket-042 (optional, later) — Safety gate expansion

- **Problem:** safety auditor scans only the public-site data dir (not `data/exports/`); route/model-tool checks are regex-based; GT24/25/26 checks are existence-only.
- **Why it matters:** keeps the audit honest as surfaces grow in Phase 2 (live runs, more export targets).
- **Suggested title:** "Extend safety auditor to data/exports and tighten evidence checks"
- **Acceptance criteria:** `data/exports/*.json` validated when present; full audit still passes; new checks covered in GT23.
- **Risk:** low. **Pre-ticket audit:** not required.

---

## Post-Phase-2 (not ticketed)

- Cloud provider adapter (OpenAI/OpenRouter) behind the existing `ModelClient` boundary, with key handling per `12_RUNTIME_CONFIG.md` and budget counters.
- Embeddings (`RGE_EMBEDDING_*` are currently unused placeholders).
- Concept graph visualization on the public site (requires export-policy audit).
- `research verify` implementation; export snapshot versioning/history.

## Recommended sequence

```txt
034 -> 035 -> 036 -> (audit) -> 037 -> 038 -> 039 -> 040 -> 041
```

040 (CI) may be pulled earlier at any point; it is independent and low-risk.
