---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-009 Audit: Relationship Builder Readiness

- Audit type: pre-implementation readiness audit (no code changes)
- Date: 2026-06-11
- Agent/model: Cursor principal-engineer audit agent (Fable 5)
- Scope: Git/main state, completed-ticket consistency, executable spine, schema/naming, relationship-builder input contract, safety boundaries

## 1. Summary

The repo is **ready for ticket-009 (mock relationship builder / Golden Test 6)** with one hardening requirement folded into the ticket itself: the `relationship_evidence` table — required by ticket-009's own acceptance criteria and by `05_DATA_MODEL.md` 4.9 — **does not exist** in the applied schema (`0001_initial.sql`) or the reference `schema.sql`. Everything else the relationship builder needs as *input* is in place and queryable: accepted claims, primary quote spans, concept links with concept IDs/labels/roles, seeded concepts (including `AI assistance` and `semantic diversity`), a `relationships` table matching the data model, a versioned `CandidateRelationshipBatch_v0_1` schema, and a `draft_relationships` method on every model client (mock currently returns an empty batch by design).

All 36 golden tests pass without Ollama. The full manual CLI spine (ingest → extract-claims → link-concepts) was verified twice: idempotently against the existing default DB (proving persistence across process restarts) and end-to-end against a fresh temporary DB. Git state is clean: `main` == `origin/main` == `f69e49b`, and all four completed ticket branches are fully contained in `main`.

The `claim_concepts` vs `claim_concept_links` naming question is **settled and harmless**: the live schema, code, tests, and `05_DATA_MODEL.md` all use `claim_concepts`; `claim_concept_links` survives only as a documented Phase-0-placeholder rename note in the ticket-006 report.

Recommendation: **proceed with ticket-009 as planned**, hardened with an explicit `0002` migration for `relationship_evidence`, a relationship repository surface, a deterministic confidence-label mapping, and machine-readable rejection reasons. No separate pre-hardening ticket is needed. A hardened implementation prompt is included in section 12.

## 2. Git / Main Status

| Check | Result | Evidence |
|---|---|---|
| Current branch | `main` | `git status` |
| Working tree clean | PASS | `nothing to commit, working tree clean` |
| `main` up to date with `origin/main` | PASS | both at `f69e49b0baf5a3cc214186e9d408d91daad075e0` |
| `f69e49b` present locally | PASS | `main` tip; `git branch -a --contains f69e49b` lists `main` and `origin/main` |
| `f69e49b` on `origin/main` | PASS | `git merge-base --is-ancestor f69e49b origin/main` exit 0 (after `git fetch origin`) |
| `1c59d14` (ticket-008 merge) on `main` | PASS | linear history: `f69e49b` → `1c59d14` → `c9571a6` → `0894f08` → `63d6e0b` → `bce08be` |

Ticket-branch containment (no completed ticket work missing from `main`):

| Branch | Tip | Ancestor of `main`? |
|---|---|---|
| `phase-0/ticket-001-repo-scaffold-model-runtime` | `63d6e0b` | yes |
| `phase-1/ticket-006-sqlite-migration-source-ingestion` | `0894f08` | yes |
| `phase-1/ticket-007-mock-claim-extraction` | `c9571a6` | yes |
| `phase-1/ticket-008-mock-concept-linking` | `1c59d14` | yes |

History is fully linear (fast-forward merges only). No force pushes, no divergence, no stray commits on ticket branches.

## 3. Completed Ticket Consistency

Cross-checked `tickets/TICKET_QUEUE.md`, the four ticket JSONs, and the four agent reports:

- **ticket-001** (done): scaffold + model runtime adapter. Report documents the Phase 0 placeholder claims tables and assigns reconciliation to ticket-006 — which happened.
- **ticket-006** (done): migration harness + ingestion. Report's Spec Deviation 3 documents the `claim_concept_links` → `claim_concepts` rename per `05_DATA_MODEL.md`. Golden Test 1 implemented (5 tests).
- **ticket-007** (done): mock claim extraction. Golden Tests 2/3/4 patterns implemented (4 tests). Documented deviation: validated claims written directly as `accepted` rather than `staged` first (noted again in section 8 below).
- **ticket-008** (done): mock concept linking. Golden Test 5 implemented (3 tests). Report documents the temporary AGENTS.md step-9 merge checkpoint and the catch-up merge of 001/006/007/008 to `main` (`bce08be` → `1c59d14`), matching observed Git history exactly.
- **ticket-009** (proposed): exists at `tickets/ticket-009.json` with acceptance criteria, test plan, non-goals, risk level, and rollback plan. Queue and reports are mutually consistent; statuses are honest.

One internal inconsistency in `tickets/ticket-009.json`: its acceptance criteria require `relationship_evidence` rows, but its `expected_files` list omits the migration file that would have to create that table (see section 6).

## 4. Tests / Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden` | PASS | 36 passed in 2.09s; no Ollama running or required |
| `python -m pytest` | PASS | 36 passed in 1.96s |
| `python -m rge.cli ingest fixtures/sources/creativity_ai_diversity_short.txt --domain creativity` | PASS | `already_ingested`, `src_fac29b647fa3cc77`, 1 chunk — proves durable persistence from prior process |
| `python -m rge.cli extract-claims --source src_fac29b647fa3cc77` | PASS | `already_extracted`, 2 accepted / 0 rejected, both Golden Test 2 claims returned with scope + limitations |
| `python -m rge.cli link-concepts --source src_fac29b647fa3cc77` | PASS | `already_linked`, 5 links (AI assistance, brainstorming, creativity, ideation, semantic diversity) with roles, confidence, and `track`/`creative_phase`/`measured_dimension` metadata |
| Same three commands against a fresh temp DB (`--db`) | PASS | `ingested` → `completed` (2 accepted) → `completed` (5 links); full spine works from an empty database |
| Direct SQLite inspection of fresh DB | DONE | confirmed table list, 2 primary `claim_quotes` rows, 5 `claim_concepts` rows, `relationships` columns, and **absence of `relationship_evidence`** |

Windows note (consistent with prior reports): `research.exe` is not on PATH; `python -m rge.cli` used throughout. PowerShell here does not support `&&`; commands chained with `;`.

## 5. Schema / Data Model Findings

Applied schema (migration `0001_initial.sql`) tables, verified against a freshly created DB:

```txt
sources, chunks, research_contracts, claims, claim_quotes, concepts,
claim_concepts, relationships, score_events, research_runs, node_reports,
run_reports, public_cards, improvement_tickets, safety_audits,
schema_migrations
```

Findings:

1. **`relationships` table is ready.** All `05_DATA_MODEL.md` 4.8 columns exist: `id`, `subject_concept_id`, `predicate`, `object_concept_id`, `scope`, `confidence` (REAL), `evidence_strength`, `domain`, `domain_metadata_json`, `status`, timestamps, plus the three spec indexes. Sufficient for Golden Test 6 without any scoring machinery.
2. **`relationship_evidence` table is missing** from both `0001_initial.sql` and `schema.sql`, despite being required by `05_DATA_MODEL.md` 4.9 (stance, relevance_score, unique `(relationship_id, claim_id, stance)`) and by ticket-009's acceptance criteria. This is the single schema gap. The migration harness (`rge/db/connection.py`) applies versioned files in sorted order and tracks `schema_migrations`, so a `0002_relationship_evidence.sql` will apply cleanly to both fresh and existing local DBs.
3. **`schema.sql` and `0001_initial.sql` are in sync** for all existing tables (schema.sql is documentation; migrations are authoritative, as documented in both files).
4. Known, documented deviations carried forward from ticket-006 (acceptable): `public_cards` retained instead of `cards`; later-phase tables (`candidate_sources`, `model_invocations`, `concept_aliases`, `domain_packs`, etc.) intentionally deferred.
5. `tests/golden/test_00_scaffold.py` checks schema tables by **presence, not equality**, so adding `relationship_evidence` will not break it — but the new table should be added to `EXPECTED_SCHEMA_TABLES` for coverage.

## 6. Claim/Concept Link Naming Finding

**Verdict: intentional, documented, and not a drift risk.**

- The only occurrence of `claim_concept_links` in the entire repo is one line in the ticket-006 report's Spec Deviations section, recording that the Phase 0 placeholder table was *renamed to* `claim_concepts` to match `05_DATA_MODEL.md` 4.7.
- Everything live uses `claim_concepts`: migration `0001`, `schema.sql`, `ClaimConceptRepository`, `rge/cli.py`, `tests/golden/test_00_scaffold.py`, `TICKET_QUEUE.md`, tickets 008/009, and the canonical data model doc itself.
- The applied table matches the spec'd shape, including the `(claim_id, concept_id, role)` unique constraint.
- Cosmetic residue only: the link ID prefix is `ccl_` (claim-concept-link) via `make_claim_concept_link_id`. IDs are opaque; no action needed.

The relationship-builder input contract is therefore unambiguous: read accepted claims from `claims`, quotes from `claim_quotes`, and concept links from `claim_concepts` (joined to `concepts` for labels).

## 7. Relationship-Builder Readiness

| Requirement | Status | Evidence |
|---|---|---|
| Accepted claims queryable | READY | `ClaimRepository.list_for_source(source_id, status="accepted")`, `get_by_id` |
| Quote spans queryable | READY | `ClaimRepository.list_quotes_for_claim(claim_id)`; fresh DB shows 2 primary quotes |
| Concept links queryable | READY | `ClaimConceptRepository.list_for_source` returns `claim_id`, `concept_id`, `concept_label`, `role`, `confidence`, `domain_metadata` |
| Concepts resolvable by label | READY | `ConceptRepository.get_by_label` (casefold-normalized); `cpt_ai_assistance` and `cpt_semantic_diversity` seeded and linked |
| `relationships` table | READY | full 4.8 shape, see section 5 |
| `relationship_evidence` table | **MISSING** | needs `0002` migration; ticket-009 acceptance criteria already require its rows |
| Repository surface for relationships | NOT YET (expected) | no `RelationshipRepository` / `RelationshipEvidenceRepository`; in ticket-009 scope per its `affected_modules` (`rge/db/repositories.py`) |
| Deterministic mock candidates | READY (needs fixture) | `ModelClient.draft_relationships` exists on the ABC, mock, and Ollama boundary; `CandidateRelationship_v0_1` carries `subject_concept`, `predicate`, `object_concept`, `stance`, `scope`, `confidence`, `supporting_claim_ids`. Mock currently returns an empty batch; ticket-009 adds a fixture + `fixture_name` parameter following the exact pattern of `extract_claims`/`link_concepts` |
| Machine-readable rejection | PATTERN READY | precedent in `claim_validator` (`missing_quote_span`, `overgeneralized_scope`) and `validate_concept_links` (`weak_concept_mapping`); relationship validation rules are explicit in `05_DATA_MODEL.md` §6 ("active only if: subject and object concept IDs, ≥1 evidence link, each link has stance, has confidence and scope") |
| Golden Test 6 fields without scoring overbuild | READY | GT6 needs subject/predicate/object concepts, stance, supporting claim, confidence — all representable now; `score_events` exists but is ticket-010+ scope and must stay untouched |

One contract decision ticket-009 must make explicitly: Golden Test 6 expresses relationship confidence as a **label** (`"medium"`), and `CandidateRelationship_v0_1.confidence` is a string, while `relationships.confidence` is **REAL (0.0–1.0)**. The implementation needs a deterministic, versioned label→value mapping (e.g. `low=0.25 / medium=0.5 / high=0.75`) applied by the Python validator — not by the model — so future score reconciliation (Golden Test 8) starts from a numeric baseline without a score event. This is called out in the hardened prompt below.

Minor non-blocking observation: `concept_linker.link_claim_concepts` retargets all fixture links onto the claim whose text contains "reduced semantic diversity". Acceptable mock-phase determinism (documented in the ticket-008 report), and the relationship builder may use an analogous deterministic selection, but candidate `supporting_claim_ids` should resolve against real accepted-claim IDs from the repository rather than trusting fixture IDs blindly — reject with `unknown_claim_id` otherwise.

## 8. Safety Findings

| Boundary | Status | Evidence |
|---|---|---|
| No live Ollama required | PASS | full suite passes with no Ollama process; `claim_extractor` and `concept_linker` force `RGE_LLM_MODE=mock`; `OllamaModelClient` structured tasks still fail honestly; registry fails closed on unknown mode (golden tests) |
| No model output writes without Python validation | PASS | `rge/llm` clients return typed candidates only; golden test source-scans `rge.llm` for DB/shell/subprocess imports; repositories are the only write path; concept links pass `validate_concept_links` before insert |
| No public write/ingestion/agent routes | PASS | public site is static-export Next.js with no API routes, no fetches, no forms (enforced by `test_00_public_site_static.py`, 6 tests passing); local CLI only — no FastAPI server exists yet at all |
| No raw prompt/source/private path leakage | PASS | `source_record_to_public_dict` excludes `local_path` and chunk text; CLI JSON outputs exclude raw chunk text; static public JSON is whitelisted and pattern-scanned by golden tests; private fields live only in local SQLite (gitignored `data/db/`) |
| No destructive Git instructions | PASS | AGENTS.md step 9 specifies merge + push only, explicitly forbids force-push, and requires honest failure reporting; observed history is fast-forward merges only |
| Models cannot push/merge | PASS | merge step is executed by the (human-supervised) builder agent per AGENTS.md, not by model output; no Git access exists anywhere in `rge/` |

Carried-forward deviation to keep visible (not a ticket-009 blocker): accepted claims are written directly as `accepted` rather than passing through `staged` (ticket-007 Spec Deviation 1). The relationship builder should mirror the same documented simplification — relationships written as `active` only after deterministic validation — and not silently introduce a third convention.

## 9. Blocking Issues

**None that require a separate pre-ticket.** The single material gap — missing `relationship_evidence` table — is already implied by ticket-009's own acceptance criteria and is a one-migration fix that belongs inside ticket-009's scope. Proceeding without acknowledging it, however, would force mid-ticket scope improvisation, so the ticket must be amended before implementation starts:

1. Add `rge/db/migrations/0002_relationship_evidence.sql` (and the matching `schema.sql` block) to `expected_files`.
2. Add `tests/golden/test_00_scaffold.py` (EXPECTED_SCHEMA_TABLES update) to `expected_files`.
3. Specify the confidence label→REAL mapping decision (section 7).

## 10. Recommended Next Ticket

**Proceed with ticket-009: Add mock relationship builder (Golden Test 6)** — with the hardened scope above. Do not split out a separate schema-hardening ticket; the migration is small, exclusively serves the relationship builder, and splitting it would violate the smallest-next-ticket principle by creating a ticket with no independently testable behavior.

## 11. Should Ticket-009 Proceed as Planned?

**Yes — proceed, hardened.** Inputs are queryable, the mock adapter seam and versioned candidate schema already exist, validation precedents are established, tests are green, Git is clean, and safety boundaries hold. The only changes versus the proposed ticket are: the `0002` migration + `schema.sql` + scaffold-test additions to `expected_files`, the explicit confidence mapping, and explicit machine-readable rejection reasons for invalid candidates.

## 12. Hardened Ticket-009 Implementation Prompt

```txt
You are the Research Graph Engine implementation agent.

Read AGENTS.md, tickets/TICKET_QUEUE.md, tickets/ticket-009.json,
docs/agents/00_GOLDEN_TESTS.md (Test 6), docs/agents/05_DATA_MODEL.md
(sections 4.8, 4.9, and 6 "Relationships"),
agent_reports/2026-06-11_phase-1_ticket-008_mock-concept-linking.md, and
agent_reports/2026-06-11_pre-ticket-009_relationship-builder-readiness-audit.md.

Implement ticket-009 only, on branch phase-1/ticket-009-mock-relationship-builder.

Scope (one ticket, no broadening):

1. Migration: add rge/db/migrations/0002_relationship_evidence.sql creating
   relationship_evidence per 05_DATA_MODEL.md 4.9 (id, relationship_id FK,
   claim_id FK, stance, relevance_score, created_at, UNIQUE(relationship_id,
   claim_id, stance)). Mirror the table in rge/db/schema.sql and add
   "relationship_evidence" to EXPECTED_SCHEMA_TABLES in
   tests/golden/test_00_scaffold.py. Do not modify 0001_initial.sql.

2. Mock candidates: add a relationship-drafting fixture
   fixtures/llm_outputs/relationship_drafting_creativity_diversity.json
   (schema_version 0.1.0, task_name relationship_drafting) proposing the
   Golden Test 6 edge: subject_concept "AI assistance", predicate
   "may_reduce", object_concept "semantic diversity", stance "supports",
   scope "short-form writing tasks", confidence "medium", supporting the
   semantic-diversity claim. Give MockModelClient.draft_relationships a
   fixture_name parameter loading this fixture, exactly like extract_claims
   and link_concepts. Force RGE_LLM_MODE=mock in the module entry point.
   Do not call Ollama.

3. Validation (Python only — model output never writes): implement
   rge/modules/relationship_builder.py with build_relationships_for_source(
   conn, source_id, *, fixture_name=None). Deterministically validate each
   candidate per 05_DATA_MODEL.md section 6: subject and object concepts must
   resolve to existing concept rows by label (reject unknown_concept_label);
   at least one supporting_claim_id must resolve to an existing accepted
   claim for the source (reject unknown_claim_id / missing_evidence_claim);
   stance must be one of supports/contradicts/qualifies (reject
   invalid_stance); scope must be present (reject missing_scope). Rejected
   candidates must be returned/reported with machine-readable reasons, never
   silently dropped.

4. Persistence: add RelationshipRepository and RelationshipEvidenceRepository
   to rge/db/repositories.py with stable IDs (rel_<hash>, rev_<hash>),
   read methods (list_for_source or list_for_concepts, get_by_id,
   list_evidence_for_relationship), and insert methods. Map the confidence
   label deterministically in the validator (low=0.25, medium=0.5,
   high=0.75) into relationships.confidence REAL; keep the label out of the
   DB. Write relationships with status "active" only after validation passes
   (mirroring the documented ticket-007 accepted-directly deviation; document
   this in the report). Idempotent: re-running returns already_built.

5. CLI: add "research build-relationships --source <source_id>" with
   optional --fixture and --db, following the link-concepts JSON output
   pattern. Output must not include raw chunk text or local paths.

6. Tests: add tests/golden/test_06_relationship_builder.py asserting:
   at least one active relationship with the Golden Test 6 shape; at least
   one relationship_evidence row with stance "supports" and the correct
   claim_id; relationships and evidence re-readable after process restart;
   an invalid candidate (e.g. unknown concept) is rejected with a
   machine-readable reason and creates no rows. Tests must pass without
   Ollama. The 0002 migration must apply cleanly to both a fresh DB and a
   DB already migrated to 0001.

Non-goals: no Ollama calls, no scoring or score_events writes, no
contradiction detection (Golden Test 7), no public export, no graph
reconciliation, no FastAPI, no changes to claim extraction or concept
linking behavior.

Run python -m pytest tests/golden/test_06_relationship_builder.py,
python -m pytest tests/golden, and python -m pytest. Verify the manual CLI
flow end-to-end on a fresh --db path. Write an agent report to
agent_reports/, update tickets/TICKET_QUEUE.md and tickets/ticket-009.json
honestly, recommend the next smallest ticket (expected: ticket-010 score
reconciliation / Golden Test 8, or contradiction detection / Golden Test 7),
then merge to main and push per AGENTS.md step 9, documenting the merge
hash. Never claim success for commands you did not run.
```

## 13. Audit Hygiene

This audit made no code, schema, ticket, or queue changes. Temporary artifacts (one throwaway inspection script and one temp-directory SQLite DB) were deleted; the manual CLI commands against the default DB were idempotent re-runs that wrote nothing new. Working tree contains only this report.
