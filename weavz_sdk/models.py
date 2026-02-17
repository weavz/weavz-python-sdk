"""Weavz SDK — Pydantic models for API responses."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class WorkspaceIntegration(BaseModel):
    """A workspace integration instance."""

    id: str
    workspace_id: str = Field(alias="workspaceId")
    integration_name: str = Field(alias="integrationName")
    alias: str = Field(alias="alias")
    connection_strategy: str = Field(alias="connectionStrategy")
    connection_id: Optional[str] = Field(default=None, alias="connectionId")
    display_name: Optional[str] = Field(default=None, alias="displayName")
    enabled_actions: Optional[list[str]] = Field(default=None, alias="enabledActions")
    sort_order: int = Field(default=0, alias="sortOrder")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    connection_status: Optional[str] = Field(default=None, alias="connectionStatus")
    connection_display_name: Optional[str] = Field(
        default=None, alias="connectionDisplayName"
    )

    model_config = {"populate_by_name": True}


class InputPartial(BaseModel):
    """An input partial — reusable pre-filled input values for integration actions."""

    id: str
    org_id: str = Field(alias="orgId")
    workspace_id: str = Field(alias="workspaceId")
    integration_name: str = Field(alias="integrationName")
    action_name: Optional[str] = Field(default=None, alias="actionName")
    name: str
    description: Optional[str] = None
    values: dict[str, Any] = Field(default_factory=dict)
    enforced_keys: list[str] = Field(default_factory=list, alias="enforcedKeys")
    is_default: bool = Field(default=False, alias="isDefault")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}
