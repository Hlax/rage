---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-064 Local Live Contradiction-Detection Probe Audit

- Audit type: focused pre-ticket readiness (live Ollama milestone)
- Date: 2026-06-12
- Scope: read-only design audit. No contradiction probe implementation in this invocation.
- Baseline HEAD: `15206942f98ac63e2997f8e2c81bc71570da723b`
- Prior probes: ticket-061 (claim extraction), ticket-062 (concept linking), ticket-063 (relationship drafting)
- Hygiene completed this pass: `live_smoke` extended for `probe-link-concepts` and `probe-draft-relationships`

## 1. Executive verdict

**GO — seed ticket-064**

Ticket-063 live relationship drafting produced one accepted probe-local edge
(`AI assistance` supports `ideation`, scope `short-form writing tasks`). Contradiction
detection can mirror the ticket-060–063 report-only probe pattern using a **committed
embedded contradiction bundle** (qualifying source claim + opposing domain claim +
base/new relationship dicts with probe-local ids). Prompt calibration for Qwen is
likely required (minimal Ollama contradiction prompt today); that is in-scope for
ticket-064, not a pre-audit blocker. No DB or export surface changes are required.

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` at audit start | `git checkout main` |
| Working tree | clean at audit start | `git status --short` empty |
| Local HEAD | `1520694` | `git rev-parse HEAD` |
| Latest Golden Gate | **success** | run **27439892066** at `1520694` |
| Golden Gate URL | https://github.com/Hlax/rage/actions/runs/27439892066 | `gh run view` |
| Principal audit cadence | **satisfied** | 2 done tickets since post-061 (`ticket-062`, `ticket-063`) |
| `principal_audit_gate --next-ticket ticket-064` | **satisfied** | `implementation_gate: not_applicable` (ticket JSON absent) |
| ticket-059 OpenAI | **proposed / deferred** | placeholder only |
| `live_smoke` coverage | **extended** | extract + link + relationship smoke tests |

## 3. Ticket-063 dependency status

| Field | Value |
| ----- | ----- |
| Documented artifact | `data/reports/live_probes/probe_draft_relationships_2026-06-12T195943Z.json` |
| Local artifact | gitignored under `data/`; may exist on operator machine only |
| Live result (ticket-063) | `accepted_count: 1`, `rejected_count: 0`, `db_writes: false` |
| Accepted relationship | `AI assistance` / `supports` / `ideation`, scope `short-form writing tasks` |
| Default bundle | `fixtures/probes/live_probe_relationship_quality_bundle.json` |

**Suitability for contradiction inputs:** **Partial — use GT07-shaped bundle, not ticket-063 quality bundle alone.**

`validate_contradiction_candidates` needs:

- `base_relationship` and `new_relationship` dicts with probe-local `id` fields
- `source_claims` containing a qualifying claim (GT07 fragment: `increased idea diversity`)
- `domain_claims` containing an opposing claim (GT07 fragment: `reduced semantic diversity`)
- `qualification_stance` in `{supports, contradicts, qualifies}` (fixture uses `qualifies`)
- `contradiction_classification` in `{qualifies, apparent_contradiction_metric_or_condition_difference}`

Ticket-063's quality bundle (idea quality / ideation) does **not** encode the
`may_reduce` vs `may_increase` diversity tension GT07 expects. Ticket-064 should
default to a **new committed contradiction bundle** aligned with GT07 mock fixtures,
not reuse the relationship quality bundle as sole input.

**Ticket-064 input recommendation:**

| Priority | Input source | Rationale |
| -------- | ------------ | --------- |
| **Default** | Committed bundle `fixtures/probes/live_probe_contradiction_quality_bundle.json` with `source_claims`, `domain_claims`, and `relationships` (base `may_reduce` / new `may_increase`) | Deterministic; mirrors GT07 without SQLite |
| **Optional** | `--from-report <probe_draft_relationships_*.json>` plus embedded opposing/base relationships | Reuses real ticket-063 output; still needs committed opposing claim + base edge |
| **Optional (non-default)** | `--chain-relationship` (extract → link → relationship → contradiction) | Operator convenience; upstream LLM variability; not sole acceptance gate |

Do **not** require a saved `data/reports/` artifact as the only default path.

## 4. Current contradiction support

| Area | Current behavior | Gap | Risk |
| ---- | ---------------- | --- | ---- |
| `detect_contradictions_for_source` | Loads claims + active relationships from DB; proposes; validates; **persists** evidence + metadata | Requires SQLite; writes qualification evidence | **High** if reused for probe |
| `propose_contradictions` | Calls `client.detect_contradictions`; mock fixture default `contradiction_detection_creativity_diversity.json` | No probe-local wrapper | Medium |
| `validate_contradiction_candidates` | Resolves qualifying/opposing claim ids by fragment fallback; checks stance/classification; requires base/new relationship dicts | No `contradiction_rejection_diagnostic` helper | Medium — opaque live rejects |
| `OllamaModelClient._contradiction_detection_prompt` | Minimal JSON schema; embeds claims + relationships | No classification rules, fragment hints, relationship triple emphasis | **High** — likely 0 accepts without calibration (061–063 pattern) |
| `research detect-contradictions` CLI | DB-backed persistence | No report-only probe sibling | Expected gap |
| `live_probe.py` | `probe-extract-claims`, `probe-link-concepts`, `probe-draft-relationships` | No contradiction probe | Expected gap |
| `tests/smoke/test_live_ollama_smoke.py` | Claim + link + relationship smoke (this pass) | No contradiction smoke yet | Low — add in ticket-064 after CLI exists |

## 5. Proposed contradiction bundle shape

Committed default (to create in ticket-064):

```json
{
  "source_claims": [
    {
      "id": "claim_live_probe_qualify_001",
      "claim_text": "AI-assisted brainstorming increased idea diversity when participants were instructed to generate multiple divergent directions.",
      "domain": "creativity",
      "source_id": "src_live_probe_contra_001"
    }
  ],
  "domain_claims": [
    { "...qualifying claim..." },
    {
      "id": "claim_live_probe_oppose_001",
      "claim_text": "AI writing assistance reduced semantic diversity in short-form creative tasks.",
      "domain": "creativity",
      "source_id": "src_live_probe_base_001"
    }
  ],
  "relationships": [
    {
      "id": "rel_live_probe_base_001",
      "subject_concept": "AI assistance",
      "predicate": "may_reduce",
      "object_concept": "semantic diversity",
      "status": "active"
    },
    {
      "id": "rel_live_probe_new_001",
      "subject_concept": "AI assistance",
      "predicate": "may_increase",
      "object_concept": "diversity",
      "status": "active"
    }
  ]
}
```

Mock fixture for unit tests: `fixtures/llm_outputs/contradiction_detection_live_probe_quality.json`
(structured like `contradiction_detection_creativity_diversity.json` with resolvable triples).

Live acceptance target: `accepted_count >= 1` with classification
`apparent_contradiction_metric_or_condition_difference` and stance `qualifies`.

## 6. Safety controls

| Control | Status |
| ------- | ------ |
| No default DB writes | **Confirmed** — report-only design |
| No public export | **Confirmed** — no exporter calls |
| No cloud/API keys | **Confirmed** — Ollama local only; ticket-059 deferred |
| No model shell/Git/file mutation | **Confirmed** — structured JSON call only |
| No direct accepted graph writes | **Confirmed** — bypass `detect_contradictions_for_source` |
| Python validation authoritative | **Confirmed** — `validate_contradiction_candidates` gates acceptance |
| Probe-local IDs sufficient | **Confirmed** — validator uses claim id membership + relationship dicts |
| No prior DB state required | **Confirmed** — in-memory claims + relationship dicts |
| Live opt-in only | **Confirmed** — reuse `assert_live_probe_env` |
| CI/golden mock-only | **Confirmed** — unit tests mock client; smoke stays env-gated |
| `live_smoke` excluded by default | **Confirmed** — 4 deselected in full pytest after link/relationship smoke added |

**Scratch DB vs report-only:** report-only artifacts remain **safer** and consistent
with tickets 060–063. Do not introduce scratch SQLite for ticket-064.

## 7. Proposed ticket-064

### Title

Safe local live contradiction-detection probe CLI

### Problem

Tickets 061–063 proved report-only live claim extraction, concept linking, and
relationship drafting. `detect-contradictions` still requires persisted claims,
relationships, and SQLite writes for qualification evidence. Operators need a
no-DB live probe for contradiction detection before any graph persistence.

### Scope

- Add `probe-detect-contradictions` CLI and `run_probe_detect_contradictions` in `live_probe.py`
- Default embedded contradiction bundle fixture (source + domain claims + base/new relationships)
- Optional `--from-report` / `--chain-relationship`
- Calibrate `OllamaModelClient._contradiction_detection_prompt` (classification, stance, triple matching, fragment hints)
- Add `contradiction_rejection_diagnostic()` for rejected rows
- Mock-only unit tests + optional `live_smoke` extension for contradiction probe
- Update `docs/agents/12_RUNTIME_CONFIG.md`

### Expected files

- `rge/modules/live_probe.py`
- `rge/modules/contradiction_detector.py`
- `rge/llm/ollama_client.py`
- `rge/cli.py`
- `fixtures/probes/live_probe_contradiction_quality_bundle.json`
- `fixtures/llm_outputs/contradiction_detection_live_probe_quality.json`
- `tests/unit/test_live_probe_detect_contradictions_cli.py`
- `tests/unit/test_contradiction_rejection_diagnostics.py`
- `tests/unit/test_ollama_contradiction_prompt.py`
- `tests/smoke/test_live_ollama_smoke.py` (contradiction smoke)
- `docs/agents/12_RUNTIME_CONFIG.md`
- `tickets/ticket-064.json`
- `agent_reports/2026-06-12_phase-2_ticket-064_*.md` (implementation report)

### Acceptance criteria

- Live probe with qwen2.5:7b yields `accepted_count >= 1` on default contradiction bundle
- `db_writes: false`; report under `data/reports/live_probes/`
- `validate_contradiction_candidates` unchanged; GT07 still passes mock-only
- Rejected rows include `validation_diagnostic`
- Mock/default pytest and CI remain green without Ollama

### Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_live_probe_detect_contradictions_cli.py -q
python -m pytest tests/unit/test_contradiction_rejection_diagnostics.py -q
python -m pytest -q
python -m rge.cli verify --skip-site
```

Manual live (operator):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli probe-detect-contradictions
```

### Safety considerations

- Reuse live opt-in gates from `live_probe.py`
- Never call `detect_contradictions_for_source` from probe path
- Pass claim dicts and relationship dicts only — no untrusted source chunk text
- Keep live smoke excluded from default pytest/CI

### Non-goals

- DB persistence of qualification evidence or relationship metadata
- Public export changes
- OpenAI/OpenRouter adapters (ticket-059 remains deferred)
- Weakening contradiction validation rules
- Ontology YAML edits

### Rollback plan

Revert CLI, probe helper, prompt calibration, fixtures, and tests. No schema migrations.

### Risk level

low-medium

### Pre-ticket audit required?

**Satisfied by this report.** Re-run `python -m rge.modules.principal_audit_gate --next-ticket ticket-064` after seeding.

## 8. Final recommendation

**Seed ticket-064 as drafted** (after human approval of this audit).

Sequence:

1. Human reviews this audit.
2. Seed `tickets/ticket-064.json` and queue row.
3. Implement on branch `phase-2/ticket-064-safe-local-live-contradiction-probe`.
4. Keep **ticket-059 OpenAI deferred** until the local probe chain (claim → link → relationship → contradiction) is stable.

`live_smoke` link + relationship coverage is **done** in this prep pass; add
contradiction smoke inside ticket-064 implementation.

Do **not** narrow/re-audit unless live contradiction probe returns zero candidates
**after** prompt calibration effort inside ticket-064.

---

*Audit complete. No ticket-064 contradiction probe implementation in this invocation.*
