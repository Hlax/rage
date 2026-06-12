---
template_id: agent_report
template_version: 1.0.0
status: current
---

# Live Probe Evidence Review

- Date: 2026-06-12
- Principal reviewer: docs/release steward + local research-agent evaluator
- Runbook commit: `0dc709c`
- Baseline: tickets 060–065 complete on `main`; operator runbook committed this session

## 1. Executive verdict

**READY_FOR_MULTI_FIXTURE_REPEATABILITY_TICKET**

The local four-stage spine meets documented acceptance floors on the default
calibration fixture and repeated cleanly today. Stage 4 contradiction detection
still depends on hybrid overlay (not pure upstream chain). Before scratch DB
persistence or synthesis tickets, prove the worker is not overfit to a single
controlled source/fixture pair.

## 2. Release state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Runbook committed | **pass** | `0dc709c` — `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` + cross-links |
| Working tree clean (no probe artifacts staged) | **pass** | `git status --short` empty after commit |
| Golden Gate CI | **pass** | run **27444777789** — success at `0dc709c` |
| Mock pytest | **pass** | 265 passed, 6 deselected |
| Safety audit | **pass** | `status: pass`, no blocked reasons |
| `python -m rge.cli verify --skip-site` | **pass** | golden + full pytest + safety audit |
| Ticket queue unchanged this session | **pass** | docs-only commit; no `tickets/` diff |
| Live probe artifacts gitignored | **pass** | `data/` in `.gitignore`; reports under `data/reports/live_probes/` |

## 3. Live probe chain status

| Stage | Latest command/artifact | Accepted | Rejected | Status |
| ----- | ----------------------- | -------: | -------: | ------ |
| extract claims | `probe-extract-claims` (ticket-061; fixture `live_probe_claim_calibration_short.txt`) | 1 | 1 | **ok** — scope verbatim gate rejects diversity claim |
| link concepts | `probe-link-concepts` (ticket-062; fixture `live_probe_concept_link_quality_claim.json`) | 3 | 0 | **ok** |
| draft relationships | `probe-draft-relationships` (ticket-063; bundle `live_probe_relationship_quality_bundle.json`) | 1 | 0 | **ok** — `AI assistance` supports `brainstorming` |
| detect contradictions | `probe-detect-contradictions` (ticket-064; bundle `live_probe_contradiction_quality_bundle.json`) | 1 | 0 | **ok** — GT07-shaped overlay |
| mini-run default | `probe-mini-run` → `data/reports/live_probes/probe_mini_run_2026-06-12T214626Z.json` | stages 1–4: 1/1, 2/0, 1/0, 1/0 | | **ok** — `contradiction_input_mode: hybrid_overlay`, `status: ok`, `db_writes: false` |
| mini-run strict-chain | `probe-mini-run --strict-chain` → `data/reports/live_probes/probe_mini_run_2026-06-12T214703Z.json` | stages 1–3: 1/1, 2/0, 1/0; stage 4 skipped | | **partial** — `contradiction_input_mode: skipped_strict_chain_insufficient_inputs`; upstream lacks `may_reduce`/`may_increase` tension |

**Stage floor check (today vs runbook / ticket-065):**

| Stage | Floor | Today default | Today strict | Met? |
| ----- | ----- | ------------- | ------------ | ---- |
| claim_extraction | ≥1 accepted | 1 | 1 | yes |
| concept_linking | ≥1 accepted | 2 | 2 | yes |
| relationship_drafting | ≥1 accepted | 1 | 1 | yes |
| contradiction_detection (default) | ≥1 accepted | 1 (hybrid) | skipped | yes (default) / expected skip (strict) |

Prior ticket-065 live run (same fixture) matched: 1/1, 2/0, 1/0, 1/0 hybrid; strict partial with stage 4 skip.

## 4. Research readiness assessment

**What can the local agent do now?**

- Run report-only live structured tasks via Ollama (`qwen2.5:7b`) with fail-closed opt-in gates.
- Extract scoped claims, link concepts, draft relationships, and detect contradictions on controlled fixtures.
- Chain stages 1–3 live end-to-end via `probe-mini-run`; stage 4 via hybrid overlay when chain lacks GT07 tension.
- Emit gitignored JSON reports with per-stage acceptance counts, validation diagnostics, and safety flags.

**What is still artificial/fixture-bound?**

- Default mini-run source is a single calibration short text (`live_probe_claim_calibration_short.txt`).
- Stages 2–4 individual probes use embedded quality fixtures/bundles, not only upstream chain output.
- Stage 4 default mode overlays `live_probe_contradiction_quality_bundle.json` — contradiction proof is not yet chain-native.
- `--strict-chain` cannot reach `contradiction_input_mode: chain` today; only `supports` edges emerge from stage 3.

**What is still report-only?**

- All live probes and mini-run outputs; no import into any SQLite graph.
- Improvement proposals remain human/principal gated; no live `generate-improvement-tickets` or `draft_ticket`.

**What is not yet persisted?**

- Accepted claims, concept links, relationships, and contradictions from live runs.
- Cross-run evidence memory or accumulated research graph from local Qwen sessions.

**What would make this feel like real research?**

- Repeat mini-run across multiple controlled fixtures with stable floors (not one calibration source).
- Optional scratch DB import of reviewed accepted candidates (isolated from default DB).
- A two-source or richer chain fixture that reaches native contradiction inputs without overlay.
- Deterministic or local summarization across accumulated probe reports (interpretation artifact, not tickets).

## 5. Evidence quality observations

**Accepted claims:** Scoped and useful when Qwen embeds scope verbatim in `claim_text`. The diversity-reduction claim is consistently rejected with a clear `overgeneralized_scope` diagnostic — validation is doing real work, not rubber-stamping.

**Concept links:** Meaningful on the quality claim fixture (brainstorming, AI assistance, ideation roles). Mini-run produces two links from the single accepted extraction claim — plausible and validator-clean.

**Relationships:** Meaningful `supports` edge (`AI assistance` → `brainstorming`) with scope and supporting claim id. Chain does not yet produce opposing predicates needed for native contradiction.

**Contradiction / tension detection:** Real structured output on GT07-shaped bundle, but **overlay-assisted** in default mini-run. Hybrid mode correctly documents `overlay_bundle_path`. Strict-chain skip is expected, not a regression — it exposes a spine gap.

**Qwen brittleness:** Scope phrasing in claim_text (verbatim scope embedding); tendency to produce `supports` rather than `may_reduce`/`may_increase` pairs from single-source chain; occasional rejected candidates on otherwise valid semantic content.

**Python validation:** Authoritative throughout — rejections carry actionable `validation_diagnostic` strings; floors are operator signals, not weakened validators.

## 6. Safety status

| Control | Status |
| ------- | ------ |
| No default DB writes | **confirmed** — all reports `db_writes: false`; `git status` clean |
| No public export | **confirmed** — `public_export: false` on mini-run reports |
| No cloud/API keys | **confirmed** — `cloud_calls: false`; ticket-059 OpenAI deferred |
| No committed live artifacts | **confirmed** — `data/` gitignored; only runbook docs committed |
| No model shell/Git/file mutation | **confirmed** — probes are read-fixture / write-report only |
| Qwen has no ticket authority | **confirmed** — runbook §Core rule and §Improvement ticket path; no queue edits |
| CI/golden remain mock-only | **confirmed** — 265 pytest + 140 golden in mock mode; live_smoke deselected in CI |

## 7. Next ticket recommendation

**Recommend: A — `ticket-066 — Multi-fixture local live mini-run repeatability`**

Run `probe-mini-run` (and optionally individual stage probes) across 3–5 controlled fixtures beyond `live_probe_claim_calibration_short.txt`. Remain report-only. Record per-fixture accepted/rejected counts and whether hybrid overlay is still required for stage 4.

**Rationale:**

- Today's repeat run confirms stability on the **same** fixture (matches ticket-065 floors).
- Scratch DB persistence (option B) would accumulate graph state from a spine proven on one calibration path and hybrid contradiction overlay — premature before generalization.
- Synthesis (option C) is more valuable after multiple comparable reports exist.
- Strict-chain gap is documented; multi-fixture work may inform whether a chain-native contradiction fixture is the following ticket vs overlay remaining acceptable for operator proof.

**Not seeding ticket-066** until human approves this recommendation.

**OpenAI / ticket-059:** remains **deferred** until explicit operator approval and a focused pre-ticket audit for cloud adapter work.
