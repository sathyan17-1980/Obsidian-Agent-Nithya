"""Search feature for querying Obsidian vault content."""

from app.features.search.service import SearchService
from app.features.search.tool import obsidian_query_vault

__all__ = ["SearchService", "obsidian_query_vault"]
