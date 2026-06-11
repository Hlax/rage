# REPORTING_SPEC.md

## 1. Purpose

Reports are how the Research Graph Engine observes itself, supports synthesis, and improves. Reports must be JSON-first and prose-second. Prose is useful for humans, but the system must be able to query reports later.

Reports must support:

- Run observability.
- Claim quality analysis.
- Score change history.
- Cluster intelligence.
- Theory candidate generation.
- Ontology pressure detection.
- Domain proposal thresholds.
- Improvement ticket generation.
- Safety audit pass/fail.

## 2. Report Types

Required report types:

```txt
node reports
run reports
claim quality reports
score change reports
cluster reports
ontology pressure reports
domain proposal reports
theory candidate reports
improvement ticket reports
safety audit reports
```

## 3. Reporting Triggers

```txt
Every run: run report
Every node execution: node report
Every 5 runs or 25 accepted claims: light intelligence review
15 claims + 3 sources in a cluster: cluster report
30 claims + 5 sources + mixed stances: strong cluster report
75 accepted claims or ontology pressure signal: ontology report
40 claims + 8 sources + distinct vocabulary + repeated mismatch: domain proposal
Every candidate theory: theory candidate report
Every public export: safety audit report
Every 20 runs or 100 accepted claims: full system review
```

## 4. Common Report Envelope

Every report JSON should use a common envelope.

```json
{
  "id": "rep_...",
  "report_type": "run_report",
  "schema_version": "0.1.0",
  "run_id": "run_...",
  "contract_id": "contract_...",
  "domain_pack": "creativity",
  "status": "pass | fail | partial | informational",
  "created_at": "...",
  "input_ids": {},
  "output_ids": {},
  "metrics": {},
  "findings": [],
  "failures": [],
  "recommendations": [],
  "prose_summary": ""
}
```

## 5. Node Reports

Every LangGraph node must emit a node report.

Required fields:

```json
{
  "report_type": "node_report",
  "run_id": "run_...",
  "node_name": "ValidateClaims",
  "status": "pass | fail | partial | skipped",
  "input_ids": {
    "candidate_claims": ["clm_..."]
  },
  "output_ids": {
    "accepted_claims": ["clm_..."],
    "rejected_claims": ["clm_..."]
  },
  "metrics": {
    "input_count": 5,
    "accepted_count": 3,
    "rejected_count": 2
  },
  "failures": [
    {
      "entity_id": "clm_...",
      "reason": "missing_quote_span"
    }
  ]
}
```

Node report rules:

- A node report must be emitted even on failure.
- Failures must be machine-readable.
- Input/output entity IDs must be stored.
- Model-assisted nodes must include `model_provider`, `model_name`, `llm_mode`, `task_name`, `schema_version`, and `prompt_template_version` in `metrics` or a dedicated `model_runtime` object.
- Model-assisted nodes must report whether mock or live Ollama mode was used.
- Raw model responses must not be public-exported.

## 6. Run Reports

Every research run must produce a run report.

Minimum JSON:

```json
{
  "run_id": "run_...",
  "topic": "Does AI improve creative output while reducing diversity?",
  "domain_pack": "creativity",
  "contract_id": "contract_...",
  "sources_discovered": 5,
  "sources_queued": 3,
  "sources_ingested": 2,
  "claims_extracted": 8,
  "claims_accepted": 4,
  "claims_rejected": 4,
  "relationships_created": 2,
  "relationships_updated": 1,
  "score_events_created": 2,
  "cards_exported": 2,
  "cluster_reports_created": 1,
  "theory_candidates_created": 1,
  "top_failure_modes": [
    {"reason": "overgeneralized_scope", "count": 2},
    {"reason": "missing_quote_span", "count": 1}
  ],
  "tickets_generated": 1,
  "safety_audit_status": "pass"
}
```

Run report acceptance:

- Must be written even if run completes with failures.
- Must include counters for accepted and rejected claims.
- Must include failure modes.
- Must be queryable by ticket generation.

## 7. Claim Quality Reports

Triggered per run and optionally per extractor version.

Required fields:

```json
{
  "report_type": "claim_quality_report",
  "run_id": "run_...",
  "extractor_model": "qwen_...",
  "claims_extracted": 8,
  "claims_accepted": 4,
  "claims_rejected": 4,
  "rejection_breakdown": {
    "missing_quote_span": 1,
    "overgeneralized_scope": 2,
    "weak_concept_mapping": 1
  },
  "examples": {
    "accepted": ["clm_..."],
    "rejected": ["clm_..."]
  },
  "recommended_actions": [
    "Tighten extraction prompt to preserve source scope.",
    "Require quote_span field in model output schema."
  ]
}
```

## 8. Score Change Reports

Triggered when score events are created.

Required fields:

```json
{
  "report_type": "score_change_report",
  "run_id": "run_...",
  "score_events": [
    {
      "entity_type": "relationship",
      "entity_id": "rel_...",
      "old_score": 0.52,
      "new_score": 0.64,
      "triggering_claim_id": "clm_...",
      "triggering_source_id": "src_...",
      "reason": "New supporting empirical claim from higher-credibility source."
    }
  ],
  "largest_increases": [],
  "largest_decreases": [],
  "relationships_with_contradiction_pressure": []
}
```

Rules:

- Score changes must reference `score_events` rows.
- Reports may summarize but must not replace score event history.

## 9. Cluster Reports

Cluster reports summarize related concepts/claims without flattening disagreement.

Trigger:

```txt
15 claims + 3 sources in a cluster
```

Strong cluster trigger:

```txt
30 claims + 5 sources + mixed stances
```

Required fields:

```json
{
  "report_type": "cluster_report",
  "cluster_id": "cluster_...",
  "cluster_label": "AI assistance and semantic diversity",
  "included_concepts": ["AI assistance", "semantic diversity", "originality", "ideation"],
  "supporting_claims": ["clm_..."],
  "contradicting_claims": ["clm_..."],
  "qualifying_claims": ["clm_..."],
  "strongest_relationships": ["rel_..."],
  "evidence_gaps": [],
  "candidate_next_questions": [],
  "evidence_packet": {}
}
```

Cluster reports must not cherry-pick only supporting evidence.

## 10. Cluster Evidence Packet

Every cluster report and theory candidate must be grounded in an evidence packet.

Required fields:

```json
{
  "cluster_id": "cluster_...",
  "top_supporting_claims": [],
  "top_contradicting_claims": [],
  "top_qualifying_claims": [],
  "highest_quality_sources": [],
  "newest_claims": [],
  "highest_score_change_events": [],
  "bridge_concepts": [],
  "open_gaps": []
}
```

Selection formula:

```txt
report_value =
  evidence_strength
+ source_quality
+ relevance_to_cluster
+ contradiction_value
+ novelty
+ score_change_impact
+ bridge_value
- redundancy_penalty
```

Rules:

- Include at least one supporting claim if available.
- Include contradiction/qualification if available.
- Avoid redundant claims from one source family when alternatives exist.
- Include only claims linked to the cluster.
- Preserve provenance IDs.

## 11. Ontology Pressure Reports

Triggered when vocabulary/claim pressure suggests the ontology is insufficient.

Example setup:

```txt
20 accepted claims mention selection burden, curation load, choice overload, taste bottleneck.
```

Required output:

```json
{
  "report_type": "ontology_pressure_report",
  "proposal_type": "promote_concept",
  "candidate_concept": "selection burden",
  "status": "draft",
  "evidence_claims": ["clm_..."],
  "aliases": ["curation load", "choice overload", "taste bottleneck"],
  "reason": "Recurring concept appears across multiple sources and is not captured cleanly by existing ontology.",
  "recommended_next_step": "Create ontology proposal for human review."
}
```

Rules:

- Do not auto-activate concepts.
- Proposals must include evidence claims.
- Duplicate prevention must check aliases.

## 12. Domain Proposal Reports

Triggered only when strict thresholds are met:

```txt
40 accepted claims
8 independent sources
15 recurring specialized terms
3 repeated extraction/scoring mismatch signals
clear reason parent domain is underspecified
```

Required output:

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

Rules:

- No automatic domain activation.
- Report must prove thresholds.
- Report must include scoring/ontology rationale.

## 13. Theory Candidate Reports

Theories emerge from graph patterns and evidence packets.

Theory flow:

```txt
graph pattern
→ evidence packet
→ constrained model inference
→ candidate theory
→ validation
→ stored as candidate, not fact
```

Graph patterns:

```txt
bridge path
repeated support
contradiction by metric
boundary condition
emerging subdomain
evidence gap
```

Required output:

```json
{
  "report_type": "theory_candidate_report",
  "type": "candidate_theory",
  "graph_pattern": "bridge_path",
  "theory_text": "As AI lowers the cost of generating variations, human taste may become more important as a selection bottleneck.",
  "confidence": "medium",
  "supporting_claims": ["clm_..."],
  "contradicting_or_qualifying_claims": ["clm_..."],
  "boundary_conditions": [],
  "weakening_evidence": [],
  "next_questions": [],
  "status": "candidate"
}
```

Rules:

- Theory candidates are not facts.
- Must include supporting claims.
- Must include caveats/boundary conditions.
- Must include weakening evidence or explicitly state none found in the packet.
- Must not claim beyond evidence packet.

## 14. Improvement Ticket Reports

Improvement tickets are generated from actual failures, reports, and audits.

Required output:

```json
{
  "report_type": "improvement_ticket_report",
  "ticket_id": "ticket_...",
  "priority": "high",
  "title": "Improve claim extractor scope preservation",
  "problem": "High rejection rate caused by overgeneralized claims.",
  "evidence": [
    "run_report:run_...:overgeneralized_scope_count=7"
  ],
  "affected_modules": ["claim_extractor", "claim_validator", "creativity_domain_pack"],
  "expected_files": [
    "rge/modules/claim_extractor.py",
    "rge/prompts/claim_extraction.md",
    "tests/golden/test_02_claim_extraction.py"
  ],
  "acceptance_criteria": [
    "Overgeneralized fixture claim is rejected or rewritten with preserved scope.",
    "No accepted claim lacks quote_span."
  ],
  "test_plan": ["pytest tests/golden/test_02_claim_extraction.py"],
  "non_goals": ["Do not refactor the full orchestration graph."],
  "risk_level": "medium",
  "rollback_plan": "Revert extractor prompt/schema changes and restore previous validator version."
}
```

Rules:

- Tickets must be actionable by Cursor/build agents.
- Tickets must have evidence.
- Tickets must have expected files.
- Tickets must have non-goals.
- Tickets must not ask for broad refactors unless explicitly approved.

## 15. Safety Audit Reports

Required output:

```json
{
  "report_type": "safety_audit_report",
  "audit_type": "public_export",
  "status": "pass",
  "blocked_reasons": [],
  "checked_routes": [],
  "checked_exports": ["apps/public-site/public/data/public_cards.json"],
  "checked_secrets": [],
  "findings": []
}
```

Safety report must fail if:

- Public write endpoints exist.
- Public source ingestion exists.
- Public agent execution exists.
- Public JSON contains local file paths.
- Public JSON contains secrets.
- Public JSON contains raw prompts.
- Public JSON contains private notes.
- UI renders raw HTML from card JSON.
- Model output controls shell or Git push.

## 16. Model Runtime Reporting

Every model-assisted node report must include runtime metadata so model/prompt changes can be audited.

Required fields inside the report envelope:

```json
{
  "model_runtime": {
    "llm_mode": "mock | ollama",
    "model_provider": "mock | ollama",
    "model_name": "mock | qwen2.5:7b",
    "task_name": "claim_extraction",
    "schema_version": "0.1.0",
    "prompt_template_version": "0.1.0",
    "raw_response_stored": false
  }
}
```

Rules:

- Golden tests should normally report `llm_mode: mock`.
- Live local runs should report `llm_mode: ollama`.
- Model output schema versions must appear in reports when model-assisted nodes run.
- Prompt template version changes must be visible in reports.
- Raw model responses may be kept in private local diagnostics only if safety audit excludes them from public export.

## 17. Reporting Acceptance Criteria

The reporting system passes MVP when:

- Every run emits a run report.
- Every node emits a node report.
- Rejections are counted by reason.
- Score changes are reportable through score events.
- A cluster report appears when fixture thresholds are met.
- A theory candidate report is generated from evidence packet, not vibes.
- At least one improvement ticket is generated from actual failures/reports.
- Safety audit report blocks unsafe exports/routes.
