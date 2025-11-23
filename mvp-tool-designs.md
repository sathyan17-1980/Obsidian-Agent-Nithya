# MVP Tool Designs - Obsidian AI Agent

## Overview

This document defines the 3 core tools for the Obsidian AI Agent MVP, designed following Anthropic's best practices for agent tool design.

**Design Principles:**
- **Consolidation over fragmentation** - Group frequently-chained operations
- **Token efficiency** - `response_format` parameter for context optimization
- **Instructive errors** - Error messages teach agents better strategies
- **Semantic clarity** - Clear naming, explicit parameters, comprehensive descriptions
- **Offload computation** - Tools handle multi-step workflows internally

---

## Tool 1: `obsidian_query_vault`

### Purpose
Discovery and access - helps users FIND information in their vault.

### Operations
- `search` - Full-text search with optional filters
- `list` - List notes by folder or tag
- `find_related` - Discover notes connected via backlinks and shared tags

### Function Signature

```python
@vault_agent.tool
async def obsidian_query_vault(
    ctx: RunContext[VaultDeps],
    operation: Literal["search", "list", "find_related"],
    query: str | None = None,
    tags: list[str] | None = None,
    folder: str | None = None,
    limit: int = 10,
    response_format: Literal["detailed", "concise"] = "concise"
) -> str:
    """
    Query and discover content in your Obsidian vault.

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
    - Concise mode: "Found X notes:\n1. [Title]: snippet...\n2. [Title]: snippet..."
    - Detailed mode: Full metadata including paths, tags, created/modified dates
    - Truncation notice: "Showing 10 of 45 results. Refine with: tags=['specific'], folder='path'"
    """
```

### Key Design Decisions

**Why consolidate search, list, and find_related?**
- All are read-only discovery operations
- Frequently chained in workflows: search → find_related
- Share common parameters (tags, folder, limit)
- Eliminates agent decision paralysis ("which search tool?")

**Why NOT include `get_daily_note`?**
- Daily notes can CREATE if missing (write operation)
- Belongs with other note modification operations
- Maintains clean read vs write separation

**Parameter overloading (query)?**
- `query` means different things per operation (search text vs note title)
- ACCEPTABLE because description clearly documents each usage
- Anthropic principle: Great documentation enables parameter flexibility

---

## Tool 2: `obsidian_manage_notes`

### Purpose
Individual note operations - CRUD and metadata management for specific notes.

### Operations
- `create` - Create new note with optional frontmatter
- `read` - Read note content
- `update` - Replace or append to note content
- `delete` - Delete a note (requires confirmation)
- `get_daily_note` - Get or create daily note for specified date
- `manage_tags` - Add or remove tags from note frontmatter

### Function Signature

```python
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
    response_format: Literal["detailed", "concise"] = "concise"
) -> str:
    """
    Manage individual notes in your Obsidian vault.

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
    """
```

### Key Design Decisions

**Why include get_daily_note here (not in query_vault)?**
- Can CREATE notes (write operation, not pure read)
- Frequently chained: get_daily_note → update → manage_tags
- All operations in this chain are in manage_notes
- Idempotent "ensure exists" pattern fits with CRUD operations

**Why auto-create folder structure?**
- Research shows folder operations are low-frequency
- Most users prefer tags over complex folder hierarchies
- Auto-creation handles 80% of folder needs without dedicated tool
- Simplifies API (don't need separate create_folder operation in MVP)

**Why separate manage_tags from update?**
- Tags are YAML frontmatter (structured metadata)
- Updates are markdown content (unstructured)
- Different error patterns (tag validation vs content validation)
- Common standalone operation: "tag all meeting notes"

**Safety patterns:**
- Delete requires `confirm_delete=True` (fail-safe default)
- Update has `create_if_missing=False` default (explicit intent required)
- Instructive errors teach correct usage

---

## Tool 3: `obsidian_manage_vault`

### Purpose
Vault organization - folder structure and bulk operations on multiple notes.

### Operations
- `create_folder` - Create folder hierarchy
- `list_folders` - List all folders in vault
- `bulk_tag` - Add/remove tags from multiple notes
- `bulk_move` - Move multiple notes to different folder
- `bulk_delete` - Delete multiple notes (requires confirmation)

### Function Signature

```python
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
    response_format: Literal["detailed", "concise"] = "concise"
) -> str:
    """
    Manage vault structure and perform bulk operations on multiple notes.

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
    """
```

### Key Design Decisions

**Why include both folder operations AND bulk operations?**
- Frequently chained: create_folder → bulk_move to new folder
- Both modify vault STRUCTURE (not content)
- Semantic grouping: "vault organization" vs "note manipulation"
- Research shows folders + bulk ops are conceptually linked for users

**Why include internal search in bulk operations?**
- **Anthropic principle**: Offload multi-step workflows to tools
- Prevents wasted context on intermediate results
- Agent doesn't orchestrate: search → parse → bulk operate
- Tool handles atomically: search + operate in one call
- Reduces errors and token consumption

**Why dry_run defaults to True?**
- **Safety by default** - prevents accidental bulk operations
- **Preview pattern** - agent reviews before executing
- Forces intentional execution (dry_run=False)
- Instructive errors teach correct workflow

**Why allow multiple selection methods?**
- Flexibility: search_query (fuzzy), tags (precise), folder_filter (location), note_titles (explicit)
- Different workflows need different selection strategies
- Tool internally handles all selection types uniformly
- Agent chooses most appropriate for context

**Error handling philosophy:**
- Partial failures don't abort entire operation (report which succeeded/failed)
- Always suggest next steps or alternatives
- Teach the dry_run → review → execute pattern
- Destructive operations have multiple safety checks

---

## Cross-Tool Patterns

### Response Format Strategy

**When to use "concise":**
- Displaying results to user
- Simple confirmations
- Token optimization priority
- No follow-up tool calls needed

**When to use "detailed":**
- Chaining to another tool call
- Need file paths or IDs for references
- Verification before destructive operations
- Debugging or detailed analysis

**Token impact:**
- Concise: ~30-70 tokens per item
- Detailed: ~150-250 tokens per item
- 3-5x difference in context consumption

### Common Workflows

**Research Session:**
```
obsidian_query_vault(operation="search", query="FastAPI", response_format="concise")
→ Review results
→ obsidian_query_vault(operation="find_related", query="FastAPI Guide", response_format="detailed")
→ obsidian_manage_notes(operation="read", title="API Design Doc")
→ obsidian_manage_notes(operation="create", title="FastAPI Summary", content="...")
```

**Daily Review:**
```
obsidian_manage_notes(operation="get_daily_note", date="2025-01-15")
→ obsidian_query_vault(operation="search", query="TODO", tags=["urgent"])
→ obsidian_manage_notes(operation="update", title="2025-01-15", content="tasks", append=True)
```

**Vault Cleanup:**
```
obsidian_manage_vault(operation="bulk_tag", folder_filter="Drafts", add_tags=["review"], dry_run=True)
→ Review preview
→ obsidian_manage_vault(operation="bulk_tag", folder_filter="Drafts", add_tags=["review"], dry_run=False)
→ obsidian_manage_vault(operation="create_folder", folder_path="Archive/2024")
→ obsidian_manage_vault(operation="bulk_move", tags=["archived"], destination_folder="Archive/2024", dry_run=True)
→ Review preview
→ obsidian_manage_vault(operation="bulk_move", tags=["archived"], destination_folder="Archive/2024", dry_run=False)
```

---

## Implementation Notes

### Shared Components

**VaultDeps (Dependency Injection):**
```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class VaultDeps:
    vault_path: Path
```

**Agent Configuration:**
```python
from pydantic_ai import Agent

vault_agent = Agent(
    'anthropic:claude-sonnet-4-0',
    deps_type=VaultDeps,
    instructions="""You are an AI assistant that helps users manage their Obsidian vault.

You can:
- Search and discover notes (obsidian_query_vault)
- Create, read, update notes (obsidian_manage_notes)
- Organize vault with folders and bulk operations (obsidian_manage_vault)

Always use response_format="concise" unless you need detailed metadata for follow-up operations.
For bulk operations, ALWAYS preview with dry_run=True before executing.
Be helpful and concise. Confirm destructive actions before proceeding."""
)
```

### Service Layer Structure

```
app/features/
├── search/
│   ├── tool.py          # obsidian_query_vault tool definition
│   └── service.py       # SearchService (obsidiantools integration)
├── notes/
│   ├── tool.py          # obsidian_manage_notes tool definition
│   └── service.py       # NoteService (CRUD operations)
└── vault/
    ├── tool.py          # obsidian_manage_vault tool definition
    └── service.py       # VaultService (folder + bulk operations)
```

### Testing Strategy

**Unit Tests:**
- Each operation independently
- Parameter validation
- Error message content
- Response format differences

**Integration Tests:**
- Multi-tool workflows
- Dry-run → execute patterns
- Token consumption measurements
- Error recovery scenarios

**Evaluation Tests:**
- Real user queries mapped to tool calls
- Success rate per operation
- Token efficiency benchmarks
- Error clarity assessments

---

## Success Metrics

### Functional Requirements
- ✅ All 3 tools implemented with all operations
- ✅ Comprehensive error handling with instructive messages
- ✅ Response format impacts token usage as expected (3-5x difference)
- ✅ Dry-run pattern prevents accidental destructive operations
- ✅ Auto-folder creation works seamlessly

### Performance Requirements
- ✅ Single note operations: <100ms
- ✅ Search on 1,000 notes: <1s
- ✅ Bulk operations preview: <2s
- ✅ Response format token difference: 3-5x measured

### User Experience Requirements
- ✅ Natural language queries map to correct tools
- ✅ Agent chooses appropriate response_format
- ✅ Error messages teach correct usage
- ✅ No false positives on destructive operations
- ✅ Workflows complete with minimal tool calls

---

## Phase 2 Additions (Future)

**Potential new operations:**
- `obsidian_query_vault`: Add `semantic_search` (vector similarity)
- `obsidian_manage_notes`: Add `apply_template`, `create_from_template`
- `obsidian_manage_vault`: Add `generate_moc`, `find_orphans`, `check_broken_links`
- New tool: `obsidian_manage_tasks` (parse TODO items, track completion)

**Enhancement opportunities:**
- Streaming responses for long operations
- Progress callbacks for bulk operations
- Rollback/undo for bulk operations
- Conflict resolution strategies for bulk_move
- Custom template support for daily notes
- Graph analytics and visualization data

---

## References

- **Anthropic Tool Design Guide**: https://www.anthropic.com/engineering/writing-tools-for-agents
- **Pydantic AI Documentation**: https://ai.pydantic.dev/
- **Obsidian API Research**: See `MCP-Obsidian-Server-Analysis.md`
- **User Workflows Research**: See `Obsidian-Vault-Operations-AI-Agent-Research.md`
- **FastAPI Integration Patterns**: See `FastAPI-AI-Agent-Integration-Patterns.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-01-23
**Status**: Ready for Implementation
