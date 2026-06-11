"""Route permission policy: public surface is static and read-only.

Phase 0 stub: policy constants from ``docs/agents/10_SAFETY_MODEL.md``
section 8. The deterministic route scanner arrives with the Phase 4 safety
audit ticket.
"""

from __future__ import annotations

ALLOWED_PUBLIC_ROUTES = (
    "GET /",
    "GET /cards/[id]",
    "GET /concepts/[id]",
    "GET /about",
    "GET /data/public_cards.json",
    "GET /data/public_memos.json",
    "GET /data/build_info.json",
)

FORBIDDEN_PUBLIC_ROUTE_KINDS = (
    "public write routes",
    "public source ingestion routes",
    "public agent execution routes",
    "routes exposing the private local API",
)
