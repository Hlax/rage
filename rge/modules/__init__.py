"""Pipeline modules of the Research Graph Engine.

Phase 0 stubs with clear contracts; implementations arrive with later
tickets. Each module is an implementation boundary with explicit inputs,
outputs, and reports (see ``docs/agents/02_ARCHITECTURE.md`` section 5).

Module rules:
- Model-assisted modules call models only through the ``rge/llm`` adapter.
- Deterministic validators run before any write to accepted graph tables.
- Every module emits structured node reports, even on failure.
"""
