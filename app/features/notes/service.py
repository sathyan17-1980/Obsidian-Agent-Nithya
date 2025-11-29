"""Note management service for individual note CRUD operations.

This module implements the business logic for:
- Creating notes with frontmatter
- Reading note content
- Updating (replacing or appending) content
- Deleting notes
- Getting/creating daily notes
- Managing note tags
"""

from datetime import UTC, datetime
from pathlib import Path

import frontmatter

from app.core.logging import get_logger

logger = get_logger(__name__)


class NoteService:
    """Service for managing individual notes in Obsidian vault."""

    def __init__(self, vault_path: Path) -> None:
        """Initialize the note service.

        Args:
            vault_path: Path to the Obsidian vault directory.
        """
        self.vault_path = vault_path

    def create(
        self,
        title: str,
        content: str,
        folder: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, str]:
        """Create a new note with optional frontmatter and folder placement.

        Args:
            title: Note title (without .md extension).
            content: Note content in markdown.
            folder: Optional folder path (auto-creates if doesn't exist).
            tags: Optional tags to add to frontmatter.

        Returns:
            Dict with created note details (title, path).

        Raises:
            FileExistsError: If note already exists.
        """
        logger.info("notes.create_started", title=title, folder=folder, tags=tags)

        # Determine file path
        if folder:
            note_dir = self.vault_path / folder
            note_dir.mkdir(parents=True, exist_ok=True)
        else:
            note_dir = self.vault_path

        file_path = note_dir / f"{title}.md"

        if file_path.exists():
            raise FileExistsError(f"Note '{title}' already exists at {file_path}")

        # Create frontmatter
        metadata: dict[str, list[str] | str] = {}
        if tags:
            metadata["tags"] = tags
        metadata["created"] = datetime.now(UTC).isoformat()

        # Create note with frontmatter
        post = frontmatter.Post(content, **metadata)

        with file_path.open("w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        logger.info(
            "notes.create_completed",
            title=title,
            path=str(file_path.relative_to(self.vault_path)),
        )

        return {
            "title": title,
            "path": str(file_path.relative_to(self.vault_path)),
            "tags": str(tags) if tags else "[]",
        }

    def read(self, title: str) -> dict[str, object]:
        """Read the full content of a specific note.

        Args:
            title: Note title (without .md extension).

        Returns:
            Dict with note content and metadata.

        Raises:
            FileNotFoundError: If note doesn't exist.
        """
        logger.info("notes.read_started", title=title)

        file_path = self._find_note_file(title)
        if not file_path:
            raise FileNotFoundError(
                f"Note '{title}' not found. Use obsidian_query_vault to find available notes."
            )

        post = frontmatter.load(file_path)

        logger.info("notes.read_completed", title=title)

        return {
            "title": title,
            "content": post.content,
            "metadata": post.metadata,
            "path": str(file_path.relative_to(self.vault_path)),
        }

    def update(
        self,
        title: str,
        content: str,
        append: bool = False,
        create_if_missing: bool = False,
    ) -> dict[str, str]:
        """Replace or append to existing note content.

        Args:
            title: Note title (without .md extension).
            content: Content to write or append.
            append: If True, append to end; if False, replace entirely.
            create_if_missing: If True, create note if it doesn't exist.

        Returns:
            Dict with update confirmation.

        Raises:
            FileNotFoundError: If note doesn't exist and create_if_missing is False.
        """
        logger.info(
            "notes.update_started", title=title, append=append, create_if_missing=create_if_missing
        )

        file_path = self._find_note_file(title)

        if not file_path:
            if create_if_missing:
                return self.create(title=title, content=content)
            raise FileNotFoundError(
                f"Note '{title}' not found. Set create_if_missing=True to create it."
            )

        # Load existing note
        post = frontmatter.load(file_path)

        if append:
            # Append content
            post.content = post.content.rstrip() + "\n\n" + content
        else:
            # Replace content
            post.content = content

        # Update modified timestamp
        post.metadata["modified"] = datetime.now(UTC).isoformat()

        # Write back
        with file_path.open("w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        logger.info("notes.update_completed", title=title, append=append)

        return {
            "title": title,
            "action": "appended" if append else "replaced",
            "path": str(file_path.relative_to(self.vault_path)),
        }

    def delete(self, title: str) -> dict[str, str]:
        """Delete a note (DESTRUCTIVE operation).

        Args:
            title: Note title (without .md extension).

        Returns:
            Dict with deletion confirmation.

        Raises:
            FileNotFoundError: If note doesn't exist.
        """
        logger.info("notes.delete_started", title=title)

        file_path = self._find_note_file(title)
        if not file_path:
            raise FileNotFoundError(f"Note '{title}' not found.")

        file_path.unlink()

        logger.info("notes.delete_completed", title=title)

        return {"title": title, "status": "deleted"}

    def get_daily_note(
        self, date: str | None = None, create_if_missing: bool = True
    ) -> dict[str, object]:
        """Get or create daily note for specified date.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today).
            create_if_missing: If True, create note if doesn't exist.

        Returns:
            Dict with daily note content and metadata.

        Raises:
            ValueError: If date format is invalid.
        """
        logger.info("notes.get_daily_note_started", date=date, create_if_missing=create_if_missing)

        # Parse or default to today
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError as e:
                raise ValueError(
                    f"Date must be YYYY-MM-DD format. You provided: '{date}'. Example: '2025-01-15'"
                ) from e
        else:
            date_obj = datetime.now(UTC)

        daily_note_title = date_obj.strftime("%Y-%m-%d")

        # Try to read existing note
        try:
            return self.read(daily_note_title)
        except FileNotFoundError:
            if not create_if_missing:
                raise

            # Create new daily note from template
            template_content = (
                f"# Daily Note - {date_obj.strftime('%B %d, %Y')}\n\n## Tasks\n\n## Notes\n\n"
            )

            self.create(
                title=daily_note_title,
                content=template_content,
                tags=["daily-note"],
            )

            logger.info("notes.get_daily_note_created", title=daily_note_title)

            return self.read(daily_note_title)

    def manage_tags(
        self,
        title: str,
        add_tags: list[str] | None = None,
        remove_tags: list[str] | None = None,
    ) -> dict[str, object]:
        """Add or remove tags from note frontmatter.

        Args:
            title: Note title (without .md extension).
            add_tags: Tags to add.
            remove_tags: Tags to remove.

        Returns:
            Dict with updated tag list.

        Raises:
            FileNotFoundError: If note doesn't exist.
        """
        logger.info(
            "notes.manage_tags_started", title=title, add_tags=add_tags, remove_tags=remove_tags
        )

        file_path = self._find_note_file(title)
        if not file_path:
            raise FileNotFoundError(f"Note '{title}' not found.")

        # Load note
        post = frontmatter.load(file_path)
        current_tags = post.metadata.get("tags", [])

        if isinstance(current_tags, str):
            current_tags = [current_tags]
        else:
            current_tags = list(current_tags)

        # Add tags
        if add_tags:
            for tag in add_tags:
                if tag not in current_tags:
                    current_tags.append(tag)

        # Remove tags
        if remove_tags:
            current_tags = [tag for tag in current_tags if tag not in remove_tags]

        # Update metadata
        post.metadata["tags"] = current_tags
        post.metadata["modified"] = datetime.now(UTC).isoformat()

        # Write back
        with file_path.open("w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        logger.info("notes.manage_tags_completed", title=title, tags=current_tags)

        return {"title": title, "tags": current_tags}

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
