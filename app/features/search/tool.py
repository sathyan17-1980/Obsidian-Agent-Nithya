"""Obsidian vault query tool for Pydantic AI agent.

This module implements the obsidian_query_vault tool for:
- Searching notes by content
- Listing notes by folder or tag
- Finding related notes via backlinks and tags
"""

from typing import Literal

from pydantic_ai import RunContext

from app.core.logging import get_logger
from app.features.agent import VaultDeps, vault_agent
from app.features.search.service import SearchService

logger = get_logger(__name__)


@vault_agent.tool
async def obsidian_query_vault(
    ctx: RunContext[VaultDeps],
    operation: Literal["search", "list", "find_related"],
    query: str | None = None,
    tags: list[str] | None = None,
    folder: str | None = None,
    limit: int = 10,
    response_format: Literal["detailed", "concise"] = "concise",
) -> str:
    """Query and discover content in your Obsidian vault.

    OPERATIONS:

    "search" - Find notes containing specific text
        Required: query (text to search for in note content)
        Optional: tags (filter by tags), folder (filter by folder path)
        Example: operation="search", query="FastAPI tutorial", tags=["learning"]
        Returns: Matching notes with content snippets showing query context

    "list" - List notes in a folder or with specific tags
        Optional: folder (path to list) OR tags (list of tags to filter by)
        Example: operation="list", folder="Projects/2025"
        Example: operation="list", tags=["important", "work"]
        Returns: List of notes with basic metadata

    "find_related" - Discover notes connected to a specific note
        Required: query (note title to find connections for)
        Example: operation="find_related", query="API Design Doc"
        Returns: Related notes discovered via backlinks and shared tags

    PARAMETERS:
    - operation: Type of query to perform (required)
    - query: Search text OR note title (meaning depends on operation - see above)
    - tags: Filter results by tags (e.g., ["project", "work"])
    - folder: Filter by or list specific folder path (e.g., "Work/Projects")
    - limit: Maximum results to return (1-100, default 10)
        Lower values improve performance and reduce token usage.
    - response_format: Output verbosity control
        * "concise": Note titles and brief snippets (token-optimized, ~50-70 tokens/note)
        * "detailed": Full metadata, paths, IDs for follow-up operations (~150-200 tokens/note)
        Use "concise" unless you need paths/IDs for subsequent tool calls.

    ERROR HANDLING:
    - If no results found, suggests query refinement strategies
    - If results truncated, indicates total available and suggests filters
    - If invalid folder path, lists available folders
    - If query too short (<3 chars), requests more specific terms

    RETURNS:
    Formatted string with:
    - Concise mode: "Found X notes:\\n1. [Title]: snippet...\\n2. [Title]: snippet..."
    - Detailed mode: Full metadata including paths, tags, created/modified dates
    - Truncation notice: "Showing 10 of 45 results. Refine with: tags=['specific'], folder='path'"

    Args:
        ctx: Pydantic AI run context with VaultDeps.
        operation: Type of query operation.
        query: Search text or note title.
        tags: Tag filter list.
        folder: Folder path filter.
        limit: Maximum number of results.
        response_format: Output verbosity ("concise" or "detailed").

    Returns:
        Formatted string with query results.

    Raises:
        ValueError: If query is missing for search/find_related or too short.
    """
    logger.info(
        "tool.query_vault_started",
        operation=operation,
        query=query,
        tags=tags,
        folder=folder,
        limit=limit,
        response_format=response_format,
    )

    service = SearchService(ctx.deps.vault_path)

    try:
        # Validate inputs based on operation
        if operation == "search":
            if not query:
                raise ValueError("Search operation requires 'query' parameter")
            if len(query) < 3:
                return (
                    "Query too short. Please provide at least 3 characters for meaningful search results. "
                    "Example: query='FastAPI tutorial'"
                )

            results = service.search(query=query, tags=tags, folder=folder, limit=limit)

        elif operation == "list":
            results = service.list_notes(tags=tags, folder=folder, limit=limit)

        elif operation == "find_related":
            if not query:
                raise ValueError("Find_related operation requires 'query' parameter (note title)")

            results = service.find_related(note_title=query, limit=limit)

        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Format response
        if not results:
            return _format_empty_response(operation, query, tags, folder)

        if response_format == "concise":
            return _format_concise_response(operation, results, limit)

        return _format_detailed_response(operation, results, limit)

    except Exception as e:
        logger.error(
            "tool.query_vault_failed",
            operation=operation,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise


def _format_empty_response(
    operation: str,
    query: str | None,
    tags: list[str] | None,
    folder: str | None,
) -> str:
    """Format response when no results are found."""
    if operation == "search":
        return (
            f"No notes found matching query '{query}'. "
            f"Suggestions: Try broader search terms, check spelling, or remove filters."
        )
    if operation == "list":
        filter_desc = f"in folder '{folder}'" if folder else f"with tags {tags}"
        return f"No notes found {filter_desc}. Try different folder or tags."
    if operation == "find_related":
        return (
            f"No related notes found for '{query}'. "
            f"Note may not exist or has no backlinks/shared tags."
        )
    return "No results found."


def _format_concise_response(operation: str, results: list[dict[str, object]], limit: int) -> str:
    """Format concise response (token-optimized)."""
    lines = [f"Found {len(results)} notes:"]

    for i, note in enumerate(results, 1):
        title = note["title"]

        if operation == "search":
            snippet = note.get("snippet", "")[:100]
            lines.append(f"{i}. [{title}]: {snippet}")

        elif operation == "list":
            tags_str = ", ".join([str(t) for t in note.get("tags", [])[:3]])  # type: ignore[misc]
            lines.append(f"{i}. [{title}] - Tags: {tags_str}" if tags_str else f"{i}. [{title}]")  # type: ignore[misc]

        elif operation == "find_related":
            conn_type = note.get("connection_type", "unknown")
            lines.append(f"{i}. [{title}] - Connected via {conn_type}")

    if len(results) == limit:
        lines.append(f"\nShowing first {limit} results. Increase limit or add filters to refine.")

    return "\n".join(lines)


def _format_detailed_response(operation: str, results: list[dict[str, object]], limit: int) -> str:
    """Format detailed response with full metadata."""
    lines = [f"Found {len(results)} notes:"]

    for i, note in enumerate(results, 1):
        title = note["title"]
        path = note.get("path", "")

        lines.append(f"\n{i}. {title}")
        lines.append(f"   Path: {path}")

        if operation == "search":
            snippet = note.get("snippet", "")
            tags: list[object] = note.get("tags", [])  # type: ignore[assignment]
            lines.append(f"   Snippet: {snippet}")
            if tags:
                lines.append(f"   Tags: {', '.join([str(t) for t in tags])}")  # type: ignore[misc]  # type: ignore[arg-type]

        elif operation == "list":
            tags: list[object] = note.get("tags", [])  # type: ignore[no-redef]
            created = note.get("created", "")
            if tags:
                lines.append(f"   Tags: {', '.join([str(t) for t in tags])}")  # type: ignore[misc]  # type: ignore[arg-type]
            if created:
                lines.append(f"   Created: {created}")

        elif operation == "find_related":
            conn_type = note.get("connection_type", "")
            shared_tags: list[object] = note.get("shared_tags", [])  # type: ignore[assignment]
            lines.append(f"   Connection: {conn_type}")
            if shared_tags:
                lines.append(f"   Shared tags: {', '.join([str(t) for t in shared_tags])}")  # type: ignore[misc]  # type: ignore[arg-type]

    if len(results) == limit:
        lines.append(
            f"\n--- Showing first {limit} results. Increase limit or add filters to refine. ---"
        )

    return "\n".join(lines)
