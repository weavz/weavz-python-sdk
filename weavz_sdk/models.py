"""Weavz SDK — Pydantic models for API responses."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProjectIntegration(BaseModel):
    """A project integration instance."""

    id: str
    project_id: str = Field(alias="projectId")
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
