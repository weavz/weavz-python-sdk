"""Weavz API client with namespaced resource access."""

from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import BaseModel

from weavz_sdk.errors import WeavzError
from weavz_sdk.models import WorkspaceIntegrationSettings

class _UnsetType:
    pass


UNSET = _UnsetType()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    return value

_APPROVAL_CAMEL_KEYS = {
    "workspace_id": "workspaceId",
    "mcp_server_ids": "mcpServerIds",
    "workspace_integration_ids": "workspaceIntegrationIds",
    "integration_aliases": "integrationAliases",
    "integration_names": "integrationNames",
    "action_names": "actionNames",
    "connection_strategies": "connectionStrategies",
    "end_user_mode": "endUserMode",
    "risk_mode": "riskMode",
    "timeout_seconds": "timeoutSeconds",
    "default_on_timeout": "defaultOnTimeout",
    "reuse_window_seconds": "reuseWindowSeconds",
    "approval_access_mode": "approvalAccessMode",
    "action_categories": "actionCategories",
    "amount_thresholds": "amountThresholds",
    "recipient_allowlist": "recipientAllowlist",
    "recipient_denylist": "recipientDenylist",
    "domain_allowlist": "domainAllowlist",
    "domain_denylist": "domainDenylist",
    "storage_path_prefixes": "storagePathPrefixes",
    "end_user_id": "endUserId",
    "mcp_server_id": "mcpServerId",
    "workspace_integration_id": "workspaceIntegrationId",
    "integration_name": "integrationName",
    "integration_alias": "integrationAlias",
    "action_name": "actionName",
    "connection_strategy": "connectionStrategy",
    "connection_scope_summary": "connectionScopeSummary",
    "partial_ids": "partialIds",
    "enforced_keys": "enforcedKeys",
    "idempotency_key": "idempotencyKey",
}


def _approval_json(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    if isinstance(value, list):
        return [_approval_json(item) for item in value]
    if isinstance(value, dict):
        return {
            _APPROVAL_CAMEL_KEYS.get(str(key), key): _approval_json(item)
            for key, item in value.items()
        }
    return value


class _BaseResource:
    """Base class for API resources."""

    def __init__(self, client: WeavzClient) -> None:
        self._client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._client.request("GET", path, params=params)

    def _post(
        self,
        path: str,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self._client.request("POST", path, json=json, headers=headers)

    def _patch(self, path: str, json: Any = None) -> Any:
        return self._client.request("PATCH", path, json=json)

    def _delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._client.request("DELETE", path, params=params)


class WorkspacesResource(_BaseResource):
    def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        include_suspended: bool | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if include_suspended is not None:
            params["includeSuspended"] = include_suspended
        return self._get("/api/v1/workspaces", params=params or None)

    def create(self, *, name: str, slug: str) -> dict[str, Any]:
        return self._post("/api/v1/workspaces", json={"name": name, "slug": slug})

    def get(self, workspace_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/workspaces/{workspace_id}")

    def update(
        self,
        workspace_id: str,
        *,
        name: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if slug is not None:
            body["slug"] = slug
        return self._patch(f"/api/v1/workspaces/{workspace_id}", json=body)

    def delete(self, workspace_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/workspaces/{workspace_id}")

    def list_integrations(self, workspace_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/workspaces/{workspace_id}/integrations")

    def add_integration(
        self,
        workspace_id: str,
        *,
        integration_name: str,
        integration_alias: str | None = None,
        connection_strategy: str | None = None,
        connection_id: str | None = None,
        display_name: str | None = None,
        enabled_actions: list[str] | None = None,
        settings: WorkspaceIntegrationSettings | dict[str, Any] | BaseModel | None = None,
        sort_order: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"integrationName": integration_name}
        if integration_alias is not None:
            body["alias"] = integration_alias
        if connection_strategy is not None:
            body["connectionStrategy"] = connection_strategy
        if connection_id is not None:
            body["connectionId"] = connection_id
        if display_name is not None:
            body["displayName"] = display_name
        if enabled_actions is not None:
            body["enabledActions"] = enabled_actions
        if settings is not None:
            body["settings"] = _to_jsonable(settings)
        if sort_order is not None:
            body["sortOrder"] = sort_order
        return self._post(
            f"/api/v1/workspaces/{workspace_id}/integrations", json=body
        )

    def update_integration(
        self,
        workspace_id: str,
        integration_id: str,
        *,
        integration_alias: str | None = None,
        connection_strategy: str | None = None,
        connection_id: str | None = None,
        display_name: str | None = None,
        enabled_actions: list[str] | None = None,
        settings: WorkspaceIntegrationSettings | dict[str, Any] | BaseModel | None = None,
        sort_order: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if integration_alias is not None:
            body["alias"] = integration_alias
        if connection_strategy is not None:
            body["connectionStrategy"] = connection_strategy
        if connection_id is not None:
            body["connectionId"] = connection_id
        if display_name is not None:
            body["displayName"] = display_name
        if enabled_actions is not None:
            body["enabledActions"] = enabled_actions
        if settings is not None:
            body["settings"] = _to_jsonable(settings)
        if sort_order is not None:
            body["sortOrder"] = sort_order
        return self._patch(
            f"/api/v1/workspaces/{workspace_id}/integrations/{integration_id}",
            json=body,
        )

    def remove_integration(
        self, workspace_id: str, integration_id: str
    ) -> dict[str, Any]:
        return self._delete(
            f"/api/v1/workspaces/{workspace_id}/integrations/{integration_id}"
        )


class ConnectionsResource(_BaseResource):
    def list(
        self,
        *,
        id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_suspended: bool | None = None,
    ) -> dict[str, Any]:
        if id is not None:
            return self._get("/api/v1/connections", params={"id": id})
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if include_suspended is not None:
            params["includeSuspended"] = include_suspended
        return self._get("/api/v1/connections", params=params or None)

    def get(self, connection_id: str) -> dict[str, Any]:
        return self._get("/api/v1/connections", params={"id": connection_id})

    def create(
        self,
        *,
        type: str,
        external_id: str,
        display_name: str,
        integration_name: str,
        workspace_id: str | None = None,
        end_user_id: str | None = None,
        scope: str | None = None,
        oauth_app_id: str | None = None,
        secret_text: str | None = None,
        username: str | None = None,
        password: str | None = None,
        props: dict[str, Any] | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_type: str | None = None,
        expires_in: int | None = None,
        scope_oauth: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "type": type,
            "externalId": external_id,
            "displayName": display_name,
            "integrationName": integration_name,
        }
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if scope is not None:
            body["scope"] = scope
        if oauth_app_id is not None:
            body["oauthAppId"] = oauth_app_id
        if secret_text is not None:
            body["secretText"] = secret_text
        if username is not None:
            body["username"] = username
        if password is not None:
            body["password"] = password
        if props is not None:
            body["props"] = props
        if access_token is not None:
            body["accessToken"] = access_token
        if refresh_token is not None:
            body["refreshToken"] = refresh_token
        if token_type is not None:
            body["tokenType"] = token_type
        if expires_in is not None:
            body["expiresIn"] = expires_in
        if scope_oauth is not None:
            body["scope_oauth"] = scope_oauth
        if data is not None:
            body["data"] = data
        return self._post("/api/v1/connections", json=body)

    def delete(self, connection_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/connections/{connection_id}")

    def resolve(
        self,
        *,
        integration_name: str,
        workspace_id: str,
        external_id: str | None = None,
        end_user_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "workspaceId": workspace_id,
        }
        if external_id is not None:
            body["externalId"] = external_id
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        return self._post("/api/v1/connections/resolve", json=body)


class ConnectResource(_BaseResource):
    """Hosted connect flow — create sessions and poll for results."""

    def create_token(
        self,
        *,
        integration_name: str,
        connection_name: str,
        external_id: str,
        workspace_id: str,
        end_user_id: str | None = None,
        scope: str | None = None,
        oauth_app_id: str | None = None,
        success_redirect_uri: str | None = None,
        error_redirect_uri: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "connectionName": connection_name,
            "externalId": external_id,
            "workspaceId": workspace_id,
        }
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if scope is not None:
            body["scope"] = scope
        if oauth_app_id is not None:
            body["oauthAppId"] = oauth_app_id
        if success_redirect_uri is not None:
            body["successRedirectUri"] = success_redirect_uri
        if error_redirect_uri is not None:
            body["errorRedirectUri"] = error_redirect_uri
        return self._post("/api/v1/connect/token", json=body)

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/connect/session/{session_id}")

    def poll(self, token: str) -> dict[str, Any]:
        """Poll connect status using the cst_ token returned by create_token."""
        return self._post("/api/v1/connect/session/poll", json={"token": token})

    def wait(
        self,
        token: str,
        *,
        timeout: float = 120.0,
        interval: float = 1.0,
    ) -> dict[str, Any]:
        """Wait until a connect session completes or fails."""
        deadline = time.monotonic() + timeout
        while time.monotonic() <= deadline:
            result = self.poll(token)
            if result.get("status") in ("COMPLETED", "FAILED"):
                return result
            time.sleep(interval)
        raise WeavzError("Connect session timed out", code="CONNECT_TIMEOUT", status=408)


class ActionsResource(_BaseResource):
    def execute(
        self,
        integration_name: str,
        action_name: str,
        *,
        workspace_id: str,
        input: dict[str, Any] | BaseModel | None = None,
        connection_external_id: str | None = None,
        workspace_integration_id: str | None = None,
        end_user_id: str | None = None,
        integration_alias: str | None = None,
        partial_ids: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "actionName": action_name,
            "input": _to_jsonable(input) if input is not None else {},
            "workspaceId": workspace_id,
        }
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        if idempotency_key is not None:
            body["idempotencyKey"] = idempotency_key
        return self._post(
            "/api/v1/actions/execute",
            json=body,
            headers={"X-Weavz-Source": "sdk"},
        )


class ApprovalPoliciesResource(_BaseResource):
    """Human Gates policies for guarded action execution."""

    def list(self, *, workspace_id: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspaceId"] = workspace_id
        return self._get("/api/v1/approval-policies", params=params or None)

    def create(self, **policy: Any) -> dict[str, Any]:
        return self._post("/api/v1/approval-policies", json=_approval_json(policy))

    def get(self, policy_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/approval-policies/{policy_id}")

    def update(self, policy_id: str, **updates: Any) -> dict[str, Any]:
        return self._patch(f"/api/v1/approval-policies/{policy_id}", json=_approval_json(updates))

    def delete(self, policy_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/approval-policies/{policy_id}")

    def test(self, *, policy: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        return self._post(
            "/api/v1/approval-policies/test",
            json={"policy": _approval_json(policy), "context": _approval_json(context)},
        )


class ApprovalsResource(_BaseResource):
    """Approval request inbox and decision APIs."""

    def list(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
        source: str | None = None,
        integration_name: str | None = None,
        action_name: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspaceId"] = workspace_id
        if status is not None:
            params["status"] = status
        if source is not None:
            params["source"] = source
        if integration_name is not None:
            params["integrationName"] = integration_name
        if action_name is not None:
            params["actionName"] = action_name
        if limit is not None:
            params["limit"] = limit
        return self._get("/api/v1/approvals", params=params or None)

    def get(self, approval_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/approvals/{approval_id}")

    def approve(
        self,
        approval_id: str,
        *,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            f"/api/v1/approvals/{approval_id}/approve",
            json={k: v for k, v in {"reason": reason, "metadata": metadata}.items() if v is not None},
        )

    def reject(
        self,
        approval_id: str,
        *,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            f"/api/v1/approvals/{approval_id}/reject",
            json={k: v for k, v in {"reason": reason, "metadata": metadata}.items() if v is not None},
        )

    def cancel(
        self,
        approval_id: str,
        *,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            f"/api/v1/approvals/{approval_id}/cancel",
            json={k: v for k, v in {"reason": reason, "metadata": metadata}.items() if v is not None},
        )

    def wait(
        self,
        approval_id: str,
        *,
        timeout: float = 120.0,
        interval: float = 1.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() <= deadline:
            result = self.get(approval_id)
            if result.get("approval", {}).get("status") != "pending":
                return result
            time.sleep(interval)
        raise WeavzError("Approval wait timed out", code="APPROVAL_TIMEOUT", status=408)


class TriggersResource(_BaseResource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspaceId"] = workspace_id
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._get("/api/v1/triggers", params=params or None)

    def enable(
        self,
        *,
        integration_name: str,
        trigger_name: str,
        callback_url: str,
        workspace_id: str,
        callback_headers: dict[str, str] | None = None,
        callback_metadata: dict[str, Any] | None = None,
        connection_external_id: str | None = None,
        workspace_integration_id: str | None = None,
        integration_alias: str | None = None,
        end_user_id: str | None = None,
        input: dict[str, Any] | None = None,
        partial_ids: list[str] | None = None,
        simulate: bool | None = None,
        polling_interval_minutes: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "triggerName": trigger_name,
            "callbackUrl": callback_url,
            "workspaceId": workspace_id,
        }
        if callback_headers is not None:
            body["callbackHeaders"] = callback_headers
        if callback_metadata is not None:
            body["callbackMetadata"] = callback_metadata
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if input is not None:
            body["input"] = input
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        if simulate is not None:
            body["simulate"] = simulate
        if polling_interval_minutes is not None:
            body["pollingIntervalMinutes"] = polling_interval_minutes
        return self._post("/api/v1/triggers/enable", json=body)

    def disable(self, trigger_source_id: str) -> dict[str, Any]:
        return self._post(
            "/api/v1/triggers/disable",
            json={"triggerSourceId": trigger_source_id},
        )

    def test(self, integration_name: str, trigger_name: str) -> dict[str, Any]:
        return self._post(
            "/api/v1/triggers/test",
            json={"integrationName": integration_name, "triggerName": trigger_name},
        )


class McpServersResource(_BaseResource):
    def list(
        self,
        *,
        workspace_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_suspended: bool | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspaceId"] = workspace_id
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if include_suspended is not None:
            params["includeSuspended"] = include_suspended
        return self._get("/api/v1/mcp/servers", params=params or None)

    def create(
        self,
        *,
        name: str,
        workspace_id: str,
        description: str | None = None,
        created_by: str | None = None,
        mode: str | None = None,
        settings: dict[str, Any] | None = None,
        auth_mode: str | None = None,
        end_user_access: str | None = None,
        end_user_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name, "workspaceId": workspace_id}
        if description is not None:
            body["description"] = description
        if created_by is not None:
            body["createdBy"] = created_by
        if mode is not None:
            body["mode"] = mode
        if settings is not None:
            body["settings"] = settings
        if auth_mode is not None:
            body["authMode"] = auth_mode
        if end_user_access is not None:
            body["endUserAccess"] = end_user_access
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        return self._post("/api/v1/mcp/servers", json=body)

    def get(self, server_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/mcp/servers/{server_id}")

    def update(
        self,
        server_id: str,
        *,
        name: str | None = None,
        description: str | None | _UnsetType = UNSET,
        mode: str | None = None,
        settings: dict[str, Any] | None = None,
        auth_mode: str | None = None,
        end_user_access: str | None = None,
        end_user_id: str | None | _UnsetType = UNSET,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not UNSET:
            body["description"] = description
        if mode is not None:
            body["mode"] = mode
        if settings is not None:
            body["settings"] = settings
        if auth_mode is not None:
            body["authMode"] = auth_mode
        if end_user_access is not None:
            body["endUserAccess"] = end_user_access
        if end_user_id is not UNSET:
            body["endUserId"] = end_user_id
        return self._patch(f"/api/v1/mcp/servers/{server_id}", json=body)

    def delete(self, server_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/mcp/servers/{server_id}")

    def regenerate_token(self, server_id: str) -> dict[str, Any]:
        return self._post(f"/api/v1/mcp/servers/{server_id}/regenerate-token")

    def create_access_token(
        self,
        server_id: str,
        *,
        end_user_id: str,
        scopes: list[str] | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"endUserId": end_user_id}
        if scopes is not None:
            body["scopes"] = scopes
        if expires_in is not None:
            body["expiresIn"] = expires_in
        return self._post(f"/api/v1/mcp/servers/{server_id}/access-tokens", json=body)

    def create_bearer_token(
        self,
        server_id: str,
        *,
        end_user_id: str,
        scopes: list[str] | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        return self.create_access_token(
            server_id,
            end_user_id=end_user_id,
            scopes=scopes,
            expires_in=expires_in,
        )

    def create_end_user_token(
        self,
        server_id: str,
        *,
        end_user_id: str,
        scopes: list[str] | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        return self.create_access_token(
            server_id,
            end_user_id=end_user_id,
            scopes=scopes,
            expires_in=expires_in,
        )

    def create_oauth_token(
        self,
        server_id: str,
        *,
        end_user_id: str,
        scopes: list[str] | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"endUserId": end_user_id}
        if scopes is not None:
            body["scopes"] = scopes
        if expires_in is not None:
            body["expiresIn"] = expires_in
        return self._post(f"/api/v1/mcp/servers/{server_id}/oauth-tokens", json=body)

    def add_tool(
        self,
        server_id: str,
        *,
        integration_name: str,
        action_name: str,
        integration_alias: str | None = None,
        tool_type: str | None = None,
        connection_id: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        input_defaults: dict[str, Any] | None = None,
        partial_ids: list[str] | None = None,
        sort_order: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "actionName": action_name,
        }
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if tool_type is not None:
            body["toolType"] = tool_type
        if connection_id is not None:
            body["connectionId"] = connection_id
        if display_name is not None:
            body["displayName"] = display_name
        if description is not None:
            body["description"] = description
        if input_defaults is not None:
            body["inputDefaults"] = input_defaults
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        if sort_order is not None:
            body["sortOrder"] = sort_order
        return self._post(f"/api/v1/mcp/servers/{server_id}/tools", json=body)

    def update_tool(
        self,
        server_id: str,
        tool_id: str,
        *,
        display_name: str | None = None,
        description: str | None | _UnsetType = UNSET,
        input_defaults: dict[str, Any] | None = None,
        connection_id: str | None | _UnsetType = UNSET,
        sort_order: int | None = None,
        integration_alias: str | None = None,
        partial_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if display_name is not None:
            body["displayName"] = display_name
        if description is not UNSET:
            body["description"] = description
        if input_defaults is not None:
            body["inputDefaults"] = input_defaults
        if connection_id is not UNSET:
            body["connectionId"] = connection_id
        if sort_order is not None:
            body["sortOrder"] = sort_order
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        return self._patch(
            f"/api/v1/mcp/servers/{server_id}/tools/{tool_id}", json=body
        )

    def delete_tool(self, server_id: str, tool_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/mcp/servers/{server_id}/tools/{tool_id}")

    def execute_code(
        self,
        server_id: str,
        code: str | None = None,
        approval_id: str | None = None,
        wait_for_approval_seconds: int | None = None,
    ) -> dict[str, Any]:
        if bool(code) == bool(approval_id):
            raise ValueError("Pass exactly one of code or approval_id")
        body = {"approvalId": approval_id} if approval_id else {"code": code}
        if wait_for_approval_seconds is not None:
            body["waitForApprovalSeconds"] = wait_for_approval_seconds
        return self._post(
            f"/api/v1/mcp/servers/{server_id}/execute-code", json=body
        )

    def get_declarations(
        self, server_id: str, integration_or_alias: str
    ) -> dict[str, Any]:
        return self._get(
            f"/api/v1/mcp/servers/{server_id}/declarations/{integration_or_alias}"
        )



class ApiKeysResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/api-keys")

    def create(
        self,
        *,
        name: str,
        expires_at: str | None = None,
        permissions: dict[str, Any] | None = None,
        scope: str | None = None,
        workspace_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expiresAt"] = expires_at
        if scope is not None:
            perms: dict[str, Any] = {"scope": scope}
            if workspace_ids is not None:
                perms["workspaceIds"] = workspace_ids
            body["permissions"] = perms
        elif permissions is not None:
            body["permissions"] = permissions
        return self._post("/api/v1/api-keys", json=body)

    def delete(self, key_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/api-keys/{key_id}")


class IntegrationsResource(_BaseResource):
    def list(self, *, summary: bool | None = None) -> dict[str, Any]:
        params = {"summary": summary} if summary is not None else None
        return self._get("/api/v1/integrations", params=params)

    def list_summary(self) -> dict[str, Any]:
        return self._get("/api/v1/integrations", params={"summary": True})

    def get(self, name: str) -> dict[str, Any]:
        return self._get("/api/v1/integrations", params={"name": name})

    def resolve_options(
        self,
        integration_name: str,
        *,
        property_name: str,
        action_name: str | None = None,
        trigger_name: str | None = None,
        connection_external_id: str | None = None,
        workspace_id: str | None = None,
        workspace_integration_id: str | None = None,
        integration_alias: str | None = None,
        end_user_id: str | None = None,
        input: dict[str, Any] | None = None,
        partial_ids: list[str] | None = None,
        search_value: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"propertyName": property_name}
        if action_name is not None:
            body["actionName"] = action_name
        if trigger_name is not None:
            body["triggerName"] = trigger_name
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if input is not None:
            body["input"] = input
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        if search_value is not None:
            body["searchValue"] = search_value
        return self._post(
            f"/api/v1/integrations/{integration_name}/properties/options", json=body
        )

    def resolve_property(
        self,
        integration_name: str,
        *,
        property_name: str,
        action_name: str | None = None,
        trigger_name: str | None = None,
        connection_external_id: str | None = None,
        workspace_id: str | None = None,
        workspace_integration_id: str | None = None,
        integration_alias: str | None = None,
        end_user_id: str | None = None,
        input: dict[str, Any] | None = None,
        partial_ids: list[str] | None = None,
    ) -> Any:
        body: dict[str, Any] = {"propertyName": property_name}
        if action_name is not None:
            body["actionName"] = action_name
        if trigger_name is not None:
            body["triggerName"] = trigger_name
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if input is not None:
            body["input"] = input
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        return self._post(
            f"/api/v1/integrations/{integration_name}/properties/resolve", json=body
        )

    def oauth_status(self) -> dict[str, Any]:
        return self._get("/api/v1/integrations/oauth-status")


class PartialsResource(_BaseResource):
    """Input partials — reusable pre-filled input values for actions or triggers."""

    def list(
        self,
        workspace_id: str,
        *,
        integration_name: str | None = None,
        workspace_integration_id: str | None = None,
        integration_alias: str | None = None,
        action_name: str | None = None,
        trigger_name: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"workspaceId": workspace_id}
        if integration_name is not None:
            params["integrationName"] = integration_name
        if workspace_integration_id is not None:
            params["workspaceIntegrationId"] = workspace_integration_id
        if integration_alias is not None:
            params["integrationAlias"] = integration_alias
        if action_name is not None:
            params["actionName"] = action_name
        if trigger_name is not None:
            params["triggerName"] = trigger_name
        return self._get("/api/v1/partials", params=params)

    def get(self, partial_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/partials/{partial_id}")

    def create(
        self,
        workspace_id: str,
        integration_name: str,
        name: str,
        *,
        workspace_integration_id: str | None = None,
        integration_alias: str | None = None,
        action_name: str | None = None,
        trigger_name: str | None = None,
        description: str | None = None,
        values: dict[str, Any] | None = None,
        enforced_keys: list[str] | None = None,
        is_default: bool = False,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "integrationName": integration_name,
            "name": name,
            "values": values or {},
            "isDefault": is_default,
        }
        if action_name is not None:
            body["actionName"] = action_name
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if trigger_name is not None:
            body["triggerName"] = trigger_name
        if description is not None:
            body["description"] = description
        if enforced_keys is not None:
            body["enforcedKeys"] = enforced_keys
        return self._post("/api/v1/partials", json=body)

    def update(
        self,
        partial_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        values: dict[str, Any] | None = None,
        enforced_keys: list[str] | None = None,
        is_default: bool | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if values is not None:
            body["values"] = values
        if enforced_keys is not None:
            body["enforcedKeys"] = enforced_keys
        if is_default is not None:
            body["isDefault"] = is_default
        return self._patch(f"/api/v1/partials/{partial_id}", json=body)

    def delete(self, partial_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/partials/{partial_id}")

    def set_default(self, partial_id: str, is_default: bool) -> dict[str, Any]:
        return self._post(
            f"/api/v1/partials/{partial_id}/set-default",
            json={"isDefault": is_default},
        )


class EndUsersResource(_BaseResource):
    """End user management and connect portal."""

    def create(
        self,
        *,
        workspace_id: str,
        external_id: str,
        display_name: str | None = None,
        email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "externalId": external_id,
        }
        if display_name is not None:
            body["displayName"] = display_name
        if email is not None:
            body["email"] = email
        if metadata is not None:
            body["metadata"] = metadata
        return self._post("/api/v1/end-users", json=body)

    def list(
        self,
        workspace_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"workspaceId": workspace_id}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._get("/api/v1/end-users", params=params)

    def get(self, end_user_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/end-users/{end_user_id}")

    def update(
        self,
        end_user_id: str,
        *,
        display_name: str | None = None,
        email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if display_name is not None:
            body["displayName"] = display_name
        if email is not None:
            body["email"] = email
        if metadata is not None:
            body["metadata"] = metadata
        return self._patch(f"/api/v1/end-users/{end_user_id}", json=body)

    def delete(self, end_user_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/end-users/{end_user_id}")

    def create_connect_token(
        self,
        end_user_id: str,
        *,
        integration_name: str | None = None,
        workspace_integration_id: str | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if integration_name is not None:
            body["integrationName"] = integration_name
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if expires_in is not None:
            body["expiresIn"] = expires_in
        return self._post(
            f"/api/v1/end-users/{end_user_id}/connect-token", json=body
        )

    def invite(
        self,
        end_user_id: str,
        *,
        email: str,
        integration_name: str | None = None,
        workspace_integration_id: str | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"email": email}
        if integration_name is not None:
            body["integrationName"] = integration_name
        if workspace_integration_id is not None:
            body["workspaceIntegrationId"] = workspace_integration_id
        if expires_in is not None:
            body["expiresIn"] = expires_in
        return self._post(
            f"/api/v1/end-users/{end_user_id}/invite", json=body
        )


class WeavzClient:
    """Weavz API client.

    Usage::

        from weavz_sdk import WeavzClient

        client = WeavzClient(api_key="wvz_...")
        connections = client.connections.list()
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.weavz.io",
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._http = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

        self.workspaces = WorkspacesResource(self)
        self.connections = ConnectionsResource(self)
        self.connect = ConnectResource(self)
        self.actions = ActionsResource(self)
        self.approval_policies = ApprovalPoliciesResource(self)
        self.approvals = ApprovalsResource(self)
        self.triggers = TriggersResource(self)
        self.mcp_servers = McpServersResource(self)
        self.api_keys = ApiKeysResource(self)
        self.integrations = IntegrationsResource(self)
        self.partials = PartialsResource(self)
        self.end_users = EndUsersResource(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Make an authenticated request to the Weavz API."""
        is_idempotent = method.upper() in ("GET", "PUT", "DELETE", "PATCH")
        last_error: WeavzError | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._http.request(method, path, params=params, json=json, headers=headers)
            except httpx.RequestError as exc:
                last_error = WeavzError(
                    str(exc),
                    code="NETWORK_ERROR",
                    status=0,
                    details={"request": str(exc.request.url) if exc.request else None},
                )
                if not is_idempotent or attempt >= self._max_retries:
                    raise last_error from exc
                time.sleep(0.5 * (2 ** attempt))
                continue

            if response.is_success:
                if response.status_code == 204 or not response.content:
                    return None
                return response.json()

            body: dict[str, Any] = {}
            error_text = ""
            try:
                if "application/json" in response.headers.get("content-type", ""):
                    parsed = response.json()
                    if isinstance(parsed, dict):
                        body = parsed
                else:
                    error_text = response.text
            except Exception:
                pass

            last_error = WeavzError(
                body.get("error", error_text or f"HTTP {response.status_code}"),
                code=body.get("code", "HTTP_ERROR"),
                status=response.status_code,
                details=body.get("details"),
            )

            is_429 = response.status_code == 429
            is_5xx = 500 <= response.status_code < 600
            should_retry = is_429 or (is_5xx and is_idempotent)

            if not should_retry or attempt >= self._max_retries:
                raise last_error

            # Calculate backoff delay
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    delay = float(retry_after)
                except ValueError:
                    # RFC 7231 date format — not common, fall back to backoff
                    delay = 0.5 * (2 ** attempt)
            else:
                # Exponential backoff: 0.5s, 1s, 2s, ...
                delay = 0.5 * (2 ** attempt)

            time.sleep(delay)

        # Should not reach here, but satisfy type checkers
        raise last_error  # type: ignore[misc]

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> WeavzClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
