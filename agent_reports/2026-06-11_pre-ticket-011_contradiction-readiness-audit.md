---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-011 Audit: Contradiction Detection Readiness

- Audit type: pre-implementation readiness audit (no code changes)
- Date: 2026-06-11
- Agent/model: Cursor principal audit agent (Auto)
- Scope: Git/main state after ticket-010, executable spine through score reconciliation, schema/repository/fixture support for Golden Test 7, safety boundaries, ticket-011 scope hardening

## 1. Summary

The repo is **ready for ticket-011 (mock contradiction detection / Golden Test 7)** with hardening requirements folded into the ticket itself. Main is clean and aligned with `origin/main` at `0d56732`. ticket-010 is merged and pushed (`011441f`). All **45** golden tests pass without Ollama. The full spine **ingest → extract-claims → link-concepts → build-relationships → reconcile-scores** is intact; Golden Test 8 proves `score_events` append-only history and relationship confidence updates work end-to-end.

What ticket-011 still lacks (expected — not yet implemented) is the contradiction module, CLI command, mock contradiction fixtures, and Golden Test 7. Existing schema and repositories already support the persistence model: `relationships` with `may_increase` / `may_reduce` predicates, `relationship_evidence` with `supports` / `contradicts` / `qualifies` stances, and cross-source claim queries. The contradiction **source fixture** (`fixtures/sources/creativity_ai_diversity_contradiction.txt`) exists; claim-extraction, concept-linking, relationship-drafting, and contradiction-detection **LLM fixtures do not**.

One contract decision ticket-011 must make explicit: Golden Test 7 and MVP Test 7 allow `qualifies` **or** `apparent_contradiction_metric_or_condition_difference`, but `relationship_evidence.stance` only permits `supports`, `contradicts`, `qualifies` per `05_DATA_MODEL.md` 4.9. The longer classification must live in `reason`, `domain_metadata_json`, or a dedicated machine-readable field on the qualification link — not as a fourth stance enum value without a migration.

Recommendation: **proceed with ticket-011 as the next smallest safe ticket**, hardened with explicit fixture set, qualification-link semantics, and supplemental concept/scope handling for the divergent-prompting edge. No separate pre-hardening ticket is required.

## 2. Git / Main Status

| Check | Result | Evidence |
|---|---|---|
| Current branch | `main` | `git status` |
| Working tree clean | PASS | `nothing to commit, working tree clean` |
| `main` up to date with `origin/main` | PASS | both at `0d5673291cce2ec6f620f7abceabfd1c9dfed0e8` |
| ticket-010 merged to `main` | PASS | merge commit `011441f5586acb1e3755fd43af675251b17cda82` |
| ticket-010 pushed to `origin/main` | PASS | `git merge-base --is-ancestor 011441f origin/main` exit 0; doc follow-up `0d56732` on remote |
| ticket-010 branch contained in `main` | PASS | `96103f3` reachable from `main` |

Recent linear history:

```txt
0d56732 docs: record main merge hash for ticket-010
011441f Merge branch 'phase-1/ticket-010-score-reconciliation'
96103f3 Implement ticket-010 score reconciliation with Golden Test 8
a086d6c docs: record main merge hash for ticket-009
705ff64 Merge branch 'phase-1/ticket-009-mock-relationship-builder'
```

## 3. Tests Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden` | PASS | 45 passed in 7.83s |
| `python -m pytest` | PASS | 45 passed in 6.06s |
| Ollama required | NO | `RGE_LLM_MODE=mock` throughout golden suite |

Golden test coverage by spine stage:

| Stage | Golden test file | Tests |
|---|---|---|
| ingest | `test_01_ingestion.py` | 5 |
| extract-claims | `test_02_claim_extraction.py` | 4 |
| link-concepts | `test_05_concept_linking.py` | 3 |
| build-relationships | `test_06_relationship_builder.py` | 5 |
| reconcile-scores | `test_08_score_reconciliation.py` | 4 |
| contradiction detection | *(none yet)* | ticket-011 scope |

## 4. Spine Verification

### Automated (Golden Test 8 — full spine + score history)

Golden Test 8 runs the complete pipeline on a fresh temp DB:

1. `ingest` base fixture → `extract-claims` → `link-concepts` → `build-relationships`
2. SQL seed relationship confidence to **0.52**
3. Ingest follow-up source → `extract-claims` (follow-up fixture) → `reconcile-scores`
4. Asserts confidence **0.64**, `score_events` row with old/new/triggering claim/reason

All four Golden Test 8 tests pass, including idempotency and process-restart persistence.

### Manual CLI (partial)

Manual verification on a fresh temp DB confirmed through `build-relationships` and relationship confidence seeding. PowerShell inline `python -c` quoting prevented a clean one-liner for follow-up source ID selection on this host; golden tests are the authoritative spine proof. Use `python -m rge.cli` on Windows when `research.exe` is not on PATH.

### score_events history

| Requirement | Status | Evidence |
|---|---|---|
| Table exists in `0001_initial.sql` | PASS | columns: entity_type, entity_id, old_score, new_score, triggering_claim_id, triggering_source_id, reason, formula_version |
| Writes only via transactional helper | PASS | `persist_relationship_score_update()` in `repositories.py` |
| Old score preserved | PASS | Golden Test 8 asserts `old_score=0.52` in `score_events` |
| Idempotent re-run | PASS | `test_reconcile_scores_is_idempotent` |
| No score change without event row | PASS | single writer path; fail-closed design |

## 5. Ticket-011 Readiness

### Is ticket-011 the next smallest safe ticket?

**Yes.** Phase 1 golden tests still missing executable coverage for Test 7 (contradiction) before Test 9 (research queue), public export, or LangGraph. ticket-010 explicitly deferred contradiction detection; queue and reports agree ticket-011 is next.

Alternatives considered and rejected:

| Alternative | Why not smaller/safer |
|---|---|
| Golden Test 9 (research queue) | Broader scope: ranking, contracts, candidate_sources — not spine-adjacent |
| Public export / cards | Phase 4; touches safety export boundaries |
| Full skeptic / LangGraph agent | Explicit non-goal |
| Separate schema migration ticket | No schema gap blocks GT7; `relationship_evidence` exists from ticket-009 |

### Schema / repository support

| Requirement | Status | Evidence |
|---|---|---|
| `relationships` table with predicates | READY | `may_reduce`, `may_increase` allowed per 05_DATA_MODEL.md 4.8 |
| `relationship_evidence` with stance | READY | migration `0002`; stances `supports`, `contradicts`, `qualifies` |
| `RelationshipRepository` | READY | insert, get, list_active, update_confidence |
| `RelationshipEvidenceRepository` | READY | insert, list_for_relationship, list_for_source, has_link |
| Cross-source claim lookup | READY | `ClaimRepository.list_for_source`, list all accepted claims for domain |
| `ScoreEventRepository` | READY | unrelated to GT7; must not be modified for contradiction scoring |
| Contradiction-specific repository | NOT NEEDED | reuse relationship + evidence repos |
| New migration for GT7 | NOT REQUIRED | unless ticket chooses a new metadata column (prefer JSON on evidence row) |

### Fixture support

| Asset | Status | Notes |
|---|---|---|
| `fixtures/sources/creativity_ai_diversity_contradiction.txt` | EXISTS | divergent-prompting / idea-diversity passage; referenced in scaffold |
| `fixtures/sources/creativity_ai_diversity_short.txt` | EXISTS | Source A for base may_reduce edge |
| Claim extraction fixture for contradiction source | **MISSING** | must add (e.g. `claim_extraction_creativity_diversity_contradiction.json`) |
| Concept linking fixture for contradiction source | **MISSING** | must add; link to AI assistance + diversity-related object |
| Relationship drafting fixture (may_increase edge) | **MISSING** | can be separate fixture or produced inside contradiction module |
| Contradiction detection fixture | **MISSING** | per ticket-011 `expected_files` |
| Follow-up fixtures (ticket-010) | EXISTS | pattern to mirror |

### Module / CLI / mock seam

| Component | Status | Notes |
|---|---|---|
| `rge/modules/contradiction_detector.py` | **MISSING** | expected; no stub file |
| `research detect-contradictions` CLI | **MISSING** | expected |
| `ModelClient.detect_contradictions` (or equivalent) | **MISSING** | ABC has extract/link/draft only; ticket-011 lists `mock_client.py` |
| `CandidateContradictionBatch` schema | **MISSING** | recommend new Pydantic batch in `schemas.py` (versioned, fail-closed) |
| `relationship_builder` validation patterns | READY | VALID_STANCES, machine-readable rejections — reuse style |
| `concept_linker` supplemental concepts | READY | pattern for adding ontology gaps without hardcoding creativity fields in core |

### Golden Test 7 contract decisions (must be explicit in implementation)

1. **Second relationship edge.** After base spine on Source A, contradiction source must yield `AI assistance → may_increase → <object>` with scope capturing divergent prompting. Golden Test names object **"idea diversity under divergent prompting"**; ontology has `semantic diversity` and `diversity`, and aliases map **idea diversity → semantic diversity**. ticket-011 should either:
   - use object concept `diversity` with scope `under divergent prompting when participants generate multiple divergent directions`, **or**
   - add a supplemental candidate concept (e.g. `idea diversity`) via domain pack / concept linker pattern, documenting the deviation.
   Prefer scope + existing concepts to avoid ontology proliferation unless golden test assertions require the literal label.

2. **Qualification link.** "Relationship between the claims" should persist as `relationship_evidence` with stance **`qualifies`**, linking the opposing claim to the relevant relationship(s). Store `apparent_contradiction_metric_or_condition_difference` as:
   - `domain_metadata_json` on the evidence row (e.g. `{"contradiction_classification": "apparent_contradiction_metric_or_condition_difference"}`), **or**
   - a machine-readable `reason` string on the evidence row if the schema supports it (currently evidence table has no reason column — use metadata JSON).

3. **Preserve both sides.** Do not delete, overwrite, or merge claims. Do not replace with "AI has mixed effects." Both relationships remain `active`.

4. **Multi-source orchestration.** Golden Test 7 spans two sources. `detect-contradictions --source <contradiction_source_id>` should read existing active relationships and accepted claims across the graph (or domain), not only the invoking source — document in module docstring and golden test setup.

### Non-goals confirmed

| Non-goal | Status |
|---|---|
| Live Ollama | Not required; force `RGE_LLM_MODE=mock` |
| Public export changes | Not required |
| LangGraph / agent execution | Not present |
| Research queue (Test 9) | Out of scope |
| Broad refactor | Not needed |
| Automated contradiction resolution | Explicit non-goal in ticket-011 |

## 6. Safety Findings

| Boundary | Status | Evidence |
|---|---|---|
| No live Ollama required | PASS | 45 golden tests pass without Ollama |
| Models propose; Python validates and writes | PASS | established pattern in claim/concept/relationship/score modules |
| No public write/ingestion/agent routes | PASS | static public site; CLI-only local writes |
| No raw source/prompt leakage in CLI JSON | PASS | public dict helpers exclude chunk text and local paths |
| Contradiction module must not delete claims | REQUIRED | align with 10_SAFETY_MODEL.md §4; GT7 failure conditions |
| No model-controlled Git/shell | PASS | merge remains agent/human step per AGENTS.md |

Safety audit (`python -m rge.modules.safety_auditor --audit full`) not required for ticket-011 per prior ticket pattern (no export/route changes), but the contradiction module must preserve claim integrity and reject injection-driven deletion requests in validation.

## 7. Blocking Issues

**None that require a separate pre-ticket.** Gaps are expected missing implementation, not structural blockers.

ticket-011 JSON should be amended before implementation starts:

1. Add missing fixtures to `expected_files`: claim extraction + concept linking + relationship drafting for contradiction source (not only `contradiction_detection_*.json`).
2. Specify qualification persistence semantics (section 5 above).
3. Specify cross-source read behavior for `detect-contradictions`.
4. Clarify mapping of `apparent_contradiction_metric_or_condition_difference` to metadata (not a fourth stance enum without migration).

## 8. Hardened Ticket-011 Scope

Implement **one ticket** on branch `phase-1/ticket-011-mock-contradiction-detection`:

1. **Schema for mock candidates:** add `CandidateContradiction_v0_1` / `CandidateContradictionBatch_v0_1` in `rge/llm/schemas.py` with `task_name: contradiction_detection`, fields for opposing relationship references, qualification stance, classification (`qualifies` | `apparent_contradiction_metric_or_condition_difference`), supporting claim IDs, and scope. Add `detect_contradictions(...)` to `ModelClient` ABC; implement in `MockModelClient` with `fixture_name` parameter (Ollama client may raise honestly until wired).

2. **Fixtures:**
   - `fixtures/llm_outputs/claim_extraction_creativity_diversity_contradiction.json` — accepted claim matching contradiction source text (increased idea diversity under divergent prompting).
   - `fixtures/llm_outputs/concept_linking_creativity_diversity_contradiction.json` — links to AI assistance + diversity-related concepts.
   - `fixtures/llm_outputs/relationship_drafting_creativity_diversity_contradiction.json` — `may_increase` edge for Golden Test 7.
   - `fixtures/llm_outputs/contradiction_detection_creativity_diversity.json` — qualification link between base may_reduce edge and new claim/edge.

3. **Module:** `rge/modules/contradiction_detector.py` with `detect_contradictions_for_source(conn, source_id, *, fixture_name=None)`. Force mock mode. Validate candidates in Python; persist via existing repositories only. Idempotent re-run. Machine-readable skip/reject reasons.

4. **CLI:** `research detect-contradictions --source <source_id> [--fixture ...] [--db ...]` with JSON output mirroring other commands.

5. **Golden Test 7:** `tests/golden/test_07_contradiction_detection.py` — build base graph on short fixture, ingest/extract/link/build contradiction source, run detect-contradictions, assert both edges active, both claims preserved, qualifies (or classified qualification) link present. Update `test_00_scaffold.py` CLI help.

6. **Non-goals:** no Ollama, no score_events writes, no public export, no queue, no LangGraph, no claim deletion/merging.

## 9. Recommended Next Action

1. **Mark ticket-011 `ready`** (optional) or implement directly from `proposed` using hardened scope above.
2. Run implementation via `.cursor/commands/rge-run-next-ticket.md` **or** the hardened prompt in section 10.
3. Do **not** implement research queue, public export, or scoring changes in the same ticket.

## 10. Hardened Implementation Prompt

```txt
You are the Research Graph Engine implementation agent.

Read AGENTS.md, tickets/TICKET_QUEUE.md, tickets/ticket-011.json,
docs/agents/00_GOLDEN_TESTS.md (Test 7), docs/agents/05_DATA_MODEL.md
(sections 4.8, 4.9, and 6),
agent_reports/2026-06-11_phase-1_ticket-010_score-reconciliation.md, and
agent_reports/2026-06-11_pre-ticket-011_contradiction-readiness-audit.md.

Implement ticket-011 only on branch phase-1/ticket-011-mock-contradiction-detection.

Follow the hardened scope in the pre-ticket-011 audit (fixtures, qualification
semantics, cross-source reads, metadata for apparent_contradiction classification).

Run pytest tests/golden/test_07_contradiction_detection.py, pytest tests/golden,
pytest, write agent report, update TICKET_QUEUE.md, merge to main and push per
AGENTS.md step 9.
```
