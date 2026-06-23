"""Operator env loading policy checks (CLI-only; public site must not load operator env)."""

from __future__ import annotations

import re

_FORBIDDEN_PATTERNS = (
    re.compile(r"dotenv.*\.env\.local", re.IGNORECASE),
    re.compile(r"loadOperatorEnv", re.IGNORECASE),
    re.compile(r"operator_env_loader", re.IGNORECASE),
    re.compile(r"process\.env\.(?:RGE_|OPENAI_|OPENROUTER_)", re.IGNORECASE),
)


def assert_public_site_does_not_load_operator_env(
    source_text: str,
    relative_path: str,
) -> list[str]:
    violations: list[str] = []
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(source_text):
            violations.append(
                f"{relative_path} may load operator env ({pattern.pattern})"
            )
    return violations
