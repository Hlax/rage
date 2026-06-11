"""Model runtime adapter boundary.

Qwen/Ollama proposes structured candidate output; Python validates, scores,
stages, writes, reports, and audits. Clients in this package return typed
candidate objects only. They never write to SQLite, shell, Git, public
exports, or accepted graph tables.

See ``docs/agents/03_MODEL_RUNTIME_SPEC.md``.
"""

from rge.llm.base import ModelCallMetadata, ModelClient
from rge.llm.registry import LlmModeError, get_model_client

__all__ = [
    "ModelCallMetadata",
    "ModelClient",
    "LlmModeError",
    "get_model_client",
]
