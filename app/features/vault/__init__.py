"""Vault feature for organizing vault structure and bulk operations."""

from app.features.vault.service import VaultService
from app.features.vault.tool import obsidian_manage_vault

__all__ = ["VaultService", "obsidian_manage_vault"]
