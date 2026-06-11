---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 0 / ticket-001 / repo-scaffold-model-runtime

## 1. Summary

Implemented the Phase 0 / 0.5 scaffold: installable `rge` Python package with a `research` CLI stub (run / export-public / verify), typed env config loading, a SQLite schema placeholder naming the 16 expected core tables, the formal LLM adapter boundary (`rge/llm`: `ModelClient` ABC, versioned Pydantic candidate-output schemas, deterministic mock client, configured Ollama client boundary, fail-closed registry), domain-general module/safety stubs, the creativity domain pack YAML stubs, deterministic fixtures, three golden scaffold tests (24 assertions total), and a static read-only Next.js public-site placeholder that builds from static JSON only.

## 2. Ticket

- Ticket ID: ticket-001
- Ticket title: Scaffold repo and model runtime adapter
- Branch: `phase-0/ticket-001-repo-scaffold-model-runtime`
- Phase: 0 / 0.5
- Agent/model: Cursor builder agent (Fable 5)
- Date: 2026-06-11

## 3. Scope

### In Scope

- Repo scaffold per the ticket's explicit expected-file list.
- Model runtime adapter boundary per `docs/agents/03_MODEL_RUNTIME_SPEC.md`.
- Mock LLM mode that is deterministic and Ollama-independent.
- Golden scaffold tests and static public-site placeholder.
- Reporting/ticket loop preservation.

### Out of Scope / Non-Goals

- Phase 1 ingestion/extraction/validation, LangGraph orchestration, live Ollama inference, public export logic, dashboard, crawling, model weights, public write/ingestion/agent routes, model-controlled shell/Git.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `pyproject.toml` | New: setuptools package `rge`, console script `research`, deps `pydantic>=2`, dev `pytest`. |
| `.env.example` | New: 9 documented model/runtime settings (Ollama URL, model, modes, timeout, temperature, schema version, embeddings). |
| `.gitignore` | New: Python, node, Next.js, `.env`, local sqlite artifacts. |
| `README.md` | Rewritten from 1-line stub: project overview, install, verification commands, layout, boundaries. |
| `rge/__init__.py`, `rge/config.py`, `rge/cli.py` | New: package, typed `RgeConfig` env/.env loader with `ConfigError`, argparse CLI with run/export-public/verify placeholders that exit non-zero with machine-readable JSON. |
| `rge/db/__init__.py`, `connection.py`, `repositories.py`, `schema.sql` | New: connection helper (unused in Phase 0), repository docstring stub, schema placeholder with 16 `CREATE TABLE IF NOT EXISTS` statements. |
| `rge/llm/__init__.py`, `base.py`, `schemas.py`, `mock_client.py`, `ollama_client.py`, `registry.py` | New: `ModelClient` ABC (5 task methods), `ModelCallMetadata` envelope, versioned `*_v0_1` candidate schemas + `validate_schema_version` (fail closed), deterministic fixture-backed mock client, configured Ollama boundary (`health_check` only; structured tasks raise `OllamaNotAvailableInPhase0`), fail-closed registry with no silent fallback. |
| `rge/models/__init__.py`, `schemas.py`, `contracts.py`, `reports.py` | New: docstring stubs referencing data model / contract / reporting specs. |
| `rge/modules/*.py` (19 modules + `__init__.py`) | New: docstring stubs with contracts and `NotImplementedError` entry functions. `safety_auditor.py` runnable via `python -m`, prints `NOT AVAILABLE IN THIS PHASE` JSON and exits 3. |
| `rge/safety/__init__.py`, `public_export_policy.py`, `prompt_injection.py`, `route_audit.py`, `secrets_audit.py` | New: policy constants from `10_SAFETY_MODEL.md` (allowed public fields/routes, forbidden export content, injection effects, secret categories); no fake logic. |
| `domain_packs/creativity/*.yaml` (10 files) | New: domain identity, ontology with the 21 required v1 concepts, aliases, source preferences, evidence types, scoring overlay, claim schema extensions, card templates, search templates, safety notes. |
| `fixtures/sources/*.txt` (3 files) | New: short AI-diversity passage, divergent-prompting contradiction passage, canonical prompt-injection fixture. |
| `fixtures/llm_outputs/*.json` (2 files) | New: claim-extraction batch (one valid claim + one missing quote span) and overgeneralized-claim batch, both `schema_version 0.1.0`. |
| `fixtures/candidate_sources/source_ranking_fixture.json` | New: 5 fake candidate sources for Golden Test 9. |
| `tests/golden/test_00_scaffold.py` | New: imports, CLI help, placeholder honesty, schema table names, domain pack/fixture/.env.example presence (11 tests). |
| `tests/golden/test_00_model_runtime.py` | New: registry mock/ollama selection, fail-closed unknown mode, deterministic versioned mock output, schema-version mismatch fails closed, Ollama honesty in Phase 0, no-write-side-effect import scan of `rge.llm` (7 tests). |
| `tests/golden/test_00_public_site_static.py` | New: static JSON existence/parsing, curated-field whitelist, forbidden-content patterns, no API routes, no write/unsafe source patterns, static export config (6 tests). |
| `tests/unit/.gitkeep` | New: materializes unit test directory. |
| `apps/public-site/package.json`, `next.config.js`, `tsconfig.json`, `app/layout.tsx`, `app/page.tsx` | New: Next.js 15 App Router placeholder, `output: 'export'`, single read-only page importing static JSON; no fetches, forms, API routes, or raw HTML rendering. |
| `apps/public-site/public/data/public_cards.json`, `public_memos.json`, `build_info.json` | New: placeholder static data with only curated public fields. |
| `apps/public-site/package-lock.json` | New: generated by `npm install` (committed for reproducible builds). |
| `tickets/ticket-001.json` | New: full ticket record for the implemented scope, status `done`. |
| `tickets/ticket-006.json` | New: recommended next ticket (migration harness + source ingestion), status `proposed`. |
| `tickets/TICKET_QUEUE.md` | Updated: ticket-001 `done` with report link; 002/004/005 `superseded` with explanation; 003 left open; ticket-006 added; queue notes appended. |

## 5. Implementation Notes

- **Minimal dependencies.** Only `pydantic>=2` at runtime; CLI is stdlib argparse, `.env` parsing is a tiny stdlib reader, the Ollama boundary uses stdlib `urllib` (and only inside the explicitly-invoked `health_check`). Keeps the scaffold small and reversible.
- **Fail-closed everywhere.** Unknown `RGE_LLM_MODE` raises `LlmModeError`; schema-version mismatch raises `SchemaVersionError`; CLI placeholders and the safety auditor exit non-zero with machine-readable JSON so nothing can be mistaken for a pass.
- **No model client side effects.** `rge/llm` imports nothing from `rge/db` and never touches sqlite3/subprocess/shutil; a golden test enforces this by source scan.
- **Claims lifecycle representation.** The ticket required placeholder tables `claims_staged` / `claims_accepted` / `claim_rejections`, while `05_DATA_MODEL.md` models a single `claims` table with a status column. The placeholder follows the ticket and documents the discrepancy in a header comment; reconciliation is assigned to ticket-006 (see Spec Deviations).
- **Public site determinism.** `outputFileTracingRoot` is pinned in `next.config.js` because a stray lockfile in the user home directory made Next infer the wrong workspace root.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Repo scaffold exists | PASS | All expected files created. |
| Python package imports | PASS | `test_rge_package_imports`, `test_subpackages_import`. |
| CLI help works | PASS | All four help commands verified via installed `research` script and `python -m rge.cli`. |
| LLM adapter boundary exists | PASS | `rge/llm` package with base/schemas/mock/ollama/registry. |
| Mock mode is deterministic | PASS | `test_mock_client_returns_deterministic_versioned_output`. |
| Ollama mode represented as local adapter boundary | PASS | Config-driven client; structured tasks fail honestly in Phase 0; no import-time network I/O. |
| `.env.example` documents model/runtime settings | PASS | All 9 keys present; asserted by golden test. |
| SQLite schema placeholder exists | PASS | 16 expected tables asserted by golden test. |
| Creativity domain pack stubs exist | PASS | 10 YAML files; core engine stays domain-general. |
| Fixture directories and sample fixtures exist | PASS | sources/llm_outputs/candidate_sources all present. |
| Public site placeholder builds from static JSON | PASS | `npm run build` succeeded (static export, 4 pages). |
| Golden scaffold tests pass or failures documented | PASS | 24/24 passed. |
| Agent report written | PASS | This file. |
| Ticket queue updated honestly | PASS | ticket-001 done; 002/004/005 superseded with explanation; 003 open; 006 proposed. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pip install -e ".[dev]"` | PASS | Editable install OK on Python 3.14.3; `research.exe` lands in a Scripts dir not on PATH (Windows note below). |
| `pytest` | PASS | 24 passed in 0.18s. |
| `pytest tests/golden` | PASS | 24 passed. |
| `research --help` | PASS | Run via full Scripts path; also verified `python -m rge.cli --help`. |
| `research run --help` | PASS | |
| `research export-public --help` | PASS | |
| `research verify --help` | PASS | |
| `cd apps/public-site && npm install && npm run build` | PASS | Static export, no API/DB required. npm reported 2 moderate advisories in transitive dev deps (noted under risks). |
| `python -m rge.modules.safety_auditor --audit full` | NOT AVAILABLE IN THIS PHASE | By design: prints machine-readable non-result JSON and exits 3. Not a pass. |
| `research run --topic ... --fixture-mode` (end-to-end) | NOT AVAILABLE IN THIS PHASE | Placeholder prints `not_implemented` JSON and exits 2. Phase 3 scope. |
| `research export-public --limit 100` (real export) | NOT AVAILABLE IN THIS PHASE | Placeholder. Phase 4 scope. |

## 8. Test Results

### Passing

- `tests/golden/test_00_scaffold.py` — 11/11.
- `tests/golden/test_00_model_runtime.py` — 7/7.
- `tests/golden/test_00_public_site_static.py` — 6/6.

### Failing

- None.

### Not Available Yet

- Golden tests 1–26 (ingestion through E2E) — later phases.
- Deterministic safety auditor — Phase 4/5.

## 9. Safety Audit Status

- Required: yes (ticket touches public site files and model runtime boundary)
- Status: not run — the deterministic auditor is NOT AVAILABLE IN THIS PHASE.
- Notes: Safety properties are partially enforced now by golden tests: no public API routes, no write/unsafe patterns or `dangerouslySetInnerHTML` in site source, curated-field whitelist and forbidden-content scan over static JSON, and a no-side-effect import scan over `rge/llm`. These are scaffold-level checks, not a substitute for the full auditor.

## 10. Spec Deviations

1. **Claims lifecycle tables.** `rge/db/schema.sql` uses `claims_staged` / `claims_accepted` / `claim_rejections` as required by ticket-001's schema list, whereas `docs/agents/05_DATA_MODEL.md` (higher-priority spec) models one `claims` table with `status` plus `claim_quotes`. Documented in the schema header; reconciliation assigned to ticket-006. No code depends on the placeholder shape.
2. **Schema placeholder breadth.** The placeholder omits several 05_DATA_MODEL.md tables (e.g. `claim_quotes`, `concept_aliases`, `relationship_evidence`, `candidate_sources`, `model_invocations`). Intentional Phase 0 minimalism; the full schema is Phase 1 scope.
3. **`research ingest` subcommand** is not stubbed (only run/export-public/verify were required by this ticket). It arrives with ticket-006.

## 11. Known Risks / Gaps

- `research.exe` installs to a Scripts directory not on PATH in this Windows environment; use the full path or `python -m rge.cli` until PATH is adjusted.
- `npm audit` reports 2 moderate advisories in transitive dev dependencies of Next 15.5.x; build-time only, no runtime exposure on a static site. Revisit when bumping Next.
- The mock client resolves `fixtures/` relative to the repo checkout (editable-install layout); a non-editable install would need an explicit `fixtures_dir`. Acceptable for the local-first MVP.
- `pytest` currently passes without forcing `RGE_LLM_MODE=mock` because no test path can reach live Ollama; tests that select clients set the mode explicitly via monkeypatch.

## 12. Rollback Plan

Delete or abandon branch `phase-0/ticket-001-repo-scaffold-model-runtime` (or revert its merge commit). The ticket touches no database, no public deployment, and no external state; `tickets/TICKET_QUEUE.md` and the new files revert with the branch. Locally generated artifacts (`*.egg-info`, `node_modules/`, `.next/`, `out/`) are gitignored and can be deleted freely.

## 13. Recommended Next Ticket

See `tickets/ticket-006.json`:

```json
{
  "title": "Add SQLite migration harness and source ingestion",
  "problem": "The scaffold has a schema placeholder but no way to create the database or persist sources. Phase 1 needs a migration harness that applies the schema (reconciled with 05_DATA_MODEL.md claims lifecycle) and a 'research ingest' command satisfying Golden Test 1.",
  "evidence": [
    "docs/agents/00_GOLDEN_TESTS.md Test 1",
    "docs/agents/02_ARCHITECTURE.md section 11 Phase 1 scope",
    "This report, Spec Deviations 1-2"
  ],
  "affected_modules": ["rge/db", "rge/modules/fetcher.py", "rge/modules/parser.py", "rge/cli.py"],
  "expected_files": [
    "rge/db/migrations/0001_initial.sql",
    "rge/db/connection.py",
    "rge/db/repositories.py",
    "rge/db/schema.sql",
    "rge/modules/fetcher.py",
    "rge/modules/parser.py",
    "rge/cli.py",
    "tests/golden/test_01_ingestion.py"
  ],
  "acceptance_criteria": [
    "Migration harness creates the DB from versioned migrations.",
    "Schema reconciles claims lifecycle with 05_DATA_MODEL.md.",
    "research ingest persists source + chunks with stable IDs, checksum, status 'ingested'.",
    "Source survives restart.",
    "pytest tests/golden passes without Ollama."
  ],
  "test_plan": ["pytest tests/golden/test_01_ingestion.py", "pytest tests/golden"],
  "non_goals": ["No claim extraction/validation", "No concept linking/relationships/scoring", "No URL/PDF fetching beyond local text", "No public site/export changes"],
  "risk_level": "low",
  "rollback_plan": "Revert the ticket branch; delete locally created data/db/*.sqlite."
}
```

## 14. Suggested Next Prompt

```txt
You are the builder agent for the Research Graph Engine repo.

Read AGENTS.md, tickets/TICKET_QUEUE.md, tickets/ticket-006.json,
docs/agents/05_DATA_MODEL.md, docs/agents/00_GOLDEN_TESTS.md (Test 1), and
agent_reports/2026-06-11_phase-0_ticket-001_repo-scaffold-model-runtime.md.

Implement ticket-006 only, on branch phase-1/ticket-006-migrations-source-ingestion:

1. Add a SQLite migration harness (rge/db/migrations/0001_initial.sql applied
   through rge/db/connection.py), reconciling the claims lifecycle with
   05_DATA_MODEL.md (single claims table with status + claim_quotes table,
   preserving rejection reasons).
2. Implement local text-file ingestion: fetcher reads the file, parser chunks
   it with checksums, repositories persist source + chunks with stable
   prefixed IDs, timestamps, and status 'ingested'.
3. Add a 'research ingest <path> --domain <domain>' subcommand.
4. Add tests/golden/test_01_ingestion.py per Golden Test 1, including
   re-read-after-restart. Tests must not require Ollama.

Do not implement claim extraction, concept linking, relationships, scoring,
URL/PDF fetching, or public export. Run pytest tests/golden and the full
ticket test plan, write an agent report to agent_reports/, update
tickets/TICKET_QUEUE.md honestly, and recommend the next smallest ticket.
```
