"""Pydantic AI agent configuration for Obsidian vault operations.

This module defines:
- VaultDeps: Dependency injection container for vault path
- vault_agent: Configured Pydantic AI agent with all tools
"""

from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent

from app.core.config import get_settings


@dataclass
class VaultDeps:
    """Dependency injection container for vault operations.

    Attributes:
        vault_path: Path to the Obsidian vault directory.
    """

    vault_path: Path


# Create the Pydantic AI agent
vault_agent = Agent(
    "anthropic:claude-sonnet-4-0",
    deps_type=VaultDeps,
    system_prompt="""You are an AI assistant that helps users manage their Obsidian vault.

You can:
- Search and discover notes (obsidian_query_vault)
- Create, read, update notes (obsidian_manage_notes)
- Organize vault with folders and bulk operations (obsidian_manage_vault)

Always use response_format="concise" unless you need detailed metadata for follow-up operations.
For bulk operations, ALWAYS preview with dry_run=True before executing.
Be helpful and concise. Confirm destructive actions before proceeding.""",
)


def get_vault_deps() -> VaultDeps:
    """Create VaultDeps instance from application settings.

    Returns:
        VaultDeps instance with configured vault path.

    Raises:
        ValueError: If vault_path is not configured or doesn't exist.
    """
    settings = get_settings()
    vault_path = Path(settings.vault_path).expanduser().resolve()

    if not vault_path.exists():
        raise ValueError(
            f"Vault path does not exist: {vault_path}. "
            f"Please set VAULT_PATH in your .env file to a valid Obsidian vault directory."
        )

    if not vault_path.is_dir():
        raise ValueError(
            f"Vault path is not a directory: {vault_path}. "
            f"Please set VAULT_PATH to a valid directory."
        )

    return VaultDeps(vault_path=vault_path)
