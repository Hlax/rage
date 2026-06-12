# MODEL_RUNTIME_SPEC.md

## 1. Purpose

This document defines how the Research Graph Engine (RGE) invokes local models for MVP scaffolding. It exists to make the local Qwen/Ollama runtime explicit before implementation begins.

The core rule is:

```txt
Qwen/Ollama proposes structured candidate output.
Python validates, scores, stages, writes, reports, and audits.
```

The repository must not contain model weights, implement local inference, or treat model output as trusted. Ollama runs as a separate local model service. The Python RGE repo calls that service through a thin adapter layer.

## 2. Runtime Boundary

### Ollama/Qwen

Ollama is the local model runtime. Qwen is the default local instruction model family for MVP structured tasks.

Ollama owns:

- Local model installation and serving.
- Model loading/unloading.
- Inference execution.
- Local API access.

Ollama does not own:

- SQLite writes.
- Source fetching.
- File deletion.
- Git operations.
- Safety pass/fail.
- Public export approval.
- Domain activation.

### Python RGE repo

The Python repo owns:

- Prompts.
- JSON schemas.
- Model adapter functions.
- Response parsing.
- Pydantic validation.
- Claim validation.
- DB writes.
- Score events.
- Reports.
- Public export filtering.
- Safety audits.

### LangGraph

LangGraph nodes call Python model-adapter functions. LangGraph does not call Ollama directly from arbitrary node code. This keeps runtime behavior inspectable and mockable.

## 3. MVP Default Runtime

Recommended MVP defaults:

```txt
Model runtime: Ollama
Default local LLM: qwen2.5:7b or available Qwen 7B instruct variant
Model API access: localhost only
Native Ollama base URL: http://127.0.0.1:11434
Default RGE LLM mode: ollama
Golden-test LLM mode: mock
Embedding model: local sentence-transformer by default; Ollama embedding model later if useful
```

Recommended `.env.example` entries:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
RGE_LOCAL_LLM=qwen2.5:7b
RGE_LLM_MODE=ollama
RGE_TEST_LLM_MODE=mock
RGE_LLM_TIMEOUT_SECONDS=60
RGE_LLM_TEMPERATURE=0
RGE_LLM_SCHEMA_VERSION=0.1.0
RGE_EMBEDDING_MODE=local_sentence_transformer
RGE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Later alternatives:

```txt
ollama → openai-compatible local endpoint
qwen2.5:7b → larger local Qwen, DeepSeek, Llama, or API model
local sentence-transformer → Ollama embeddings, OpenAI embeddings, or vector DB adapter
single provider adapter → provider registry with local/API fallback
```

**Task-tier alignment (ticket-058):** Local Ollama handles four pipeline structured
tasks when `RGE_ALLOW_LIVE_LLM=1`. Python owns validation, scoring, and all DB
writes. Cluster/theory/ontology synthesis remains deterministic until future cloud
escalation. Mode ladder, forbidden actions, and responsibility split:
`docs/agents/13_MODEL_ESCALATION_POLICY.md`.

## 4. Adapter Module Layout

Add a formal model adapter package:

```txt
rge/
  llm/
    __init__.py
    base.py
    ollama_client.py
    mock_client.py
    schemas.py
    registry.py
```

### `rge/llm/base.py`

Defines the interface all model clients must implement.

Expected responsibilities:

- Define a common `ModelClient` protocol or abstract base class.
- Define common request/response envelopes.
- Require `schema_version` and `task_name` on every structured call.
- Return typed candidate objects, not raw unvalidated strings.

Required interface shape:

```txt
extract_claims(chunk, contract, domain_pack, schema_version) -> CandidateClaimBatch
link_concepts(claims, domain_pack, schema_version) -> CandidateConceptLinkBatch
draft_relationships(claims, concepts, domain_pack, schema_version) -> CandidateRelationshipBatch
draft_run_summary(run_report_packet, schema_version) -> CandidateRunSummary
draft_ticket(report_packet, schema_version) -> CandidateImprovementTicket
```

This document does not require exact Python code yet. The scaffold should create these files and testable boundaries.

### `rge/llm/ollama_client.py`

Responsible for:

- Calling local Ollama.
- Sending prompt + JSON schema.
- Receiving model response.
- Parsing JSON.
- Returning typed Pydantic objects.
- Recording runtime metadata.

Required metadata on every call:

```json
{
  "provider": "ollama",
  "model": "qwen2.5:7b",
  "base_url": "http://127.0.0.1:11434",
  "task_name": "claim_extraction",
  "schema_version": "0.1.0",
  "prompt_template_version": "0.1.0",
  "temperature": 0,
  "created_at": "..."
}
```

The adapter may call Ollama through either:

1. The official Ollama Python client.
2. Direct HTTP requests to the local Ollama API.

MVP recommendation: use direct HTTP or the official client, not LangChain `ChatOllama`, unless a later ticket explicitly adds that dependency. The reason is easier debugging, easier fixture replacement, and less abstraction in golden tests.

### `rge/llm/mock_client.py`

Used for golden tests and fixture mode.

Responsible for:

- Returning deterministic fixture outputs.
- Simulating valid outputs.
- Simulating malformed outputs.
- Simulating missing quote spans.
- Simulating overgeneralized claims.
- Simulating weak concept mappings.
- Allowing golden tests to run without Ollama installed or running.

Golden tests must force mock mode with:

```txt
RGE_LLM_MODE=mock
```

or:

```txt
RGE_TEST_LLM_MODE=mock
```

The test suite must not depend on live Qwen output.

### `rge/llm/schemas.py`

Defines versioned model-output schemas.

Required schemas for MVP:

```txt
CandidateClaimBatch_v0_1
CandidateClaim_v0_1
CandidateConceptLinkBatch_v0_1
CandidateRelationshipBatch_v0_1
CandidateRunSummary_v0_1
CandidateImprovementTicket_v0_1
```

Rules:

- Every structured output schema has a `schema_version`.
- Every prompt template has a `prompt_template_version`.
- Every DB record created from model output stores model name, provider, schema version, and prompt template version where relevant.
- Schema changes require fixture updates and golden tests.
- Backward-incompatible schema changes must increment schema version.

### `rge/llm/registry.py`

Selects provider based on config.

Selection rules:

```txt
if RGE_LLM_MODE=mock: use MockModelClient
if RGE_LLM_MODE=ollama: use OllamaModelClient
otherwise: fail closed with clear config error
```

The registry should not silently fall back from `ollama` to `mock` in normal mode. Silent fallback can hide real runtime failures. Tests may explicitly choose mock.

## 5. Structured Output Contract

All model tasks must request structured JSON and validate it after receipt.

Required post-response validation chain:

```txt
raw model response
→ JSON parse
→ Pydantic schema validation
→ schema_version check
→ task-specific validator
→ source/chunk/provenance validator
→ domain-pack validator
→ staged output
→ deterministic acceptance/rejection
```

Rules:

- Invalid JSON is rejected with `invalid_json`.
- Missing quote spans are rejected with `missing_quote_span`.
- Unsupported claims are rejected with `unsupported_claim`.
- Overgeneralized claims are rejected or rewritten with preserved scope before acceptance.
- Prompt-injection content is rejected with `unsafe_or_injected_content` when it appears as instruction-following rather than source content.

## 6. LangGraph Node Integration

Model-assisted nodes must call the adapter through stable module functions.

Example flow:

```txt
ExtractCandidateClaims node
→ rge.modules.claim_extractor.extract_candidate_claims(...)
→ rge.llm.registry.get_model_client(...)
→ OllamaModelClient.extract_claims(...) or MockModelClient.extract_claims(...)
→ CandidateClaimBatch schema validation
→ claim_validator.py validates quote spans/scope/source IDs
→ Python writes staged/accepted/rejected claims
→ node_report emitted
```

Qwen never writes directly to SQLite. It only returns candidate JSON.

## 7. MVP Tasks Powered by Qwen/Ollama

Qwen/Ollama may power these early nodes:

```txt
research_planner.py        query drafts / contract draft suggestions
claim_extractor.py         candidate claim JSON
concept_linker.py          proposed concept links
relationship_builder.py    proposed relationship drafts
run_evaluator.py           small run summary draft
ticket_writer.py           first-pass ticket wording
```

Python still validates all outputs before durable writes.

## 8. Tasks Qwen/Ollama Must Not Control

Qwen/Ollama must not directly handle:

```txt
DB writes
source fetching
browser actions
file deletes
Git commands
public export approval
safety pass/fail
domain activation
score changes without score_events
accepted graph mutation
shell commands
route creation
secret handling
```

Model tool calling may be supported by Ollama, but RGE MVP must not expose tools directly to Qwen. Python owns tools; Qwen proposes structured outputs.

## 9. Mock Model Mode for Tests

Golden tests must be deterministic and independent of local model availability.

Mock mode requirements:

- `pytest tests/golden` must pass without Ollama running.
- Fixture-mode research run must be able to use mock model outputs.
- Mock outputs must include both valid and invalid examples.
- Tests must verify Python validation, not Qwen phrasing.
- Model output fixture files must be versioned alongside schemas.

Recommended fixture files:

```txt
fixtures/llm_outputs/claim_extraction_valid.json
fixtures/llm_outputs/claim_extraction_valid_and_missing_quote.json
fixtures/llm_outputs/claim_extraction_overgeneralized.json
fixtures/llm_outputs/concept_linking_valid.json
fixtures/llm_outputs/relationship_builder_valid.json
fixtures/llm_outputs/run_summary_valid.json
fixtures/llm_outputs/improvement_ticket_valid.json
```

## 10. LLM Output Schema Versioning

Every model output must include:

```json
{
  "task_name": "claim_extraction",
  "schema_version": "0.1.0",
  "items": []
}
```

Every prompt template should include front matter or metadata:

```yaml
prompt_template_id: claim_extraction
prompt_template_version: 0.1.0
expected_output_schema: CandidateClaimBatch_v0_1
```

DB records derived from model output should preserve:

```txt
extractor_model
model_provider
model_runtime
schema_version
prompt_template_version
validator_version
```

Schema versioning acceptance criteria:

- Golden fixtures declare the schema version they target.
- Tests fail if fixture schema version and parser schema version mismatch.
- Prompt changes that alter output shape require schema or fixture updates.
- Reports include model/schema/prompt version when a model-assisted node runs.

## 11. Runtime Health Checks

Add a local runtime health command:

```bash
research model health
```

Expected behavior:

- In `mock` mode: reports mock provider active and exits successfully.
- In `ollama` mode: checks local Ollama base URL and model availability.
- Does not pull models automatically in MVP unless a later ticket explicitly adds that behavior.
- Does not fail golden tests when tests explicitly use mock mode.

Suggested output fields:

```json
{
  "mode": "ollama",
  "provider": "ollama",
  "base_url": "http://127.0.0.1:11434",
  "model": "qwen2.5:7b",
  "reachable": true,
  "model_available": true,
  "schema_version": "0.1.0"
}
```

## 12. Reporting Requirements

Every model-assisted node report must include:

```json
{
  "model_provider": "ollama | mock",
  "model_name": "qwen2.5:7b | mock",
  "llm_mode": "ollama | mock",
  "task_name": "claim_extraction",
  "schema_version": "0.1.0",
  "prompt_template_version": "0.1.0",
  "raw_response_stored": false,
  "candidate_count": 0,
  "validation_failures": []
}
```

Raw model responses should not be public-exported. They may be stored locally for debugging only if marked private and excluded by safety audit.

## 13. Safety Requirements

- Source text is untrusted, including text passed to Qwen.
- Model output is untrusted until validated.
- Qwen cannot mark sources as credible because source text asks it to.
- Qwen cannot delete claims.
- Qwen cannot approve public export.
- Qwen cannot activate domains.
- Qwen cannot call shell/Git/browser tools directly.
- Deterministic safety checks override model commentary.

## 14. Phase 0 / Pre-Scaffold Ticket

Ticket:

```txt
Add model runtime adapter spec and mock LLM mode
```

Goal:

```txt
Define how local Ollama/Qwen is called and ensure golden tests can run without a live model.
```

Expected files:

```txt
MODEL_RUNTIME_SPEC.md
rge/llm/__init__.py
rge/llm/base.py
rge/llm/ollama_client.py
rge/llm/mock_client.py
rge/llm/schemas.py
rge/llm/registry.py
fixtures/llm_outputs/*.json
.env.example
tests/golden/test_00_model_runtime.py
```

Acceptance criteria:

```txt
rge/llm/base.py defines the model client interface.
rge/llm/ollama_client.py calls local Ollama through configured base URL.
rge/llm/mock_client.py returns deterministic fixture outputs.
rge/llm/schemas.py defines versioned output schemas.
.env.example includes Ollama and mock-mode settings.
tests can force RGE_LLM_MODE=mock.
pytest tests/golden can run without Ollama.
No model client can write directly to accepted DB tables.
Model-assisted node reports include model/provider/schema/prompt metadata.
```

Non-goals:

```txt
Do not bundle model weights.
Do not implement inference inside the repo.
Do not add model-controlled shell tools.
Do not add model-controlled Git access.
Do not add public model endpoints.
Do not add LangChain provider abstraction unless a later ticket requires it.
```

Rollback plan:

```txt
Disable ollama mode through config, keep mock mode for tests, and revert adapter files without touching DB schema or public export logic.
```

## 15. MVP Acceptance Criteria

The model runtime layer is acceptable for MVP when:

- The adapter package exists.
- Mock mode runs deterministic golden tests without a live model.
- Ollama mode can be health-checked locally.
- Model outputs are schema-versioned.
- Python validation gates every model output before DB writes.
- Model-assisted node reports include runtime metadata.
- Safety audit confirms models cannot write directly, execute shell/Git, approve public export, or activate domains.
