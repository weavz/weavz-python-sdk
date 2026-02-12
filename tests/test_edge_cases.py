"""
SDK Edge Case & Negative Tests (Python)

Tests validation errors, duplicate handling, boundary conditions,
authorization edge cases, and resource lifecycle correctness.

Runs against a live local Node.js API server (http://localhost:3000).
Requires: Docker (Postgres, Redis, MinIO) + running `npm run dev:node`.
"""

import httpx
import pytest

from weavz_sdk import WeavzClient, WeavzError

BASE_URL = "http://localhost:3000"
SERVICE_KEY = "local-test-service-key-12345"
TEST_ORG_ID = "6555c8f1-c057-4c02-9980-1ef723c23855"

# Module-level state
_client: WeavzClient | None = None
_api_key_plain: str = ""
_api_key_id: str = ""
_cleanup_stack: list = []


def _service_key_request(method: str, path: str, json: dict | None = None) -> httpx.Response:
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


@pytest.fixture(scope="session", autouse=True)
def setup_client():
    global _client, _api_key_plain, _api_key_id

    health = httpx.get(f"{BASE_URL}/health", timeout=5.0)
    assert health.status_code == 200, f"Server not reachable: {health.status_code}"

    res = _service_key_request("POST", "/api/v1/api-keys", {"name": "python-edge-test-key"})
    assert res.status_code == 201, f"Failed to create API key: {res.status_code} {res.text}"
    data = res.json()
    _api_key_plain = data["plainKey"]
    _api_key_id = data["apiKey"]["id"]

    _client = WeavzClient(api_key=_api_key_plain, base_url=BASE_URL)
    yield

    # Cleanup stack
    for fn in reversed(_cleanup_stack):
        try:
            fn()
        except Exception:
            pass
    try:
        if _api_key_id:
            _service_key_request("DELETE", f"/api/v1/api-keys/{_api_key_id}")
    except Exception:
        pass
    _client.close()


# ── Project Edge Cases ────────────────────────────────────────────────────────


class TestProjectEdgeCases:
    def test_reject_empty_name(self):
        with pytest.raises(WeavzError):
            _client.projects.create(name="", slug="valid-slug-py")

    def test_reject_empty_slug(self):
        with pytest.raises(WeavzError):
            _client.projects.create(name="Valid", slug="")

    def test_reject_slug_with_uppercase(self):
        with pytest.raises(WeavzError):
            _client.projects.create(name="Test", slug="Invalid-Slug-Py")

    def test_reject_slug_with_special_chars(self):
        with pytest.raises(WeavzError):
            _client.projects.create(name="Test", slug="invalid slug!")

    def test_reject_slug_starting_with_hyphen(self):
        with pytest.raises(WeavzError):
            _client.projects.create(name="Test", slug="-leading-hyphen")

    def test_create_project_with_unicode_name(self):
        result = _client.projects.create(
            name="Projet Spécial 日本語",
            slug="py-unicode-name-test",
        )
        assert "project" in result
        assert result["project"]["name"] == "Projet Spécial 日本語"
        pid = result["project"]["id"]
        _cleanup_stack.append(lambda: _client.projects.delete(pid))

    def test_reject_duplicate_slug(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.projects.create(name="Dup", slug="py-unicode-name-test")
        assert exc_info.value.status >= 400

    def test_error_for_nonexistent_project(self):
        with pytest.raises(WeavzError):
            _client.projects.get("00000000-0000-0000-0000-000000000000")

    def test_delete_already_deleted_project(self):
        result = _client.projects.create(name="PyDelMe", slug="py-del-me-edge")
        pid = result["project"]["id"]
        _client.projects.delete(pid)
        with pytest.raises(WeavzError):
            _client.projects.delete(pid)


# ── Connection Edge Cases ─────────────────────────────────────────────────────


class TestConnectionEdgeCases:
    _project_id: str = ""
    _conn_id: str = ""

    @classmethod
    def _ensure_project(cls):
        if not cls._project_id:
            result = _client.projects.create(name="Py Conn Edge", slug="py-conn-edge-test")
            cls._project_id = result["project"]["id"]
            _cleanup_stack.append(lambda: _client.projects.delete(cls._project_id))

    def test_create_secret_text_connection(self):
        self._ensure_project()
        result = _client.connections.create(
            type="SECRET_TEXT",
            external_id="py-edge-secret-1",
            display_name="Py Edge Secret Text",
            integration_name="openai",
            secret_text="sk-test-py-edge-12345",
            project_id=self._project_id,
        )
        assert "connection" in result
        TestConnectionEdgeCases._conn_id = result["connection"]["id"]
        _cleanup_stack.append(lambda: _client.connections.delete(self._conn_id))

    def test_reject_duplicate_connection(self):
        self._ensure_project()
        with pytest.raises(WeavzError) as exc_info:
            _client.connections.create(
                type="SECRET_TEXT",
                external_id="py-edge-secret-1",
                display_name="Duplicate",
                integration_name="openai",
                secret_text="sk-dupe",
                project_id=self._project_id,
            )
        assert exc_info.value.status == 409

    def test_allow_same_external_id_different_integration(self):
        self._ensure_project()
        result = _client.connections.create(
            type="SECRET_TEXT",
            external_id="py-edge-secret-1",
            display_name="Same ExtID Diff Integration",
            integration_name="anthropic",
            secret_text="sk-ant-py-edge",
            project_id=self._project_id,
        )
        assert "connection" in result
        cid = result["connection"]["id"]
        _cleanup_stack.append(lambda: _client.connections.delete(cid))

    def test_create_basic_auth_connection(self):
        self._ensure_project()
        result = _client.connections.create(
            type="BASIC_AUTH",
            external_id="py-edge-basic-1",
            display_name="Py Edge Basic Auth",
            integration_name="http",
            username="testuser",
            password="testpass123",
            project_id=self._project_id,
        )
        assert "connection" in result
        cid = result["connection"]["id"]
        _cleanup_stack.append(lambda: _client.connections.delete(cid))

    def test_create_custom_auth_connection(self):
        self._ensure_project()
        result = _client.connections.create(
            type="CUSTOM_AUTH",
            external_id="py-edge-custom-1",
            display_name="Py Edge Custom Auth",
            integration_name="http",
            props={"headerName": "X-Custom-Token", "headerValue": "test-token-value"},
            project_id=self._project_id,
        )
        assert "connection" in result
        cid = result["connection"]["id"]
        _cleanup_stack.append(lambda: _client.connections.delete(cid))

    def test_reject_missing_required_fields(self):
        with pytest.raises(WeavzError):
            _client.connections.create(
                type="SECRET_TEXT",
                external_id="",
                display_name="",
                integration_name="",
            )

    def test_resolve_valid_connection(self):
        self._ensure_project()
        result = _client.connections.resolve(
            integration_name="openai",
            external_id="py-edge-secret-1",
            project_id=self._project_id,
        )
        assert "connection" in result
        assert result["connection"]["id"] == self._conn_id

    def test_resolve_nonexistent_connection(self):
        self._ensure_project()
        with pytest.raises(WeavzError):
            _client.connections.resolve(
                integration_name="openai",
                external_id="does-not-exist-xyz",
                project_id=self._project_id,
            )


# ── MCP Server Edge Cases ────────────────────────────────────────────────────


class TestMcpServerEdgeCases:
    _project_id: str = ""
    _tools_server_id: str = ""
    _code_server_id: str = ""

    @classmethod
    def _ensure_project(cls):
        if not cls._project_id:
            result = _client.projects.create(name="Py MCP Edge", slug="py-mcp-edge-test")
            cls._project_id = result["project"]["id"]
            _cleanup_stack.append(lambda: _client.projects.delete(cls._project_id))

    def test_create_tools_mode_server(self):
        self._ensure_project()
        result = _client.mcp_servers.create(
            name="Py Edge Tools Server",
            description="Testing tools mode",
            project_id=self._project_id,
            mode="TOOLS",
        )
        assert "server" in result
        assert "bearerToken" in result
        assert result["bearerToken"].startswith("mcp_")
        assert "mcpEndpoint" in result
        TestMcpServerEdgeCases._tools_server_id = result["server"]["id"]
        _cleanup_stack.append(lambda: _client.mcp_servers.delete(self._tools_server_id))

    def test_create_code_mode_server(self):
        self._ensure_project()
        result = _client.mcp_servers.create(
            name="Py Edge Code Server",
            description="Testing code mode",
            project_id=self._project_id,
            mode="CODE",
        )
        assert "server" in result
        assert result["server"]["mode"] == "CODE"
        TestMcpServerEdgeCases._code_server_id = result["server"]["id"]
        _cleanup_stack.append(lambda: _client.mcp_servers.delete(self._code_server_id))

    def test_add_tool_with_valid_alias(self):
        result = _client.mcp_servers.add_tool(
            self._tools_server_id,
            integration_name="openai",
            action_name="ask_chatgpt",
            integration_alias="openai-primary",
        )
        assert "tool" in result
        tool_id = result["tool"]["id"]
        _cleanup_stack.append(
            lambda: _client.mcp_servers.delete_tool(self._tools_server_id, tool_id)
        )

    def test_reject_duplicate_tool(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.mcp_servers.add_tool(
                self._tools_server_id,
                integration_name="openai",
                action_name="ask_chatgpt",
                integration_alias="openai-primary",
            )
        assert exc_info.value.status == 409

    def test_allow_same_action_different_alias(self):
        result = _client.mcp_servers.add_tool(
            self._tools_server_id,
            integration_name="openai",
            action_name="ask_chatgpt",
            integration_alias="openai-secondary",
        )
        assert "tool" in result
        tool_id = result["tool"]["id"]
        _cleanup_stack.append(
            lambda: _client.mcp_servers.delete_tool(self._tools_server_id, tool_id)
        )

    def test_reject_alias_with_uppercase(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.mcp_servers.add_tool(
                self._tools_server_id,
                integration_name="openai",
                action_name="ask_chatgpt",
                integration_alias="OpenAI",
            )
        assert exc_info.value.status == 400

    def test_reject_alias_starting_with_underscore(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.mcp_servers.add_tool(
                self._tools_server_id,
                integration_name="openai",
                action_name="ask_chatgpt",
                integration_alias="_openai",
            )
        assert exc_info.value.status == 400

    def test_reject_alias_with_special_chars(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.mcp_servers.add_tool(
                self._tools_server_id,
                integration_name="openai",
                action_name="ask_chatgpt",
                integration_alias="openai@bot",
            )
        assert exc_info.value.status == 400

    def test_reject_alias_conflict(self):
        # 'openai-primary' alias already maps to openai — try with anthropic
        with pytest.raises(WeavzError) as exc_info:
            _client.mcp_servers.add_tool(
                self._tools_server_id,
                integration_name="anthropic",
                action_name="ask_claude",
                integration_alias="openai-primary",
            )
        assert exc_info.value.status == 409

    def test_add_tool_with_custom_display_name(self):
        result = _client.mcp_servers.add_tool(
            self._tools_server_id,
            integration_name="slack",
            action_name="send_channel_message",
            display_name="Post to Slack",
            description="Custom description for edge test",
        )
        assert "tool" in result
        assert result["tool"]["displayName"] == "Post to Slack"
        tool_id = result["tool"]["id"]
        _cleanup_stack.append(
            lambda: _client.mcp_servers.delete_tool(self._tools_server_id, tool_id)
        )

    def test_regenerate_token_gives_new_value(self):
        result1 = _client.mcp_servers.regenerate_token(self._tools_server_id)
        result2 = _client.mcp_servers.regenerate_token(self._tools_server_id)
        assert result1["bearerToken"].startswith("mcp_")
        assert result2["bearerToken"].startswith("mcp_")
        assert result1["bearerToken"] != result2["bearerToken"]

    def test_get_server_with_tools(self):
        result = _client.mcp_servers.get(self._tools_server_id)
        assert "server" in result
        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) > 0

    def test_reject_operations_on_nonexistent_server(self):
        with pytest.raises(WeavzError):
            _client.mcp_servers.get("00000000-0000-0000-0000-000000000000")


# ── Project Integration Edge Cases ────────────────────────────────────────────


class TestProjectIntegrationEdgeCases:
    _project_id: str = ""
    _conn_id: str = ""

    @classmethod
    def _ensure_resources(cls):
        if not cls._project_id:
            result = _client.projects.create(name="Py Intg Edge", slug="py-intg-edge-test")
            cls._project_id = result["project"]["id"]
            _cleanup_stack.append(lambda: _client.projects.delete(cls._project_id))

            conn = _client.connections.create(
                type="SECRET_TEXT",
                external_id="py-intg-edge-conn",
                display_name="Py Intg Edge Conn",
                integration_name="github",
                secret_text="ghp_testtoken123",
                project_id=cls._project_id,
            )
            cls._conn_id = conn["connection"]["id"]
            _cleanup_stack.append(lambda: _client.connections.delete(cls._conn_id))

    def test_reject_fixed_without_connection_id(self):
        self._ensure_resources()
        with pytest.raises(WeavzError) as exc_info:
            _client.projects.add_integration(
                self._project_id,
                integration_name="github",
                connection_strategy="fixed",
            )
        assert exc_info.value.status == 400

    def test_create_fixed_with_connection_id(self):
        self._ensure_resources()
        result = _client.projects.add_integration(
            self._project_id,
            integration_name="github",
            connection_strategy="fixed",
            connection_id=self._conn_id,
        )
        assert "integration" in result
        assert result["integration"]["connectionStrategy"] == "fixed"
        inst_id = result["integration"]["id"]
        _cleanup_stack.append(
            lambda: _client.projects.remove_integration(self._project_id, inst_id)
        )

    def test_create_per_user_integration(self):
        self._ensure_resources()
        result = _client.projects.add_integration(
            self._project_id,
            integration_name="notion",
            connection_strategy="per_user",
        )
        assert "integration" in result
        assert result["integration"]["connectionStrategy"] == "per_user"
        inst_id = result["integration"]["id"]
        _cleanup_stack.append(
            lambda: _client.projects.remove_integration(self._project_id, inst_id)
        )

    def test_create_per_user_with_fallback(self):
        self._ensure_resources()
        result = _client.projects.add_integration(
            self._project_id,
            integration_name="slack",
            connection_strategy="per_user_with_fallback",
        )
        assert "integration" in result
        assert result["integration"]["connectionStrategy"] == "per_user_with_fallback"
        inst_id = result["integration"]["id"]
        _cleanup_stack.append(
            lambda: _client.projects.remove_integration(self._project_id, inst_id)
        )

    def test_add_integration_with_custom_alias(self):
        self._ensure_resources()
        result = _client.projects.add_integration(
            self._project_id,
            integration_name="openai",
            alias="openai_primary",
            connection_strategy="per_user",
            display_name="OpenAI Primary",
        )
        assert "integration" in result
        assert result["integration"]["alias"] == "openai_primary"
        assert result["integration"]["displayName"] == "OpenAI Primary"
        inst_id = result["integration"]["id"]
        _cleanup_stack.append(
            lambda: _client.projects.remove_integration(self._project_id, inst_id)
        )

    def test_update_integration_strategy(self):
        self._ensure_resources()
        # Create a per_user integration, then update to per_user_with_fallback
        result = _client.projects.add_integration(
            self._project_id,
            integration_name="anthropic",
            connection_strategy="per_user",
        )
        inst_id = result["integration"]["id"]
        _cleanup_stack.append(
            lambda: _client.projects.remove_integration(self._project_id, inst_id)
        )

        updated = _client.projects.update_integration(
            self._project_id,
            inst_id,
            connection_strategy="per_user_with_fallback",
        )
        assert updated["integration"]["connectionStrategy"] == "per_user_with_fallback"

    def test_remove_integration(self):
        self._ensure_resources()
        result = _client.projects.add_integration(
            self._project_id,
            integration_name="http",
            connection_strategy="per_user",
        )
        inst_id = result["integration"]["id"]

        del_result = _client.projects.remove_integration(self._project_id, inst_id)
        assert del_result["deleted"] is True

    def test_list_integrations(self):
        self._ensure_resources()
        result = _client.projects.list_integrations(self._project_id)
        assert "integrations" in result
        assert isinstance(result["integrations"], list)


# ── API Key Edge Cases ────────────────────────────────────────────────────────


class TestApiKeyEdgeCases:
    def test_reject_empty_key_name(self):
        with pytest.raises(WeavzError):
            _client.api_keys.create(name="")

    def test_create_multiple_keys(self):
        key1 = _client.api_keys.create(name="py-edge-key-1")
        key2 = _client.api_keys.create(name="py-edge-key-2")
        _cleanup_stack.append(lambda: _client.api_keys.delete(key1["apiKey"]["id"]))
        _cleanup_stack.append(lambda: _client.api_keys.delete(key2["apiKey"]["id"]))

        assert key1["plainKey"].startswith("wvz_")
        assert key2["plainKey"].startswith("wvz_")
        assert key1["plainKey"] != key2["plainKey"]

        listing = _client.api_keys.list()
        names = [k["name"] for k in listing["apiKeys"]]
        assert "py-edge-key-1" in names
        assert "py-edge-key-2" in names

    def test_new_key_works_for_auth(self):
        key = _client.api_keys.create(name="py-edge-auth-test")
        _cleanup_stack.append(lambda: _client.api_keys.delete(key["apiKey"]["id"]))

        new_client = WeavzClient(api_key=key["plainKey"], base_url=BASE_URL)
        health = new_client.health()
        assert health["status"] == "healthy"
        integrations = new_client.integrations.list()
        assert integrations["total"] > 0
        new_client.close()

    def test_deleted_key_stops_working(self):
        key = _client.api_keys.create(name="py-edge-delete-test")
        key_client = WeavzClient(api_key=key["plainKey"], base_url=BASE_URL)

        # Should work
        key_client.health()

        # Delete the key
        _client.api_keys.delete(key["apiKey"]["id"])

        # Should fail
        with pytest.raises(WeavzError) as exc_info:
            key_client.api_keys.list()
        assert exc_info.value.status == 401
        key_client.close()


# ── Integration Edge Cases ────────────────────────────────────────────────────


class TestIntegrationEdgeCases:
    def test_not_found_for_nonexistent_integration(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.integrations.get("definitely-not-real-integration")
        assert exc_info.value.status == 404

    def test_list_integrations_structure(self):
        result = _client.integrations.list()
        assert "integrations" in result
        assert "total" in result
        assert "registered" in result
        assert result["total"] > 30
        assert isinstance(result["registered"], list)

        first = result["integrations"][0]
        assert "name" in first
        assert "displayName" in first

    def test_get_integration_metadata(self):
        result = _client.integrations.get("slack")
        integration = result["integration"]
        assert integration["name"] == "slack"
        assert "displayName" in integration
        assert "actions" in integration
        assert "triggers" in integration


# ── Activity Edge Cases ───────────────────────────────────────────────────────


class TestActivityEdgeCases:
    def test_list_with_default_pagination(self):
        result = _client.activity.list()
        assert "events" in result
        assert "total" in result
        assert isinstance(result["total"], int)

    def test_filter_with_limit(self):
        result = _client.activity.list(limit=5)
        assert "events" in result
        assert len(result["events"]) <= 5

    def test_filter_with_offset(self):
        result1 = _client.activity.list(limit=2, offset=0)
        result2 = _client.activity.list(limit=2, offset=2)
        assert "events" in result1
        assert "events" in result2

    def test_future_since_filter_empty(self):
        import datetime

        future = (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=365)
        ).isoformat()
        result = _client.activity.list(since=future)
        assert "events" in result
        assert len(result["events"]) == 0


# ── Trigger Edge Cases ────────────────────────────────────────────────────────


class TestTriggerEdgeCases:
    def test_reject_nonexistent_trigger(self):
        with pytest.raises(WeavzError):
            _client.triggers.test("slack", "nonexistent-trigger")

    def test_reject_nonexistent_integration(self):
        with pytest.raises(WeavzError):
            _client.triggers.test("nonexistent-integration", "some-trigger")


# ── Error Shape Consistency ───────────────────────────────────────────────────


class TestErrorShapeConsistency:
    def test_error_has_message_code_status(self):
        bad_client = WeavzClient(api_key="wvz_totally_invalid", base_url=BASE_URL)
        with pytest.raises(WeavzError) as exc_info:
            bad_client.api_keys.list()
        err = exc_info.value
        assert isinstance(str(err), str)  # message is in args[0]
        assert isinstance(err.code, str)
        assert isinstance(err.status, int)
        assert err.status == 401
        bad_client.close()

    def test_validation_error_status(self):
        with pytest.raises(WeavzError) as exc_info:
            _client.projects.create(name="", slug="")
        err = exc_info.value
        assert 400 <= err.status < 500


# ── Client Configuration Edge Cases ───────────────────────────────────────────


class TestClientConfig:
    def test_strips_trailing_slashes(self):
        c = WeavzClient(api_key=_api_key_plain, base_url=BASE_URL + "///")
        health = c.health()
        assert health["status"] == "healthy"
        c.close()

    def test_context_manager(self):
        with WeavzClient(api_key=_api_key_plain, base_url=BASE_URL) as c:
            health = c.health()
            assert health["status"] == "healthy"
