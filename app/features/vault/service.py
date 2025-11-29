"""Vault organization service for folder structure and bulk operations.

This module implements the business logic for:
- Creating folder hierarchies
- Listing all folders
- Bulk tagging operations
- Bulk move operations
- Bulk delete operations
"""

import shutil
from datetime import UTC, datetime
from pathlib import Path

import frontmatter

from app.core.logging import get_logger

logger = get_logger(__name__)


class VaultService:
    """Service for managing vault structure and bulk operations."""

    def __init__(self, vault_path: Path) -> None:
        """Initialize the vault service.

        Args:
            vault_path: Path to the Obsidian vault directory.
        """
        self.vault_path = vault_path

    def create_folder(self, folder_path: str) -> dict[str, str]:
        """Create new folder hierarchy in vault.

        Args:
            folder_path: Folder path to create (e.g., "Projects/2025/Q1").

        Returns:
            Dict with created folder details.
        """
        logger.info("vault.create_folder_started", folder_path=folder_path)

        full_path = self.vault_path / folder_path
        full_path.mkdir(parents=True, exist_ok=True)

        logger.info("vault.create_folder_completed", folder_path=folder_path)

        return {"folder_path": folder_path, "status": "created"}

    def list_folders(self) -> list[dict[str, object]]:
        """List all folders in vault with note counts.

        Returns:
            List of folders with metadata.
        """
        logger.info("vault.list_folders_started")

        folders = []

        for item in self.vault_path.rglob("*"):
            if item.is_dir() and not item.name.startswith("."):
                note_count = len(list(item.glob("*.md")))
                folders.append(
                    {
                        "path": str(item.relative_to(self.vault_path)),
                        "note_count": note_count,
                    }
                )

        logger.info("vault.list_folders_completed", folder_count=len(folders))

        return folders

    def bulk_tag(
        self,
        add_tags: list[str] | None = None,
        remove_tags: list[str] | None = None,
        search_query: str | None = None,
        tags: list[str] | None = None,
        folder_filter: str | None = None,
        note_titles: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict[str, object]:
        """Add or remove tags from multiple notes.

        Args:
            add_tags: Tags to add.
            remove_tags: Tags to remove.
            search_query: Content search to find notes.
            tags: Filter by existing tags.
            folder_filter: Filter by folder path.
            note_titles: Explicit list of note titles.
            dry_run: If True, preview without making changes.

        Returns:
            Dict with affected notes and count.
        """
        logger.info(
            "vault.bulk_tag_started",
            add_tags=add_tags,
            remove_tags=remove_tags,
            dry_run=dry_run,
        )

        # Find matching notes
        matching_notes = self._find_matching_notes(
            search_query=search_query,
            tags=tags,
            folder_filter=folder_filter,
            note_titles=note_titles,
        )

        if dry_run:
            logger.info("vault.bulk_tag_dry_run", affected_count=len(matching_notes))
            return {"affected_notes": matching_notes, "count": len(matching_notes), "dry_run": True}

        # Apply tag changes
        updated_notes = []
        for note in matching_notes:
            try:
                file_path = self.vault_path / note["path"]
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

                updated_notes.append(note)

            except Exception as e:
                logger.error(
                    "vault.bulk_tag_file_failed",
                    file=note["path"],
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

        logger.info("vault.bulk_tag_completed", updated_count=len(updated_notes))

        return {"affected_notes": updated_notes, "count": len(updated_notes), "dry_run": False}

    def bulk_move(
        self,
        destination_folder: str,
        search_query: str | None = None,
        tags: list[str] | None = None,
        folder_filter: str | None = None,
        note_titles: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict[str, object]:
        """Move multiple notes to a different folder.

        Args:
            destination_folder: Target folder path.
            search_query: Content search to find notes.
            tags: Filter by existing tags.
            folder_filter: Filter by folder path.
            note_titles: Explicit list of note titles.
            dry_run: If True, preview without making changes.

        Returns:
            Dict with affected notes and count.
        """
        logger.info(
            "vault.bulk_move_started",
            destination_folder=destination_folder,
            dry_run=dry_run,
        )

        # Find matching notes
        matching_notes = self._find_matching_notes(
            search_query=search_query,
            tags=tags,
            folder_filter=folder_filter,
            note_titles=note_titles,
        )

        if dry_run:
            logger.info("vault.bulk_move_dry_run", affected_count=len(matching_notes))
            return {
                "affected_notes": matching_notes,
                "count": len(matching_notes),
                "destination": destination_folder,
                "dry_run": True,
            }

        # Create destination folder
        dest_path = self.vault_path / destination_folder
        dest_path.mkdir(parents=True, exist_ok=True)

        # Move files
        moved_notes = []
        for note in matching_notes:
            try:
                src_path = self.vault_path / note["path"]
                dst_path = dest_path / src_path.name

                # Check for conflicts
                if dst_path.exists():
                    logger.warning(
                        "vault.bulk_move_conflict",
                        note=note["title"],
                        destination=str(dst_path),
                    )
                    continue

                shutil.move(str(src_path), str(dst_path))
                moved_notes.append(note)

            except Exception as e:
                logger.error(
                    "vault.bulk_move_file_failed",
                    file=note["path"],
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

        logger.info("vault.bulk_move_completed", moved_count=len(moved_notes))

        return {
            "affected_notes": moved_notes,
            "count": len(moved_notes),
            "destination": destination_folder,
            "dry_run": False,
        }

    def bulk_delete(
        self,
        search_query: str | None = None,
        tags: list[str] | None = None,
        folder_filter: str | None = None,
        note_titles: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict[str, object]:
        """Delete multiple notes (DESTRUCTIVE operation).

        Args:
            search_query: Content search to find notes.
            tags: Filter by existing tags.
            folder_filter: Filter by folder path.
            note_titles: Explicit list of note titles.
            dry_run: If True, preview without making changes.

        Returns:
            Dict with affected notes and count.
        """
        logger.info("vault.bulk_delete_started", dry_run=dry_run)

        # Find matching notes
        matching_notes = self._find_matching_notes(
            search_query=search_query,
            tags=tags,
            folder_filter=folder_filter,
            note_titles=note_titles,
        )

        if dry_run:
            logger.info("vault.bulk_delete_dry_run", affected_count=len(matching_notes))
            return {"affected_notes": matching_notes, "count": len(matching_notes), "dry_run": True}

        # Delete files
        deleted_notes = []
        for note in matching_notes:
            try:
                file_path = self.vault_path / note["path"]
                file_path.unlink()
                deleted_notes.append(note)

            except Exception as e:
                logger.error(
                    "vault.bulk_delete_file_failed",
                    file=note["path"],
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

        logger.info("vault.bulk_delete_completed", deleted_count=len(deleted_notes))

        return {"affected_notes": deleted_notes, "count": len(deleted_notes), "dry_run": False}

    def _find_matching_notes(
        self,
        search_query: str | None = None,
        tags: list[str] | None = None,
        folder_filter: str | None = None,
        note_titles: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Find notes matching selection criteria.

        Args:
            search_query: Content search.
            tags: Tag filter.
            folder_filter: Folder path filter.
            note_titles: Explicit note titles.

        Returns:
            List of matching notes.
        """
        matching_notes = []

        # Use explicit titles if provided
        if note_titles:
            for title in note_titles:
                for md_file in self.vault_path.rglob("*.md"):
                    if md_file.stem == title:
                        matching_notes.append(
                            {
                                "title": title,
                                "path": str(md_file.relative_to(self.vault_path)),
                            }
                        )
            return matching_notes

        # Otherwise search by criteria
        search_path = self.vault_path / folder_filter if folder_filter else self.vault_path

        if not search_path.exists():
            return []

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

                # Check search query
                if search_query and search_query.lower() not in content.lower():
                    continue

                matching_notes.append(
                    {
                        "title": md_file.stem,
                        "path": str(md_file.relative_to(self.vault_path)),
                    }
                )

            except Exception as e:
                logger.error(
                    "vault.find_matching_notes_failed",
                    file=str(md_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

        return matching_notes
