"""Shared pytest defaults (isolate operator gates from gitignored .env.local)."""

from __future__ import annotations

import pytest

_OPERATOR_GATE_DEFAULTS = {
    "RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR": "0",
    "RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM": "0",
    "RGE_ALLOW_SOURCE_NETWORK": "0",
}


@pytest.fixture(autouse=True)
def _pin_operator_gate_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure file-based operator gates do not leak into tests by default."""
    for key, value in _OPERATOR_GATE_DEFAULTS.items():
        monkeypatch.setenv(key, value)
