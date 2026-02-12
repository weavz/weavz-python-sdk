"""Weavz API client with namespaced resource access."""

from __future__ import annotations

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


class ProjectsResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/projects")

    def create(self, *, name: str, slug: str) -> dict[str, Any]:
        return self._post("/api/v1/projects", json={"name": name, "slug": slug})

    def get(self, project_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/projects/{project_id}")

    def delete(self, project_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/projects/{project_id}")


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
        project_id: str | None = None,
        user_id: str | None = None,
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
        if project_id is not None:
            body["projectId"] = project_id
        if user_id is not None:
            body["userId"] = user_id
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
        external_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"integrationName": integration_name}
        if external_id is not None:
            body["externalId"] = external_id
        if project_id is not None:
            body["projectId"] = project_id
        if user_id is not None:
            body["userId"] = user_id
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


class OAuthResource(_BaseResource):
    def authorize(
        self,
        *,
        integration_name: str,
        redirect_url: str,
        connection_name: str,
        scope: list[str] | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "redirectUrl": redirect_url,
            "connectionName": connection_name,
        }
        if scope is not None:
            body["scope"] = scope
        if extra_params is not None:
            body["extraParams"] = extra_params
        return self._post("/api/v1/oauth/authorize", json=body)

    def claim(
        self,
        *,
        integration_name: str,
        code: str,
        redirect_url: str,
        connection_name: str,
        external_id: str,
        code_verifier: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "code": code,
            "redirectUrl": redirect_url,
            "connectionName": connection_name,
            "externalId": external_id,
        }
        if code_verifier is not None:
            body["codeVerifier"] = code_verifier
        return self._post("/api/v1/oauth/callback", json=body)

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
        input: dict[str, Any] | None = None,
        connection_external_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "actionName": action_name,
            "input": input or {},
        }
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if project_id is not None:
            body["projectId"] = project_id
        if user_id is not None:
            body["userId"] = user_id
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
        callback_headers: dict[str, str] | None = None,
        callback_metadata: dict[str, Any] | None = None,
        connection_external_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
        simulate: bool | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "triggerName": trigger_name,
            "callbackUrl": callback_url,
        }
        if callback_headers is not None:
            body["callbackHeaders"] = callback_headers
        if callback_metadata is not None:
            body["callbackMetadata"] = callback_metadata
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if project_id is not None:
            body["projectId"] = project_id
        if user_id is not None:
            body["userId"] = user_id
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
        description: str | None = None,
        project_id: str | None = None,
        created_by: str | None = None,
        sharing: str | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if project_id is not None:
            body["projectId"] = project_id
        if created_by is not None:
            body["createdBy"] = created_by
        if sharing is not None:
            body["sharing"] = sharing
        if mode is not None:
            body["mode"] = mode
        return self._post("/api/v1/mcp/servers", json=body)

    def get(self, server_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/mcp/servers/{server_id}")

    def update(
        self,
        server_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sharing: str | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if sharing is not None:
            body["sharing"] = sharing
        if mode is not None:
            body["mode"] = mode
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


class ApiKeysResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/api-keys")

    def create(
        self,
        *,
        name: str,
        expires_at: str | None = None,
        permissions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expiresAt"] = expires_at
        if permissions is not None:
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
        role: str = "MEMBER",
    ) -> dict[str, Any]:
        return self._post(
            "/api/v1/members", json={"userId": user_id, "role": role}
        )

    def update(self, member_id: str, *, role: str) -> dict[str, Any]:
        return self._patch(f"/api/v1/members/{member_id}", json={"role": role})

    def delete(self, member_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/members/{member_id}")


class ProjectMembersResource(_BaseResource):
    def create(
        self,
        *,
        project_id: str,
        member_id: str,
        role: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "projectId": project_id,
            "memberId": member_id,
        }
        if role is not None:
            body["role"] = role
        return self._post("/api/v1/project-members", json=body)

    def delete(self, project_member_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/project-members/{project_member_id}")


class ConnectionPoliciesResource(_BaseResource):
    def list(self) -> dict[str, Any]:
        return self._get("/api/v1/connection-policies")

    def create(
        self,
        *,
        integration_name: str,
        policy: str,
        project_id: str | None = None,
        connection_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "integrationName": integration_name,
            "policy": policy,
        }
        if project_id is not None:
            body["projectId"] = project_id
        if connection_id is not None:
            body["connectionId"] = connection_id
        return self._post("/api/v1/connection-policies", json=body)

    def update(
        self,
        policy_id: str,
        *,
        policy: str | None = None,
        connection_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if policy is not None:
            body["policy"] = policy
        if connection_id is not None:
            body["connectionId"] = connection_id
        return self._patch(f"/api/v1/connection-policies/{policy_id}", json=body)

    def delete(self, policy_id: str) -> dict[str, Any]:
        return self._delete(f"/api/v1/connection-policies/{policy_id}")


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
        project_id: str | None = None,
        user_id: str | None = None,
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
        if project_id is not None:
            body["projectId"] = project_id
        if user_id is not None:
            body["userId"] = user_id
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
        project_id: str | None = None,
        user_id: str | None = None,
        input: dict[str, Any] | None = None,
    ) -> Any:
        body: dict[str, Any] = {"propertyName": property_name}
        if action_name is not None:
            body["actionName"] = action_name
        if trigger_name is not None:
            body["triggerName"] = trigger_name
        if connection_external_id is not None:
            body["connectionExternalId"] = connection_external_id
        if project_id is not None:
            body["projectId"] = project_id
        if user_id is not None:
            body["userId"] = user_id
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
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

        self.organizations = OrganizationsResource(self)
        self.projects = ProjectsResource(self)
        self.connections = ConnectionsResource(self)
        self.oauth_apps = OAuthAppsResource(self)
        self.oauth = OAuthResource(self)
        self.webhook_secrets = WebhookSecretsResource(self)
        self.actions = ActionsResource(self)
        self.triggers = TriggersResource(self)
        self.mcp_servers = McpServersResource(self)
        self.api_keys = ApiKeysResource(self)
        self.members = MembersResource(self)
        self.project_members = ProjectMembersResource(self)
        self.connection_policies = ConnectionPoliciesResource(self)
        self.integrations = IntegrationsResource(self)
        self.activity = ActivityResource(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """Make an authenticated request to the Weavz API."""
        response = self._http.request(method, path, params=params, json=json)

        if not response.is_success:
            try:
                body = response.json()
            except Exception:
                body = {}
            raise WeavzError(
                body.get("error", f"HTTP {response.status_code}"),
                code=body.get("code", "HTTP_ERROR"),
                status=response.status_code,
                details=body.get("details"),
            )

        return response.json()

    def health(self) -> dict[str, Any]:
        """Health check."""
        return self.request("GET", "/health")

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> WeavzClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
