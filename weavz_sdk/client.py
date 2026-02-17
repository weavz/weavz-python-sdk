"""Weavz API client with namespaced resource access."""

from __future__ import annotations

import time
from typing import Any

import httpx

from weavz_sdk.errors import WeavzError


class _BaseResource:
    """Base class for API resources."""

    def __init__(self, client: WeavzClient) -> None:
        self._client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._client.request("GET", path, params=params)

    def _post(self, path: str, json: Any = None) -> Any:
        return self._client.request("POST", path, json=json)

    def _patch(self, path: str, json: Any = None) -> Any:
        return self._client.request("PATCH", path, json=json)

    def _delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._client.request("DELETE", path, params=params)


class OrganizationsResource(_BaseResource):
    def get(self, org_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/orgs/{org_id}")

    def update(
        self,
        org_id: str,
        *,
        name: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if slug is not None:
            body["slug"] = slug
        return self._patch(f"/api/v1/orgs/{org_id}", json=body)


class WorkspacesResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/workspaces")

    def create(self, *, name: str, slug: str) -> dict[str, Any]:
        return self._post("/api/v1/workspaces", json={"name": name, "slug": slug})

    def get(self, workspace_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/workspaces/{workspace_id}")

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
    def list(self, *, id: str | None = None) -> dict[str, Any]:
        if id is not None:
            return self._get("/api/v1/connections", params={"id": id})
        return self._get("/api/v1/connections")

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


class OAuthAppsResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/oauth-apps")

    def create(
        self,
        *,
        integration_name: str,
        client_id: str,
        client_secret: str,
        auth_url: str | None = None,
        token_url: str | None = None,
        scope: str | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "clientId": client_id,
            "clientSecret": client_secret,
        }
        if auth_url is not None:
            body["authUrl"] = auth_url
        if token_url is not None:
            body["tokenUrl"] = token_url
        if scope is not None:
            body["scope"] = scope
        if extra_params is not None:
            body["extraParams"] = extra_params
        return self._post("/api/v1/oauth-apps", json=body)

    def delete(self, app_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/oauth-apps/{app_id}")


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
        if success_redirect_uri is not None:
            body["successRedirectUri"] = success_redirect_uri
        if error_redirect_uri is not None:
            body["errorRedirectUri"] = error_redirect_uri
        return self._post("/api/v1/connect/token", json=body)

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/connect/session/{session_id}")


class OAuthResource(_BaseResource):
    """OAuth2 token refresh."""

    def refresh(self, external_id: str) -> dict[str, Any]:
        return self._post(
            "/api/v1/oauth/refresh", json={"externalId": external_id}
        )


class WebhookSecretsResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/webhook-secrets")

    def create(self, *, integration_name: str, secret: str) -> dict[str, Any]:
        return self._post(
            "/api/v1/webhook-secrets",
            json={"integrationName": integration_name, "secret": secret},
        )

    def delete(self, secret_id: str, *, integration_name: str) -> dict[str, Any]:
        return self._delete(
            f"/api/v1/webhook-secrets/{secret_id}",
            params={"integrationName": integration_name},
        )


class ActionsResource(_BaseResource):
    def execute(
        self,
        integration_name: str,
        action_name: str,
        *,
        workspace_id: str,
        input: dict[str, Any] | None = None,
        connection_external_id: str | None = None,
        end_user_id: str | None = None,
        integration_alias: str | None = None,
        partial_ids: list[str] | None = None,
    ) -> Any:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "actionName": action_name,
            "input": input or {},
            "workspaceId": workspace_id,
        }
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if integration_alias is not None:
            body["integrationAlias"] = integration_alias
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        return self._post("/api/v1/actions/execute", json=body)


class TriggersResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/triggers")

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
        end_user_id: str | None = None,
        input: dict[str, Any] | None = None,
        partial_ids: list[str] | None = None,
        simulate: bool | None = None,
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
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if input is not None:
            body["input"] = input
        if partial_ids is not None:
            body["partialIds"] = partial_ids
        if simulate is not None:
            body["simulate"] = simulate
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
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/mcp/servers")

    def create(
        self,
        *,
        name: str,
        workspace_id: str,
        description: str | None = None,
        created_by: str | None = None,
        mode: str | None = None,
        end_user_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name, "workspaceId": workspace_id}
        if description is not None:
            body["description"] = description
        if created_by is not None:
            body["createdBy"] = created_by
        if mode is not None:
            body["mode"] = mode
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
        description: str | None = None,
        mode: str | None = None,
        end_user_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if mode is not None:
            body["mode"] = mode
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        return self._patch(f"/api/v1/mcp/servers/{server_id}", json=body)

    def delete(self, server_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/mcp/servers/{server_id}")

    def regenerate_token(self, server_id: str) -> dict[str, Any]:
        return self._post(f"/api/v1/mcp/servers/{server_id}/regenerate-token")

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
        description: str | None = None,
        input_defaults: dict[str, Any] | None = None,
        connection_id: str | None = None,
        sort_order: int | None = None,
        integration_alias: str | None = None,
        partial_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if display_name is not None:
            body["displayName"] = display_name
        if description is not None:
            body["description"] = description
        if input_defaults is not None:
            body["inputDefaults"] = input_defaults
        if connection_id is not None:
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

    def execute_code(self, server_id: str, code: str) -> dict[str, Any]:
        return self._post(
            f"/api/v1/mcp/servers/{server_id}/execute-code", json={"code": code}
        )

    def get_declarations(
        self, server_id: str, integration_or_alias: str
    ) -> dict[str, Any]:
        return self._get(
            f"/api/v1/mcp/servers/{server_id}/declarations/{integration_or_alias}"
        )

    def sync_from_workspace(
        self,
        server_id: str,
        *,
        aliases: list[str] | None = None,
        actions: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if aliases is not None:
            body["aliases"] = aliases
        if actions is not None:
            body["actions"] = actions
        return self._post(
            f"/api/v1/mcp/servers/{server_id}/sync-from-workspace", json=body
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


class MembersResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/members")

    def create(
        self,
        *,
        user_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        return self._post(
            "/api/v1/members", json={"userId": user_id, "role": role}
        )

    def update(self, member_id: str, *, role: str) -> dict[str, Any]:
        return self._patch(f"/api/v1/members/{member_id}", json={"role": role})

    def delete(self, member_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/members/{member_id}")


class WorkspaceMembersResource(_BaseResource):
    def create(
        self,
        *,
        workspace_id: str,
        member_id: str,
        role: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "memberId": member_id,
        }
        if role is not None:
            body["role"] = role
        return self._post("/api/v1/workspace-members", json=body)

    def delete(self, workspace_member_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/workspace-members/{workspace_member_id}")


class IntegrationsResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/integrations")

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
        end_user_id: str | None = None,
        input: dict[str, Any] | None = None,
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
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if input is not None:
            body["input"] = input
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
        end_user_id: str | None = None,
        input: dict[str, Any] | None = None,
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
        if end_user_id is not None:
            body["endUserId"] = end_user_id
        if input is not None:
            body["input"] = input
        return self._post(
            f"/api/v1/integrations/{integration_name}/properties/resolve", json=body
        )

    def oauth_status(self) -> dict[str, Any]:
        return self._get("/api/v1/integrations/oauth-status")


class ActivityResource(_BaseResource):
    def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        type: str | None = None,
        integration_name: str | None = None,
        since: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if type is not None:
            params["type"] = type
        if integration_name is not None:
            params["integrationName"] = integration_name
        if since is not None:
            params["since"] = since
        return self._get("/api/v1/activity", params=params)


class PartialsResource(_BaseResource):
    """Input partials — reusable pre-filled input values for integration actions."""

    def list(
        self,
        workspace_id: str,
        *,
        integration_name: str | None = None,
        action_name: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"workspaceId": workspace_id}
        if integration_name is not None:
            params["integrationName"] = integration_name
        if action_name is not None:
            params["actionName"] = action_name
        return self._get("/api/v1/partials", params=params)

    def get(self, partial_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/partials/{partial_id}")

    def create(
        self,
        workspace_id: str,
        integration_name: str,
        name: str,
        *,
        action_name: str | None = None,
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

    def list(self, workspace_id: str) -> dict[str, Any]:
        return self._get("/api/v1/end-users", params={"workspaceId": workspace_id})

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
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if integration_name is not None:
            body["integrationName"] = integration_name
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
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"email": email}
        if integration_name is not None:
            body["integrationName"] = integration_name
        if expires_in is not None:
            body["expiresIn"] = expires_in
        return self._post(
            f"/api/v1/end-users/{end_user_id}/invite", json=body
        )


class InvitationsResource(_BaseResource):
    """Organization invitations."""

    def send(
        self,
        email: str,
        organization_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"email": email, "organizationId": organization_id, "role": role}
        return self._post("/api/v1/members/invite", json=body)

    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/members/invitations")

    def revoke(self, invitation_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/members/invitations/{invitation_id}")

    def accept(self, invitation_id: str) -> dict[str, Any]:
        return self._post(f"/api/v1/members/invitations/{invitation_id}/accept")


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

        self.organizations = OrganizationsResource(self)
        self.workspaces = WorkspacesResource(self)
        self.connections = ConnectionsResource(self)
        self.connect = ConnectResource(self)
        self.oauth_apps = OAuthAppsResource(self)
        self.oauth = OAuthResource(self)
        self.webhook_secrets = WebhookSecretsResource(self)
        self.actions = ActionsResource(self)
        self.triggers = TriggersResource(self)
        self.mcp_servers = McpServersResource(self)
        self.api_keys = ApiKeysResource(self)
        self.members = MembersResource(self)
        self.workspace_members = WorkspaceMembersResource(self)
        self.integrations = IntegrationsResource(self)
        self.activity = ActivityResource(self)
        self.partials = PartialsResource(self)
        self.invitations = InvitationsResource(self)
        self.end_users = EndUsersResource(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """Make an authenticated request to the Weavz API."""
        is_idempotent = method.upper() in ("GET", "PUT", "DELETE", "PATCH")
        last_error: WeavzError | None = None

        for attempt in range(self._max_retries + 1):
            response = self._http.request(method, path, params=params, json=json)

            if response.is_success:
                return response.json()

            try:
                body = response.json()
            except Exception:
                body = {}

            last_error = WeavzError(
                body.get("error", f"HTTP {response.status_code}"),
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
