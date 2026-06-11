"""Secrets and private-path leak policy for public exports.

Phase 0 stub: pattern categories the deterministic secrets audit must cover
(``docs/agents/10_SAFETY_MODEL.md`` sections 7 and 13). The scanner
implementation arrives with the Phase 4 safety audit ticket.
"""

from __future__ import annotations

# Content categories that must never appear in public JSON.
SECRET_LEAK_CATEGORIES = (
    "API keys and tokens",
    "secret-like strings",
    "local file paths (drive letters, home directories)",
    "private local service URLs",
    "environment variable values from .env",
)
