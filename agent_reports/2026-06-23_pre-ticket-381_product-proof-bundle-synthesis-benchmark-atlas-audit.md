---
template_id: pre_ticket_audit
status: GO
date: 2026-06-23
risk_level: medium
ticket: ticket-381
category: Phase 3 / operator product proof
---

# Pre-Ticket Audit: ticket-381 Researcher Product Proof

## Verdict: **GO** (mock-first operator artifact; no accepted-graph writes from synthesis; no export-public widening)

Single mock-first operator proof chaining `prove-arbitrary-source-bundle` → `synthesize --packet`
(mock_cloud) → synthesis packet benchmark dry-run → safety audit snapshot → committed
`/atlas-preview` fixture visibility reference. Addresses principal-audit product-risk drift
(post-ticket-379).

## Milestone triggers

| Trigger | Applies? | Mitigation |
|---------|----------|------------|
| Public export (`export-public`, `card_exporter`) | **No** | Proof bundle uses existing mock export on temp paths only |
| Public site / committed public JSON | **Reference only** | Read committed `atlas_snapshot_preview.json`; no JSON rewrite in v0 |
| Schema migrations | **No** | Read-only graph counts |
| Theory / inference generation | **No** | Synthesis packet candidate output only (`no_accepted_graph_writes`) |
| Live OpenAI | **No** | `mock_cloud` default; benchmark refuses `--provider openai` |

## Hardened scope

### In scope

1. **`rge/modules/researcher_product_proof.py`**
   - Orchestrate mock proof bundle on temp `--db`
   - Record `source_count`, `claim_count`, `evidence_count` (relationship_evidence)
   - Run grounded fixture `synthesize --packet` (mock_cloud); record `synthesis_output_path`
   - Run synthesis packet benchmark (small default runs in tests; operator script may use 25)
   - Record `reports_per_hour_estimate` from benchmark summary
   - Run `run_safety_audit("full")`; record `status` + scan scope fields
   - Inspect committed atlas preview paths for visibility (`atlas_snapshot_preview.json`,
     `atlas_coherence_preview.json`)
   - Write gitignored artifact `data/reports/researcher_product_proof_latest.json`
   - Emit `product_verdict`: `GO` | `PARTIAL` | `NO-GO`

2. **CLI:** `prove-researcher-product` with temp `--work-dir` (or derived temp paths)

3. **Script:** `scripts/run_researcher_product_proof.py` operator wrapper

4. **Tests:** `tests/unit/test_researcher_product_proof.py` (mock network; injectable runners)

5. **Golden scaffold:** add CLI help entry for `prove-researcher-product`

### Out of scope

- README/AGENTS docs-only tickets
- Live OpenAI HTTP
- Model output → accepted DB tables
- `export-public` policy changes
- Public-site UI or committed preview JSON refresh
- Operator loop plan-mode wiring (follow-on)

## Safety checklist

| Risk | Control |
|------|---------|
| Model → accepted graph | Synthesis path keeps `no_accepted_graph_writes: true` |
| Secrets in artifact | `_private_value_violations` on artifact payload |
| Live OpenAI default | `mock_cloud` only; gates unchanged |
| Public write routes | Safety audit full pass required for GO |

## Test plan (implementation)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_researcher_product_proof.py -q
python -m pytest tests/golden -q
python -m rge.cli verify --skip-site
python -m rge.modules.safety_auditor --audit full
```

## Recommendation

**GO** — smallest end-to-end product proof artifact closing docs/wiring → product lane.
Rollback = revert new module, script, CLI subcommand, and tests.
