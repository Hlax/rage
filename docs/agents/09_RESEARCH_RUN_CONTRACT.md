# RESEARCH_RUN_CONTRACT.md

## 1. Purpose

Every research run starts with a contract. The contract prevents topic drift, defines source strategy, constrains follow-up questions, and gives the queue an explicit scoring basis.

The research run contract is not a prompt. It is a durable database object that controls a run from planning through reports, public export, and improvement tickets.

## 2. Contract Responsibilities

A contract must:

1. Define the root topic and primary question.
2. Select the domain pack.
3. Identify allowed, adjacent, and out-of-scope concepts.
4. Set source and search budgets.
5. Set follow-up depth.
6. Define drift threshold.
7. Define success criteria.
8. Define source strategy.
9. Define evidence requirements.
10. Define active vs parked follow-up question rules.
11. Define queue priority formula.
12. Define topic drift scoring.

## 3. Required Fields

```json
{
  "id": "contract_...",
  "root_topic": "Does AI improve creative output while reducing diversity?",
  "primary_question": "Does AI assistance improve creative output while reducing semantic diversity in creative work?",
  "domain_pack": "creativity",
  "allowed_concepts": [],
  "adjacent_concepts": [],
  "out_of_scope_concepts": [],
  "source_budget": 5,
  "search_budget": 10,
  "follow_up_depth": 1,
  "drift_threshold": 0.35,
  "success_criteria": [],
  "source_strategy": {},
  "evidence_requirements": {},
  "active_follow_up_questions": [],
  "parked_follow_up_questions": [],
  "queue_priority_formula": "v1",
  "topic_drift_scoring": "v1",
  "created_at": "...",
  "updated_at": "..."
}
```

## 4. Concept Scope Rules

### Allowed concepts

Allowed concepts are directly relevant to the run and can enter active source discovery, extraction, queueing, and reports.

Example:

```txt
AI assistance
creative output
semantic diversity
idea quality
ideation
originality
human control
```

### Adjacent concepts

Adjacent concepts are useful context but should not dominate the run unless evidence shows they are necessary.

Example:

```txt
authorship
ownership
selection burden
prompt engineering
creative phase
```

### Out-of-scope concepts

Out-of-scope concepts should be rejected or parked if proposed as follow-ups.

Example:

```txt
AI consciousness
general labor displacement
military AI
general copyright law unless the run includes authorship/legal policy
```

## 5. Follow-Up Question Thresholds

A follow-up question may enter the active queue only if:

```txt
topic_fit >= 0.65
evidence_fit >= 0.60
drift_risk <= 0.35
```

Questions that are interesting but fail these thresholds go to the parking lot with a reason.

## 6. New Question Score

```txt
new_question_score =
  concept_novelty * 0.20
+ contradiction_value * 0.25
+ evidence_gap_value * 0.25
+ source_quality * 0.15
+ topic_fit * 0.15
```

Interpretation:

- `concept_novelty`: Does it open a useful concept path not already saturated?
- `contradiction_value`: Does it clarify a real disagreement or scope/metric conflict?
- `evidence_gap_value`: Does it target a known gap from reports?
- `source_quality`: Are likely sources strong enough to justify research time?
- `topic_fit`: Does it fit the contract?

## 7. Queue Priority Formula

Recommended MVP formula:

```txt
queue_priority =
  relevance_score * 0.25
+ credibility_prior * 0.20
+ gap_fill_score * 0.20
+ domain_match_score * 0.15
+ source_diversity_score * 0.10
+ recency_score * 0.05
+ novelty_score * 0.05
- drift_risk * 0.25
```

Rules:

- Marketing pages should rank low unless the contract specifically asks for product behavior or vendor claims.
- Peer-reviewed empirical sources should rank high when the contract asks for empirical evidence.
- Expert interviews can rank high for practitioner questions but lower for general empirical claims.
- Every queue item must store a reason.

## 8. Topic Drift Scoring

Recommended MVP drift scoring:

```txt
drift_risk =
  out_of_scope_overlap * 0.40
+ missing_allowed_concept_overlap * 0.25
+ weak_primary_question_similarity * 0.20
+ excessive_adjacent_concept_weight * 0.15
```

A drift score above `drift_threshold` means the item is parked or rejected.

## 9. Research Modes

The contract may set one mode:

```txt
best_evidence_first
breadth_first
contradiction_hunting
gap_filling
```

### `best_evidence_first`

Prioritizes source credibility and direct relevance.

### `breadth_first`

Prioritizes source diversity and concept coverage.

### `contradiction_hunting`

Prioritizes sources likely to challenge current relationships or reveal metric/scope differences.

### `gap_filling`

Prioritizes open gaps identified by run or cluster reports.

## 10. Source Strategy

Example source strategy object:

```json
{
  "mode": "best_evidence_first",
  "source_acquisition_levels": ["manual", "fixture", "search_api"],
  "preferred_source_types": ["peer_reviewed_empirical", "meta_analysis", "benchmark_paper"],
  "allowed_source_types": ["expert_interview", "theory", "case_study"],
  "avoid_as_primary": ["marketing_page", "SEO_summary"],
  "max_sources_to_ingest": 3,
  "min_independent_sources": 2
}
```

## 11. Evidence Requirements

Example:

```json
{
  "must_include": ["supporting_claim", "qualifying_or_contradicting_claim"],
  "preferred_evidence_types": ["empirical", "meta_analysis", "benchmark"],
  "require_quote_spans": true,
  "require_scope": true,
  "require_limitations": true,
  "minimum_accepted_claims": 2,
  "minimum_rejected_claims_for_validation_proof": 1,
  "minimum_relationships": 1,
  "minimum_score_events": 1
}
```

## 12. Example Contract

Topic:

```txt
Does AI improve creative output while reducing diversity?
```

Contract:

```json
{
  "root_topic": "AI assistance, creative output, and diversity",
  "primary_question": "Does AI assistance improve creative output while reducing semantic diversity in creative work?",
  "domain_pack": "creativity",
  "allowed_concepts": [
    "AI assistance",
    "creative output",
    "average idea quality",
    "semantic diversity",
    "idea diversity",
    "ideation",
    "originality",
    "creative phase"
  ],
  "adjacent_concepts": [
    "human control",
    "prompt engineering",
    "selection burden",
    "variation volume",
    "taste"
  ],
  "out_of_scope_concepts": [
    "AI consciousness",
    "general labor displacement",
    "military AI",
    "general copyright law"
  ],
  "source_budget": 5,
  "search_budget": 10,
  "follow_up_depth": 1,
  "drift_threshold": 0.35,
  "success_criteria": [
    "ingest at least two sources",
    "extract at least two accepted scoped claims",
    "reject at least one invalid or overgeneralized claim with reason",
    "build at least one support relationship",
    "build at least one contradiction or qualification if fixture evidence exists",
    "write at least one score event",
    "generate run report",
    "generate public card JSON",
    "pass safety audit"
  ],
  "source_strategy": {
    "mode": "best_evidence_first",
    "preferred_source_types": ["peer_reviewed_empirical", "meta_analysis", "benchmark_paper"],
    "allowed_source_types": ["expert_interview", "case_study", "theory"],
    "avoid_as_primary": ["marketing_page"],
    "fixture_mode_sources": [
      "fixtures/sources/creativity_ai_diversity_short.txt",
      "fixtures/sources/creativity_ai_diversity_contradiction.txt",
      "fixtures/sources/prompt_injection_source.txt"
    ]
  },
  "evidence_requirements": {
    "require_quote_spans": true,
    "require_scope": true,
    "require_limitations": true,
    "must_preserve_contradictions": true,
    "minimum_independent_sources": 2
  },
  "queue_priority_formula": "v1",
  "topic_drift_scoring": "v1"
}
```

## 13. Example Follow-Up Decisions

### Candidate: active

```txt
Does divergent prompting reduce AI-driven semantic convergence?
```

Reason:

```json
{
  "topic_fit": 0.88,
  "evidence_fit": 0.76,
  "drift_risk": 0.12,
  "status": "active",
  "reason": "Directly tests a condition under which AI assistance may affect semantic diversity."
}
```

### Candidate: parked

```txt
Will AI become conscious?
```

Reason:

```json
{
  "topic_fit": 0.18,
  "evidence_fit": 0.22,
  "drift_risk": 0.91,
  "status": "parked",
  "reason": "Out-of-scope topic drift. The current contract is about AI assistance and creative diversity, not AI consciousness."
}
```

### Candidate: parked as adjacent

```txt
Who owns copyright for AI-generated work?
```

Reason:

```json
{
  "topic_fit": 0.48,
  "evidence_fit": 0.62,
  "drift_risk": 0.42,
  "status": "parked",
  "reason": "Adjacent to authorship and ownership but outside this run unless legal policy is added to the contract."
}
```

## 14. Contract Acceptance Criteria

The contract subsystem passes MVP when:

- A fixture run creates a durable `research_contracts` record.
- Queue ranking uses the contract.
- Follow-up questions are active or parked with reasons.
- Out-of-scope questions do not enter the active queue.
- The original contract is referenced in run reports.
- Topic drift rules remain active after source ingestion, not just at run start.
