"""Weavz SDK — Pydantic models for API responses."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

AdvancedCodeSandboxPersistence = Literal["ephemeral", "persistent"]
AdvancedCodeStorageMountScope = Literal["none", "end_user", "workspace", "external"]
PersistenceScope = Literal["end_user", "workspace", "external"]


class AdvancedCodeSettings(BaseModel):
    """Owner-controlled Advanced Code sandbox policy for a workspace integration."""

    timeout_seconds: int = Field(default=30, alias="timeoutSeconds")
    sandbox_persistence: AdvancedCodeSandboxPersistence = Field(
        default="ephemeral", alias="sandboxPersistence"
    )
    storage_mount_scope: AdvancedCodeStorageMountScope = Field(
        default="none", alias="storageMountScope"
    )
    storage_external_id: Optional[str] = Field(default=None, alias="storageExternalId")

    model_config = {"populate_by_name": True}


class PersistenceSettings(BaseModel):
    """Owner-controlled state scope for a stateful built-in workspace integration."""

    scope: PersistenceScope = "end_user"
    external_id: Optional[str] = Field(default=None, alias="externalId")

    model_config = {"populate_by_name": True}


class WorkspaceIntegrationSettings(BaseModel):
    """Owner-controlled settings for a workspace integration instance."""

    advanced_code: Optional[AdvancedCodeSettings] = Field(
        default=None, alias="advancedCode"
    )
    persistence: Optional[PersistenceSettings] = None

    model_config = {"populate_by_name": True}


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
    settings: WorkspaceIntegrationSettings = Field(
        default_factory=WorkspaceIntegrationSettings
    )
    sort_order: int = Field(default=0, alias="sortOrder")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    connection_status: Optional[str] = Field(default=None, alias="connectionStatus")
    connection_display_name: Optional[str] = Field(
        default=None, alias="connectionDisplayName"
    )

    model_config = {"populate_by_name": True}


class InputPartial(BaseModel):
    """An input partial — reusable pre-filled input values for actions or triggers."""

    id: str
    org_id: str = Field(alias="orgId")
    workspace_id: str = Field(alias="workspaceId")
    integration_name: str = Field(alias="integrationName")
    workspace_integration_id: Optional[str] = Field(default=None, alias="workspaceIntegrationId")
    integration_alias: Optional[str] = Field(default=None, alias="integrationAlias")
    action_name: Optional[str] = Field(default=None, alias="actionName")
    trigger_name: Optional[str] = Field(default=None, alias="triggerName")
    name: str
    description: Optional[str] = None
    values: dict[str, Any] = Field(default_factory=dict)
    enforced_keys: list[str] = Field(default_factory=list, alias="enforcedKeys")
    is_default: bool = Field(default=False, alias="isDefault")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class ApprovalCodeRunToolPlanItem(BaseModel):
    """A predicted or policy-gated Code Mode tool call."""

    integration_name: str = Field(alias="integrationName")
    integration_alias: str = Field(alias="integrationAlias")
    action_name: str = Field(alias="actionName")
    namespace: str
    matched: bool
    approval_policy_id: Optional[str] = Field(default=None, alias="approvalPolicyId")
    approval_policy_name: Optional[str] = Field(default=None, alias="approvalPolicyName")
    approval_access_mode: Optional[str] = Field(default=None, alias="approvalAccessMode")

    model_config = {"populate_by_name": True}


class ApprovalCodeRunGroup(BaseModel):
    """A Code Mode approval decision group keyed by policy."""

    approval_policy_id: str = Field(alias="approvalPolicyId")
    approval_policy_name: str = Field(alias="approvalPolicyName")
    approval_access_mode: str = Field(alias="approvalAccessMode")
    tools: list[ApprovalCodeRunToolPlanItem] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ApprovalCodeRunPreview(BaseModel):
    """Structured redacted reviewer context for MCP Code Mode approvals."""

    type: str
    code_run_id: Optional[str] = Field(default=None, alias="codeRunId")
    server_id: Optional[str] = Field(default=None, alias="serverId")
    server_name: Optional[str] = Field(default=None, alias="serverName")
    workspace_id: Optional[str] = Field(default=None, alias="workspaceId")
    code: Optional[str] = None
    code_hash: Optional[str] = Field(default=None, alias="codeHash")
    tool_surface_hash: Optional[str] = Field(default=None, alias="toolSurfaceHash")
    intent_summary: Optional[str] = Field(default=None, alias="intentSummary")
    impact_summary: list[str] = Field(default_factory=list, alias="impactSummary")
    predicted_tools: list[ApprovalCodeRunToolPlanItem] = Field(default_factory=list, alias="predictedTools")
    approval_required_tools: list[ApprovalCodeRunToolPlanItem] = Field(default_factory=list, alias="approvalRequiredTools")
    approval_groups: list[ApprovalCodeRunGroup] = Field(default_factory=list, alias="approvalGroups")
    available_apps: list[dict[str, Any]] = Field(default_factory=list, alias="availableApps")
    external_domains: list[str] = Field(default_factory=list, alias="externalDomains")
    storage_indicators: list[str] = Field(default_factory=list, alias="storageIndicators")
    analysis_confidence: Optional[str] = Field(default=None, alias="analysisConfidence")
    dynamic_signals: list[str] = Field(default_factory=list, alias="dynamicSignals")
    limitations: list[str] = Field(default_factory=list)
    triggered_action: Optional[dict[str, Any]] = Field(default=None, alias="triggeredAction")

    model_config = {"populate_by_name": True}


class ApprovalWebhookApiUrls(BaseModel):
    """Authenticated API endpoints included in approval webhook payloads."""

    detail_url: str = Field(alias="detailUrl")
    approve_url: str = Field(alias="approveUrl")
    reject_url: str = Field(alias="rejectUrl")
    cancel_url: str = Field(alias="cancelUrl")

    model_config = {"populate_by_name": True}


class ApprovalWebhookPayload(BaseModel):
    """Payload sent to webhook approvers for approval lifecycle events."""

    event: str
    created_at: str = Field(alias="createdAt")
    approval: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    receipt: Optional[dict[str, Any]] = None
    decision: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}
