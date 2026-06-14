---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: medium
ticket: ticket-114
---

# Pre-Ticket Audit: ticket-114 Domain Pack evidence_types.yaml Loader Proof

## Verdict: **GO** (hardened scope)

Ticket-113 proved `scoring.yaml` drives score reconciliation. The creativity pack's
`evidence_types.yaml` exists with six categories and base_strength priors but is **not
loaded at runtime**. Claim validation today checks `evidence_type` presence only — no
pack-backed allowlist. Wiring a narrow loader plus claim-validator gate is bounded,
deterministic, and does not require schema migrations, live Ollama, or public export changes.

## Current state

### Domain pack loader (`rge/modules/domain_pack_loader.py`)

| Loaded today | Not loaded |
|--------------|------------|
| `ontology.yaml` | `evidence_types.yaml` |
| `aliases.yaml` | `claim_schema.yaml`, `source_preferences.yaml`, … |
| `scoring.yaml` (`score_reconciliation` only) | |

`DomainPack` fields: `pack_id`, `concepts`, `aliases`, `alias_to_canonical`, `score_reconciliation`.

### Creativity `evidence_types.yaml` (committed)

Six types: `empirical`, `meta_analysis`, `case_study`, `theory`, `interview`, `benchmark`
each with `base_strength` and `notes`. Matches `docs/agents/06_DOMAIN_PACK_SPEC.md` section 9.

### Claim validator (`rge/modules/claim_validator.py`)

- Requires `evidence_type` field non-empty (`REJECTION_UNSUPPORTED`)
- **No allowlist** against pack-defined types
- Golden/manual fixtures use `evidence_type: "empirical"` (in pack)
- Prompt-injection fixture uses `evidence_type: "instruction"` — rejected earlier via
  `candidate_has_prompt_injection()` before evidence-type gate; behavior unchanged

### Tests that lock current behavior

| Test | evidence_type used |
|------|-------------------|
| `tests/golden/test_02_claim_extraction.py` | `empirical` |
| `tests/unit/test_manual_source_pipeline_e2e.py` | `empirical` (fixtures) |
| `tests/golden/test_24_prompt_injection.py` | `empirical` accepted; `instruction` rejected via injection |
| `tests/unit/test_claim_rejection_diagnostics.py` | `empirical` |

All must remain green when creativity pack allowlist includes `empirical`.

## Hardened scope for ticket-114

### In

1. Add `EvidenceTypeDefinition` frozen dataclass + `parse_evidence_types_yaml()` in
   `domain_pack_loader.py`.
2. Extend `DomainPack` with `evidence_types: tuple[EvidenceTypeDefinition, ...]`.
3. `load_domain_pack()` loads `evidence_types.yaml`; fail closed if section missing or empty.
4. Add helper `evidence_type_ids(pack) -> frozenset[str]` (normalized ids).
5. **Consumer:** `claim_validator.validate_candidate_claim()` — after injection/scope checks,
   when `domain` is present, load pack and reject unknown `evidence_type` with
   `unsupported_claim` (existing reason) and diagnostic naming the unknown type.
   Skip allowlist when domain pack cannot be loaded (fail closed → reject).
6. **Proof test** `tests/unit/test_domain_pack_evidence_types_loader.py`:
   - Creativity pack loads six types with expected `base_strength` for `empirical` (0.80)
   - Temp pack with only `benchmark` rejects `empirical` for `domain: demo`
   - Temp pack accepts `benchmark` when other validation passes
7. Update existing temp-pack stubs in loader/scoring tests to include minimal
   `evidence_types.yaml` (required once `load_domain_pack` loads it).

### Explicitly out (do not broaden)

- Applying `base_strength` priors to confidence scoring (future ticket)
- Loading `claim_schema.yaml`, `source_preferences.yaml`, or other pack files
- Schema migrations
- Cloud / live Ollama
- Public site / export

## Minimal safe implementation path

```
load_domain_pack(pack_id)
  → parse evidence_types.yaml
  → DomainPack(..., evidence_types=(EvidenceTypeDefinition(...), ...))

validate_candidate_claim(candidate, ...)
  → domain = candidate.get("domain")
  → pack = load_domain_pack(domain)
  → if candidate["evidence_type"] not in evidence_type_ids(pack):
        reject unsupported_claim
```

## Mock/golden determinism preservation

- Creativity allowlist includes `empirical` used by all golden/manual fixtures.
- Prompt-injection `instruction` types still rejected by injection gate first.
- Proof of pack authority via temp-pack test with restricted allowlist.

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Golden claim extraction drift | Medium | Creativity list includes `empirical` |
| Prompt-injection test drift | Low | Injection check precedes evidence-type gate |
| `DomainPack` dataclass change | Low | Add field; update temp-pack stubs |
| Over-scoping into base_strength scoring | Medium | Hardened scope: allowlist only |

## Expected files to change

| File | Change |
|------|--------|
| `rge/modules/domain_pack_loader.py` | Parse evidence_types; extend `DomainPack` |
| `rge/modules/claim_validator.py` | Pack-backed evidence_type allowlist |
| `tests/unit/test_domain_pack_evidence_types_loader.py` | New proof tests |
| `tests/unit/test_domain_pack_loader.py` | Scoring stubs + evidence_types stubs |
| `tests/unit/test_domain_pack_scoring_loader.py` | evidence_types stubs in demo packs |
| `agent_reports/2026-06-14_ticket-114_domain-pack-evidence-types-loader.md` | Implementation report |

## Tests to add / run

**New:**

- `test_creativity_pack_loads_evidence_types`
- `test_temp_pack_restricted_allowlist_rejects_empirical`
- `test_temp_pack_accepts_benchmark_evidence_type`

**Regression (ticket test_plan):**

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_domain_pack_evidence_types_loader.py -q
python -m pytest tests/unit/test_domain_pack_scoring_loader.py -q
python -m pytest tests/golden -q
python -m pytest -q
python -m rge.modules.safety_auditor --audit full
```

## Principal audit gate

After this report is committed, `python -m rge.modules.principal_audit_gate --next-ticket ticket-114`
should show `implementation_gate: satisfied` for medium-risk ticket-114.

Cadence: satisfied (1 done ticket since post-ticket-110 checkpoint; ticket-113).

## NO-GO triggers (none active)

- Would be NO-GO if golden fixtures used evidence types absent from creativity pack — **they use `empirical`, which is in pack**.
- Would be NO-GO if allowlist gate ran before injection check and changed GT24 — **injection check stays first**.
- Would be NO-GO if schema migration required — **it is not**.

## Recommendation

Proceed with ticket-114 on branch `phase-2/ticket-114-domain-pack-evidence-types-loader`.
Next smallest product move: wire `claim_schema.yaml` or apply `base_strength` priors — not another doc cross-link.
