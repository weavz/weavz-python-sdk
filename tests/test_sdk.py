"""
SDK Integration Tests

Runs against a live local Node.js API server (http://localhost:3000).
Requires: Docker (Postgres, Redis, MinIO) + running `npm run dev:node`.

Bootstrap: creates an API key via service key auth, then uses it for all tests.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
import pytest

from weavz_sdk import WeavzClient, WeavzError

BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:3000")
SERVICE_KEY = "local-test-service-key-12345"
TEST_ORG_ID = ""

# Module-level state
_client: Optional[WeavzClient] = None
_api_key_plain: str = ""
_api_key_id: str = ""
_workspace_id: str = ""
_connection_id: str = ""
_mcp_server_id: str = ""
_integration_instance_id: str = ""
_openai_integration_instance_id: str = ""
_bearer_workspace_id: str = ""
_bearer_mcp_server_id: str = ""
_approval_workspace_id: str = ""
_approval_policy_id: str = ""


def _service_key_request(method: str, path: str, json: Optional[dict] = None) -> httpx.Response:
    return httpx.request(
        method,
        f"{BASE_URL}{path}",
        headers={
            "X-Service-Key": SERVICE_KEY,
            "X-Org-ID": TEST_ORG_ID,
            "Content-Type": "application/json",
        },
        json=json,
        timeout=15.0,
    )


def _ensure_openai_workspace_integration() -> None:
    """Partials are valid only for integrations configured in the workspace."""
    global _openai_integration_instance_id
    if _openai_integration_instance_id:
        return
    result = _client.workspaces.add_integration(
        _workspace_id,
        integration_name="openai",
        integration_alias="openai_primary",
        connection_strategy="fixed",
        connection_id=_connection_id,
    )
    _openai_integration_instance_id = result["integration"]["id"]


@pytest.fixture(scope="session", autouse=True)
def setup_client():
    """Bootstrap: create org, API key and initialize client."""
    global _client, _api_key_plain, _api_key_id, TEST_ORG_ID

    # Verify server is up
    health = httpx.get(f"{BASE_URL}/health", timeout=5.0)
    assert health.status_code == 200, f"Server not reachable: {health.status_code}"

    # Create a test org
    import time
    org_res = httpx.post(
        f"{BASE_URL}/api/v1/orgs",
        headers={"X-Service-Key": SERVICE_KEY, "Content-Type": "application/json"},
        json={"name": "Python SDK Test Org", "slug": f"py-sdk-test-{int(time.time())}"},
        timeout=15.0,
    )
    assert org_res.status_code == 201, f"Failed to create org: {org_res.status_code} {org_res.text}"
    TEST_ORG_ID = org_res.json()["org"]["id"]

    # Create API key via service key
    res = _service_key_request("POST", "/api/v1/api-keys", {"name": "python-sdk-test-key"})
    assert res.status_code == 201, f"Failed to create API key: {res.status_code} {res.text}"
    data = res.json()
    _api_key_plain = data["plainKey"]
    _api_key_id = data["apiKey"]["id"]

    _client = WeavzClient(api_key=_api_key_plain, base_url=BASE_URL)
    yield

    # Cleanup
    try:
        if _openai_integration_instance_id and _workspace_id:
            _client.workspaces.remove_integration(_workspace_id, _openai_integration_instance_id)
    except Exception:
        pass
    try:
        if _integration_instance_id and _workspace_id:
            _client.workspaces.remove_integration(_workspace_id, _integration_instance_id)
    except Exception:
        pass
    try:
        if _mcp_server_id:
            _client.mcp_servers.delete(_mcp_server_id)
    except Exception:
        pass
    try:
        if _bearer_mcp_server_id:
            _client.mcp_servers.delete(_bearer_mcp_server_id)
    except Exception:
        pass
    try:
        if _connection_id:
            _client.connections.delete(_connection_id)
    except Exception:
        pass
    try:
        if _approval_policy_id:
            _client.approval_policies.delete(_approval_policy_id)
    except Exception:
        pass
    try:
        if _approval_workspace_id:
            _client.workspaces.delete(_approval_workspace_id)
    except Exception:
        pass
    try:
        if _bearer_workspace_id:
            _client.workspaces.delete(_bearer_workspace_id)
    except Exception:
        pass
    try:
        if _workspace_id:
            _client.workspaces.delete(_workspace_id)
    except Exception:
        pass
    try:
        if _api_key_id:
            _service_key_request("DELETE", f"/api/v1/api-keys/{_api_key_id}")
    except Exception:
        pass
    _client.close()


# ── API Keys ─────────────────────────────────────────────────────────────────

class TestApiKeys:
    def test_list_api_keys(self):
        result = _client.api_keys.list()
        assert "apiKeys" in result
        assert len(result["apiKeys"]) > 0

    def test_create_and_delete_api_key(self):
        result = _client.api_keys.create(name="temp-py-test-key")
        assert "plainKey" in result
        assert result["plainKey"].startswith("wvz_")
        assert result["apiKey"]["name"] == "temp-py-test-key"

        del_result = _client.api_keys.delete(result["apiKey"]["id"])
        assert del_result["deleted"] is True


# ── Workspaces ────────────────────────────────────────────────────────────────

class TestWorkspaces:
    def test_create_workspace(self):
        global _workspace_id
        result = _client.workspaces.create(name="Python SDK Test", slug="python-sdk-test")
        assert "workspace" in result
        assert result["workspace"]["name"] == "Python SDK Test"
        _workspace_id = result["workspace"]["id"]

    def test_list_workspaces(self):
        result = _client.workspaces.list()
        assert "workspaces" in result
        assert len(result["workspaces"]) > 0

    def test_get_workspace(self):
        result = _client.workspaces.get(_workspace_id)
        assert result["workspace"]["id"] == _workspace_id


# ── Human Gates / Approvals ─────────────────────────────────────────────────

class TestApprovals:
    def test_manage_approval_policies_and_list_requests(self):
        global _approval_workspace_id, _approval_policy_id
        import time

        workspace = _client.workspaces.create(
            name="Python Approval Workspace",
            slug=f"py-approval-{int(time.time())}",
        )
        _approval_workspace_id = workspace["workspace"]["id"]

        policy = {
            "workspace_id": _approval_workspace_id,
            "name": "Python approval policy",
            "description": "Created by the Python SDK test suite",
            "sources": ["sdk"],
            "decision": "require_approval",
            "risk_mode": "always",
            "approvers": [{"type": "org_role", "roles": ["owner", "admin"]}],
            "timeout_seconds": 3600,
            "default_on_timeout": "reject",
            "approval_access_mode": "dashboard_only",
        }

        created = _client.approval_policies.create(**policy)
        _approval_policy_id = created["policy"]["id"]
        assert created["policy"]["name"] == policy["name"]
        assert created["policy"]["workspaceId"] == _approval_workspace_id
        assert created["policy"]["approvalAccessMode"] == "dashboard_only"

        listed = _client.approval_policies.list(workspace_id=_approval_workspace_id)
        assert any(item["id"] == _approval_policy_id for item in listed["policies"])

        fetched = _client.approval_policies.get(_approval_policy_id)
        assert fetched["policy"]["id"] == _approval_policy_id

        tested = _client.approval_policies.test(
            policy=policy,
            context={
                "workspace_id": _approval_workspace_id,
                "source": "sdk",
                "integration_name": "openai",
                "action_name": "chat_completion",
                "input": {"prompt": "hello"},
            },
        )
        assert tested["matched"] is True
        assert tested["decision"] == "require_approval"

        updated = _client.approval_policies.update(_approval_policy_id, enabled=False)
        assert updated["policy"]["enabled"] is False

        approvals = _client.approvals.list(
            workspace_id=_approval_workspace_id,
            status="pending",
            limit=5,
        )
        assert isinstance(approvals["approvals"], list)

        deleted = _client.approval_policies.delete(_approval_policy_id)
        assert deleted["deleted"] is True
        _approval_policy_id = ""


# ── Integrations ─────────────────────────────────────────────────────────────

class TestIntegrations:
    def test_list_integrations(self):
        result = _client.integrations.list()
        assert "integrations" in result
        assert result["total"] > 30

    def test_get_integration(self):
        result = _client.integrations.get("slack")
        assert "integration" in result
        assert result["integration"]["name"] == "slack"

    def test_oauth_status(self):
        result = _client.integrations.oauth_status()
        assert "configured" in result
        assert isinstance(result["configured"], list)


# ── Connections ──────────────────────────────────────────────────────────────

class TestConnections:
    def test_create_connection(self):
        global _connection_id
        result = _client.connections.create(
            type="SECRET_TEXT",
            external_id="py-sdk-test-ext",
            display_name="Python SDK Test Connection",
            integration_name="openai",
            secret_text="sk-test-fake-key-py-12345",
            workspace_id=_workspace_id,
        )
        assert "connection" in result
        assert result["connection"]["displayName"] == "Python SDK Test Connection"
        _connection_id = result["connection"]["id"]

    def test_list_connections(self):
        result = _client.connections.list()
        assert "connections" in result
        assert len(result["connections"]) > 0

    def test_resolve_connection(self):
        result = _client.connections.resolve(
            integration_name="openai",
            external_id="py-sdk-test-ext",
            workspace_id=_workspace_id,
        )
        assert "connection" in result
        assert result["connection"]["id"] == _connection_id


# ── Workspace Integrations ────────────────────────────────────────────────────

class TestWorkspaceIntegrations:
    def test_add_integration(self):
        global _integration_instance_id
        result = _client.workspaces.add_integration(
            _workspace_id,
            integration_name="github",
            connection_strategy="per_user",
        )
        assert "integration" in result
        assert result["integration"]["integrationName"] == "github"
        assert result["integration"]["connectionStrategy"] == "per_user"
        _integration_instance_id = result["integration"]["id"]

    def test_list_integrations(self):
        result = _client.workspaces.list_integrations(_workspace_id)
        assert "integrations" in result
        assert len(result["integrations"]) > 0
        names = [i["integrationName"] for i in result["integrations"]]
        assert "github" in names

    def test_update_integration(self):
        result = _client.workspaces.update_integration(
            _workspace_id,
            _integration_instance_id,
            connection_strategy="per_user_with_fallback",
        )
        assert result["integration"]["connectionStrategy"] == "per_user_with_fallback"

    def test_add_integration_with_alias(self):
        result = _client.workspaces.add_integration(
            _workspace_id,
            integration_name="slack",
            integration_alias="slack_bot",
            connection_strategy="per_user",
            display_name="Slack Bot",
        )
        assert "integration" in result
        assert result["integration"]["alias"] == "slack_bot"
        assert result["integration"]["displayName"] == "Slack Bot"
        inst_id = result["integration"]["id"]
        # Clean up
        _client.workspaces.remove_integration(_workspace_id, inst_id)


# ── MCP Servers ──────────────────────────────────────────────────────────────

class TestMcpServers:
    _tool_id: str = ""

    def test_create_mcp_server(self):
        global _mcp_server_id
        result = _client.mcp_servers.create(
            name="Python SDK Test Server",
            description="Integration test server",
            workspace_id=_workspace_id,
            mode="TOOLS",
        )
        assert "server" in result
        assert "bearerToken" not in result
        assert result["server"]["authMode"] == "oauth"
        assert "mcpEndpoint" in result
        _mcp_server_id = result["server"]["id"]

    def test_list_mcp_servers(self):
        result = _client.mcp_servers.list()
        assert "servers" in result
        assert len(result["servers"]) > 0

    def test_get_mcp_server(self):
        result = _client.mcp_servers.get(_mcp_server_id)
        assert result["server"]["name"] == "Python SDK Test Server"

    def test_add_tool(self):
        result = _client.mcp_servers.add_tool(
            _mcp_server_id,
            integration_name="openai",
            action_name="chat_completion",
        )
        assert "tool" in result
        TestMcpServers._tool_id = result["tool"]["id"]

    def test_update_tool(self):
        result = _client.mcp_servers.update_tool(
            _mcp_server_id,
            TestMcpServers._tool_id,
            display_name="Ask ChatGPT (py-renamed)",
        )
        assert result["tool"]["displayName"] == "Ask ChatGPT (py-renamed)"

    def test_update_mcp_server(self):
        result = _client.mcp_servers.update(
            _mcp_server_id,
            name="Python SDK Test Server (updated)",
        )
        assert result["server"]["name"] == "Python SDK Test Server (updated)"

    def test_create_end_user_oauth_mcp_token(self):
        import time
        external_id = f"py-mcp-eu-{int(time.time() * 1000)}"
        end_user = _client.end_users.create(
            workspace_id=_workspace_id,
            external_id=external_id,
            display_name="Python MCP OAuth End User",
            email="py-mcp-oauth@example.com",
        )

        try:
            result = _client.mcp_servers.create_oauth_token(
                _mcp_server_id,
                end_user_id=external_id,
                scopes=["mcp:tools"],
                expires_in=3600,
            )
            assert "accessToken" in result
            assert result["accessToken"].startswith("mcpo_")
            assert "mcpEndpoint" in result
            assert "mcp:tools" in result["token"]["scopes"]
            assert result["token"]["endUserId"] == external_id
        finally:
            _client.end_users.delete(end_user["endUser"]["id"])

    def test_reject_regenerate_token_when_bearer_disabled(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.mcp_servers.regenerate_token(_mcp_server_id)
        assert exc_info.value.status == 409

    def test_bearer_auth_in_workspace_without_per_user_integrations(self):
        global _bearer_workspace_id, _bearer_mcp_server_id
        import time
        workspace = _client.workspaces.create(
            name="Python SDK Bearer Workspace",
            slug=f"py-sdk-bearer-{int(time.time() * 1000)}",
        )
        _bearer_workspace_id = workspace["workspace"]["id"]

        server = _client.mcp_servers.create(
            name="Python SDK Bearer Server",
            workspace_id=_bearer_workspace_id,
            mode="TOOLS",
            auth_mode="bearer",
        )
        _bearer_mcp_server_id = server["server"]["id"]

        assert "bearerToken" in server
        assert server["bearerToken"].startswith("mcp_")
        assert server["server"]["authMode"] == "bearer"

        result = _client.mcp_servers.regenerate_token(_bearer_mcp_server_id)
        assert "bearerToken" in result
        assert result["bearerToken"].startswith("mcp_")

    def test_delete_tool(self):
        result = _client.mcp_servers.delete_tool(_mcp_server_id, TestMcpServers._tool_id)
        assert result["deleted"] is True


# ── Triggers ─────────────────────────────────────────────────────────────────

class TestTriggers:
    def test_list_triggers(self):
        result = _client.triggers.list()
        assert "triggers" in result
        assert isinstance(result["triggers"], list)

    def test_sample_trigger_data(self):
        result = _client.triggers.test("slack", "new_message")
        assert "sampleData" in result


# ── Input Partials ──────────────────────────────────────────────────────────

class TestPartials:
    _partial_id: str = ""

    def test_create_partial(self):
        _ensure_openai_workspace_integration()
        result = _client.partials.create(
            _workspace_id,
            "openai",
            "Default OpenAI Config",
            description="Pre-filled model and temperature",
            values={"model": "gpt-4o", "temperature": 0.7},
            enforced_keys=["model"],
            is_default=False,
        )
        assert "partial" in result
        assert result["partial"]["name"] == "Default OpenAI Config"
        assert result["partial"]["integrationName"] == "openai"
        assert result["partial"]["values"] == {"model": "gpt-4o", "temperature": 0.7}
        assert result["partial"]["enforcedKeys"] == ["model"]
        assert result["partial"]["isDefault"] is False
        TestPartials._partial_id = result["partial"]["id"]

    def test_list_partials(self):
        result = _client.partials.list(_workspace_id)
        assert "partials" in result
        assert isinstance(result["partials"], list)
        assert len(result["partials"]) > 0
        ids = [p["id"] for p in result["partials"]]
        assert TestPartials._partial_id in ids

    def test_list_partials_with_filter(self):
        result = _client.partials.list(
            _workspace_id, integration_name="openai"
        )
        assert "partials" in result
        for p in result["partials"]:
            assert p["integrationName"] == "openai"

    def test_get_partial(self):
        result = _client.partials.get(TestPartials._partial_id)
        assert "partial" in result
        assert result["partial"]["id"] == TestPartials._partial_id
        assert result["partial"]["name"] == "Default OpenAI Config"

    def test_update_partial(self):
        result = _client.partials.update(
            TestPartials._partial_id,
            name="Updated OpenAI Config",
            values={"model": "gpt-4o-mini", "temperature": 0.5},
        )
        assert "partial" in result
        assert result["partial"]["name"] == "Updated OpenAI Config"
        assert result["partial"]["values"]["model"] == "gpt-4o-mini"

    def test_set_default(self):
        result = _client.partials.set_default(TestPartials._partial_id, True)
        assert "partial" in result
        assert result["partial"]["isDefault"] is True

        # Unset default
        result = _client.partials.set_default(TestPartials._partial_id, False)
        assert result["partial"]["isDefault"] is False

    def test_create_action_scoped_partial(self):
        result = _client.partials.create(
            _workspace_id,
            "openai",
            "Chat Completion Defaults",
            action_name="chat_completion",
            values={"model": "gpt-4o"},
        )
        assert "partial" in result
        assert result["partial"]["actionName"] == "chat_completion"
        # Cleanup
        _client.partials.delete(result["partial"]["id"])

    def test_delete_partial(self):
        result = _client.partials.delete(TestPartials._partial_id)
        assert result["deleted"] is True
        assert result["id"] == TestPartials._partial_id

    def test_get_deleted_partial_404(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.partials.get(TestPartials._partial_id)
        assert exc_info.value.status == 404


# ── endUserId Parameter ──────────────────────────────────────────────────────

class TestEndUserId:
    def test_create_connection_with_end_user_id(self):
        result = _client.connections.create(
            type="SECRET_TEXT",
            external_id="py-enduser-test",
            display_name="endUserId Test Connection",
            integration_name="openai",
            secret_text="sk-test-enduser-py-key",
            workspace_id=_workspace_id,
            end_user_id="end-user-py-001",
        )
        assert "connection" in result
        assert result["connection"]["endUserId"] == "end-user-py-001"
        assert "userId" not in result["connection"]

        # Cleanup
        _client.connections.delete(result["connection"]["id"])

    def test_resolve_connection_with_end_user_id(self):
        # Create a connection with end_user_id first
        created = _client.connections.create(
            type="SECRET_TEXT",
            external_id="py-resolve-enduser",
            display_name="Resolve endUserId Test",
            integration_name="openai",
            secret_text="sk-test-resolve-enduser-py",
            workspace_id=_workspace_id,
            end_user_id="end-user-py-002",
        )

        result = _client.connections.resolve(
            integration_name="openai",
            external_id="py-resolve-enduser",
            workspace_id=_workspace_id,
            end_user_id="end-user-py-002",
        )
        assert "connection" in result
        assert result["connection"]["endUserId"] == "end-user-py-002"

        # Cleanup
        _client.connections.delete(created["connection"]["id"])


# ── Workspace-Scoped API Keys ────────────────────────────────────────────────

class TestWorkspaceScopedApiKeys:
    def test_create_workspace_scoped_key(self):
        result = _client.api_keys.create(
            name="py-workspace-scoped-key",
            permissions={"scope": "workspace", "workspaceIds": [_workspace_id]},
        )
        assert "plainKey" in result
        assert result["plainKey"].startswith("wvz_")
        assert result["apiKey"]["permissions"] == {
            "scope": "workspace",
            "workspaceIds": [_workspace_id],
        }

        # Cleanup
        _client.api_keys.delete(result["apiKey"]["id"])


# ── End Users ───────────────────────────────────────────────────────────────

class TestEndUsers:
    _end_user_id: str = ""

    def test_create_end_user(self):
        import time
        result = _client.end_users.create(
            workspace_id=_workspace_id,
            external_id=f"py-eu-{int(time.time())}",
            display_name="Python SDK End User",
            email="py-enduser@example.com",
            metadata={"plan": "pro"},
        )
        assert "endUser" in result
        assert result["endUser"]["displayName"] == "Python SDK End User"
        assert result["endUser"]["email"] == "py-enduser@example.com"
        assert result["endUser"]["type"] == "external"
        TestEndUsers._end_user_id = result["endUser"]["id"]

    def test_list_end_users(self):
        result = _client.end_users.list(_workspace_id)
        assert "endUsers" in result
        assert "total" in result
        assert len(result["endUsers"]) > 0
        ids = [eu["id"] for eu in result["endUsers"]]
        assert TestEndUsers._end_user_id in ids

    def test_get_end_user(self):
        result = _client.end_users.get(TestEndUsers._end_user_id)
        assert "endUser" in result
        assert result["endUser"]["id"] == TestEndUsers._end_user_id
        assert "connections" in result
        assert isinstance(result["connections"], list)

    def test_update_end_user(self):
        result = _client.end_users.update(
            TestEndUsers._end_user_id,
            display_name="Updated Python End User",
            email="updated-py@example.com",
        )
        assert "endUser" in result
        assert result["endUser"]["displayName"] == "Updated Python End User"
        assert result["endUser"]["email"] == "updated-py@example.com"

    def test_create_connect_token(self):
        result = _client.end_users.create_connect_token(TestEndUsers._end_user_id)
        assert "connectUrl" in result
        assert "token" in result
        assert "expiresAt" in result
        assert result["token"].startswith("eut_")
        assert "/connect/portal" in result["connectUrl"]

    def test_delete_end_user(self):
        result = _client.end_users.delete(TestEndUsers._end_user_id)
        assert result["deleted"] is True
        assert result["id"] == TestEndUsers._end_user_id


# ── Error Handling ───────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_invalid_api_key(self):
        bad_client = WeavzClient(api_key="wvz_invalid", base_url=BASE_URL)
        with pytest.raises(WeavzError) as exc_info:
            bad_client.api_keys.list()
        assert exc_info.value.status == 401
        bad_client.close()

    def test_not_found(self):
        with pytest.raises(WeavzError):
            _client.workspaces.get("nonexistent-id")

    def test_validation_error(self):
        with pytest.raises(WeavzError):
            _client.workspaces.create(name="", slug="")
