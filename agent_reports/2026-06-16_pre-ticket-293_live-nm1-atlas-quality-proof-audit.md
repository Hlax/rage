---
template_id: pre_ticket_audit
status: GO
date: 2026-06-16
risk_level: high
ticket: ticket-293
category: Phase 3 / live research quality / Research Atlas validation
---

# Pre-Ticket Audit: ticket-293 Live NM-1 Extraction + Atlas Coherence Quality Proof v0

## Verdict: **GO** (operator-only live Ollama run; no default pytest live collection)

Product-centered proof that live research extraction produces meaningful graph data for
future Research Atlas UI — not another pipeline-mechanics-only ticket.

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Live Ollama | **Yes** | Operator opt-in only (`RGE_ALLOW_LIVE_LLM=1`, `RGE_LLM_MODE=ollama`); `model-health` preflight |
| Live network | **No** | Manual_text NM-1/NM-4 path only; no OpenAlex |
| Public export | **No** | Private `export-atlas-snapshot` to gitignored `data/` paths |
| Public site | **No** | No site or committed public JSON changes |
| Schema migrations | **No** | Temp/evidence DB via existing CLI |
| Theory / inference | **No** | Read-only atlas projection + coherence report |

## Hardened scope

### In scope

1. **Operator live run** on explicit non-default-graph DB (gitignored under `data/`):
   - `model-health` preflight
   - Ingest `fixtures/sources/ticket127_arbitrary_manual_live.txt` as `manual_text`
   - **NM-1 core:** `extract-claims-live` (or equivalent live validated write)
   - **NM-4 expansion (allowed, same gates):** optional live fallthrough
     `link-concepts`, `build-relationships` for linkage/edge quality assessment
2. **Private atlas export:** `export-atlas-snapshot` (no `--fixture-mode`) to gitignored path
3. **Coherence report:** `atlas-coherence-report` on exported snapshot
4. **Agent report** with human-readable quality verdict **GO / PARTIAL / NO-GO** answering:
   - useful claims, source linkage, concept/domain linkage, edges, follow-ups, lineage,
     frontend-readiness, next concrete improvement ticket
5. **Mock regression:** `pytest tests/golden` + full `pytest` remain green (mock LLM)

### Out of scope

- New default pytest live tests or CI live collection
- Public atlas route / public-site UI
- Schema migrations / `review_batch` persistence
- Staged OpenAlex network proofs
- Production code changes unless minimal operator helper (prefer CLI-only)
- Golden card seeding masquerading as live card quality (document honestly if `ensure_golden_public_cards` activates)

### Quality verdict rubric (agent report)

| Verdict | When |
|---------|------|
| **GO** | Live claims accepted with quotes; concepts linked; edges present; atlas coherence partial+ with meaningful population |
| **PARTIAL** | Pipeline works but weak linkage, missing runs/reports, golden card placeholder, or sparse graph |
| **NO-GO** | Live gates block run, zero accepted claims, or atlas export/coherence fail-closed |

## Safety

- All DB/JSON/MD artifacts under gitignored `data/` — never `apps/public-site/` or `data/exports/` public paths
- Fail-closed export: validation + private-field scan before atlas write (existing builder)
- Refuse default graph DB for live writes (existing gate)
- Honest blocker documentation when Ollama unavailable (NO-GO with exact env gate)

## Operator verification commands (post-implementation)

Document exact paths in agent report. Template:

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python -m rge.cli model-health
# ingest → extract-claims-live → [link/build live fallthrough] → export-atlas-snapshot → atlas-coherence-report
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q
python -m pytest -q
```

## Recommendation

**GO** — implement operator live quality proof + agent report; pivot from Atlas pipeline
mechanics (289–292) to live research output validation.
