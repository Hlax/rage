"""Public export policy: curated allowed fields and forbidden content.

Deterministic validation for public card JSON. Export must fail closed: one
unsafe record blocks the entire export (``docs/agents/10_SAFETY_MODEL.md`` section 7).
"""

from __future__ import annotations

import re
from typing import Any

ALLOWED_PUBLIC_CARD_FIELDS = frozenset(
    {
        "id",
        "type",
        "title",
        "summary",
        "confidence",
        "concepts",
        "source_count",
        "public_caveats",
        "public_source_metadata",
        "related_cards",
        "public_detail_level",
        "updated_at",
    }
)

REQUIRED_PUBLIC_CARD_FIELDS = (
    "id",
    "type",
    "title",
    "summary",
    "confidence",
    "concepts",
    "source_count",
    "public_detail_level",
    "updated_at",
)

FORBIDDEN_PUBLIC_EXPORT_CONTENT = (
    "raw private notes",
    "local file paths",
    "API keys",
    "full private source text",
    "prompt text",
    "hidden evaluator notes",
    "unsafe raw HTML/script content",
    "unreviewed draft claims unless marked public-safe",
    "private chain/reasoning",
)

FORBIDDEN_KEY_SUBSTRINGS = (
    "private",
    "prompt",
    "secret",
    "evaluator",
    "claim_id",
    "local_path",
    "raw_text",
    "body_markdown",
    "chunk_id",
    "source_id",
    "api_key",
)

FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/(?:home|Users)/\w+"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"IGNORE ALL PREVIOUS INSTRUCTIONS", re.IGNORECASE),
)


def _iter_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _key_is_forbidden(key: str) -> bool:
    lowered = key.casefold()
    return any(fragment in lowered for fragment in FORBIDDEN_KEY_SUBSTRINGS)


def _value_violations(text: str) -> list[str]:
    violations: list[str] = []
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(text):
            violations.append(
                f"forbidden content matching {pattern.pattern!r}: {text!r}"
            )
    return violations


def validate_public_card(card: dict[str, Any]) -> list[str]:
    """Return machine-readable violations for a single public card."""
    violations: list[str] = []

    extra_keys = set(card) - ALLOWED_PUBLIC_CARD_FIELDS
    if extra_keys:
        violations.append(f"non-public card fields: {sorted(extra_keys)}")

    for key in card:
        if _key_is_forbidden(key):
            violations.append(f"forbidden card key: {key}")

    for field in REQUIRED_PUBLIC_CARD_FIELDS:
        if field not in card:
            violations.append(f"missing required card field: {field}")

    if "concepts" in card and not isinstance(card["concepts"], list):
        violations.append("concepts must be a list")

    if "source_count" in card and not isinstance(card["source_count"], int):
        violations.append("source_count must be an integer")

    for text in _iter_strings(card):
        violations.extend(_value_violations(text))

    return violations


def validate_public_export_bundle(
    cards: list[dict[str, Any]],
    memos: list[dict[str, Any]],
    build_info: dict[str, Any],
) -> list[str]:
    """Validate an entire export bundle before writing files."""
    violations: list[str] = []
    for index, card in enumerate(cards):
        for issue in validate_public_card(card):
            violations.append(f"card[{index}] ({card.get('id', '?')}): {issue}")

    for index, memo in enumerate(memos):
        for text in _iter_strings(memo):
            violations.extend(
                f"memo[{index}]: {issue}" for issue in _value_violations(text)
            )

    for text in _iter_strings(build_info):
        violations.extend(f"build_info: {issue}" for issue in _value_violations(text))

    return violations


def curated_public_card(card: dict[str, Any]) -> dict[str, Any]:
    """Return only whitelisted public card fields."""
    return {key: card[key] for key in ALLOWED_PUBLIC_CARD_FIELDS if key in card}
