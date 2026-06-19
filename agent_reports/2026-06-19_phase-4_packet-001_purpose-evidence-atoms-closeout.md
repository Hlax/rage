# Packet 001 Closeout: Purpose + Evidence Atom Schema Foundation

Date: 2026-06-19
Branch: `phase-4/packet-001-purpose-evidence-atoms`
Decision: GO

## Outcome

Packet 1 is complete as a conservative foundation packet. RGE now has a
deterministic research-purpose layer, versioned evidence atom/card contracts,
operator-private evidence atom persistence, and report propagation for purpose,
asset affordance, evidence maturity, and training suitability.

This packet deliberately did not expand frontend/public export behavior, live
network behavior, bulk corpus acquisition, PDF parsing, or autonomous ticket loops.

## GO / PARTIAL / NO-GO

GO.

Reason:

- The schema foundation exists.
- Purpose metadata is persisted on research contracts.
- Run and cluster reports expose purpose/maturity/training fields.
- Evidence atoms can only be promoted from accepted quote-backed claims.
- Canonical evidence cards are available as operator-private objects.
- Mock-only verification passed.
- Safety audit passed.

## Verification

- Targeted Packet 1 tests: PASS.
- Migration/report/schema tests: PASS.
- `python -m rge.cli verify --skip-site`: PASS.
  - Golden tests: 157 passed.
  - Full pytest: 934 passed, 35 deselected.
  - Safety audit: pass.

Site build was skipped through the repo-supported `--skip-site` verification path.
No public-site or public export allowlist changes were made.

## Ranked Next 3 Packets

1. Packet 2: Evidence atom promotion and clustering.
   Build a deterministic claim-to-atom promotion pass over accepted claims, atom
   merge rules, contradiction/qualification attachment, cluster-level top atom
   selection, and idempotency tests.

2. Packet 3: Source acquisition and text quality gates before extraction.
   Add hard gates for dirty PDF/text extraction, source quality metrics in reports,
   and explicit parse/acquisition failure categories before LLM calls.

3. Packet 4: Quote-first extraction hardening.
   Move extraction toward quote-span-first candidate generation, zero-quoteable-span
   outcomes, and narrower entailment/scope validation before claim proposal.

## Honest Drift / Weakness Notes

- Evidence atoms are foundation-ready but not yet automatically produced in the
  normal extraction/link/build spine. Promotion exists as a deterministic function,
  not as a default pipeline stage.
- Atom merging is not implemented yet. Current atom IDs are stable per canonical
  claim text and scope, which is safe but does not yet collapse semantically similar
  claims.
- `top_evidence_atoms` is wired into cluster evidence packets, but remains empty
  until atom promotion is invoked.
- The deterministic classifier is intentionally simple. It passed the required
  fixture categories, but it is keyword-based and should not be treated as deep
  semantic understanding.
- Training suitability remains conservative. Nothing is marked `training_ready`.
- Canonical evidence cards are operator-private only. Public evidence-card export
  still needs a dedicated safety/allowlist packet.
- Runtime proof is mock-only. No live OpenAlex, live fetch, live PDF, or live Ollama
  proof was run for this packet because Packet 1 did not require live APIs.

## Suggested Next Prompt

Implement Packet 2: deterministic evidence atom promotion and cluster integration.
Start from accepted quote-backed claims, add idempotent atom promotion for all
accepted claims in a domain/run, attach support/contradiction/qualification counts,
surface top atoms in cluster reports, and add tests for claim-to-atom creation,
similar-meaning merge boundaries, contradiction attachment, and conservative
maturity updates.
