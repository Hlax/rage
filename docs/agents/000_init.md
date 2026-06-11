The core architecture should be:

    Source library→ extracted claims→ concept graph→ evidence graph→ inference engine→ reports / dashboards / memos

The whole point is that later you can ask things like:

    Show me all evidence that AI increases creative output but reduces diversity.Which sources connect human taste, constraint, and originality?What are the strongest arguments that AI creativity is remix rather than creation?Which co-creative workflows preserve human agency?Where do psychology papers and AI papers accidentally agree?

That is way more powerful than RAG alone.

* * *

# 1. The key distinction: RAG vs research graph

Normal RAG is usually:

    Question → retrieve similar chunks → answer from chunks

That is useful, but it is shallow.

A research graph is:

    Question→ retrieve sources, claims, concepts, relationships, contradictions, and evidence paths→ answer with provenance and confidence

Classic RAG combines a model’s internal knowledge with an external retriever so responses can use explicit non-parametric memory, which helps with factuality, specificity, and updating knowledge without retraining. 

GraphRAG goes further by extracting a knowledge graph from raw text, building communities/hierarchies, summarizing those communities, and using the structure during retrieval. Microsoft describes GraphRAG as combining text extraction, network analysis, and LLM summarization into an end-to-end system for understanding text datasets. 

So for your creativity research agent, do **hybrid RAG + knowledge graph**, not just vector search.

* * *

# 2. What your graph should store

You want several layers of data, not one blob.

## Layer A: Sources

These are papers, books, essays, interviews, talks, product docs, case studies, articles, forum threads, and creative examples.

Example source record:

    { "source_id": "src_2026_001", "title": "Creativity and Generative AI", "authors": ["..."], "year": 2025, "source_type": "paper", "domain": "human-ai co-creativity", "url": "...", "quality_score": 0.82, "credibility_notes": "Peer-reviewed, strong sample size, limited domain diversity", "ingested_at": "2026-06-10"}

## Layer B: Claims

This is the most important layer.

A source is not a fact. A source contains **claims**. Extract claims as independent objects.

Example:

    { "claim_id": "claim_001", "source_id": "src_2026_001", "claim": "Human-AI collaboration can increase creative output but may reduce diversity of ideas.", "claim_type": "empirical", "track": "co-creativity", "evidence_strength": 0.74, "confidence": 0.68, "method": "meta-analysis", "limitations": ["creative tasks varied", "evaluation metrics inconsistent"], "quote_span": "..."}

This is what makes later inference possible.

## Layer C: Concepts

Concepts are reusable research nodes.

For your topic, concepts might include:

    tastenoveltyoriginalitydiversityconstraintagencyauthorshipintentionalitymeaningembodimentiterationselectionlatent spacestyle collapsepromptingcurationhuman controlco-creationautomationcreative risk

Each concept should have aliases:

    { "concept_id": "concept_taste", "label": "taste", "aliases": ["aesthetic judgment", "creative judgment", "selection ability"], "definition": "The ability to evaluate, select, and refine creative possibilities according to goals, context, and standards.", "track": "human creativity"}

## Layer D: Relationships

This is where the graph comes alive.

Example relationships:

    { "edge_id": "edge_001", "subject": "human control", "predicate": "increases", "object": "creative ownership", "supporting_claims": ["claim_014", "claim_022"], "contradicting_claims": ["claim_031"], "confidence": 0.72}

Good relationship predicates:

    increasesdecreasesenablesconstrainsdepends_oncontradictssupportscausescorrelates_withis_apart_ofmeasured_byevaluated_bysimilar_todifferent_from

## Layer E: Research questions

Your agent should store questions as first-class objects too.

    { "question_id": "q_001", "question": "Does AI improve creative productivity while reducing diversity?", "status": "active", "related_concepts": ["AI creativity", "diversity", "productivity", "co-creation"], "strongest_supporting_claims": ["claim_001", "claim_008"], "strongest_opposing_claims": ["claim_017"], "open_gaps": ["Need non-writing domains", "Need longitudinal evidence"]}

This lets the agent keep asking better questions instead of randomly researching.

* * *

# 3. The best schema for human creativity + AI creativity

I’d design your graph around **three major research tracks**:

    Human creativityAI creativityHuman-AI co-creativity

Then every claim gets tagged by:

    TrackDomainMethodCreative phaseEvidence typeConfidence

## Track

    humanAIhuman-AI

## Domain

    writingvisual artmusicfilmadvertisingdesignsoftwarescienceeducationproduct innovation

## Creative phase

    ideationdivergenceselectioniterationexecutioncritiquepublishingaudience interpretation

## Evidence type

    empirical studymeta-analysiscase studytheoryinterviewhistorical examplebenchmarkproduct behaviorpersonal experiment

## Measured dimensions

    noveltyusefulnessdiversityqualityspeedemotional resonanceauthorshipagencyownershipsurprisecoherencememorabilitycultural impact

This matters because “AI creativity” is too broad. You want to be able to filter:

    Show empirical studies about AI and idea diversity in writing tasks.Show theory papers about authorship in visual art.Show case studies where human control increased ownership.Show claims about taste during the selection phase.

That is the whole game.

* * *

# 4. The data model I’d actually build

Use a relational database first, then add graph/vector layers.

I would not start with a pure graph database. Start with **Postgres + pgvector** or **SQLite + sqlite-vss/Chroma** locally, then add Neo4j/Kùzu later if you need richer graph queries.

For your local 3070 box, a simple but powerful stack:

    SQLite or Postgres+ vector index+ Markdown memo output+ JSON graph exports+ optional graph visualization

## Tables

### `sources`

    idtitleauthorsyearsource_typedomainurlpublisherabstractquality_scorecreated_at

### `chunks`

    idsource_idchunk_textpagesectionembedding

### `claims`

    idsource_idchunk_idclaim_textclaim_typetrackdomaincreative_phaseevidence_typeevidence_strengthconfidencelimitationscreated_at

### `concepts`

    idlabeldefinitionaliasestrackparent_concept_id

### `claim_concepts`

    claim_idconcept_idrole

Roles can be:

    subjectobjectcontextmethodmetriclimitation

### `relationships`

    idsubject_concept_idpredicateobject_concept_idconfidenceevidence_strengthcreated_at

### `relationship_evidence`

    relationship_idclaim_idstance

Stance:

    supportscontradictsqualifies

### `questions`

    idquestionstatusprioritycreated_at

### `question_claims`

    question_idclaim_idrelevance_scorestance

This schema is simple enough to build quickly, but strong enough to support real inference later.

* * *

# 5. The research graph should not only store “facts”

For this topic, you need at least five node types:

    SourceClaimConceptPerson / AuthorMethodMetricCreative workflowCreative artifactResearch question

And edges like:

    Source CONTAINS ClaimClaim SUPPORTS ConceptRelationshipClaim CONTRADICTS ClaimConcept INFLUENCES ConceptMethod MEASURES MetricWorkflow PRESERVES AgencyWorkflow REDUCES DiversityAuthor ARGUES ClaimQuestion SEEKS Evidence

The graph should be able to answer:

    Which claims support this inference?Which claims contradict it?Which concepts connect these two fields?Which evidence is empirical vs theoretical?Which ideas are well-supported vs speculative?

That is the difference between “cool AI summaries” and “research infrastructure.”

* * *

# 6. The best agent methods

I’d use a multi-pass research loop. Do not let one model call do everything.

## Agent 1: Scout

Finds sources.

    Input: research questionOutput: candidate sources with reason for inclusion

Methods:

- Search academic sources
- Search books/essays/interviews
- Search product/tool examples
- Deduplicate
- Rank by relevance and credibility

## Agent 2: Reader

Reads source chunks and extracts structured notes.

    Input: source textOutput: summary, claims, concepts, methods, limitations

Important: this agent should not synthesize too much. Its job is extraction.

## Agent 3: Claim extractor

Turns prose into atomic claims.

Bad claim:

    AI changes creativity.

Good claim:

    In brainstorming tasks, generative AI may increase average idea quality while reducing semantic diversity across participants.

Atomic claims need:

- subject
- predicate
- object
- scope
- evidence
- limitations

## Agent 4: Concept linker

Links claims to existing concepts or proposes new concepts.

    "semantic diversity" → concept_diversity"human ownership" → concept_creative_ownership"AI suggestions" → concept_AI_assistance

## Agent 5: Contradiction detector

Finds conflicts.

    Claim A: AI improves novelty.Claim B: AI reduces originality.Question: Are they measuring different things?

This is huge. Many creativity debates are fake contradictions caused by different definitions.

## Agent 6: Inference builder

Generates provisional inferences only from linked evidence.

Example:

    Inference:AI appears to be more useful in divergence and execution than in final taste-making.Evidence:- Claims 12, 19, 44 support increased ideation speed.- Claims 31 and 37 warn of reduced diversity.- Claims 52 and 59 suggest user control increases ownership.Confidence:Medium.Open gaps:Need evidence from film/design, not just writing tasks.

## Agent 7: Skeptic / auditor

Audits the inference.

It asks:

    Are the cited claims actually enough?Are we overgeneralizing?Are sources low quality?Are we mixing domains?Are we confusing novelty with usefulness?

This should run before anything becomes a “strong conclusion.”

* * *

# 7. The most important design rule: separate observations, claims, and inferences

Do not let the database blur these.

## Observation

Something directly found in a source.

    The study used 300 participants in a writing task.

## Claim

What the source argues or finds.

    Participants using AI generated higher-rated ideas.

## Inference

What your system concludes after comparing sources.

    AI may improve average creative output in short-form writing tasks, but the evidence does not yet generalize to film, music, or long-term creative practice.

This separation is everything.

Your system should tag every statement as:

    observationsource_claimagent_inferenceuser_notehypothesis

Later, when you ask “what do we know?”, the agent can avoid pretending its own speculation is source-backed.

* * *

# 8. Confidence scoring

You want evidence-backed inference, so each claim needs scoring.

I’d use simple scores at first:

    Source credibility: 0–1Evidence strength: 0–1Relevance: 0–1Recency: 0–1Domain match: 0–1Contradiction penalty: 0–1

Then compute an inference score:

    inference_confidence = average supporting evidence strength × source credibility × domain match - contradiction penalty

Do not over-engineer it. The score is not truth. It is a sorting/filtering tool.

Example:

    { "inference": "AI can increase ideation speed but may reduce diversity.", "support_count": 12, "contradiction_count": 3, "avg_source_quality": 0.78, "domain_coverage": ["writing", "design", "education"], "confidence": "medium-high", "caveat": "Most evidence comes from short-form ideation tasks."}

That caveat is as important as the confidence score.

* * *

# 9. How filtering should work

Your UI should feel like a research cockpit.

Filter by:

    Track: human / AI / human-AIDomain: writing / film / design / music / advertising / codeEvidence type: empirical / theory / case study / interview / benchmarkCreative phase: ideation / selection / execution / critiqueConcept: taste / novelty / diversity / agency / ownershipConfidence: low / medium / highStance: supports / contradicts / qualifiesYearAuthorSource quality

Example filters:

    Track = human-AIConcept = diversityEvidence type = empiricalCreative phase = ideationStance = supports

Result:

    All empirical claims supporting the idea that human-AI ideation affects diversity.

Or:

    Track = humanConcept = tasteDomain = advertisingEvidence type = interview / case study

Result:

    How creative professionals describe taste in real-world work.

* * *

# 10. The query modes you want

Build several retrieval modes, not one.

GraphRAG and related approaches are useful because graph structure can retrieve relationships and communities, not just isolated chunks. Microsoft’s GraphRAG docs describe a structured, hierarchical approach where the pipeline extracts a graph from text, builds a community hierarchy, summarizes communities, and uses those structures for RAG tasks. 

LightRAG is another useful reference point because it combines graph structures with text indexing and uses dual-level retrieval for both low-level entity details and higher-level knowledge discovery. 

For your system, use these retrieval modes:

## Local claim retrieval

Best for specific questions.

    “What does source X say about diversity?”

Retrieves:

- source chunks
- claims from that source
- linked concepts

## Concept neighborhood retrieval

Best for theory-building.

    “What is taste connected to?”

Retrieves:

- concept node
- adjacent relationships
- supporting/contradicting claims
- related sources

## Community retrieval

Best for broad synthesis.

    “What are the main schools of thought around AI creativity?”

Retrieves:

- concept clusters
- community summaries
- representative claims

## Contradiction retrieval

Best for serious analysis.

    “What evidence challenges the idea that AI improves creativity?”

Retrieves:

- opposing claims
- methodological differences
- weak spots

## Evidence path retrieval

Best for explainability.

    “Why do we believe human control increases creative ownership?”

Returns:

    human control→ supportscreative ownership→ backed by claims 12, 19, 21→ from sources A, B, C→ confidence medium

This is what makes it feel data-backed.

* * *

# 11. The inference engine

Do not make the agent infer freely from vibes. Make it infer from graph patterns.

Useful inference patterns:

## Pattern 1: Repeated support

    Many independent sources support same relationship.

Example:

    human control → increases → ownership

## Pattern 2: Cross-domain convergence

    A concept appears in multiple fields.

Example:

    constraint improves creativity appears in design, writing, advertising, and psychology.

## Pattern 3: Contradiction by metric

    Sources disagree because they measure different outcomes.

Example:

    AI improves usefulness but reduces diversity.

## Pattern 4: Boundary conditions

    A claim is true only under certain conditions.

Example:

    AI improves ideation when the human remains curator, but may homogenize output when users accept first suggestions.

## Pattern 5: Missing evidence

    A popular claim has low empirical support.

Example:

    “AI is creative like humans” has lots of essays, fewer strong empirical definitions of creativity.

## Pattern 6: Bridge concepts

    A concept connects two domains.

Example:

    taste bridges human creativity and AI creativity because AI can generate variations, but humans often select and contextualize meaning.

These are the patterns that can make the agent genuinely insightful.

* * *

# 12. Recommended build architecture

For v1:

    Frontend:Next.js or simple React dashboardBackend:Python FastAPIAgent orchestration:LangGraph or simple queue workerDatabase:Postgres + pgvectoror SQLite + Chroma for local-onlyGraph:Start with relational edge tablesLater add Neo4j or KùzuSearch:Tavily / Brave / SerpAPI / Semantic Scholar / arXivManual PDF upload supportParsing:Unstructured / PyMuPDF / trafilatura / BeautifulSoupEmbeddings:Local embedding model if possibleOpenAI embeddings if you want higher qualityLLM:Local model for extraction/taggingPaid API for hard synthesis and final memos

LangGraph is a reasonable fit if you want durable, long-running agent flows because it is designed for stateful agents. Its docs also distinguish long-term memory from short-term thread memory, with long-term memory saved across sessions in namespaces. 

But be honest: you do **not** need LangGraph on day one. You can start with a Python script and a database.

The smallest useful v1:

    ingest_source.pyextract_claims.pylink_concepts.pybuild_edges.pyquery_graph.pywrite_memo.py

That is enough.

* * *

# 13. The actual pipeline

## Step 1: Ingest

Inputs:

    PDFURLYouTube transcriptbook notesmanual notespaper abstract

Outputs:

    source recordraw textchunksembeddings

## Step 2: Extract source card

The agent creates:

    summarymain claimsmethodlimitationsconceptsuseful quotes

## Step 3: Extract atomic claims

Each claim gets structured.

    { "claim": "AI-assisted brainstorming increased average idea quality but reduced semantic diversity.", "subject": "AI-assisted brainstorming", "predicate": "reduces", "object": "semantic diversity", "scope": "short-form ideation tasks", "evidence_type": "empirical", "confidence": 0.71}

## Step 4: Link concepts

Map:

    AI-assisted brainstorming → human-AI co-creativitysemantic diversity → diversityidea quality → usefulness / quality

## Step 5: Build edges

Create graph relationship:

    AI assistance → may_reduce → idea diversity

With support:

    claim_001claim_004claim_011

## Step 6: Detect contradictions

Example:

    AI assistance → increases → noveltyAI assistance → decreases → diversity

The agent should ask:

    Are novelty and diversity being measured differently?Are tasks different?Are domains different?Is this a real contradiction or a scope mismatch?

## Step 7: Generate synthesis memo

Every memo should include:

    Research questionCurrent answerSupporting evidenceContradicting evidenceConfidenceCaveatsOpen questionsNext sources to find

* * *

# 14. The best MVP to build first

Build a **Claim Graph MVP**.

Forget fancy UI at first.

The first useful thing should let you do this:

    research ingest paper.pdf --track human-ai --domain creativityresearch extract-claims src_001research link-concepts src_001research ask "Does AI reduce creative diversity?"research memo "AI and creative diversity"

Output should look like:

    Answer:There is medium evidence that AI assistance can improve average output quality while reducing diversity in some short-form ideation tasks.Supporting claims:- claim_001 from Source A- claim_006 from Source B- claim_012 from Source CContradicting/qualifying claims:- claim_019 says diversity improves when users are prompted to explore multiple divergent directions.- claim_024 says results vary by domain.Confidence:Medium.Caveat:Most evidence is from writing/brainstorming tasks, not film, music, or long-term creative practice.

That is already valuable.

* * *

# 15. How to make it data-backed rather than fake-intellectual

Use these rules:

## Rule 1: No uncited conclusions

Every conclusion needs linked claims.

## Rule 2: Claims must preserve scope

Bad:

    AI reduces creativity.

Good:

    In short-form ideation tasks, AI may reduce semantic diversity across participant outputs.

## Rule 3: Separate evidence types

An interview with a creative director is valuable, but it is not the same as a controlled study.

## Rule 4: Always store limitations

Limitations should be queryable.

    Show me all claims about AI creativity that are based only on writing tasks.

## Rule 5: Contradictions are assets

Do not hide disagreement. Store it.

## Rule 6: Confidence should decrease when domain transfer is weak

A finding from “students writing short stories” should not automatically apply to “professional film directors making campaigns.”

## Rule 7: Keep raw quotes/chunks

You need provenance. Summaries are not enough.

* * *

# 16. Your “creativity ontology”

This is the secret weapon. Create a custom ontology for creativity.

Start with this:

    Creativity├── Generation│ ├── Ideation│ ├── Divergence│ ├── Variation│ └── Recombination├── Selection│ ├── Taste│ ├── Judgment│ ├── Curation│ └── Rejection├── Execution│ ├── Craft│ ├── Technique│ ├── Iteration│ └── Polish├── Meaning│ ├── Intention│ ├── Emotion│ ├── Identity│ ├── Context│ └── Audience interpretation├── Evaluation│ ├── Novelty│ ├── Usefulness│ ├── Diversity│ ├── Coherence│ ├── Surprise│ └── Resonance└── Co-Creation ├── Human control ├── AI agency ├── Feedback loop ├── Ownership └── Authorship

Every claim should attach somewhere in this ontology.

That lets you later ask:

    Show me all research about selection/taste, not generation.Show me where AI helps execution but hurts originality.Show me concepts connected to authorship and ownership.

* * *

# 17. How to research human and AI creativity separately, then together

## Human-only graph

Focus on:

    psychologyneurosciencecreative practiceart/design theoryadvertising/film/music case studies

Core relationships:

    constraint → increases → originalitytaste → improves → selection qualitycraft → improves → executionlived experience → shapes → meaningculture → shapes → interpretation

## AI-only graph

Focus on:

    computational creativityLLM/diffusion behaviorbenchmarksnovelty/diversity metricstraining datamodel collapse/style convergence

Core relationships:

    training data → shapes → output distributiontemperature → affects → variationprompt framing → affects → noveltyRLHF → may increase → helpfulnessRLHF → may decrease → weirdnessretrieval → expands → reference space

## Human-AI graph

Focus on:

    co-creation workflowsagencycontrolownershipinterface designcreative productivityhomogenization

Core relationships:

    human control → increases → ownershipAI suggestion → increases → ideation speedAI suggestion → may decrease → diversityhuman curation → improves → final qualityconstraints → reduce → generic output

Then bridge them:

    taste links human selection with AI generationconstraint links human creative process with AI prompt designdiversity links psychological creativity with model output evaluationagency links creative identity with tool/interface design

This is where the original insights come from.

* * *

# 18. Example query and answer path

User asks:

    Is taste becoming more important than execution in the AI era?

The system should retrieve:

    Concept: tasteConcept: executionConcept: AI assistanceConcept: human controlConcept: creative ownership

Then evidence paths:

    AI assistance → reduces execution bottleneckAI assistance → increases variation volumetaste → improves selection among variationshuman control → increases ownershipAI-first outputs → may reduce diversity

Then answer:

    Inference:Taste appears to become more important in workflows where AI reduces the cost of generating and executing variations. However, this is strongest in domains where AI output quality is already high enough for rapid iteration, and weaker in domains where craft constraints remain difficult.Confidence:Medium.Evidence:Claims 12, 19, 31 support AI increasing output volume.Claims 44, 47 support the importance of human control and ownership.Claims 51, 52 warn that AI suggestions may narrow diversity.

That is the kind of “data-backed inference” you want.

* * *

# 19. The agent loop I’d run daily

    Daily Creativity Research Loop1. Choose one active research question.2. Find 3–5 candidate sources.3. Score sources for relevance and quality.4. Ingest the best 1–2 sources.5. Extract atomic claims.6. Link claims to concepts.7. Add/update graph edges.8. Check for contradictions.9. Update confidence scores.10. Write a 300-word research log.11. Propose tomorrow’s research question.

Weekly:

    Weekly Synthesis Loop1. Pick one major question.2. Retrieve all linked claims.3. Cluster by stance and evidence type.4. Identify strongest inference.5. Identify strongest caveat.6. Identify missing evidence.7. Write a memo.8. Generate 3 creative/product experiments.

Monthly:

    Monthly Theory Loop1. Find the densest concept clusters.2. Find bridge concepts between human and AI creativity.3. Find unresolved contradictions.4. Generate a theory map.5. Write one polished essay or product thesis.

* * *

# 20. What I would build first, concretely

## Phase 1: Local research database

Build CLI only.

Commands:

    research add-source <url-or-pdf>research extract <source_id>research concepts <source_id>research graph-buildresearch ask "question"research memo "topic"

## Phase 2: Simple dashboard

Pages:

    SourcesClaimsConceptsRelationshipsQuestionsMemos

Filters:

    trackdomainconceptevidence typeconfidencestanceyear

## Phase 3: Graph view

Show:

    concept nodesclaim nodessource nodessupport/contradict edgesconfidence thickness

## Phase 4: Inference engine

Add:

    support countcontradiction countconfidencedomain coverageevidence diversityopen gaps

## Phase 5: Research copilot

Chat with the graph:

    Ask a question→ retrieve evidence paths→ answer with claims→ show filters→ suggest next research

* * *

# 21. Best technical version for you

I’d build it as:

    /creativity-research-agent /data sources/ memos/ graph_exports/ /app dashboard /agent ingest.py extract_claims.py link_concepts.py build_edges.py contradiction_check.py synthesize.py /db schema.sql /prompts source_card.md claim_extractor.md concept_linker.md skeptic.md synthesis.md

Use:

    PythonFastAPIPostgres + pgvector, or SQLite firstNetworkX for graph analysisPyMuPDF for PDFsBeautifulSoup/trafilatura for web pagesLocal Ollama model for extractionPaid API model for synthesisReact/Next.js dashboard later

NetworkX is nice early because you can compute:

    central conceptsbridge conceptsdense clustersshortest paths between ideascommunities

That gives you questions like:

    What concept connects “lived experience” and “prompt engineering”?

Potential answer:

    constrainttastereference selection

That is exactly the kind of connection engine you want.

* * *

# 22. The most valuable “research graph” features

Prioritize these:

## Must-have

    Source cardsAtomic claimsConcept linkingSupport/contradict edgesFiltersEvidence-backed answersResearch memos

## Nice-to-have

    Graph visualizationCommunity detectionTimeline viewsAuthor mapsCitation networksPDF highlightingAuto-source discovery

## Later

    Multi-agent debateExperiment trackerCreative workflow generatorPublic essay generatorProduct idea miner

* * *

# 23. A strong first build prompt for your local agent

Use this:

    You are building a local-first Creativity Research Graph Agent.Goal:Create a research system that ingests sources about human creativity, AI creativity, and human-AI co-creativity, extracts atomic claims, links them to concepts, builds support/contradiction relationships, and answers questions with evidence-backed inferences.Build v1 as a simple Python + SQLite project, CLI-first. Do not build a fancy UI yet.Core requirements:1. Create a SQLite schema with tables: - sources - chunks - claims - concepts - claim_concepts - relationships - relationship_evidence - research_questions - memos2. Add CLI commands: - add-source - ingest-text - extract-claims - link-concepts - build-relationships - ask - write-memo3. The system must separate: - observation - source_claim - agent_inference - user_note - hypothesis4. Every claim must store: - claim text - source id - source chunk id - track: human / AI / human-AI - domain - creative phase - evidence type - confidence - limitations - related concepts5. Every relationship must store: - subject concept - predicate - object concept - supporting claims - contradicting claims - confidence6. The ask command must answer with: - direct answer - supporting claims - contradicting claims - confidence - caveats - open research gaps7. Include a starter creativity ontology with concepts: - taste - novelty - originality - diversity - constraint - agency - authorship - ownership - intention - meaning - iteration - curation - human control - AI assistance - co-creation - style collapse - prompt engineering8. Include sample seed data with 3 fake/example sources so the CLI can be tested without external APIs.9. Write a README explaining: - project purpose - schema - commands - research workflow - how evidence-backed inference worksImportant:Do not create vague summaries only. The core artifact is the claim graph.Every inference must be traceable back to source claims.

* * *

# 24. My honest recommendation

Build this in this order:

    1. Claim database2. Concept ontology3. Relationship edges4. Evidence-backed ask command5. Weekly memo generator6. Dashboard7. Graph visualization

Do **not** start with a fancy autonomous web crawler. That is tempting, but it creates garbage fast.

Start with **high-quality manual ingestion + strong extraction**.

The compounding value comes from clean claims and relationships. A small graph of 50 excellent sources is more valuable than 5,000 noisy scraped pages.