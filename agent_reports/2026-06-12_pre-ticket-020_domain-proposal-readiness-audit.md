---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-020 Audit: Domain Proposal Readiness

- Audit type: pre-implementation readiness audit (no ticket-020 code changes)
- Date: 2026-06-12
- Agent/model: Cursor builder agent (Auto)
- Scope: Git/main state after ticket-019, spine through ontology pressure, schema/repository/module support for Golden Test 18, ticket-020 scope hardening, safety boundaries

## 1. Summary

The repo is **ready for ticket-020 (domain proposal threshold trigger / Golden Test 18)** with hardening folded into the ticket. Main is clean and aligned with `origin/main` at `36b6606750f2850c9f7cccd8c09acdf8ba5aa69b`. All **81** golden tests pass without Ollama. Tickets **017–019** are merged, pushed, and consistently marked `done`. The intelligence spine through `generate-ontology-pressure` is implemented and verified by Golden Tests 15–17. **`domain_proposer.py` is a Phase 0 stub**; **`domain_proposals` table, repository, CLI, and Golden Test 18 are absent** — expected pre-implementation state.

**Contract decisions for ticket-020:**

1. Add migration `0007_domain_proposals.sql` per `05_DATA_MODEL.md` §4.24 and reference DDL in `schema.sql`.
2. Add `DomainProposalRepository` with idempotent insert keyed on stable proposal ID.
3. CLI: `generate-domain-proposal` with `--domain`, `--db`, optional `--output-dir`, optional `--no-pad`.
4. Deterministic golden padding to meet strict thresholds (40 accepted claims, 8 independent sources, 15 recurring specialized terms, ≥3 mismatch signals, parent-underspecified reason) using art/design/film/music vocabulary per Golden Test 18.
5. Proposed domain example: `creativity.film` with `status: draft`; include `threshold_report_json` / `thresholds` block proving all gates.
6. No Ollama, no LangGraph, no live web discovery, no public export/site changes, no automatic domain activation.

**Recommendation: proceed with ticket-020 as the next smallest safe ticket** — after this audit report is committed to `main`.

## 2. Git / Main Status

| Check | Result |
|---|---|
| Current branch | `main` |
| Working tree | **clean** (no staged/unstaged/untracked changes) |
| `main` vs `origin/main` | **aligned** — both at `36b6606750f2850c9f7cccd8c09acdf8ba5aa69b` |
| ticket-017 merged & pushed | **yes** — merge `4aa2296`, docs hash `90316c6` |
| ticket-018 merged & pushed | **yes** — merge `f8de970`, docs hash `b6dbe39` |
| ticket-019 merged & pushed | **yes** — merge `c0c2327`, docs hash `36b6606` |
| Unmerged work | **none** on main |
| Dangling local branches | `phase-1/ticket-001` through `phase-1/ticket-019` exist locally; all merged to main — **no suspicious drift** |
| Suspicious drift | **none** — `phase-1/ticket-019-ontology-pressure` tip is ancestor of main |

## 3. Ticket / Report Consistency

| Ticket | Queue | JSON | Report | Pre-ticket audit | Consistent |
|---|---|---|---|---|---|
| ticket-017 | `done` | `done` | `agent_reports/2026-06-12_phase-1_ticket-017_theory-generator.md` | `2026-06-12_pre-ticket-017_theory-generator-readiness-audit.md` | **yes** |
| ticket-018 | `done` | `done` | `agent_reports/2026-06-12_phase-1_ticket-018_question-generation.md` | `2026-06-12_pre-ticket-018_question-generation-readiness-audit.md` | **yes** |
| ticket-019 | `done` | `done` | `agent_reports/2026-06-12_phase-1_ticket-019_ontology-pressure.md` | `2026-06-12_pre-ticket-019_ontology-pressure-readiness-audit.md` | **yes** |
| ticket-020 | `proposed` | `proposed` | — (not yet) | **this report** | **correct next ticket** |

**Next ticket:** ticket-020 is the lowest-order `proposed` ticket in `TICKET_QUEUE.md`.

**Risk / audit gate:** ticket-020 JSON `risk_level: medium`. Runner protocol (`.cursor/commands/rge-run-next-ticket.md` §3.5) requires a pre-ticket audit for medium/high risk tickets and for theory/inference/proposal generation milestones. **Gate unmet until this report is committed; satisfied once committed.**

## 4. Report Claims vs Repo Reality

### ticket-017 claimed files

| Claimed | Exists |
|---|---|
| `rge/db/migrations/0005_theory_candidates.sql` | **yes** |
| `rge/modules/theory_generator.py` (full impl) | **yes** |
| `rge/cli.py` → `generate-theory-candidates` | **yes** |
| `tests/golden/test_15_theory_generator.py` | **yes** (4 tests) |
| `fixtures/llm_outputs/theory_generation_creativity_diversity.json` | **yes** |
| `theory_candidates` in `schema.sql` | **yes** |

### ticket-018 claimed files

| Claimed | Exists |
|---|---|
| `rge/modules/research_planner.py` (follow-up generation) | **yes** |
| `rge/cli.py` → `generate-followup-questions` | **yes** |
| `tests/golden/test_16_question_generation.py` | **yes** (4 tests) |
| `fixtures/llm_outputs/followup_question_generation_golden_test_16.json` | **yes** |
| No schema migration | **confirmed** |

### ticket-019 claimed files

| Claimed | Exists |
|---|---|
| `rge/db/migrations/0006_ontology_proposals.sql` | **yes** |
| `rge/modules/ontology_pressure.py` (full impl) | **yes** |
| `rge/cli.py` → `generate-ontology-pressure` | **yes** |
| `tests/golden/test_17_ontology_pressure.py` | **yes** (4 tests) |
| `ontology_proposals` in `schema.sql` | **yes** |
| Migration in `test_01_ingestion.py` list | **yes** (`0006_ontology_proposals`) |

### Mismatches

| Item | Notes |
|---|---|
| `domain_proposals` absent | **Expected** — ticket-020 scope |
| `tests/golden/test_18_domain_proposal.py` absent | **Expected** — ticket-020 scope |
| Doc drift: `02_ARCHITECTURE.md` / `04_CURSOR_BUILD_LOOP.md` reference `test_13_domain_proposals.py` | Historical naming; canonical Golden Test is **Test 18** in `00_GOLDEN_TESTS.md`. Non-blocking. |

## 5. Tests / Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | **PASS** | **81 passed** in ~22s |
| `RGE_LLM_MODE=mock python -m pytest` | **PASS** | **81 passed** |
| `python -m pytest tests/golden/test_15_theory_generator.py tests/golden/test_16_question_generation.py tests/golden/test_17_ontology_pressure.py` | **PASS** | **12 passed** (GT15–17) |
| Ollama required | **NO** | Mock mode only |
| Public site build | **NOT RUN** | No public-site changes since ticket-015; not required for this audit |

## 6. Spine Verification

Golden Tests 13–17 exercise the deterministic intelligence spine end-to-end on temp DBs with `RGE_LLM_MODE=mock`:

```txt
ingest → extract-claims → link-concepts → build-relationships
→ detect-contradictions → reconcile-scores → generate-cluster-report
→ generate-theory-candidates → generate-followup-questions
→ generate-ontology-pressure
```

| Command | Registered in `rge/cli.py` | Golden test coverage |
|---|---|---|
| `ingest` | yes | GT1+ |
| `extract-claims` | yes | GT2+ |
| `link-concepts` | yes | GT5+ |
| `build-relationships` | yes | GT6+ |
| `detect-contradictions` | yes | GT7+ |
| `reconcile-scores` | yes | GT8+ |
| `generate-cluster-report` | yes | GT13 |
| `generate-theory-candidates` | yes | GT15 |
| `generate-followup-questions` | yes | GT16 |
| `generate-ontology-pressure` | yes | GT17 |
| `export-public` | yes | GT11 (safety boundary) |
| `generate-domain-proposal` | **no** | **GT18 not yet** |

**export-public safety boundary:** `card_exporter.py` exports only `public_cards` via `PublicCardRepository.list_public_safe`. Golden Test 11 asserts curated field allowlist and forbids paths, prompts, evaluator notes. No theory, ontology, or domain proposal tables are queried.

## 7. Domain-Proposer Readiness

### Current state

| Component | Status |
|---|---|
| `rge/modules/domain_proposer.py` | **Phase 0 stub** — `propose_domain()` raises `NotImplementedError` |
| `domain_proposals` table / migration | **absent** (latest migration: `0006_ontology_proposals`) |
| `DomainProposalRepository` | **absent** |
| `generate-domain-proposal` CLI | **absent** |
| `tests/golden/test_18_domain_proposal.py` | **absent** |
| `domain_proposals` in `schema.sql` | **absent** |
| `test_00_scaffold.py` table list | lists `theory_candidates`, `ontology_proposals`; **not** `domain_proposals` |

### What ticket-020 must add

Per specs and hardened scope:

1. **Migration `0007_domain_proposals.sql`** — columns per `05_DATA_MODEL.md` §4.24:
   - `id`, `domain_id`, `status`, `parent_domains_json`, `overlap_domains_json`, `specialized_terms_json`, `scoring_overlay_proposals_json`, `evidence_claims_json`, `threshold_report_json`, `created_at`, `updated_at`
2. **`DomainProposalRepository`** — insert/get/count/idempotent re-run (mirror `OntologyProposalRepository` pattern).
3. **`domain_proposer.py`** — threshold assessment, deterministic golden padding, report build, persist, optional JSON export.
4. **CLI `generate-domain-proposal`** — `--domain`, `--db`, `--output-dir`, `--no-pad`.
5. **Golden Test 18** — `tests/golden/test_18_domain_proposal.py` (target 4 tests, consistent with GT15–17).
6. **Scaffold updates** — `test_00_scaffold.py`, `test_01_ingestion.py` migration list.

### Golden Test 18 thresholds (canonical)

From `docs/agents/00_GOLDEN_TESTS.md` Test 18 and `05_DATA_MODEL.md` §4.24 / `06_DOMAIN_PACK_SPEC.md` §15:

| Threshold | Value |
|---|---|
| Accepted claims | **40** |
| Independent sources | **8** |
| Recurring specialized terms | **15** |
| Repeated extraction/scoring mismatch signals | **≥3** (data model); GT18 prose says "repeated" |
| Parent domain underspecified reason | **required** (boolean gate) |

**Expected draft proposal shape** (Golden Test 18 / `08_REPORTING_SPEC.md` §12):

```json
{
  "report_type": "domain_proposal_report",
  "domain_id": "creativity.film",
  "status": "draft",
  "thresholds": {
    "accepted_claims": 42,
    "independent_sources": 9,
    "recurring_specialized_terms": 18,
    "mismatch_signals": 4,
    "parent_underspecified_reason_present": true
  },
  "parent_domains": ["creativity", "art"],
  "overlap_domains": ["digital_media"],
  "specialized_terms": ["storyboarding", "cinematography", "editing rhythm"],
  "scoring_overlay_proposals": ["production_context", "collaboration_scale", "craft_dependency"],
  "evidence_claims": ["clm_..."]
}
```

Also include `reason_parent_domain_is_underspecified` per `06_DOMAIN_PACK_SPEC.md` §15.

### Evidence ticket-020 should consume

| Source | Use |
|---|---|
| **Accepted claims** | Count gate (40); `evidence_claims` sample IDs |
| **Independent sources** | Count gate (8); requires multi-source ingest or golden padding sources |
| **Specialized terms** | Recurring art/design/film/music vocabulary in claim text (15+) |
| **Mismatch signals** | Score events, contradiction metadata, or deterministic golden-stamped mismatch records (≥3) |
| **Parent domain context** | Current domain pack (`creativity`) underspecification rationale |
| Cluster reports | **Optional context** — not primary threshold input |
| Theory candidates | **Optional context** — not primary threshold input |
| Follow-up questions | **Optional context** — not primary threshold input |
| Ontology pressure proposals | **Optional cross-signal** — draft ontology pressure may support rationale but must not auto-activate |

Live fixture corpus has **4 creativity sources only**; ticket-020 must use **deterministic golden padding** (same pattern as GT13 cluster report and GT17 ontology pressure) rather than live web discovery or Ollama.

### What must remain draft/candidate only

- Domain proposals: `status: draft` (never `active`, `experimental`, or merged without human checkpoint).
- No writes to domain registry / active domain tables.
- Theory candidates remain `status: candidate`.
- Ontology proposals remain `status: draft`.

### What must not be exported publicly

- Theory candidate reports / `theory_candidates` rows
- Ontology pressure reports / `ontology_proposals` rows
- Domain proposal reports / `domain_proposals` rows (future)
- Raw source text, prompts, secrets, local paths in persisted report JSON

## 8. Safety Findings

| Boundary | Status |
|---|---|
| Public export exposes theory candidates | **NO** — `export-public` uses `public_cards` only |
| Public export exposes ontology proposals | **NO** |
| Public export exposes domain proposals | **NO** — table does not exist yet |
| Theory candidates stored as facts | **NO** — GT15 asserts `status: candidate` |
| Ontology proposals auto-activate concepts | **NO** — GT17 asserts no active concept rows |
| Public write routes | **NONE** |
| Public ingestion routes | **NONE** |
| Public agent execution routes | **NONE** |
| Ticket-020 must not auto-activate domains | **spec requirement** — enforce in implementation |
| Ticket-020 must not write accepted concepts/domains/facts | **spec requirement** |
| Report JSON leaks paths/prompts/secrets | **NO** in current artifacts; GT11 guards export |

## 9. Runner / Audit Gate

From `.cursor/commands/rge-run-next-ticket.md`:

| Rule | Status |
|---|---|
| One ticket per invocation | **intact** |
| Medium/high risk → pre-ticket audit required | **ticket-020 medium** — this audit satisfies |
| Theory/inference/proposal milestones → audit | **domain proposal qualifies** — this audit satisfies |
| ≥3 consecutive done tickets since last audit | ticket-019 done; pre-ticket-019 audit existed before 019 impl; **020 audit required and provided** |
| Audits read-only (no queued ticket impl) | **this run complied** |
| ticket-020 blocked until audit committed | **YES — commit this report before `/rge-run-next-ticket`** |

## 10. Blocking Issues

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| B1 | **gate** | No pre-ticket-020 audit on main before implementation | **Commit this report**, then run `/rge-run-next-ticket` |
| — | — | No code/schema blockers for ticket-020 | — |

No failing tests, no main/origin drift, no ticket queue inconsistency, no report-vs-repo mismatches for tickets 017–019.

## 11. Recommended Next Action

1. **Commit** `agent_reports/2026-06-12_pre-ticket-020_domain-proposal-readiness-audit.md` to `main`.
2. Run **`/rge-run-next-ticket`** to implement ticket-020 on branch `phase-1/ticket-020-domain-proposal`.

## 12. Hardened Ticket-020 Scope

Implement exactly:

- [ ] `rge/db/migrations/0007_domain_proposals.sql` + `schema.sql` reference
- [ ] `DomainProposalRepository` + `make_domain_proposal_id` in `repositories.py`
- [ ] Full `domain_proposer.py` (threshold assess, golden padding, report build, persist, idempotent re-run)
- [ ] CLI `generate-domain-proposal`
- [ ] `tests/golden/test_18_domain_proposal.py` (4 tests: creates draft proposal with threshold proof, no auto-activation, no duplicate domains, idempotent CLI)
- [ ] Update `test_00_scaffold.py` and `test_01_ingestion.py`
- [ ] Deterministic art/design/film/music specialized-term vocabulary padding
- [ ] Proposed domain `creativity.film`; parent `creativity` + `art`; overlap `digital_media`
- [ ] `threshold_report_json` / `thresholds` block in proposal JSON
- [ ] Status always `draft`
- [ ] No Ollama, LangGraph, live web discovery, public export, public site, or automatic domain activation

**Non-goals (reconfirm):** Ollama, LangGraph, live web discovery, public write routes, public export changes, automatic domain activation.

---

**Recommendation: proceed with ticket-020 as the next smallest safe ticket** (after committing this audit report).
