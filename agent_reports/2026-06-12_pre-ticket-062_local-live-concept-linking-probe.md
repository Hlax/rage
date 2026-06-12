---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-062 Local Live Concept-Linking Probe Audit

- Audit type: focused pre-ticket readiness (live Ollama milestone)
- Date: 2026-06-12
- Scope: read-only design audit. No implementation. No ticket seeding.
- Baseline HEAD (audit start): `63ce729` → cleaned to `6783037` before this report commit
- Prior checkpoint: `agent_reports/2026-06-12_principal-audit-post-ticket-061.md`

## 1. Executive verdict

**GO — seed ticket-062**

Ticket-061 live claim extraction is repeatable (`accepted_count: 1` on two consecutive
runs). Concept linking can safely mirror the ticket-060/061 report-only probe pattern
using **probe-local claim IDs** and a **controlled default input** (embedded accepted
claim fixture), with optional `--from-report` for saved probe artifacts. Prompt
calibration for Qwen is likely required (same class of gap as pre-ticket-061); that is
in-scope for ticket-062, not a pre-audit blocker.

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` | `git checkout main` |
| Working tree (after cleanup) | **clean** | recovery addendum + principal audit committed (`73bfd4f`, `6783037`) |
| Local HEAD | `6783037` | `git rev-parse HEAD` (pre–pre-ticket-062 report commit) |
| `origin/main` (before push) | `63ce729` | push pending for doc commits |
| Golden Gate at prior tip | **success** | run **27436453068** at `63ce729` |
| Principal audit cadence | **satisfied** | `agent_reports/2026-06-12_principal-audit-post-ticket-061.md` on main |
| Pending improvement drafts | **none** | operator loop `draft_count: 0` |
| ticket-059 OpenAI | **proposed / deferred** | placeholder JSON only; no adapter code |
| `data/` artifacts | gitignored | `data/reports/live_probes/` local only; not committed |

## 3. Ticket-061 dependency status

| Field | Value |
| ----- | ----- |
| Documented artifact (ticket-061) | `data/reports/live_probes/probe_extract_claims_2026-06-12T185110Z.json` |
| Recovery re-run artifact | `data/reports/live_probes/probe_extract_claims_2026-06-12T191423Z.json` |
| Pre-audit repeatability run | `data/reports/live_probes/probe_extract_claims_2026-06-12T192431Z.json` |
| Repeatability checked | **yes** — Ollama/qwen2.5:7b available |
| Repeatability result | `accepted_count: 1`, `rejected_count: 1`, `db_writes: false` (consistent across runs) |
| Accepted claim shape | scoped empirical claim with SPO fields; quality/increase claim accepts |
| Live probe accepted rows | **no persisted `id`** — only `source_id` / `chunk_id` probe constants |

**Ticket-062 input recommendation:**

| Priority | Input source | Rationale |
| -------- | ------------ | --------- |
| **Default** | Controlled embedded accepted-claim fixture in probe module | Deterministic acceptance gate; no upstream LLM variability |
| **Optional** | `--from-report <path>` loading `accepted[]` from `probe_extract_claims_*.json` | Reuses real ticket-061 output; assign `claim_live_probe_*` IDs when missing |
| **Optional (non-default)** | `--chain-extract` two-step extract→link in one CLI invocation | Operator convenience only; document variability; do not use as sole CI/live gate |

Do **not** require inline live claim extraction as the only input path.

## 4. Current concept-linking support

| Area | Current behavior | Gap | Risk |
| ---- | ---------------- | --- | ---- |
| `link_concepts_for_source` | Loads accepted claims from DB; ensures ontology rows; calls model; validates; **persists** `claim_concepts` | Requires SQLite state; writes graph records | **High** if reused for probe — must not use in ticket-062 |
| `link_claim_concepts` | Calls `client.link_concepts`; overwrites all link `claim_id` to diversity claim or first claim | Heuristic OK for single-claim probe; misleading if multi-claim probe later | Low for v1 single-claim probe |
| `validate_concept_links` | Requires `claim_id`, `concept_label`, `confidence`; batch needs ≥2 **specific** labels (excludes generic-only `ai`/`creativity`) | No ontology label membership check; no `validation_diagnostic` helper | Medium — live rejects may be opaque without diagnostics |
| `OllamaModelClient._concept_linking_prompt` | Minimal JSON schema; embeds claims JSON only | No ontology label list, no weak-mapping rules, no examples (unlike calibrated claim prompt) | **High** — likely 0 accepts without calibration (ticket-061 pattern) |
| `CandidateConceptLink_v0_1` | `claim_id`, `concept_label`, `role`, `confidence`, `domain_metadata` | Schema sufficient for probe reports | Low |
| `load_domain_pack_concepts` | Reads creativity ontology + supplemental labels | Not passed to Ollama prompt today | Medium — probe should inject allowed labels for calibration |
| `research link-concepts` CLI | DB-backed persistence path | No report-only probe sibling | Expected gap — ticket-062 adds `probe-link-concepts` |
| `live_probe.py` | `run_probe_extract_claims` only | No concept-link probe | Expected gap |
| Golden GT05 | Mock fixture links diversity claim → 5 concepts | Proves validation+persistence; mock-only | No live coverage |
| `live_smoke` / CI | 2 tests deselected by default | New smoke test must stay behind marker | Low if convention followed |

## 5. Recommended probe design

### CLI command

`python -m rge.cli probe-link-concepts`

Flags (proposed):

| Flag | Purpose |
| ---- | ------- |
| `--domain creativity` | Domain pack (default creativity) |
| `--from-report PATH` | Load accepted claims from prior `probe_extract_claims_*.json` |
| `--chain-extract` | Optional: run `probe-extract-claims` first, use its `accepted` rows |
| `--fixture-claim PATH` | Optional JSON file overriding default embedded claim |

### Input source (default)

Embedded dict matching ticket-061 **accepted** quality claim, with probe-local ID:

```json
{
  "id": "claim_live_probe_link_001",
  "claim_text": "AI-assisted brainstorming increased average idea quality in short-form writing tasks.",
  "subject": "AI-assisted brainstorming",
  "predicate": "increased",
  "object": "average idea quality",
  "domain": "creativity"
}
```

Include `source_id` / `chunk_id` metadata in report for traceability (probe constants from `live_probe.py`).

### Live env

Same as ticket-061:

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
python -m rge.cli probe-link-concepts
```

### Output artifact path

`data/reports/live_probes/probe_link_concepts_<UTC-stamp>.json` (under gitignored `data/`)

### Report schema (extends ticket-061 pattern)

| Field | Required |
| ----- | -------- |
| `report_type` | `live_probe_report` |
| `command` | `probe-link-concepts` |
| `probe` | `concept_linking` |
| `status`, `created_at` | yes |
| `domain_pack`, `effective_llm_mode`, `provider`, `model`, `base_url`, `schema_version` | yes |
| `input_claims` | probe-local claim dicts (with IDs) |
| `input_source` | `embedded_fixture` \| `from_report` \| `chain_extract` |
| `from_report_path` | when applicable |
| `ontology_labels_exposed` | list of allowed labels sent to model (audit trail) |
| `accepted_count`, `rejected_count` | yes |
| `accepted`, `rejected` | link candidates post-validation |
| `rejected[].validation_diagnostic` | yes (new helper in `concept_linker.py`) |
| `db_writes` | **false** |
| `default_db_path` | informational |
| `report_path` | written JSON path |

### Failure conditions

| Condition | Behavior |
| --------- | -------- |
| Missing live opt-in / wrong mode | exit 2 (`LiveProbeGateError`) |
| Ollama unreachable / model missing | exit 2 |
| Zero parseable link candidates | exit 1 (`LiveProbeError`) |
| All links rejected | report written with `accepted_count: 0`; exit 0 if report succeeds (mirror ticket-061) |

Live acceptance target: **`accepted_count >= 1`** with ≥2 specific concept labels per `validate_concept_links`.

### What must not happen

- No writes to default `data/db/creative_research.sqlite`
- No `ClaimConceptRepository.insert` / concept seeding in default DB
- No `export-public` / committed public JSON changes
- No OpenAI/OpenRouter or API keys
- No broad `research run` live discovery
- No weakening `validate_concept_links` / GT05 rules to force passes
- No committing `data/reports/` artifacts

## 6. Safety controls

| Control | Status |
| ------- | ------ |
| No default DB writes | **Confirmed** — design is report-only; `db_writes: false` in report |
| No public export | **Confirmed** — probe module has no exporter calls |
| No cloud/API keys | **Confirmed** — Ollama local only; ticket-059 deferred |
| No model shell/Git/file mutation | **Confirmed** — structured JSON call only |
| No direct accepted graph writes | **Confirmed** — bypass `link_concepts_for_source` persistence |
| Python validation authoritative | **Confirmed** — `validate_concept_links` gates acceptance; model proposes only |
| Probe-local claim IDs sufficient | **Confirmed** — validator checks `claim_id` presence, not DB FK |
| Concept linking without prior DB | **Confirmed** — `link_claim_concepts` + `validate_concept_links` need only in-memory claim dicts |
| Raw prompt/source leakage | **Mitigated** — concept prompt receives claim dicts only (no full chunk text required); ontology labels are curated pack data; report must not include raw source chunk unless operator passes `--chain-extract` (then include fixture path metadata only) |
| Live opt-in only | **Confirmed** — reuse `assert_live_probe_env` pattern |
| CI/golden mock-only | **Confirmed** — unit tests mock HTTP/client; any smoke test uses `live_smoke` marker |

**Scratch DB vs report-only:** report-only artifacts are **safer** and consistent with ticket-060/061. Do not introduce scratch SQLite for ticket-062.

## 7. Proposed ticket-062

### Title

Safe local live concept-linking probe CLI

### Problem

Ticket-061 proved live Qwen claim extraction with report-only probes. The next
structured-task gap is **concept linking**: `link-concepts` today requires persisted
claims in SQLite and writes `claim_concepts`. Operators need a no-DB live probe to
validate Ollama concept linking before any persistence work.

### Scope

- Add `probe-link-concepts` CLI and `run_probe_link_concepts` in `live_probe.py` (or focused helper)
- Default embedded accepted-claim fixture; optional `--from-report` / `--chain-extract`
- Calibrate `OllamaModelClient._concept_linking_prompt` (ontology labels, weak-mapping rules, examples)
- Add `concept_link_rejection_diagnostic()` for rejected rows
- Mock-only unit tests + optional `live_smoke` test (env-gated)
- Update `docs/agents/12_RUNTIME_CONFIG.md`

### Expected files

- `rge/modules/live_probe.py`
- `rge/modules/concept_linker.py`
- `rge/llm/ollama_client.py`
- `rge/cli.py`
- `fixtures/claims/live_probe_concept_link_quality_claim.json` (or equivalent)
- `tests/unit/test_live_probe_link_concepts_cli.py`
- `tests/unit/test_concept_link_rejection_diagnostics.py`
- `tests/unit/test_ollama_concept_link_prompt.py`
- `docs/agents/12_RUNTIME_CONFIG.md`
- `tickets/ticket-062.json` (seed **after human approval** of this audit)
- `agent_reports/2026-06-12_phase-2_ticket-062_*.md` (implementation report)

### Acceptance criteria

- Live probe with qwen2.5:7b yields `accepted_count >= 1` on default embedded claim input
- `db_writes: false`; report under `data/reports/live_probes/`
- `validate_concept_links` unchanged; GT05 still passes mock-only
- Rejected rows include `validation_diagnostic`
- Mock/default pytest and CI remain green without Ollama

### Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_live_probe_link_concepts_cli.py -q
python -m pytest tests/unit/test_concept_link_rejection_diagnostics.py -q
python -m pytest -q
python -m rge.cli verify --skip-site
```

Manual live (operator):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli probe-link-concepts
```

### Safety considerations

- Reuse live opt-in gates from `live_probe.py`
- Never call `link_concepts_for_source` from probe path
- Do not pass full untrusted source text to concept prompt unless `--chain-extract` (even then, prefer claim fields only)
- Keep live smoke excluded from default pytest/CI

### Non-goals

- DB persistence of concepts or links
- Public export changes
- OpenAI/OpenRouter adapters
- Relationship/contradiction live probes
- Weakening `weak_concept_mapping` validation
- Ontology YAML edits (use existing labels in prompt)

### Rollback plan

Revert CLI, probe helper, prompt calibration, and tests. No schema migrations.

### Risk level

low-medium

### Pre-ticket audit required?

**Satisfied by this report.** Re-run `python -m rge.modules.principal_audit_gate --next-ticket ticket-062` after seeding.

## 8. Final recommendation

**Seed ticket-062 as drafted** (after human approval of this audit).

Sequence:

1. Human reviews this audit.
2. Seed `tickets/ticket-062.json` and queue row (implementation agent).
3. Implement on branch `phase-2/ticket-062-safe-local-live-concept-linking-probe`.
4. Keep **ticket-059 OpenAI deferred** until claim + concept live probes are stable.

Do **not** narrow/re-audit unless live concept probe repeatedly returns zero candidates **after** prompt calibration effort inside ticket-062.

---

*Audit complete. No ticket-062 implementation in this invocation.*
