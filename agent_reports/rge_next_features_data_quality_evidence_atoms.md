# RGE Next Features: Data Quality, Research Purpose, and Evidence Atoms

**Build direction:** make RGE a research-to-knowledge-asset engine before pushing harder on automation/self-improvement.

The immediate priority is not more ticket automation, frontend polish, or broader crawling. The priority is higher-quality acquisition, parsing, claim handling, and reusable evidence structures so the graph/Atlas can become real research memory.

---

## Executive Priority Order

1. **Research Question Purpose + Asset Affordance Layer**
   - Every research question should declare what kind of research object it is trying to produce.
   - This lets the system distinguish reasoning data, visual descriptor data, eval candidates, theory maps, product insights, and public cards.

2. **Evidence Atoms**
   - Use stable semantic units instead of raw model tokens.
   - Evidence atoms are reusable, quote-backed, graph-linked research units that can later power reports, Atlas views, evals, LoRA/data curation, visual descriptor systems, and training candidates.

3. **Research Purpose Classifier / Maturity Layer**
   - Label questions, clusters, reports, and atoms with research intent, asset affordance, maturity, and downstream usefulness.

4. **Source Acquisition + Text Quality Gates**
   - Improve scraping/fetching/parsing before more automation.
   - Sources should be classified as metadata-only, abstract-available, clean-text-ready, extractable, parse-failed, etc.

5. **Quote-First Claim Extraction**
   - Claims should come from exact quotes, not from topic-shaped LLM guesses.
   - The system should extract quote spans first, then derive narrow claims from those spans.

6. **Canonical Frontend-Safe Evidence Cards**
   - Normalize outputs now so Atlas/frontend can later render papers, abstracts, PDFs, webpages, essays, and interviews through one schema.

7. **Scrapling/Web Adapter as a Source Adapter**
   - Use Scrapling or similar tools for public webpage extraction, not as the core research brain.
   - Keep PDF parsing as a separate milestone.

8. **Automation/Self-Improvement Later**
   - Keep lightweight failure recommendations, but do not invest heavily in autonomous ticket loops until data quality is stable.

---

# Feature 001 — Research Question Purpose + Asset Affordance

## Goal

RGE should not only answer: **“What does the research say?”**

It should also answer: **“What is this research useful for next?”**

A research question should carry intent and downstream asset labels before the agent starts pulling sources.

## Why this matters

The same research run can produce very different downstream assets:

- philosophical reasoning data
- visual descriptor vocabularies
- argument maps
- contradiction maps
- product strategy insights
- eval questions
- prompt patterns
- public research cards
- training/LoRA curation candidates

Without an explicit purpose layer, all research collapses into generic summaries.

## Required schema fields

Add or support fields similar to:

```json
{
  "question_id": "q_...",
  "question": "How does AI affect human creativity?",
  "research_intent": [
    "theory_building",
    "evidence_review"
  ],
  "asset_affordance": [
    "reasoning_training_candidate",
    "argument_map_candidate",
    "concept_ontology_candidate"
  ],
  "domain": "creativity",
  "evidence_need": "mixed empirical + theory",
  "acceptable_source_types": [
    "paper",
    "abstract",
    "essay",
    "book",
    "interview",
    "webpage"
  ],
  "output_targets": [
    "cluster_report",
    "evidence_cards",
    "atlas_map"
  ]
}
```

## Recommended enum values

### `research_intent`

- `evidence_review`
- `theory_building`
- `contradiction_mapping`
- `style_taxonomy`
- `visual_descriptor_mining`
- `product_strategy`
- `benchmark_design`
- `training_data_mining`
- `eval_design`
- `concept_ontology_building`
- `field_mapping`
- `historical_context`

### `asset_affordance`

- `reasoning_training_candidate`
- `visual_descriptor_candidate`
- `eval_question_candidate`
- `concept_ontology_candidate`
- `prompt_pattern_candidate`
- `public_card_candidate`
- `memo_candidate`
- `argument_map_candidate`
- `contradiction_map_candidate`
- `dataset_curation_candidate`
- `style_vocabulary_candidate`
- `product_principle_candidate`

### `evidence_need`

- `abstract_only_ok`
- `full_text_preferred`
- `full_text_required`
- `empirical_required`
- `theory_ok`
- `mixed_empirical_theory`
- `visual_examples_required`
- `historical_sources_required`

## Implementation notes

- Start deterministic/rule-based.
- Do not require an LLM for the first version.
- Use keyword/domain hints from the question and existing domain packs if available.
- The classifier can be upgraded later to LLM-assisted mode.

## Acceptance criteria

- A research run can store question purpose metadata before source discovery.
- Purpose metadata appears in evidence/cluster/report outputs.
- Tests cover at least:
  - AI + creativity question → theory/evidence/reasoning affordance
  - art/design question → style/visual descriptor affordance
  - benchmark/evaluation question → eval/benchmark affordance
  - generic question → conservative `field_mapping` fallback

---

# Feature 002 — Evidence Atoms

## Goal

Replace the vague idea of “research-backed tokens” with stable semantic units called **Evidence Atoms**.

Evidence atoms are reusable, quote-backed, graph-linked research units. They are not tokenizer tokens. They are compact units of meaning that can be referenced, clustered, exported, and reused.

## Why not raw tokens?

Model tokens are implementation details of a tokenizer. They are not reliable research objects. They do not know source, scope, quote, stance, concept, or evidence type.

RGE should instead create semantic atoms:

- source IDs
- quote IDs
- claim IDs
- concept IDs
- relationship IDs
- cluster IDs
- atom IDs
- embedding IDs/fingerprints
- asset tags

## Evidence atom schema

```json
{
  "atom_id": "atom_ai_creativity_diversity_001",
  "atom_type": "claim",
  "canonical_text": "AI assistance can narrow semantic diversity in some ideation tasks.",
  "source_claim_ids": ["clm_001", "clm_017"],
  "source_quote_ids": ["quote_001", "quote_017"],
  "support_count": 2,
  "contradiction_count": 1,
  "concepts": [
    "AI assistance",
    "semantic diversity",
    "ideation"
  ],
  "stance_profile": {
    "supports": 2,
    "contradicts": 1,
    "qualifies": 1
  },
  "scope": "short-form ideation tasks",
  "evidence_type": "empirical",
  "asset_tags": [
    "reasoning_training_candidate",
    "eval_question_candidate"
  ],
  "evidence_maturity": "promising",
  "confidence": "medium"
}
```

## Atom types

- `claim`
- `definition`
- `distinction`
- `mechanism`
- `method`
- `statistic`
- `limitation`
- `contradiction`
- `design_principle`
- `visual_descriptor`
- `evaluation_rubric`
- `open_question`

## Atom maturity states

- `seed`
- `weak`
- `promising`
- `clustered`
- `synthesis_ready`
- `eval_ready`
- `training_ready`
- `rejected`

## Atom lifecycle

```text
source → clean text → chunk → exact quote → narrow claim → concept links → relationships → evidence atom → cluster/report/Atlas/export
```

## Rules

- An atom must be backed by at least one accepted quote-backed claim unless explicitly marked as `hypothesis` or `user_thesis`.
- Atoms should preserve source scope.
- Atoms should not overgeneralize beyond the underlying evidence.
- Atoms can merge multiple claims only when their meaning and scope are compatible.
- Conflicting claims should not be erased; they should increase contradiction/qualification counts.

## Acceptance criteria

- Accepted claims can be promoted into evidence atoms.
- Multiple claims with similar meaning can link to one atom.
- Contradictory claims can attach to an atom without deleting the atom.
- Each atom has asset tags and maturity labels.
- Reports can list top evidence atoms per cluster.
- Tests cover claim → atom creation, atom merging, contradiction attachment, and maturity updates.

---

# Feature 003 — Research Purpose Classifier + Maturity Layer

## Goal

Classify each question, cluster, report, and atom by what it is useful for and how mature it is.

This is the Atlas intelligence layer.

## Required fields

Add or propagate:

```json
{
  "research_intent": ["evidence_review"],
  "asset_affordance": ["reasoning_training_candidate"],
  "evidence_maturity": "promising",
  "training_suitability": "not_ready",
  "frontend_card_type": "evidence_cluster",
  "domain_scope": "AI and human creativity"
}
```

## Training suitability labels

- `not_ready`
- `candidate`
- `needs_human_review`
- `eval_ready`
- `training_ready`
- `do_not_train`

## Why this matters

A cluster may be useful even before it is “true enough” for training.

Example:

- A cluster can be `synthesis_ready` for a memo but `not_ready` for training.
- A cluster can be a `visual_descriptor_candidate` based on interpretive essays but not empirical evidence.
- A cluster can be `eval_question_candidate` if it contains contradictions or scope limitations.

## Acceptance criteria

- Cluster reports state what each cluster is useful for.
- Reports distinguish evidence maturity from training suitability.
- Training/export candidates are conservative by default.
- Unsafe or copyrighted raw-text export is avoided.

---

# Feature 004 — Source Acquisition + Text Quality Gates

## Goal

Improve source fetching, scraping, parsing, and quality classification before expanding automation.

The agent should know whether it has clean evidence before asking an LLM to extract claims.

## Source statuses

Use explicit statuses:

- `metadata_only`
- `abstract_available`
- `oa_pdf_available`
- `oa_tei_available`
- `download_failed`
- `parse_failed`
- `dirty_text`
- `clean_text_ready`
- `extractable`

## Source adapters

Recommended adapter roles:

| Adapter | Role |
|---|---|
| OpenAlex | scholarly discovery, metadata, OA locations, abstract reconstruction |
| Unpaywall | DOI → open-access resolver, best OA location |
| arXiv | open preprint metadata/abstract/PDF source |
| Scrapling | public webpage extraction adapter |
| PyMuPDF/pypdf | basic PDF text extraction |
| GROBID/OpenAlex TEI | structured scholarly full-text extraction milestone |
| manual fixtures | deterministic test sources |

## Quality metrics

Before LLM extraction, compute:

- character count
- readable character ratio
- sentence count
- paragraph count
- quoteable span count
- binary/noise ratio
- repeated header/footer ratio
- reference-section ratio if available
- parser backend used
- source type
- acquisition status

## Required behavior

- Bad PDF extraction should not reach the LLM.
- Dirty sources should produce `parse_failed` or `dirty_text`, not mass `unsupported_claim`.
- Abstract-only sources should still produce useful evidence cards when full text is unavailable.
- Source quality metrics should appear in reports.

## Acceptance criteria

- The old failure mode “UTF-8 decode PDF noise → unsupported_claim wall” is blocked.
- Clean abstracts can produce accepted claims.
- Dirty PDF extraction is rejected before LLM extraction.
- Reports explain whether failures came from acquisition, parsing, extraction, or validation.

---

# Feature 005 — Quote-First Claim Extraction

## Goal

Change extraction from claim-first to quote-first.

The model should first copy exact quote spans from clean text, then generate narrow claims only from those quote spans.

## Current failure pattern to avoid

```text
question/topic → LLM invents plausible claim → no exact quote → unsupported_claim
```

## Target pattern

```text
clean chunk → exact quote span → quote validation → narrow claim → entailment/scope validation → concept links
```

## Claim schema

```json
{
  "claim_id": "clm_...",
  "claim_text": "...",
  "quote": "exact substring copied from source chunk",
  "source_id": "src_...",
  "chunk_id": "chunk_...",
  "evidence_type": "empirical | theory | case_study | benchmark | design_argument | definition",
  "stance": "supports | contradicts | qualifies | defines | contextualizes | extends",
  "scope": "...",
  "limitations": [],
  "concepts": []
}
```

## Extraction rules

- Quotes must be literal substrings of source chunks.
- Claims must be narrower than or equal to the quote’s scope.
- Claims must not import the user’s question as if it came from the source.
- If no quoteable spans exist, extraction should return `zero_quoteable_spans`, not invented claims.

## Acceptance criteria

- Unsupported-claim rejection rate drops because invalid claims are prevented earlier.
- Tests include a chunk with relevant prose and a chunk with no relevant prose.
- The extractor returns no claims rather than hallucinated topic-shaped claims when evidence is absent.

---

# Feature 006 — Canonical Evidence Cards for Atlas/Frontend

## Goal

Create a uniform evidence card shape that can render different source types without requiring every source format to be identical.

## Evidence card schema

```json
{
  "card_type": "evidence_claim",
  "claim": "...",
  "quote": "...",
  "source": {
    "title": "...",
    "authors": [],
    "year": 2026,
    "url": "...",
    "source_type": "paper | abstract | webpage | essay | book | interview | dataset"
  },
  "stance": "supports | contradicts | qualifies | defines | contextualizes | extends",
  "evidence_type": "empirical | theory | case_study | interview | benchmark | design_argument | definition",
  "scope": "...",
  "concepts": [],
  "confidence": "low | medium | high",
  "limitations": [],
  "asset_tags": [],
  "evidence_maturity": "seed | weak | promising | clustered | synthesis_ready | eval_ready | training_ready"
}
```

## Frontend design implication

Use one shell with badges:

- source type badge
- evidence type badge
- stance badge
- maturity badge
- asset affordance badge
- confidence badge

Do not build separate frontend card systems for every source type.

## Acceptance criteria

- Abstracts, PDFs, web pages, and manual fixtures can all produce the same card shell.
- Reports export frontend-safe JSON without raw private content.
- Cards preserve quote/source traceability.

---

# Feature 007 — Scrapling/Web Source Adapter

## Goal

Add Scrapling or a comparable web extraction adapter for public webpages and public reports.

## Role

Scrapling should help acquire clean text from:

- public web articles
- public research pages
- documentation pages
- public reports
- journal landing pages
- project pages

## Non-role

Scrapling should not be treated as:

- a PDF parser
- a paywall bypass tool
- a claim extraction tool
- the graph brain
- a replacement for OpenAlex/Unpaywall/arXiv

## Adapter output

The adapter should output the same normalized source artifact shape:

```json
{
  "source_id": "src_...",
  "source_type": "webpage",
  "url": "...",
  "title": "...",
  "authors": [],
  "published_date": null,
  "raw_text": "...",
  "clean_text": "...",
  "quality_metrics": {},
  "acquisition_status": "clean_text_ready"
}
```

## Acceptance criteria

- Webpage extraction can be tested using deterministic local HTML fixtures.
- The adapter does not require live network for default tests.
- The adapter feeds the same quote-first extraction pipeline as abstracts/PDFs.

---

# Feature 008 — Agent / Atlas / Graph Boundary

## Goal

Clarify responsibilities so the system does not collapse into generic summaries.

## Roles

```text
Research Agent = investigator/worker
Atlas = field map + UI-ready research memory
Graph = durable evidence brain
```

## Research Agent responsibilities

- interpret question purpose
- discover candidate sources
- acquire metadata/abstract/full text
- classify source quality
- extract quote-backed claims
- validate quotes/scopes
- create evidence atoms
- update clusters
- write reports

## Graph responsibilities

- store source, chunk, quote, claim, concept, relationship, atom, cluster, report nodes
- preserve provenance
- support retrieval by concept, claim, source, stance, cluster, asset tag, and maturity
- track contradictions/qualifications instead of flattening them away

## Atlas responsibilities

- show the field map
- show evidence maturity
- show useful downstream assets
- show source gaps
- show contradiction zones
- show what can become public cards, evals, visual descriptors, or training candidates

## Acceptance criteria

- Reports distinguish worker output, graph state, and Atlas-facing summaries.
- Evidence atoms are graph objects, not just report text.
- Atlas-facing exports are deterministic and safe.

---

# Feature 009 — Training/Eval/Descriptor Export Guardrails

## Goal

Allow RGE to identify useful future data assets without irresponsibly exporting raw copyrighted text as training data.

## Key distinction

Do not treat every paper/source as direct training data.

Use this safer transformation chain:

```text
source → quote-backed claim → annotation → evidence atom → derived eval/style/reasoning artifact
```

## Export categories

- `reasoning_eval_candidate`
- `qa_eval_candidate`
- `rubric_candidate`
- `style_descriptor_candidate`
- `visual_taxonomy_candidate`
- `prompt_pattern_candidate`
- `concept_ontology_candidate`
- `do_not_export`

## Guardrails

- Avoid exporting long raw quotes.
- Preserve source attribution internally.
- Public exports should be derived/summarized and safe.
- Training suitability should default conservative.
- Human review can be required before `training_ready`.

## Acceptance criteria

- Evidence atoms can be tagged as export candidates.
- Raw source text is not blindly exported.
- Reports clearly separate evidence, inference, user thesis, and derived training/eval candidates.

---

# Feature 010 — Delay Heavy Automation Until Data Layer Is Stable

## Goal

Keep the useful parts of the ticket/audit system while reducing overhead.

## Operating shift

Move from per-ticket heavy audits to **phase-packet commits** for this stage.

## Recommended packet cadence

Each packet should contain:

- one branch
- small logical commits
- targeted tests during development
- one evidence report
- one packet closeout report
- full verification at packet close

## When to run full verification immediately

Run full verification when touching:

- migrations
- quote validation
- source acquisition/live fetch behavior
- public/private export boundaries
- safety auditor
- schema compatibility
- report/public card formats

## What to avoid for now

- autonomous ticket generation loops beyond lightweight recommendations
- frontend polish
- bulk corpus downloads
- complex scheduling/daemon behavior
- deep self-upgrading agent execution

## Acceptance criteria

- The system moves faster without losing evidence discipline.
- Every packet still produces a clear GO / PARTIAL / NO-GO closeout.
- Improvement recommendations are generated but not overbuilt.

---

# Recommended Implementation Order

## Packet 1 — Purpose + Evidence Atom Schema Foundation

Implement schemas/enums for:

- research question purpose
- research intent
- asset affordance
- evidence maturity
- training suitability
- evidence atom
- canonical evidence card

Add deterministic classifier stubs and tests.

## Packet 2 — Source Quality + Acquisition Status Layer

Implement or improve:

- source acquisition statuses
- quality metrics
- clean text readiness gates
- OpenAlex abstract reconstruction handling if not already present
- Unpaywall/arXiv resolver compatibility where appropriate
- fixture-based tests

## Packet 3 — Quote-First Extraction

Refactor extraction to:

- identify exact quote spans first
- validate quote spans before claim creation
- prevent topic-shaped hallucinated claims
- return structured failure reasons when no quoteable evidence exists

## Packet 4 — Claim → Evidence Atom Promotion

Implement:

- atom creation from accepted claims
- atom merging rules
- contradiction/qualification attachment
- maturity scoring
- top atoms in cluster reports

## Packet 5 — Atlas/Frontend-Safe Evidence Cards

Implement:

- canonical evidence card export
- source/evidence/maturity/asset badges
- safe public/private boundary
- deterministic JSON outputs

## Packet 6 — Scrapling/Web Adapter

Implement:

- optional web source adapter
- local HTML fixture tests
- same source artifact output shape as other adapters

## Packet 7 — PDF/TEI Milestone

Implement:

- real PDF parser instead of UTF-8 decode
- PyMuPDF/pypdf path
- GROBID or OpenAlex TEI path where available
- dirty PDF quality rejection
- parser backend metrics in reports

## Packet 8 — Data Asset Export Candidates

Implement:

- eval candidate export
- style descriptor candidate export
- reasoning example candidate export
- conservative training suitability labels
- human-review-required states

## Packet 9 — Self-Improvement Re-entry

Only after data quality stabilizes:

- smarter failure-to-ticket mapping
- parser failure self-ticketing
- acquisition fallback recommendations
- cluster maturity improvement suggestions
- autonomous loop improvements

---

# Principal Build Rule

For the next stretch, prioritize this rule:

> Do not make the agent more autonomous until the evidence it handles is cleaner, more structured, more reusable, and more honest.

