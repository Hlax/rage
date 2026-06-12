---
template_id: audit_report
template_version: 1.0.0
status: current
---

# Pre-Ticket-059 Local Live Structured Task Probe Audit

- Audit type: read-only — local Qwen/Ollama structured-task probe readiness (before cloud)
- Date: 2026-06-12
- Scope: no OpenAI, no live runs in this audit, no code changes, no secrets
- Human goal: prove local Qwen/Ollama research path with one small live structured task outside CI

## 1. Executive verdict

**GO — seed local live probe ticket**

Live structured inference is wired for four pipeline tasks and Ollama/Qwen is ready on the operator machine, but there is **no fail-closed probe CLI**. Existing `extract-claims` can hit the default production SQLite path, its help text still describes mock-only behavior, live smoke tests only call `health_check()`, and `model_invocations` reporting is not implemented. The smallest safe path today is a **documented Python module call** (`extract_and_validate_for_chunk`) with no DB writes; that is sufficient for a one-off manual probe but not sufficient as the operator runbook. **Seed ticket-060** for a dedicated probe command, scratch report artifact, and optional smoke extension. **Keep ticket-059** as a deferred OpenAI placeholder — do not rewrite it for local probe work.

## 2. Release / repo state

| Check | Result | Evidence |
| ----- | ------ | -------- |
| Branch | `main` | `git checkout main` |
| Working tree | **clean** | `git status --short` → empty |
| Local HEAD | `57ac840c582be3aa525c6cf5f3cec3ec86c99d0a` | `git rev-parse HEAD` |
| `origin/main` | `57ac840c582be3aa525c6cf5f3cec3ec86c99d0a` | `git rev-parse origin/main` |
| Local equals remote | **yes** | HEAD == origin/main |
| Latest Golden Gate | **success** | run **27434448098** at `57ac840` |
| Prior implementation gate | **success** | run **27434370291** (ticket-058 `e5ff08b`) |
| ticket-058 | **done** | queue + agent report |
| CI mock-only | **yes** | Golden Gate sets `RGE_LLM_MODE=mock`, `RGE_ALLOW_LIVE_LLM=0` |
| Ollama / qwen2.5:7b | **ready** (human) | ticket-058 report; `model_available: true` |

## 3. Ticket-059 scope decision

**Keep ticket-059 as proposed/deferred OpenAI placeholder. Seed ticket-060 for local live structured probe.**

| Option | Recommendation | Rationale |
| ------ | -------------- | --------- |
| Keep ticket-059 as OpenAI placeholder | **Yes** | JSON status `proposed`, empty `expected_files`, title explicitly says OpenAI cloud adapter. Matches ticket-058 deferral and human instruction not to promote cloud yet. |
| Rewrite ticket-059 into local probe | **No** | Would orphan the cloud placeholder numbering and confuse queue history. OpenAI remains a distinct future concern after local path is proven. |
| Seed ticket-060 as local probe | **Yes** | Clean scope boundary: 059 = future cloud adapter; 060 = prove local Ollama structured task safely outside CI. |

Queue state: `TICKET_QUEUE.md` row 59 = `proposed` OpenAI placeholder; active ticket = `(none)`.

## 4. Current local live support

| Task | Live Ollama wired? | CLI available? | Safe to probe? | Notes |
| ---- | ------------------ | -------------- | -------------- | ----- |
| Claim extraction | **Yes** (`OllamaModelClient.extract_claims`) | `extract-claims` (persists to DB) | **Partial** | Best probe candidate. Module fn `extract_and_validate_for_chunk` is no-DB. CLI always persists; default `--db` is production path. |
| Concept linking | **Yes** (`link_concepts`) | `link-concepts` (persists) | **No** (for first probe) | Requires accepted claims + ontology seed in DB first. |
| Relationship drafting | **Yes** (`draft_relationships`) | `build-relationships` (persists) | **No** | Requires accepted claims + concept links. |
| Contradiction detection | **Yes** (`detect_contradictions`) | `detect-contradictions` (persists) | **No** | Requires claims + relationships across sources. |
| Run summary | **No** | none | **No** | `draft_run_summary` raises `OllamaNotAvailableInPhase0`. |
| Ticket drafting | **No** | none | **No** | `draft_ticket` raises `OllamaNotAvailableInPhase0`. |
| Health check | **Yes** (`health_check`) | `model-health` | **Yes** | Already proven; not a structured task. |
| Live smoke | health only | `pytest -m live_smoke` | **Partial** | `tests/smoke/test_live_ollama_smoke.py` — no structured call. |

**Effective mode:** `rge/llm/mode.py` — live only when `RGE_LLM_MODE=ollama` **and** `RGE_ALLOW_LIVE_LLM=1`. Fixture orchestration forces mock.

**Schema path:** Ollama `_structured_call` → JSON parse → `validate_schema_version` → Pydantic `CandidateClaimBatch_v0_1` → `claim_validator.validate_candidate_claims` (Python).

**Metadata gap:** `ModelCallMetadata` exists in `rge/llm/base.py` but is **not** persisted to `model_invocations` (table deferred). On DB persist path, `extractor_provider` / `extractor_model` / `llm_schema_version` are stored on claim rows only.

## 5. Recommended live probe

### Smallest safe probe (available today — module path, no new code)

Use **claim extraction on one fixture chunk** via `extract_and_validate_for_chunk` — no SQLite writes, no export, no Git.

**Input fixture:** `fixtures/sources/creativity_ai_diversity_short.txt` (~20 lines; golden GT02 source; contains quality ↑ and diversity ↓ claims plus limitations paragraph).

**Environment:**

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
```

**Pre-check:**

```powershell
python -m rge.cli model-health
# Expect: reachable=true, model_available=true, live_llm_enabled=true, effective_llm_mode=ollama
```

**Command (manual Python probe — not run in this audit):**

```powershell
python -c @"
import json
from pathlib import Path
from rge.config import load_config
from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client
from rge.modules.claim_extractor import extract_and_validate_for_chunk

text = Path('fixtures/sources/creativity_ai_diversity_short.txt').read_text(encoding='utf-8')
chunk = {'id': 'chunk_live_probe_001', 'source_id': 'src_live_probe_001', 'chunk_index': 0, 'chunk_text': text}
cfg = load_config()
client = get_model_client(cfg, mode=effective_llm_mode(cfg))
result = extract_and_validate_for_chunk(chunk, domain_pack='creativity', client=client)
report = {
    'probe': 'claim_extraction',
    'effective_llm_mode': effective_llm_mode(cfg),
    'provider': client.provider,
    'model': getattr(client, 'model', None),
    'schema_version': cfg.llm_schema_version,
    'accepted_count': len(result['accepted']),
    'rejected_count': len(result['rejected']),
    'accepted': result['accepted'],
    'rejected': result['rejected'],
}
print(json.dumps(report, indent=2))
"@
```

**Expected outputs:**

- Ollama `/api/generate` invoked with JSON format prompt
- stdout JSON with `provider: ollama`, `model: qwen2.5:7b`
- `accepted` / `rejected` lists after Python quote-span, scope, and injection checks
- Some rejections are **expected** (live model may omit quote spans — same as mock fixture path)

**Artifact location (operator):** redirect stdout to gitignored path, e.g. `data/reports/live_probe_claim_extraction.json` (directory under gitignored `data/`).

**What must NOT happen:**

- No writes to default `data/db/creative_research.sqlite` (this probe path avoids DB entirely)
- No `export-public` or `--publish`
- No `research run` (fixture orchestration forces mock; live discovery not implemented)
- No pytest in CI/golden with live env
- No shell/Git/file mutation from model adapter
- No API keys or cloud calls

### Secondary path (exists but not recommended as first probe)

Two-step CLI with **explicit scratch DB** under gitignored `data/`:

```powershell
$db = "data/db/live_probe_scratch.sqlite"
python -m rge.cli ingest fixtures/sources/creativity_ai_diversity_short.txt --domain creativity --db $db
# Parse source.id from ingest JSON output
python -m rge.cli extract-claims --source <source_id> --db $db
```

**Risk:** operator omits `--db` → writes to production SQLite; help text says "mock LLM"; persists accepted/rejected rows (staging-only if scratch path used). **Prefer ticket-060 CLI with mandatory scratch/probe guard.**

## 6. Safety controls

| Control | Status | Evidence |
| ------- | ------ | -------- |
| Model has no shell/Git access | **Confirmed** | `test_llm_package_has_no_write_side_effect_imports`; no subprocess in `rge/llm/` |
| Model does not directly write accepted DB | **Confirmed** | Clients return Pydantic candidates; `ClaimRepository` writes after validation |
| No public publish | **Confirmed** | Probe path excludes `export-public`; live export needs `--publish` for site dir |
| No cloud/API keys | **Confirmed** | No OpenAI/OpenRouter code; registry only `mock`/`ollama` |
| CI/golden mock-only | **Confirmed** | `pyproject.toml` excludes `live_smoke`; Golden Gate env |
| Python validation authoritative | **Confirmed** | `validate_candidate_claims` after model batch |
| Model output as candidate/report only | **Partial** | Module probe: stdout only. DB path: accepted/rejected tables after validation. `model_invocations` table not wired. |
| Live opt-in required | **Confirmed** | `RGE_ALLOW_LIVE_LLM=1` + `RGE_LLM_MODE=ollama` |

Policy alignment: `docs/agents/13_MODEL_ESCALATION_POLICY.md`, `10_SAFETY_MODEL.md`.

## 7. Proposed implementation ticket if needed

A dedicated ticket is **needed** for operator-grade probe UX. Proposed **ticket-060** (do not implement in this audit).

### Title

Local live structured probe CLI for claim extraction (scratch report, no production DB)

### Problem

Operators can run `model-health` and ticket-037 enables live Ollama structured tasks, but there is no fail-closed CLI to prove claim extraction end-to-end outside CI. Existing `extract-claims` persists to the default SQLite path and documents mock-only behavior. Live smoke tests do not call structured tasks. Manual Python one-liners are fragile and not in the runbook.

### Scope

- Add `python -m rge.cli probe-extract-claims` (or equivalent) that:
  - Requires live opt-in env (`RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`)
  - Reads one chunk from a fixture file or `--chunk-text` / `--fixture-source` path
  - Calls `extract_and_validate_for_chunk` only — **no DB persist by default**
  - Writes JSON report to `data/reports/live_probes/` (gitignored) with provider, model, schema_version, effective mode, accepted/rejected counts and payloads
  - Exits non-zero on Ollama unreachable or structured call failure
- Update `extract-claims` help text to mention live mode when opt-in is set (docs-only or help string)
- Extend `tests/smoke/` with optional `test_live_extract_claims_on_fixture_chunk` (marker `live_smoke`, skipped by default)
- Document probe in `13_MODEL_ESCALATION_POLICY.md` and `12_RUNTIME_CONFIG.md`
- Unit tests with mocked HTTP for CLI wiring (no CI Ollama)

### Expected files

- `rge/cli.py` — probe subcommand
- `rge/modules/live_probe.py` (optional small helper)
- `tests/unit/test_live_probe_cli.py`
- `tests/smoke/test_live_ollama_smoke.py` — optional structured probe test
- `docs/agents/13_MODEL_ESCALATION_POLICY.md`
- `docs/agents/12_RUNTIME_CONFIG.md`
- `tickets/ticket-060.json`
- `tickets/TICKET_QUEUE.md`
- agent report

### Acceptance criteria

- Operator can run one documented command with live env and fixture chunk; report lands under `data/reports/live_probes/`
- No write to default DB unless explicit `--persist-scratch-db` flag (default off)
- Golden/CI remain mock-only; new unit tests mock Ollama HTTP
- Probe report includes provider, model, effective_llm_mode, schema_version, accepted/rejected split
- Safety audit unchanged or extended with probe evidence check

### Test plan

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_live_probe_cli.py -q
python -m pytest -q
python -m rge.cli verify --skip-site
```

Manual (operator, outside CI):

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LOCAL_LLM = "qwen2.5:7b"
python -m rge.cli probe-extract-claims --fixture-source fixtures/sources/creativity_ai_diversity_short.txt
```

### Non-goals

- OpenAI / OpenRouter adapters (ticket-059 stays deferred)
- Full live research orchestration or live discovery
- Persisting to production SQLite by default
- Public export or `--publish`
- Wiring `model_invocations` table (separate ticket)
- CI Ollama dependency
- Live concept linking / relationships / contradictions probe (claim extraction only)

### Rollback plan

Remove probe subcommand and smoke extension; docs revert; no schema changes.

### Risk level

**low-medium** (new CLI + gitignored report path; no export/DB contract changes if default is no-persist)

## 8. Final recommendation

**Seed local live probe ticket (ticket-060). Defer OpenAI ticket-059.**

Do **not** implement OpenAI or rewrite ticket-059. Do **not** run live smoke or broad live research in this audit pass. After ticket-060 lands, run the documented `probe-extract-claims` command once on the operator machine. Optionally, a cautious operator may run the **module-path manual probe** in §5 today (no DB writes) before ticket-060 — that is acceptable but not the long-term runbook.

## Commands executed (read-only audit)

```powershell
git checkout main
git pull origin main
git status --short
git rev-parse HEAD
git rev-parse origin/main
gh run list --limit 3
```

Code/doc inspection only — no live Ollama structured calls, no API keys, no commits in this audit pass.
