"""Source discovery provider registry (Phase 3)."""

from rge.modules.source_providers.arxiv import ArxivProvider
from rge.modules.source_providers.openalex import OpenAlexProvider
from rge.modules.source_providers.registry import (
    SourceProvider,
    get_provider,
    list_provider_ids,
    register_provider,
)

register_provider(OpenAlexProvider())
register_provider(ArxivProvider())

__all__ = [
    "ArxivProvider",
    "OpenAlexProvider",
    "SourceProvider",
    "get_provider",
    "list_provider_ids",
    "register_provider",
]
