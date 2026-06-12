---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-063 Local Live Relationship-Drafting Probe Audit

- Audit type: focused pre-ticket readiness (live Ollama milestone)
- Date: 2026-06-12
- Scope: read-only design audit. No implementation. No ticket seeding.
- Baseline HEAD: `58e89fbbebe86fb34e9100d3ccf0a75a832f0d9a`
- Prior probes: ticket-061 (claim extraction), ticket-062 (concept linking)

## 1. Executive verdict

**GO — seed ticket-063**

Ticket-062 live concept linking produced three accepted probe-local links on a
controlled quality claim (`brainstorming`, `AI assistance`, `ideation`). Relationship
drafting can mirror the ticket-060/062 report-only probe pattern using a **committed
embedded bundle fixture** (claim + accepted links + probe-local concept dicts).
Prompt calibration for Qwen is likely required (minimal Ollama relationship prompt
today); that is in-scope for ticket-063, not a pre-audit blocker. No DB or export
surface changes are required.

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` | `git checkout main` |
| Working tree | **clean** | `git status --short` empty |
| Local HEAD | `58e89fbbebe86fb34e9100d3ccf0a75a832f0d9a` | `git rev-parse HEAD` |
| `origin/main` | `58e89fb` (matches HEAD) | `git pull origin main` |
| Latest Golden Gate | **success** | run **27438923691** at `58e89fb` |
| Golden Gate URL | https://github.com/Hlax/rage/actions/runs/27438923691 | `gh run view` |
| Principal audit cadence | **satisfied** | 1 done ticket since post-061 (`ticket-062`) |
| `principal_audit_gate --next-ticket ticket-063` | **satisfied** | `implementation_gate: not_applicable` (ticket JSON absent) |
| ticket-059 OpenAI | **proposed / deferred** | placeholder only |
| Pending improvement drafts | not re-checked | post-062 operator loop expected clean |

## 3. Ticket-062 dependency status

| Field | Value |
| ----- | ----- |
| Documented artifact | `data/reports/live_probes/probe_link_concepts_2026-06-12T194039Z.json` |
| Local artifact | gitignored under `data/`; may exist on operator machine only |
| Live result (ticket-062) | `accepted_count: 3`, `rejected_count: 0`, `db_writes: false` |
| Input claim ID | `claim_live_probe_link_001` |
| Accepted concept labels | `brainstorming` (method), `AI assistance` (subject), `ideation` (context) |
| Claim scope (for relationship scope guidance) | `short-form writing tasks` |

**Suitability for relationship inputs:** **Yes.** `validate_relationship_candidates`
needs (a) `concept_labels` drawn from linked concepts, (b) `accepted_claim_ids`
including the probe claim id, (c) non-empty `scope`, (d) `supporting_claim_ids`
referencing a known claim id, (e) stance in `{supports, contradicts, qualifies}`,
(f) confidence label in `{low, medium, high}`. Ticket-062 outputs provide the label
set and claim id; scope can be taken from the embedded claim fixture.

**Ticket-063 input recommendation:**

| Priority | Input source | Rationale |
| -------- | ------------ | --------- |
| **Default** | Committed bundle fixture `fixtures/probes/live_probe_relationship_quality_bundle.json` containing claim + accepted concept links + probe-local concept dicts | Deterministic; no dependency on prior `data/reports/` artifacts |
| **Optional** | `--from-report <probe_link_concepts_*.json>` | Reuses real ticket-062 output; derive concept dicts from `accepted[]` labels |
| **Optional (non-default)** | `--chain-link` (extract → link → relationship) or `--chain-link` from embedded claim only | Operator convenience; upstream LLM variability; not sole acceptance gate |

Do **not** require a saved `data/reports/` artifact as the only default path.

## 4. Current relationship support

| Area | Current behavior | Gap | Risk |
| ---- | ---------------- | --- | ---- |
| `build_relationships_for_source` | Loads claims + full domain concepts from DB; drafts; validates; **persists** relationships + evidence | Requires SQLite; writes graph edges | **High** if reused for probe |
| `draft_relationships_for_source` | Calls `client.draft_relationships`; `_resolve_supporting_claim_ids` diversity fallback | Diversity heuristic wrong for quality-claim probe | Medium — probe needs `diversity_heuristic=False` variant |
| `validate_relationship_candidates` | Checks concept labels, scope, stance, predicate, supporting claim ids, confidence label | No `validation_diagnostic` helper | Medium — opaque live rejects |
| `OllamaModelClient._relationship_drafting_prompt` | Minimal JSON schema; embeds claims + concepts | No stance/scope/confidence rules, no examples, no allowed-label emphasis | **High** — likely 0 accepts without calibration (061/062 pattern) |
| `CandidateRelationship_v0_1` | subject/object concepts, predicate, stance, scope, confidence label, supporting_claim_ids | Schema sufficient for probe reports | Low |
| `research build-relationships` CLI | DB-backed persistence | No report-only probe sibling | Expected gap |
| `live_probe.py` | `probe-extract-claims`, `probe-link-concepts` | No relationship probe | Expected gap |
| Mock fixture | `relationship_drafting_creativity_diversity.json` (diversity narrative) | Does not match quality-claim probe bundle | Medium — need probe-specific mock fixture for unit tests |
| Golden GT06 | Mock diversity claim → AI assistance `may_reduce` semantic diversity | Proves DB path + validation; mock-only | No live coverage |
| `live_smoke` | `test_live_probe_extract_claims_on_fixture_chunk` only | No smoke for link/relationship probes | Low — optional follow-on, not blocker |

### Rejection reasons (existing validator — do not weaken)

| Reason | Trigger |
| ------ | ------- |
| `unknown_concept_label` | subject/object not in allowed concept label set |
| `missing_scope` | empty scope |
| `invalid_stance` | not supports/contradicts/qualifies |
| `missing_predicate` | empty predicate |
| `missing_evidence_claim` | no supporting_claim_ids in accepted claim id set |
| `invalid_confidence_label` | confidence not low/medium/high |

## 5. Recommended probe design

### CLI command

`python -m rge.cli probe-draft-relationships`

Flags (proposed):

| Flag | Purpose |
| ---- | ------- |
| `--domain creativity` | Domain pack (default creativity) |
| `--bundle PATH` | Override default embedded bundle fixture |
| `--from-report PATH` | Load claim + links from `probe-link-concepts` report |
| `--chain-link` | Run `probe-link-concepts` first (optional extract chain via existing flags) |
| `--claim-fixture` / `--fixture-source` | Pass-through for chain modes only |

### Default embedded bundle fixture (proposed)

Path: `fixtures/probes/live_probe_relationship_quality_bundle.json`

```json
{
  "claim": { "...": "same as fixtures/claims/live_probe_concept_link_quality_claim.json" },
  "concept_links": [
    { "claim_id": "claim_live_probe_link_001", "concept_label": "brainstorming", "role": "method", "confidence": 0.8 },
    { "claim_id": "claim_live_probe_link_001", "concept_label": "AI assistance", "role": "subject", "confidence": 0.85 },
    { "claim_id": "claim_live_probe_link_001", "concept_label": "ideation", "role": "context", "confidence": 0.6 }
  ],
  "concepts": [
    { "id": "concept_live_probe_001", "label": "brainstorming" },
    { "id": "concept_live_probe_002", "label": "AI assistance" },
    { "id": "concept_live_probe_003", "label": "ideation" }
  ]
}
```

Probe-local concept **IDs** are synthetic audit metadata; validator uses **labels**
only. No DB concept row ids required.

### Live env

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m rge.cli model-health
python -m rge.cli probe-draft-relationships
```

### Output artifact path

`data/reports/live_probes/probe_draft_relationships_<UTC-stamp>.json` (gitignored)

### Report schema

| Field | Required |
| ----- | -------- |
| `report_type` | `live_probe_report` |
| `command` | `probe-draft-relationships` |
| `probe` | `relationship_drafting` |
| `status`, `created_at` | yes |
| `input_source` | `embedded_bundle` \| `from_report` \| `chain_link` |
| `from_report_path` | when applicable |
| `chain_link_report_path` | when applicable |
| `input_claim` / `input_claims` | probe-local claim dict(s) |
| `input_concept_links` | accepted links used for label set |
| `input_concepts` | probe-local concept dicts passed to model |
| `domain_pack`, `effective_llm_mode`, `provider`, `model`, `base_url`, `schema_version` | yes |
| `concept_labels_allowed` | labels used for validation |
| `accepted_claim_ids` | ids used for supporting_claim validation |
| `accepted_count`, `rejected_count` | yes |
| `accepted`, `rejected` | relationship candidates post-validation |
| `rejected[].validation_diagnostic` | yes (new helper) |
| `db_writes` | **false** |
| `default_db_path` | informational |
| `report_path` | written JSON path |

### Failure conditions

| Condition | Behavior |
| --------- | -------- |
| Missing live opt-in / wrong mode | exit 2 (`LiveProbeGateError`) |
| Ollama unreachable / model missing | exit 2 |
| Zero parseable relationship candidates | exit 1 (`LiveProbeError`) |
| All rejected | report written with `accepted_count: 0`; exit 0 if report succeeds |

Live acceptance target: **`accepted_count >= 1`** with valid stance, scope, predicate,
confidence label, and supporting claim id referencing the probe claim.

Example acceptable edge (calibration target, not validator change):
`AI assistance` —supports→ `ideation` with scope `short-form writing tasks`,
`supporting_claim_ids: ["claim_live_probe_link_001"]`, `confidence: "medium"`.

### What must not happen

- No writes to default `data/db/creative_research.sqlite`
- No `RelationshipRepository.insert` / evidence persistence
- No `export-public` / committed public JSON changes
- No OpenAI/OpenRouter or API keys
- No broad `research run` live discovery
- No weakening `validate_relationship_candidates` / GT06 rules
- No committing `data/reports/` artifacts
- No raw source chunk text in relationship prompt (claim fields + concept labels only)

## 6. Safety controls

| Control | Status |
| ------- | ------ |
| No default DB writes | **Confirmed** — report-only design |
| No public export | **Confirmed** — no exporter calls |
| No cloud/API keys | **Confirmed** — Ollama local only; ticket-059 deferred |
| No model shell/Git/file mutation | **Confirmed** — structured JSON call only |
| No direct accepted graph writes | **Confirmed** — bypass `build_relationships_for_source` |
| Python validation authoritative | **Confirmed** — `validate_relationship_candidates` gates acceptance |
| Probe-local IDs sufficient | **Confirmed** — validator uses label sets and claim id membership, not DB FKs |
| No prior DB state required | **Confirmed** — in-memory claim + concept dicts |
| Live opt-in only | **Confirmed** — reuse `assert_live_probe_env` |
| CI/golden mock-only | **Confirmed** — unit tests mock client; smoke stays env-gated |
| `live_smoke` excluded by default | **Confirmed** — 2 deselected in full pytest |

**Scratch DB vs report-only:** report-only artifacts remain **safer** and consistent
with tickets 060–062. Do not introduce scratch SQLite for ticket-063.

## 7. Proposed ticket-063

### Title

Safe local live relationship-drafting probe CLI

### Problem

Tickets 061–062 proved report-only live claim extraction and concept linking.
`build-relationships` still requires persisted claims, concepts, and SQLite writes.
Operators need a no-DB live probe for relationship drafting before any graph persistence.

### Scope

- Add `probe-draft-relationships` CLI and `run_probe_draft_relationships` in `live_probe.py`
- Default embedded bundle fixture (claim + links + concept dicts)
- Optional `--from-report` / `--chain-link`
- `propose_relationship_drafts()` without diversity fallback for probe path
- Calibrate `OllamaModelClient._relationship_drafting_prompt` (stances, scope, confidence labels, examples)
- Add `relationship_rejection_diagnostic()` for rejected rows
- Mock-only unit tests + optional `live_smoke` extension (non-blocking)
- Update `docs/agents/12_RUNTIME_CONFIG.md`

### Expected files

- `rge/modules/live_probe.py`
- `rge/modules/relationship_builder.py`
- `rge/llm/ollama_client.py`
- `rge/cli.py`
- `fixtures/probes/live_probe_relationship_quality_bundle.json`
- `fixtures/llm_outputs/relationship_drafting_live_probe_quality.json` (mock unit tests)
- `tests/unit/test_live_probe_draft_relationships_cli.py`
- `tests/unit/test_relationship_rejection_diagnostics.py`
- `tests/unit/test_ollama_relationship_prompt.py`
- `docs/agents/12_RUNTIME_CONFIG.md`
- `tickets/ticket-063.json` (seed after human approval)
- `agent_reports/2026-06-12_phase-2_ticket-063_*.md` (implementation report)

### Acceptance criteria

- Live probe with qwen2.5:7b yields `accepted_count >= 1` on default bundle fixture
- `db_writes: false`; report under `data/reports/live_probes/`
- `validate_relationship_candidates` unchanged; GT06 still passes mock-only
- Rejected rows include `validation_diagnostic`
- Mock/default pytest and CI remain green without Ollama

### Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_live_probe_draft_relationships_cli.py -q
python -m pytest tests/unit/test_relationship_rejection_diagnostics.py -q
python -m pytest -q
python -m rge.cli verify --skip-site
```

Manual live (operator):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli probe-draft-relationships
```

### Safety considerations

- Reuse live opt-in gates from `live_probe.py`
- Never call `build_relationships_for_source` from probe path
- Pass claim dict fields and concept labels only — no untrusted source chunk text
- Keep live smoke excluded from default pytest/CI

### Non-goals

- DB persistence of relationships or evidence rows
- Public export changes
- OpenAI/OpenRouter adapters
- Contradiction-detection live probe (ticket-064+)
- Weakening relationship validation rules
- Ontology YAML edits

### Rollback plan

Revert CLI, probe helper, prompt calibration, fixtures, and tests. No schema migrations.

### Risk level

low-medium

### Pre-ticket audit required?

**Satisfied by this report.** Re-run `python -m rge.modules.principal_audit_gate --next-ticket ticket-063` after seeding.

## 8. Final recommendation

**Seed ticket-063 as drafted** (after human approval of this audit).

Sequence:

1. Human reviews this audit.
2. Seed `tickets/ticket-063.json` and queue row.
3. Implement on branch `phase-2/ticket-063-safe-local-live-relationship-probe`.
4. Keep **ticket-059 OpenAI deferred** until claim + concept + relationship live probes are stable.

Optional parallel hygiene (not blocking): extend `tests/smoke/test_live_ollama_smoke.py`
with `probe-link-concepts` smoke — defer to a tiny follow-on if desired; do not delay
ticket-063 for smoke-only work.

Do **not** narrow/re-audit unless live relationship probe returns zero candidates
**after** prompt calibration effort inside ticket-063.

---

*Audit complete. No ticket-063 implementation in this invocation.*
