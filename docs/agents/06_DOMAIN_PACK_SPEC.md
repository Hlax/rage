# DOMAIN_PACK_SPEC.md

## 1. Purpose

Domain packs customize the General Research Graph Engine for specific research areas without contaminating the core engine. The first domain pack is `creativity`, but the engine must support future domain packs for unrelated topics.

A domain pack defines:

- Ontology and concept definitions.
- Aliases and vocabulary normalization.
- Preferred source types.
- Evidence type preferences.
- Scoring overlays.
- Claim extraction schema extensions.
- Search templates.
- Public card templates.
- Safety notes.
- Domain graph/overlap definitions.
- Domain and subdomain proposal lifecycle rules.

The core engine must never hardcode creativity-specific fields. Creativity-specific information belongs in domain pack files or per-record `domain_metadata`.

## 2. General Engine vs Domain Pack

### General engine owns

- Source ingestion.
- Chunking.
- Claim lifecycle.
- Quote span validation.
- Concept and relationship storage.
- Score events.
- Research contracts.
- Queue execution.
- Reports.
- Public export safety.
- Improvement ticket generation.

### Domain pack owns

- Domain ontology.
- Concept aliases.
- Domain-specific metadata schema.
- Source ranking preferences.
- Evidence weighting overlays.
- Claim extraction hints.
- Concept linking rules.
- Domain-specific card templates.
- Search query templates.
- Domain-specific safety warnings.

## 3. Folder Structure

```txt
domain_packs/
  creativity/
    domain.yaml
    ontology.yaml
    aliases.yaml
    source_preferences.yaml
    evidence_types.yaml
    scoring.yaml
    claim_schema.yaml
    card_templates.yaml
    search_templates.yaml
    safety_notes.yaml
    examples/
      claims.json
      relationships.json
      cards.json
```

### Runtime loading (NM-5; creativity MVP)

Tickets 113–122 load every YAML file in the creativity pack via `load_domain_pack()`.
The operator table of pack files, runtime consumers, and overlap-domain claim rules
is maintained in README **Operator Quickstart**
(**Creativity domain pack runtime loading (NM-5; tickets 113–122)**). See also
`AGENTS.md` Operator Loop (**Creativity domain pack runtime loading (NM-5)**).

Candidate claim `domain` labels must appear in `domain.yaml` as `primary_domains` or
`overlap_domains`. During `extract-claims`, `claim_validator` rejects labels outside
`allowed_domains_for_pack()` (overlap labels such as `art` are accepted when the
source pack is `creativity`). Golden mock proof:
`tests/golden/test_02_claim_extraction_overlap_domain.py`.

## 4. `domain.yaml`

Defines pack identity and lifecycle.

Required fields:

```yaml
id: creativity
name: Creativity
version: 0.1.0
status: active
summary: >
  Domain pack for human creativity, AI creativity, and human-AI co-creativity.
primary_domains:
  - creativity
overlap_domains:
  - art
  - design
  - film
  - music
  - digital_media
lifecycle_states:
  - candidate
  - draft
  - experimental
  - active
  - deprecated
  - merged
```

## 5. Creativity Domain Pack v1

### Required concepts

Creativity v1 must include at least:

```txt
taste
novelty
originality
diversity
semantic diversity
constraint
agency
authorship
ownership
intention
meaning
iteration
curation
human control
AI assistance
co-creation
style collapse
prompt engineering
selection burden
variation volume
creative phase
```

### Recommended concept groups

```txt
Generation
  ideation
  divergence
  variation
  recombination

Selection
  taste
  judgment
  curation
  rejection
  selection burden

Execution
  craft
  technique
  iteration
  polish

Meaning
  intention
  emotion
  identity
  context
  audience interpretation

Evaluation
  novelty
  originality
  diversity
  semantic diversity
  usefulness
  coherence
  surprise
  resonance

Co-Creation
  human control
  AI assistance
  AI agency
  co-creation
  ownership
  authorship
  prompt engineering
  style collapse
```

### Domain metadata fields

The creativity pack may add these to `domain_metadata`:

```json
{
  "track": "human | AI | human-AI",
  "creative_phase": "ideation | divergence | selection | iteration | execution | critique | publishing | audience_interpretation",
  "measured_dimension": "novelty | usefulness | diversity | quality | speed | agency | ownership | originality | coherence | resonance",
  "creative_domain": "writing | visual_art | music | film | advertising | design | software | science | education | product_innovation",
  "method": "empirical_study | meta_analysis | case_study | theory | interview | historical_example | benchmark | product_behavior | personal_experiment"
}
```

Core schema must treat this as JSON. Core logic may validate that it is valid JSON but should delegate allowed values to the domain pack.

## 6. `ontology.yaml`

Defines canonical concepts.

Example:

```yaml
concepts:
  - id: concept_ai_assistance
    label: AI assistance
    definition: Use of AI systems to support ideation, variation, execution, selection, or critique in creative work.
    status: active
    groups: [Co-Creation, Generation]
    domain_metadata:
      track: human-AI

  - id: concept_semantic_diversity
    label: semantic diversity
    definition: The degree to which generated ideas differ meaningfully from one another in semantic content.
    status: active
    groups: [Evaluation]
    domain_metadata:
      measured_dimension: diversity

  - id: concept_selection_burden
    label: selection burden
    definition: The cognitive and creative load created by needing to evaluate and choose among many generated options.
    status: active
    groups: [Selection]
```

Rules:

- Every active concept must have a definition.
- Aliases must point to canonical concepts.
- New concepts proposed by model output start as `draft` or `candidate`, never `active`.
- Merged concepts must preserve alias redirects.

## 7. `aliases.yaml`

Maps recurring terms to canonical concepts.

Example:

```yaml
aliases:
  AI assistance:
    - AI-assisted brainstorming
    - generative AI support
    - AI suggestion
    - AI co-pilot
  semantic diversity:
    - idea diversity
    - semantic spread
    - diversity of ideas
    - semantic variance
  taste:
    - aesthetic judgment
    - creative judgment
    - selection ability
  selection burden:
    - curation load
    - choice overload
    - taste bottleneck
```

Alias rules:

- Alias matching may propose links, but validation must prevent duplicate concepts.
- Ambiguous aliases should lower confidence or require manual review.
- Alias source should be stored as `domain_pack`, `model_proposed`, or `human_added`.

## 8. `source_preferences.yaml`

Defines source ranking priors for the domain.

Example:

```yaml
source_type_weights:
  meta_analysis: 0.95
  peer_reviewed_empirical: 0.90
  benchmark_paper: 0.80
  expert_interview: 0.70
  case_study: 0.65
  theory_essay: 0.60
  product_docs: 0.45
  marketing_page: 0.20

preferred_sources:
  - Semantic Scholar
  - OpenAlex
  - Crossref
  - arXiv
  - manual PDFs
  - expert interviews

avoid_as_primary:
  - marketing landing pages
  - uncited hot takes
  - SEO summaries
```

Source preferences influence queue priority but do not determine truth.

## 9. `evidence_types.yaml`

Defines evidence categories and relative priors.

Example:

```yaml
evidence_types:
  empirical:
    base_strength: 0.80
    notes: Controlled or observational study with method details.
  meta_analysis:
    base_strength: 0.90
    notes: Aggregates multiple studies.
  case_study:
    base_strength: 0.55
    notes: Useful for practice context, weaker for general claims.
  theory:
    base_strength: 0.45
    notes: Useful for conceptual framing, not empirical proof.
  interview:
    base_strength: 0.50
    notes: Valuable practitioner evidence, not generalized population evidence.
  benchmark:
    base_strength: 0.65
    notes: Strong for model behavior if metrics match question.
```

## 10. `scoring.yaml`

Defines domain-specific scoring overlays.

Base scoring signals:

```txt
source credibility
method strength
sample strength
recency
domain match
scope clarity
replication/support
contradiction pressure
```

Creativity overlay examples:

```yaml
claim_scoring_overlay:
  domain_match:
    writing_task_to_general_creativity_penalty: 0.15
    student_sample_to_professional_work_penalty: 0.10
  scope_clarity:
    requires_creative_phase: true
    requires_measured_dimension_when_empirical: true
  evidence_bonus:
    cross_domain_replication: 0.10
    mixed_methods_support: 0.05
  contradiction_handling:
    metric_difference_should_qualify_not_flatten: true
```

Scoring rules:

- Scores are derived, not manually overwritten.
- Score changes require `score_events`.
- Domain overlays influence formulas but must be versioned.

## 11. `claim_schema.yaml`

Defines domain-specific extraction extensions.

Example:

```yaml
required_domain_metadata_for_creativity_claims:
  - track
  - creative_phase
  - measured_dimension

allowed_tracks:
  - human
  - AI
  - human-AI

allowed_creative_phases:
  - ideation
  - divergence
  - selection
  - iteration
  - execution
  - critique
  - publishing
  - audience_interpretation

allowed_measured_dimensions:
  - novelty
  - usefulness
  - diversity
  - semantic diversity
  - quality
  - speed
  - agency
  - ownership
  - originality
  - coherence
  - resonance
```

The core engine validates that domain metadata exists and is JSON. The domain pack validates domain-specific allowed values.

## 12. `card_templates.yaml`

Defines public card styles.

Example card types:

```yaml
cards:
  claim_card:
    required_fields:
      - title
      - summary
      - confidence
      - concepts
      - source_count
      - public_caveats
  cluster_card:
    required_fields:
      - title
      - summary
      - confidence
      - concepts
      - source_count
      - strongest_support
      - strongest_qualification
      - open_gaps
  theory_card:
    required_fields:
      - title
      - summary
      - confidence
      - supporting_claim_count
      - weakening_evidence
      - boundary_conditions
      - status
```

Public card templates must never request raw private notes, full source text, raw prompts, hidden evaluator notes, local paths, API keys, or unsafe HTML.

## 13. `search_templates.yaml`

Defines reusable query patterns.

Example:

```yaml
queries:
  ai_diversity_empirical:
    template: "generative AI brainstorming semantic diversity empirical study creativity"
    preferred_source_types: [peer_reviewed_empirical, meta_analysis, benchmark_paper]
  human_control_ownership:
    template: "human control creative ownership AI co-creation study"
    preferred_source_types: [empirical, interview, theory]
  divergent_prompting:
    template: "divergent prompting AI ideation originality diversity"
    preferred_source_types: [empirical, benchmark_paper]
```

Search templates are query drafts only. Candidate ranking decides what enters the queue.

## 14. Domain Graph and Overlap Model

Domains must be modeled as graph/overlay relationships, not only a strict tree.

A claim can belong to multiple domains:

```json
{
  "primary_domain": "creativity",
  "secondary_domains": ["design", "digital_media"],
  "overlap_reason": "Claim discusses AI-assisted ideation in design workflows."
}
```

Domain relationships may include:

```txt
parent_of
child_of
overlaps_with
shares_methods_with
uses_scoring_overlay_from
merged_into
```

Rules:

- The core `claims.domain` stores primary domain.
- Secondary/overlap domains live in `domain_metadata` or join tables later.
- New domains are proposed first, not auto-activated.
- Domain activation requires human/checkpoint approval.

## 15. Subdomain Proposal Lifecycle

Lifecycle states:

```txt
candidate
draft
experimental
active
deprecated
merged
```

Meaning:

- `candidate`: detected vocabulary/domain pressure, not yet formalized.
- `draft`: proposal has evidence and rationale.
- `experimental`: pack exists and can be used in test runs.
- `active`: approved for production research runs.
- `deprecated`: no longer preferred.
- `merged`: merged into another domain; aliases preserved.

Proposal thresholds:

```txt
40 accepted claims
8 independent sources
15 recurring specialized terms
3 repeated extraction/scoring mismatch signals
clear reason parent domain is underspecified
```

A proposal must include:

```json
{
  "domain_id": "creativity.film",
  "status": "draft",
  "parent_domains": ["creativity", "art"],
  "overlap_domains": ["digital_media"],
  "specialized_terms": ["storyboarding", "cinematography", "editing rhythm"],
  "scoring_overlay_proposals": ["production_context", "collaboration_scale", "craft_dependency"],
  "evidence_claims": ["clm_..."],
  "reason_parent_domain_is_underspecified": "..."
}
```

## 16. MVP Domain Pack Acceptance Criteria

The `creativity` domain pack is acceptable for MVP when:

- The pack loads and validates.
- Required concepts exist.
- Aliases map `AI-assisted brainstorming` to `AI assistance` and `semantic diversity` to `semantic diversity`.
- The fixture claim `AI-assisted brainstorming reduced semantic diversity in short-form writing tasks` links to `AI assistance`, `brainstorming`, `semantic diversity`, `ideation`, and `creativity`.
- Domain metadata includes `creative_phase: ideation`, `measured_dimension: diversity`, and `track: human-AI` for the fixture claim.
- Domain pack metadata is stored in `domain_metadata`, not hardcoded into the core schema.
