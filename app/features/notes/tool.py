"""Obsidian note management tool for Pydantic AI agent.

This module implements the obsidian_manage_notes tool for:
- Creating notes with frontmatter
- Reading note content
- Updating (replacing or appending) content
- Deleting notes
- Getting/creating daily notes
- Managing note tags
"""

from typing import Literal

from pydantic_ai import RunContext

from app.core.logging import get_logger
from app.features.agent import VaultDeps, vault_agent
from app.features.notes.service import NoteService

logger = get_logger(__name__)


@vault_agent.tool
async def obsidian_manage_notes(
    ctx: RunContext[VaultDeps],
    operation: Literal["create", "read", "update", "delete", "get_daily_note", "manage_tags"],
    title: str,
    content: str | None = None,
    folder: str | None = None,
    tags: list[str] | None = None,
    add_tags: list[str] | None = None,
    remove_tags: list[str] | None = None,
    append: bool = False,
    date: str | None = None,
    create_if_missing: bool = False,
    confirm_delete: bool = False,
    response_format: Literal["detailed", "concise"] = "concise",
) -> str:
    """Manage individual notes in your Obsidian vault.

    OPERATIONS:

    "create" - Create a new note with optional frontmatter and folder placement
        Required: title, content
        Optional: folder (auto-creates if doesn't exist), tags (added to frontmatter)
        Example: operation="create", title="Meeting Notes", content="...", tags=["meeting"]
        Returns: Confirmation with file path and metadata
        Note: Automatically creates folder structure if folder doesn't exist

    "read" - Read the full content of a specific note
        Required: title
        Example: operation="read", title="Project Plan"
        Returns: Full note content including frontmatter

    "update" - Replace or append to existing note content
        Required: title, content
        Optional: append (True=append to end, False=replace entirely)
        Optional: create_if_missing (True=create if doesn't exist)
        Example: operation="update", title="Todo", content="- New task", append=True
        Returns: Confirmation with updated content preview

    "delete" - Delete a note (DESTRUCTIVE - requires confirmation)
        Required: title, confirm_delete=True
        Example: operation="delete", title="Old Draft", confirm_delete=True
        Returns: Confirmation of deletion
        Error if confirm_delete=False: Instructive message explaining requirement

    "get_daily_note" - Get or create daily note for specified date
        Optional: date (YYYY-MM-DD format, defaults to today)
        Optional: create_if_missing (default True)
        Example: operation="get_daily_note", date="2025-01-15"
        Returns: Daily note content (creates from template if missing)
        Note: Uses standard daily note naming convention (YYYY-MM-DD.md)

    "manage_tags" - Add or remove tags from note frontmatter
        Required: title
        Optional: add_tags (tags to add), remove_tags (tags to remove)
        Example: operation="manage_tags", title="Blog Post", add_tags=["published"]
        Returns: Confirmation with updated tag list

    PARAMETERS:
    - operation: Type of note operation (required)
    - title: Note title without .md extension (required for all operations)
    - content: Note content in markdown (required for create/update)
    - folder: Folder path for new notes (e.g., "Work/Projects")
        Automatically creates folder hierarchy if it doesn't exist
    - tags: Tags for new notes (create operation) - added to YAML frontmatter
    - add_tags: Tags to add (manage_tags operation)
    - remove_tags: Tags to remove (manage_tags operation)
    - append: Append vs replace content (update operation)
        True: Append content to end of note
        False: Replace entire note content
    - date: Date for daily notes in YYYY-MM-DD format (get_daily_note operation)
    - create_if_missing: Auto-create note if doesn't exist (update/get_daily_note)
    - confirm_delete: MUST be True for delete operations (safety requirement)
    - response_format: Output verbosity control
        * "concise": Confirmation message only (~20-50 tokens)
        * "detailed": Full note metadata, frontmatter, content preview (~150-250 tokens)
        Use "concise" for simple confirmations, "detailed" for verification/chaining

    ERROR HANDLING:
    - Note not found: "Note 'X' not found. Available notes in folder: [list]. Did you mean: [suggestions]"
    - Delete without confirm: "Destructive operation requires confirm_delete=True. This will permanently delete 'X'. Call again with confirm_delete=True to proceed."
    - Invalid date format: "Date must be YYYY-MM-DD format. You provided: 'X'. Example: '2025-01-15'"
    - Folder creation failure: Details parent directory permissions/issues
    - Tag already exists: "Note already has tag 'X'. Current tags: [list]"

    RETURNS:
    - create: "Created note 'X' at path/to/note.md [detailed: + frontmatter]"
    - read: Full note content with frontmatter
    - update: "Updated note 'X' [detailed: + content preview]"
    - delete: "Deleted note 'X' from vault"
    - get_daily_note: Daily note content (creates if missing with template)
    - manage_tags: "Updated tags for 'X'. Tags: [list]"

    Args:
        ctx: Pydantic AI run context with VaultDeps.
        operation: Type of note operation.
        title: Note title (without .md extension).
        content: Note content (for create/update).
        folder: Folder path for new notes.
        tags: Tags for new notes.
        add_tags: Tags to add (manage_tags).
        remove_tags: Tags to remove (manage_tags).
        append: Append vs replace (update).
        date: Date for daily notes (YYYY-MM-DD).
        create_if_missing: Auto-create if doesn't exist.
        confirm_delete: Delete confirmation (required for delete).
        response_format: Output verbosity.

    Returns:
        Formatted string with operation result.

    Raises:
        ValueError: If required parameters are missing or invalid.
        FileNotFoundError: If note doesn't exist (when required).
        FileExistsError: If note already exists (create).
    """
    logger.info(
        "tool.manage_notes_started",
        operation=operation,
        title=title,
        response_format=response_format,
    )

    service = NoteService(ctx.deps.vault_path)

    try:
        if operation == "create":
            if not content:
                raise ValueError("Create operation requires 'content' parameter")

            result = service.create(title=title, content=content, folder=folder, tags=tags)

            if response_format == "concise":
                return f"Created note '{title}' at {result['path']}"

            return f"Created note '{title}'\nPath: {result['path']}\nTags: {result['tags']}"

        elif operation == "read":
            result: dict[str, object] = service.read(title=title)  # type: ignore[assignment]

            if response_format == "concise":
                return f"# {title}\n\n{result['content']}"

            metadata_str = (
                "\n".join(f"{k}: {v}" for k, v in result["metadata"].items())
                if isinstance(result["metadata"], dict)
                else ""
            )
            return (
                f"# {title}\n"
                f"Path: {result['path']}\n"
                f"Metadata:\n{metadata_str}\n\n"
                f"Content:\n{result['content']}"
            )

        elif operation == "update":
            if not content:
                raise ValueError("Update operation requires 'content' parameter")

            result = service.update(
                title=title,
                content=content,
                append=append,
                create_if_missing=create_if_missing,
            )

            action = result["action"]
            if response_format == "concise":
                return f"Updated note '{title}' ({action})"

            return f"Updated note '{title}'\nAction: {action}\nPath: {result['path']}"

        elif operation == "delete":
            if not confirm_delete:
                return (
                    f"Destructive operation requires confirm_delete=True. "
                    f"This will permanently delete '{title}'. "
                    f"Call again with confirm_delete=True to proceed."
                )

            result = service.delete(title=title)  # type: ignore[assignment]
            return f"Deleted note '{title}' from vault"

        elif operation == "get_daily_note":
            result: dict[str, object] = service.get_daily_note(
                date=date, create_if_missing=create_if_missing
            )

            note_title = (
                result["title"] if isinstance(result, dict) and "title" in result else title
            )
            note_content = (
                result["content"] if isinstance(result, dict) and "content" in result else ""
            )

            if response_format == "concise":
                return f"# {note_title}\n\n{note_content}"

            metadata_str = ""
            if isinstance(result, dict) and "metadata" in result:
                metadata = result["metadata"]
                if isinstance(metadata, dict):
                    metadata_str = "\n".join(f"{k}: {v}" for k, v in metadata.items())

            return f"# {note_title}\nMetadata:\n{metadata_str}\n\nContent:\n{note_content}"  # type: ignore[assignment]

        elif operation == "manage_tags":
            if not add_tags and not remove_tags:
                raise ValueError("Manage_tags operation requires 'add_tags' or 'remove_tags'")

            result: dict[str, object] = service.manage_tags(
                title=title, add_tags=add_tags, remove_tags=remove_tags
            )

            tags_list = result["tags"]
            tags_str = ", ".join(tags_list) if tags_list else "(no tags)"

            if response_format == "concise":
                return f"Updated tags for '{title}'. Tags: [{tags_str}]"

            return f"Updated tags for note '{title}'\nCurrent tags: [{tags_str}]"

        else:
            raise ValueError(f"Unknown operation: {operation}")

    except Exception as e:
        logger.error(
            "tool.manage_notes_failed",
            operation=operation,
            title=title,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise
