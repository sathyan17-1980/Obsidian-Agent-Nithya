"""Search service for Obsidian vault query operations.

This module implements the business logic for:
- Full-text search across notes
- Listing notes by folder or tag
- Finding related notes via backlinks and tags
"""

from pathlib import Path

import frontmatter

from app.core.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for searching and querying Obsidian vault content."""

    def __init__(self, vault_path: Path) -> None:
        """Initialize the search service.

        Args:
            vault_path: Path to the Obsidian vault directory.
        """
        self.vault_path = vault_path

    def search(
        self,
        query: str,
        tags: list[str] | None = None,
        folder: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Search for notes containing specific text.

        Args:
            query: Text to search for in note content.
            tags: Optional tag filter.
            folder: Optional folder path filter.
            limit: Maximum number of results.

        Returns:
            List of matching notes with snippets.
        """
        logger.info(
            "search.query_started",
            query=query,
            tags=tags,
            folder=folder,
            limit=limit,
        )

        results = []
        search_path = self.vault_path / folder if folder else self.vault_path

        if not search_path.exists():
            logger.warning(
                "search.folder_not_found", folder=folder, vault_path=str(self.vault_path)
            )
            return []

        # Search through all markdown files
        for md_file in search_path.rglob("*.md"):
            try:
                post = frontmatter.load(md_file)
                content = post.content
                metadata = post.metadata

                # Check tag filter
                if tags:
                    note_tags = metadata.get("tags", [])
                    if isinstance(note_tags, str):
                        note_tags = [note_tags]
                    if not any(tag in note_tags for tag in tags):
                        continue

                # Check if query is in content
                if query.lower() in content.lower():
                    # Extract snippet around match
                    snippet = self._extract_snippet(content, query)

                    results.append(
                        {
                            "title": md_file.stem,
                            "path": str(md_file.relative_to(self.vault_path)),
                            "snippet": snippet,
                            "tags": note_tags if tags else metadata.get("tags", []),
                        }
                    )

                    if len(results) >= limit:
                        break

            except Exception as e:
                logger.error(
                    "search.file_read_failed",
                    file=str(md_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

        logger.info("search.query_completed", results_count=len(results), query=query)
        return results

    def list_notes(
        self,
        tags: list[str] | None = None,
        folder: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """List notes in a folder or with specific tags.

        Args:
            tags: Optional tag filter.
            folder: Optional folder path to list.
            limit: Maximum number of results.

        Returns:
            List of notes with basic metadata.
        """
        logger.info("search.list_started", tags=tags, folder=folder, limit=limit)

        results = []
        search_path = self.vault_path / folder if folder else self.vault_path

        if not search_path.exists():
            logger.warning(
                "search.folder_not_found", folder=folder, vault_path=str(self.vault_path)
            )
            return []

        for md_file in search_path.rglob("*.md"):
            try:
                post = frontmatter.load(md_file)
                metadata = post.metadata
                note_tags = metadata.get("tags", [])

                if isinstance(note_tags, str):
                    note_tags = [note_tags]

                # Check tag filter
                if tags and not any(tag in note_tags for tag in tags):
                    continue

                results.append(
                    {
                        "title": md_file.stem,
                        "path": str(md_file.relative_to(self.vault_path)),
                        "tags": note_tags,
                        "created": metadata.get("created", ""),
                    }
                )

                if len(results) >= limit:
                    break

            except Exception as e:
                logger.error(
                    "search.file_read_failed",
                    file=str(md_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

        logger.info("search.list_completed", results_count=len(results))
        return results

    def find_related(self, note_title: str, limit: int = 10) -> list[dict[str, object]]:
        """Find notes related to a specific note via backlinks and tags.

        Args:
            note_title: Title of the note to find connections for.
            limit: Maximum number of results.

        Returns:
            List of related notes.
        """
        logger.info("search.find_related_started", note_title=note_title, limit=limit)

        # Find the source note
        source_file = self._find_note_file(note_title)
        if not source_file:
            logger.warning("search.note_not_found", note_title=note_title)
            return []

        try:
            source_post = frontmatter.load(source_file)
            source_tags = source_post.metadata.get("tags", [])
            if isinstance(source_tags, str):
                source_tags = [source_tags]

            related_notes = []

            # Search for notes that link to this note or share tags
            for md_file in self.vault_path.rglob("*.md"):
                if md_file == source_file:
                    continue

                try:
                    post = frontmatter.load(md_file)
                    content = post.content
                    metadata = post.metadata

                    # Check for backlinks (Obsidian link format: [[Note Title]])
                    has_backlink = f"[[{note_title}]]" in content

                    # Check for shared tags
                    note_tags = metadata.get("tags", [])
                    if isinstance(note_tags, str):
                        note_tags = [note_tags]

                    shared_tags = set(source_tags) & set(note_tags)

                    if has_backlink or shared_tags:
                        related_notes.append(
                            {
                                "title": md_file.stem,
                                "path": str(md_file.relative_to(self.vault_path)),
                                "connection_type": "backlink" if has_backlink else "shared_tags",
                                "shared_tags": list(shared_tags),
                            }
                        )

                        if len(related_notes) >= limit:
                            break

                except Exception as e:
                    logger.error(
                        "search.file_read_failed",
                        file=str(md_file),
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True,
                    )

            logger.info(
                "search.find_related_completed",  # type: ignore[return-value]
                note_title=note_title,
                results_count=len(related_notes),
            )
            return related_notes

        except Exception as e:
            logger.error(
                "search.find_related_failed",
                note_title=note_title,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return []

    def _find_note_file(self, note_title: str) -> Path | None:
        """Find the file path for a note by title.

        Args:
            note_title: Title of the note (without .md extension).

        Returns:
            Path to the note file, or None if not found.
        """
        for md_file in self.vault_path.rglob("*.md"):
            if md_file.stem == note_title:
                return md_file
        return None

    def _extract_snippet(self, content: str, query: str, context_chars: int = 100) -> str:
        """Extract a snippet of text around the search query.

        Args:
            content: Full content to extract from.
            query: Query text to find.
            context_chars: Number of characters to include before and after match.

        Returns:
            Snippet with context around the match.
        """
        lower_content = content.lower()
        lower_query = query.lower()

        idx = lower_content.find(lower_query)
        if idx == -1:
            return content[:200] + "..." if len(content) > 200 else content

        start = max(0, idx - context_chars)
        end = min(len(content), idx + len(query) + context_chars)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
