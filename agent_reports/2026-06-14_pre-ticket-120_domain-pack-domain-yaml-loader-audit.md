---
template_id: pre_ticket_audit
status: GO
date: 2026-06-14
risk_level: low
ticket: ticket-120
---

# Pre-Ticket Audit: ticket-120 Domain Pack domain.yaml Loader Proof

## Verdict: **GO** (hardened scope)

Final NM-5 pack file. Load `domain.yaml` identity overlay; validate directory
`pack_id` matches YAML `id`; extend safety auditor domain-pack check to verify
`status: active` from pack metadata.

## Hardened scope

### In

1. `DomainIdentityOverlay` + `parse_domain_yaml()` (id, name, version, status, summary, lists).
2. Extend `DomainPack` with `domain_identity`.
3. `load_domain_pack()` loads `domain.yaml`; fail if `pack_id` ≠ `domain_identity.id`.
4. `verify_pack_identity_for_audit(pack)` — active status + id consistency.
5. Extend `safety_auditor._audit_domain_pack_safety_notes` to call identity verification.
6. Unit tests + `domain.yaml` stubs in all temp-pack tests.

### Out

- claim_validator primary_domains wiring (follow-on ticket).
- Public site / schema / live Ollama changes.

## Recommendation

Implement ticket-120 per hardened scope.
