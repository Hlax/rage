"""Public export policy: curated allowed fields and forbidden content.

Phase 0 stub: policy constants from ``docs/agents/10_SAFETY_MODEL.md``
section 7. The enforcement logic (key/value inspection, fail-closed export
validation) arrives with the Phase 4 export ticket. Export must fail closed:
one unsafe record blocks the entire export.
"""

from __future__ import annotations

ALLOWED_PUBLIC_CARD_FIELDS = (
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
