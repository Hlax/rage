# RGE Strongest MVP Phased Plan

**Goal:** turn RGE into a working autonomous research agent by proving a clean, quote-grounded, abstract-first research loop before expanding into selective full-text and PDF parsing.

**North star:** the agent should reliably discover scholarly sources, acquire clean evidence, extract quote-supported claims, synthesize a research report, and self-ticket the correct improvement when the loop fails.

---

## Executive Verdict

The current build does not need better abstract ranking first. The latest evidence shows it needs a cleaner evidence acquisition layer.

The dominant failure is:

```text
bad PDF decode / noisy chunks -> topic-shaped LLM claims -> quote validation fails -> unsupported_claim wall
```

The fastest useful MVP is:

```text
OpenAlex + Unpaywall + arXiv metadata
-> abstract-first evidence cards
-> quote-first extraction
-> cluster/synthesis report
-> failure-classified self-improvement tickets
-> selective full-text/PDF milestone after the abstract loop works
```

Do not bulk-download the world yet. Use APIs and small selected pulls until the research loop proves itself.

---

## Source Strategy

### OpenAlex

Use OpenAlex as the broad scholarly map:

- works
- authors
- venues/sources
- concepts/topics
- citation graph
- open-access status
- OA locations
- abstract inverted index
- selected hosted PDF/TEI content when available

OpenAlex should be the default discovery layer, not the only evidence layer.

### Unpaywall

Use Unpaywall as a DOI open-access resolver:

- DOI -> OA status
- best OA location
- PDF URL when available
- landing page URL
- license/version information
- repository vs publisher location

Unpaywall complements OpenAlex when the work has a DOI and the agent needs to resolve open full text.

### arXiv

Use arXiv as the easiest MVP corpus for AI/CS/math-adjacent topics:

- clean metadata
- abstract-first access
- selected PDFs
- machine-access-friendly bulk metadata paths

For the current domain, arXiv is likely the fastest way to prove real research-agent behavior without login/paywall complexity.

### Later sources

Add these only after the abstract-first loop works:

- Semantic Scholar for related-paper discovery and citation/recommendation signals
- Crossref for DOI/bibliographic resolution
- CORE for OA full-text expansion
- PubMed Central / Europe PMC only if the domain shifts toward biomedical/life sciences

---

## Local Download Policy

### Rule 1 — never download a giant corpus before a size preflight

Add a CLI command such as:

```bash
python -m rge.cli source-size-preflight --source openalex --scope works
python -m rge.cli source-size-preflight --source openalex --scope topics
python -m rge.cli source-size-preflight --source arxiv --scope metadata
```

OpenAlex S3 examples:

```bash
aws s3 ls --summarize --human-readable --no-sign-request --recursive "s3://openalex/"
aws s3 ls --summarize --human-readable --no-sign-request --recursive "s3://openalex/data/works/"
aws s3 ls --summarize --human-readable --no-sign-request --recursive "s3://openalex/data/topics/"
aws s3 ls --summarize --human-readable --no-sign-request --recursive "s3://openalex/data/sources/"
```

### Rule 2 — metadata first, documents second

The metadata database is the map. It is not enough for grounded claims.

Use metadata to:

- discover candidate papers
- rank relevance
- cluster topic neighborhoods
- resolve citations and venues
- decide which sources deserve evidence extraction

Use actual abstracts/full text to:

- extract quote-grounded claims
- validate support
- produce evidence cards
- write trustworthy reports

### Rule 3 — fetch selected full text only after ranking

Do not ask the LLM to read thousands of PDFs.

Use this loop:

```text
pull 100-500 metadata records
-> rank/filter/cluster
-> select top 5-20 sources
-> use abstracts first
-> fetch full text only for top sources that need deeper evidence
```

---

## Phase 0 — Baseline and Failure Taxonomy

**Purpose:** lock in the current failure signal so future work can prove improvement.

### Deliverables

- Add or update a reproducible baseline command for the latest failure pattern.
- Persist run metrics in a clear evidence DB/report.
- Add failure categories beyond `unsupported_claim`.

Suggested failure categories:

- `metadata_only`
- `abstract_missing`
- `no_oa_location`
- `download_failed`
- `parse_failed`
- `dirty_text`
- `zero_quoteable_spans`
- `unsupported_claim`
- `unsupported_claim_wall`
- `overgeneralized_scope`
- `ranker_selected_bad_source`
- `extractor_prompt_drift`

### Acceptance criteria

- A clean baseline report shows accepted/rejected counts by source.
- PDF failure is classified as acquisition/parsing failure, not ranking failure.
- Tests prove the failure classifier chooses the correct recommended improvement class.

---

## Phase 1 — Source Resolver Layer

**Purpose:** give the agent a real acquisition map before it tries to read documents.

### Deliverables

Add a unified source resolver interface:

```text
resolve_work(query/topic/doi/openalex_id/arxiv_id)
-> candidate works
-> source status
-> abstract availability
-> OA availability
-> best full-text location
-> source confidence
```

Add source status fields:

- `source_id`
- `source_kind`: `openalex`, `unpaywall`, `arxiv`, `manual_fixture`
- `doi`
- `openalex_id`
- `arxiv_id`
- `title`
- `year`
- `authors`
- `venue`
- `abstract_text`
- `abstract_source`
- `is_oa`
- `oa_status`
- `best_oa_location_url`
- `pdf_url`
- `landing_page_url`
- `license`
- `resolver_backend`
- `source_status`

### OpenAlex behavior

- Search works by query/topic.
- Reconstruct `abstract_inverted_index` into plaintext abstract.
- Store OA metadata and OpenAlex IDs.
- Do not require full text.

### Unpaywall behavior

- For DOI-backed works, query Unpaywall.
- Store `is_oa`, `oa_status`, `best_oa_location`, `url_for_pdf`, `url`, `license`, and version if available.
- If Unpaywall has no OA location, preserve the metadata record as `metadata_only` instead of failing.

### arXiv behavior

- Search arXiv for relevant AI/CS/math papers.
- Store abstract and selected PDF URL.
- Treat arXiv abstracts as first-class evidence.

### Acceptance criteria

- A query can return ranked candidates from OpenAlex and/or arXiv.
- DOI candidates can be enriched with Unpaywall OA info.
- Missing full text does not fail the run.
- Source status is explicit and queryable.

---

## Phase 2 — Abstract-First Evidence MVP

**Purpose:** prove that RGE can produce real, quote-grounded research summaries without depending on fragile PDF parsing.

### Deliverables

Add `abstract_evidence_card` generation:

```text
source metadata + abstract text
-> exact abstract quote spans
-> narrow claims grounded only in those spans
-> concept links
-> evidence card
```

Extraction must be quote-first:

1. Select exact quote spans from the abstract.
2. Validate each quote is a literal substring.
3. Generate a narrow claim from each quote.
4. Reject claims that add facts not present in the quote.
5. Persist accepted and rejected claims with reason.

### Prompting rule

The model should not be asked to “summarize the paper” first. It should be asked to select evidence spans first.

Bad:

```text
Tell me what this paper says about AI and creativity.
```

Good:

```text
Copy 1-3 exact substrings from this abstract that support narrow claims. Then write one claim per quote using only information contained in the quote.
```

### Acceptance criteria

- Abstract-only run produces accepted quote-grounded claims.
- No unsupported-claim wall on clean abstracts.
- Report clearly labels evidence as `abstract_only`.
- Concept linking works from accepted abstract claims.
- If abstract evidence is too thin, the system recommends selective full-text acquisition instead of hallucinating.

---

## Phase 3 — Field Map and Synthesis

**Purpose:** let the agent “understand the field” from mass metadata pulls without reading all documents.

### Deliverables

Add a field-map run:

```text
topic query
-> pull 100-500 metadata records
-> filter by relevance/year/OA/citation/venue
-> cluster by concepts, abstracts, citation links, and source similarity
-> select top sources
-> extract abstract evidence
-> synthesize field report
```

The field report should include:

- topic definition
- major clusters
- representative papers
- strongest quote-grounded claims
- weak or missing evidence areas
- disagreement/tension candidates
- recommended next sources to fetch full text for
- recommended self-improvement ticket if the run failed

### Acceptance criteria

- The agent can explain why it selected the top sources.
- Report distinguishes metadata-level conclusions from quote-grounded evidence.
- The system does not pretend metadata is full-text proof.
- Report generation succeeds even when some sources have no OA/full text.

---

## Phase 4 — Selective Full-Text Acquisition

**Purpose:** deepen evidence only for high-value sources.

### Deliverables

Add selective acquisition for top-ranked sources:

```text
ranked source
-> prefer OpenAlex TEI/XML if available
-> else use Unpaywall best OA PDF URL
-> else use arXiv PDF if arXiv source
-> else mark as not fetchable
```

Add document acquisition states:

- `full_text_not_needed`
- `full_text_requested`
- `full_text_available`
- `full_text_downloaded`
- `full_text_parse_failed`
- `full_text_clean_text_ready`
- `full_text_extract_failed`
- `full_text_evidence_ready`

### Acceptance criteria

- The agent fetches full text only for selected sources.
- The run records why each source was or was not fetched.
- Failures do not kill the whole research run.
- Abstract-only evidence remains valid even if full text fails.

---

## Phase 5 — PDF / TEI Milestone

**Purpose:** fix the current wall: dirty PDF text causing unsupported claims.

### Preferred parser order

1. OpenAlex TEI/XML when available.
2. GROBID TEI for scholarly PDFs if local setup is acceptable.
3. PyMuPDF / fitz for fast local PDF text extraction.
4. pypdf only as a lightweight fallback.
5. Never UTF-8 decode raw PDF bytes as text.

### Text quality gates

Before LLM extraction, score each parsed document/chunk:

- readable character ratio
- sentence count
- average line length
- binary/noise ratio
- repeated header/footer ratio
- quoteable span count
- language detection if useful
- parser backend
- page count
- extracted character count

If clean text is bad, do not call the LLM. Mark it:

```text
dirty_text -> parser improvement needed
```

### Full-text extraction rule

Same as abstracts: quote-first.

```text
chunk -> exact quote spans -> quote validation -> narrow claims -> concept links -> evidence card
```

### Acceptance criteria

- The previous PDF timing proof no longer produces a pure unsupported-claim wall.
- Bad PDFs are classified as `dirty_text` or `parse_failed` before LLM extraction.
- Good PDFs produce quote-supported claims from actual prose.
- Rank-2 zero-accepted failure triggers fallback instead of pipeline death.

---

## Phase 6 — Self-Improvement Loop Upgrade

**Purpose:** convert failures into useful next actions without creating heavy human audit drag.

### Deliverables

Add a failure-to-ticket recommender:

```text
run metrics + rejection reasons + source statuses
-> classify dominant bottleneck
-> recommend next improvement packet
```

Examples:

| Dominant signal | Recommended improvement |
|---|---|
| `unsupported_claim_wall` + dirty PDF chunks | PDF parser / quote-first extraction ticket |
| many `metadata_only` | OA resolver / source expansion ticket |
| many `abstract_missing` | source selection or metadata enrichment ticket |
| few relevant candidates | ranking/query expansion ticket |
| accepted claims but weak synthesis | report synthesis / concept linking ticket |
| validator rejects good claims | validator calibration ticket |

### Acceptance criteria

- The agent recommends parser fixes when parsing fails.
- The agent recommends ranker fixes only when candidate quality is actually the problem.
- Reports include both product diagnosis and engineering diagnosis.

---

## Phase 7 — Demo-Ready Research Loop

**Purpose:** prove the research agent as a product, not just infrastructure.

### Demo command

Example target command:

```bash
python -m rge.cli research-run \
  --topic "AI assisted creativity and idea diversity" \
  --sources openalex,unpaywall,arxiv \
  --mode abstract-first \
  --max-candidates 200 \
  --top-sources 12 \
  --full-text-top-n 3 \
  --out data/reports/research_runs/latest
```

### Demo output

- source candidate table
- source status table
- evidence cards
- accepted/rejected claim summary
- cluster report
- self-improvement recommendation
- public-safe export bundle if applicable

### Acceptance criteria

- One command produces a useful research report.
- The report includes quote-grounded evidence.
- Failures are explainable and actionable.
- The system can run mock/default tests without live APIs.
- Live mode is explicitly gated.

---

# Better Commit and Audit Cadence

The ticketed system was useful for discipline, but it slowed down experimentation. Replace “audit after every other ticket” with a phase packet system.

## New unit of work: change packet

A change packet is larger than a ticket but smaller than a release.

Each packet has:

- purpose
- scope
- target files/modules
- acceptance criteria
- targeted tests
- risk level
- final evidence report

Suggested packet naming:

```text
MVP-P1-source-resolver
MVP-P2-abstract-evidence
MVP-P3-field-map
MVP-P5-pdf-parser-milestone
```

## Commit style

Use frequent small commits inside a packet:

```text
feat(source-resolver): add unified source status schema
feat(openalex): reconstruct abstract inverted index
feat(unpaywall): enrich DOI works with OA locations
test(source-resolver): cover missing DOI and metadata-only fallbacks
evidence(mvp-p1): add source resolver run report
audit(mvp-p1): close source resolver packet
```

## Audit cadence

### Lightweight checks after each microcommit

Run only the relevant targeted tests:

```bash
pytest tests/golden/test_source_resolver.py -q
pytest tests/golden/test_abstract_evidence.py -q
python -m rge.cli verify --skip-site
```

### Full audit only at packet close

Run the full verification suite when closing a packet:

```bash
pytest tests/golden -q
pytest -q
pytest --collect-only
python -m rge.cli verify --skip-site
safety_auditor --audit full
npm run build
```

Use whichever commands are valid in the repo; do not invent broken commands.

### Triggered full audit

Run a full audit immediately if the packet changes:

- database migrations
- public export schema
- safety auditor
- validation/quote-grounding rules
- live API/network behavior
- source download behavior
- private/public boundary
- agent instruction protocol

Otherwise, keep moving with targeted tests.

## Branching

Use one branch per phase packet:

```text
phase/mvp-p1-source-resolver
phase/mvp-p2-abstract-evidence
phase/mvp-p5-pdf-parser-milestone
```

Do not create a new branch per tiny ticket unless the change is risky or unrelated.

## Reports

Keep reports, but reduce overhead:

- one preflight note per phase packet
- one evidence report per meaningful live/dry run
- one closeout audit per packet
- self-ticket recommendations inside the closeout report

Suggested report names:

```text
agent_reports/2026-XX-XX_mvp-p1-source-resolver-preflight.md
agent_reports/2026-XX-XX_mvp-p1-source-resolver-evidence.md
agent_reports/2026-XX-XX_mvp-p1-source-resolver-closeout.md
```

## Promotion gate

A packet can merge when:

- targeted tests pass
- no new safety/private-public violations
- evidence report exists
- failure modes are classified
- full packet closeout passes required checks
- any remaining gaps are written as next packet recommendations

---

# Recommended Build Order

## Packet 1 — Source resolver foundation

Implement OpenAlex + Unpaywall + arXiv source status layer.

**Why first:** it lets the agent know what it has before trying to extract claims.

## Packet 2 — Abstract-first evidence cards

Implement quote-first extraction from abstracts.

**Why second:** fastest path to a real functioning research-agent MVP.

## Packet 3 — Field map report

Implement mass metadata pull, ranking, clustering, and abstract-grounded synthesis.

**Why third:** proves the agent can reason across a research field without reading every PDF.

## Packet 4 — Self-improvement recommender

Implement failure-to-ticket recommendations.

**Why fourth:** makes the build autonomous in the right way.

## Packet 5 — Selective full-text acquisition

Fetch top-N full text using OpenAlex TEI, Unpaywall OA URLs, and arXiv PDFs.

**Why fifth:** full text becomes a targeted upgrade rather than a blocker.

## Packet 6 — PDF / TEI parser milestone

Replace raw PDF decoding with real parsing and quality gates.

**Why sixth:** fixes the current unsupported-claim wall.

## Packet 7 — Demo loop polish

One command creates candidate map, evidence cards, report, and self-improvement recommendation.

**Why seventh:** turns the build into a product demo.

---

# Non-Goals for Now

Do not prioritize:

- bulk downloading the full OpenAlex snapshot
- bulk downloading OpenAlex full-text PDFs/TEI corpus
- crawling paywalled publisher sites
- login-based research access
- general web browsing over precise scholarly acquisition
- tuning ranking before text acquisition is fixed
- making the public frontend the main focus
- building a giant local vector database before evidence cards work

---

# Product Definition of Done

The MVP is working when a user can run one command with a research topic and receive:

1. A source map of candidate papers.
2. A ranked source table with OA/access status.
3. Quote-grounded claims from abstracts.
4. Optional selected full-text evidence when available.
5. A research synthesis report.
6. A clear diagnosis of weak evidence or failed acquisition.
7. A recommended next improvement packet.

That is the first real autonomous research-agent product loop.
