"""Obsidian vault organization tool for Pydantic AI agent.

This module implements the obsidian_manage_vault tool for:
- Creating folder hierarchies
- Listing all folders
- Bulk tagging operations
- Bulk move operations
- Bulk delete operations
"""

from typing import Literal

from pydantic_ai import RunContext

from app.core.logging import get_logger
from app.features.agent import VaultDeps, vault_agent
from app.features.vault.service import VaultService

logger = get_logger(__name__)


@vault_agent.tool
async def obsidian_manage_vault(
    ctx: RunContext[VaultDeps],
    operation: Literal["create_folder", "list_folders", "bulk_tag", "bulk_move", "bulk_delete"],
    folder_path: str | None = None,
    search_query: str | None = None,
    tags: list[str] | None = None,
    folder_filter: str | None = None,
    note_titles: list[str] | None = None,
    add_tags: list[str] | None = None,
    remove_tags: list[str] | None = None,
    destination_folder: str | None = None,
    dry_run: bool = True,
    confirm_delete: bool = False,
    response_format: Literal["detailed", "concise"] = "concise",
) -> str:
    """Manage vault structure and perform bulk operations on multiple notes.

    OPERATIONS:

    "create_folder" - Create new folder hierarchy in vault
        Required: folder_path
        Example: operation="create_folder", folder_path="Projects/2025/Q1"
        Returns: Confirmation with created folder structure
        Note: Creates parent directories automatically

    "list_folders" - List all folders in vault with note counts
        Example: operation="list_folders"
        Returns: Hierarchical list of folders with note counts

    "bulk_tag" - Add or remove tags from multiple notes
        Required: add_tags OR remove_tags
        Selection (one required):
            - search_query: Content search to find notes
            - tags: Filter by existing tags
            - folder_filter: Filter by folder path
            - note_titles: Explicit list of note titles
        Example: operation="bulk_tag", folder_filter="Drafts", add_tags=["review"]
        Note: Tool internally searches for matching notes, then applies tag changes
        Always use dry_run=True first to preview affected notes

    "bulk_move" - Move multiple notes to a different folder
        Required: destination_folder
        Selection (one required): search_query, tags, folder_filter, or note_titles
        Example: operation="bulk_move", tags=["archived"], destination_folder="Archive/2024"
        Note: Tool internally finds matching notes, then moves them
        Destination folder is auto-created if it doesn't exist

    "bulk_delete" - Delete multiple notes (DESTRUCTIVE)
        Required: confirm_delete=True
        Selection (one required): search_query, tags, folder_filter, or note_titles
        Example: operation="bulk_delete", folder_filter="Temp", confirm_delete=True
        WARNING: Permanent deletion. ALWAYS use dry_run=True first to preview.

    PARAMETERS:
    - operation: Type of vault operation (required)
    - folder_path: Folder path for create_folder (e.g., "Projects/2025/Q1")
    - search_query: Content search to select notes for bulk operations
        Example: "meeting notes from January"
    - tags: Tag filter to select notes for bulk operations
        Example: ["draft", "needs-review"]
    - folder_filter: Folder path to select notes for bulk operations
        Example: "Work/Archives"
    - note_titles: Explicit list of note titles for bulk operations
        Example: ["Note 1", "Note 2", "Note 3"]
    - add_tags: Tags to add in bulk_tag operation
    - remove_tags: Tags to remove in bulk_tag operation
    - destination_folder: Target folder for bulk_move operation
    - dry_run: Preview mode (IMPORTANT - default True)
        True: Show what WOULD be affected without making changes
        False: Execute the operation
        ALWAYS call with dry_run=True first, review results, then call with False
    - confirm_delete: MUST be True for bulk_delete (safety requirement)
    - response_format: Output verbosity control
        * "concise": Count and summary (~30-50 tokens)
        * "detailed": Full list of affected files with paths (~100-300 tokens)
        Use "detailed" for dry_run previews, "concise" for execution confirmations

    BULK OPERATION WORKFLOW:
    1. Agent calls with dry_run=True to preview
    2. Tool searches internally for matching notes
    3. Tool returns: "Would affect X notes: [list]"
    4. Agent reviews the list
    5. Agent calls with dry_run=False to execute
    6. Tool applies changes and returns confirmation

    This pattern offloads the search + operate workflow from the agent to the tool,
    reducing context consumption and preventing errors.

    ERROR HANDLING:
    - No selection criteria: "Bulk operations require selection criteria. Provide one of: search_query, tags, folder_filter, or note_titles."
    - Delete without confirm: "Destructive bulk_delete requires confirm_delete=True. This will permanently delete X notes: [list]. Review carefully and call with confirm_delete=True to proceed."
    - Dry run reminder: "Operation executed with dry_run=True. No changes made. Review results and call with dry_run=False to execute."
    - No matches found: "No notes match criteria. Try different search_query, tags, or folder_filter. Available folders: [list]"
    - Partial failures: "Operation completed with errors. Successfully processed X of Y notes. Failures: [details]"
    - Destination exists: "Note 'X' already exists in destination folder. Specify conflict resolution strategy."

    RETURNS:
    - create_folder: "Created folder structure: path/to/folder"
    - list_folders: Hierarchical folder tree with note counts
    - bulk_tag (dry_run=True): "Would affect 15 notes: [list]. Call with dry_run=False to execute."
    - bulk_tag (dry_run=False): "Updated tags for 15 notes"
    - bulk_move (dry_run=True): "Would move 8 notes to 'Archive': [list]"
    - bulk_move (dry_run=False): "Moved 8 notes to 'Archive'"
    - bulk_delete (dry_run=True): "Would DELETE 5 notes: [list]. Review carefully."
    - bulk_delete (dry_run=False): "Deleted 5 notes from vault"

    Args:
        ctx: Pydantic AI run context with VaultDeps.
        operation: Type of vault operation.
        folder_path: Folder path for create_folder.
        search_query: Content search for bulk operations.
        tags: Tag filter for bulk operations.
        folder_filter: Folder filter for bulk operations.
        note_titles: Explicit note titles for bulk operations.
        add_tags: Tags to add (bulk_tag).
        remove_tags: Tags to remove (bulk_tag).
        destination_folder: Target folder (bulk_move).
        dry_run: Preview mode (default True).
        confirm_delete: Delete confirmation (required for bulk_delete).
        response_format: Output verbosity.

    Returns:
        Formatted string with operation result.

    Raises:
        ValueError: If required parameters are missing or invalid.
    """
    logger.info(
        "tool.manage_vault_started",
        operation=operation,
        dry_run=dry_run,
        response_format=response_format,
    )

    service = VaultService(ctx.deps.vault_path)

    try:
        if operation == "create_folder":
            if not folder_path:
                raise ValueError("Create_folder operation requires 'folder_path' parameter")

            result = service.create_folder(folder_path=folder_path)
            return f"Created folder structure: {result['folder_path']}"

        elif operation == "list_folders":
            folders = service.list_folders()

            if response_format == "concise":
                return _format_folders_concise(folders)  # type: ignore[arg-type]

            return _format_folders_detailed(folders)  # type: ignore[arg-type]

        elif operation == "bulk_tag":
            if not add_tags and not remove_tags:
                raise ValueError("Bulk_tag operation requires 'add_tags' or 'remove_tags'")

            if not any([search_query, tags, folder_filter, note_titles]):
                raise ValueError(
                    "Bulk operations require selection criteria. "
                    "Provide one of: search_query, tags, folder_filter, or note_titles."
                )

            result: dict[str, object] = service.bulk_tag(  # type: ignore[no-redef]
                add_tags=add_tags,
                remove_tags=remove_tags,
                search_query=search_query,
                tags=tags,
                folder_filter=folder_filter,
                note_titles=note_titles,
                dry_run=dry_run,
            )

            return _format_bulk_result("tag", result, response_format)  # type: ignore[arg-type]

        elif operation == "bulk_move":
            if not destination_folder:
                raise ValueError("Bulk_move operation requires 'destination_folder' parameter")

            if not any([search_query, tags, folder_filter, note_titles]):
                raise ValueError(
                    "Bulk operations require selection criteria. "
                    "Provide one of: search_query, tags, folder_filter, or note_titles."
                )

            result: dict[str, object] = service.bulk_move(  # type: ignore[no-redef]
                destination_folder=destination_folder,
                search_query=search_query,
                tags=tags,
                folder_filter=folder_filter,
                note_titles=note_titles,
                dry_run=dry_run,
            )

            return _format_bulk_result("move", result, response_format, destination_folder)  # type: ignore[arg-type]

        elif operation == "bulk_delete":
            if not confirm_delete:
                # Find notes to show what would be deleted
                matching_notes = service._find_matching_notes(
                    search_query=search_query,
                    tags=tags,
                    folder_filter=folder_filter,
                    note_titles=note_titles,
                )
                note_list = ", ".join([n["title"] for n in matching_notes[:5]])
                more = f" and {len(matching_notes) - 5} more" if len(matching_notes) > 5 else ""
                return (
                    f"Destructive bulk_delete requires confirm_delete=True. "
                    f"This will permanently delete {len(matching_notes)} notes: [{note_list}{more}]. "
                    f"Review carefully and call with confirm_delete=True to proceed."
                )

            if not any([search_query, tags, folder_filter, note_titles]):
                raise ValueError(
                    "Bulk operations require selection criteria. "
                    "Provide one of: search_query, tags, folder_filter, or note_titles."
                )

            result: dict[str, object] = service.bulk_delete(  # type: ignore[no-redef]
                search_query=search_query,
                tags=tags,
                folder_filter=folder_filter,
                note_titles=note_titles,
                dry_run=dry_run,
            )

            return _format_bulk_result("delete", result, response_format)  # type: ignore[arg-type]

        else:
            raise ValueError(f"Unknown operation: {operation}")

    except Exception as e:
        logger.error(
            "tool.manage_vault_failed",
            operation=operation,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise


def _format_folders_concise(folders: list[dict[str, object]]) -> str:
    """Format folder list in concise mode."""
    if not folders:
        return "No folders found in vault."

    lines = [f"Found {len(folders)} folders:"]
    for folder in folders[:20]:
        path = folder["path"]
        count = folder["note_count"]
        lines.append(f"- {path} ({count} notes)")

    if len(folders) > 20:
        lines.append(f"\n... and {len(folders) - 20} more folders")

    return "\n".join(lines)


def _format_folders_detailed(folders: list[dict[str, object]]) -> str:
    """Format folder list in detailed mode."""
    if not folders:
        return "No folders found in vault."

    lines = [f"Found {len(folders)} folders:\n"]
    for folder in folders:
        path = folder["path"]
        count = folder["note_count"]
        lines.append(f"Path: {path}")
        lines.append(f"Note count: {count}\n")

    return "\n".join(lines)


def _format_bulk_result(
    operation: str,
    result: dict[str, object],
    response_format: str,
    destination: str | None = None,
) -> str:
    """Format bulk operation result."""
    count = result["count"] if isinstance(result["count"], int) else 0
    dry_run = result.get("dry_run", False)
    affected_notes = result.get("affected_notes", [])

    if isinstance(affected_notes, list):
        note_list = [n["title"] for n in affected_notes] if affected_notes else []
    else:
        note_list = []

    if dry_run:
        if response_format == "concise":
            if operation == "delete":
                return f"Would DELETE {count} notes. Review carefully and call with dry_run=False to execute."
            if operation == "move":
                return f"Would move {count} notes to '{destination}'. Call with dry_run=False to execute."
            return f"Would affect {count} notes. Call with dry_run=False to execute."

        # Detailed preview
        notes_str = "\n".join([f"  - {title}" for title in note_list[:20]])
        more = f"\n  ... and {len(note_list) - 20} more" if len(note_list) > 20 else ""

        if operation == "delete":
            return f"Would DELETE {count} notes:\n{notes_str}{more}\n\nReview carefully and call with dry_run=False to execute."
        if operation == "move":
            return f"Would move {count} notes to '{destination}':\n{notes_str}{more}\n\nCall with dry_run=False to execute."
        return (
            f"Would affect {count} notes:\n{notes_str}{more}\n\nCall with dry_run=False to execute."
        )

    # Execution results
    if response_format == "concise":
        if operation == "delete":
            return f"Deleted {count} notes from vault"
        if operation == "move":
            return f"Moved {count} notes to '{destination}'"
        if operation == "tag":
            return f"Updated tags for {count} notes"
        return f"Operation completed. Affected {count} notes."

    # Detailed execution results
    notes_str = "\n".join([f"  - {title}" for title in note_list[:20]])
    more = f"\n  ... and {len(note_list) - 20} more" if len(note_list) > 20 else ""

    if operation == "delete":
        return f"Deleted {count} notes from vault:\n{notes_str}{more}"
    if operation == "move":
        return f"Moved {count} notes to '{destination}':\n{notes_str}{more}"
    if operation == "tag":
        return f"Updated tags for {count} notes:\n{notes_str}{more}"
    return f"Operation completed. Affected {count} notes:\n{notes_str}{more}"
