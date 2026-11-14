"""Offline transport, customer contract, and adapter regressions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from pydantic import BaseModel, Field

from weavz_sdk import WeavzClient, WeavzError, WorkspaceIntegration
from weavz_sdk.adapters import (
    WeavzActionTool, create_mcp_server_action_tools, create_tool_executor,
    props_to_json_schema, to_google_adk_function, to_openai_chat_tool,
    to_openai_responses_tool, to_google_function_declaration, _langchain_args_schema,
)


@pytest.fixture
def client_factory():
    clients = []
    def make(handler, retries=0, **options):
        client = WeavzClient("wvz_test", base_url="https://api.example.com", max_retries=retries, **options)
        default_headers = client._http.headers
        client._http.close()
        client._http = httpx.Client(base_url="https://api.example.com", headers=default_headers, timeout=310, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client
    yield make
    for client in clients:
        client.close()


@pytest.mark.parametrize("kwargs", [
    {"api_key": ""}, {"api_key": "  "}, {"max_retries": -1}, {"max_retries": 1.5},
    {"max_retries": True}, {"timeout": 0}, {"timeout": -1}, {"timeout": float("inf")},
    {"timeout": float("nan")}, {"base_url": "ftp://example.com"},
    {"base_url": "https://user:password@example.com"}, {"base_url": "https://example.com?token=private"},
])
def test_reject_invalid_config(kwargs):
    with pytest.raises(ValueError):
        WeavzClient(**{"api_key": "wvz_test", **kwargs})


def test_hosted_connect_sends_configured_frontend_origin_without_mutating_headers(client_factory):
    requests = []
    headers = {"Origin": "https://app.example.com", "X-Example": "configured"}
    client = client_factory(lambda req: (requests.append(req), httpx.Response(200, json={}))[1], headers=headers)
    headers["Origin"] = "https://changed.example.com"
    headers["X-Example"] = "changed"
    client.connect.create_token(integration_name="slack", connection_name="Example", external_id="account", workspace_id="workspace")
    assert requests[0].headers["origin"] == "https://app.example.com"
    assert requests[0].headers["x-example"] == "configured"
    assert requests[0].headers["authorization"] == "Bearer wvz_test"


@pytest.mark.parametrize("name", ["Authorization", "authorization", "AUTHORIZATION"])
def test_custom_headers_cannot_override_api_key_case_insensitively(client_factory, name):
    requests = []
    headers = {"Authorization": "global-one", "authorization": "global-two", "AUTHORIZATION": "global-three", "Origin": "https://app.example.com"}
    original = headers.copy()
    client = client_factory(lambda req: (requests.append(req), httpx.Response(200, json={}))[1], headers=headers)
    assert client._http.headers.get_list("Authorization") == ["Bearer wvz_test"]
    client.workspaces.list()
    request_headers = {name: "request-override", "X-Example": "request"}
    client.request("GET", "/api/v1/workspaces", headers=request_headers)
    assert headers == original and request_headers == {name: "request-override", "X-Example": "request"}
    for request in requests:
        assert request.headers.get_list("Authorization") == ["Bearer wvz_test"]
        assert request.headers["origin"] == "https://app.example.com"
    assert requests[-1].headers["x-example"] == "request"


@pytest.mark.parametrize("path", ["https://other.example/api", "//other.example/api", "http://api.example.com/api"])
def test_never_send_credentials_to_another_origin(client_factory, path):
    handler = Mock()
    client = client_factory(handler)
    with pytest.raises(ValueError, match="configured API origin"):
        client.request("GET", path)
    handler.assert_not_called()


def test_resource_identifiers_and_query_serialization(client_factory):
    requests = []
    client = client_factory(lambda req: (requests.append(req), httpx.Response(200, json={}))[1])
    client.workspaces.get("id/?# space")
    client.workspaces.list(include_suspended=True, offset=0)
    assert requests[0].url.raw_path == b"/api/v1/workspaces/id%2F%3F%23%20space"
    assert requests[0].url.query == b""
    assert requests[1].url.params["includeSuspended"] == "true"
    assert requests[1].url.params["offset"] == "0"
    assert requests[0].headers["authorization"] == "Bearer wvz_test"
    with pytest.raises(ValueError):
        client.workspaces.get("..")


def test_network_retry_is_bounded_and_execution_is_not_replayed(client_factory, monkeypatch):
    calls, sleeps = [], []
    def handler(req):
        calls.append(req.method)
        raise httpx.ConnectError("offline")
    client = client_factory(handler, retries=2)
    monkeypatch.setattr("weavz_sdk.client.time.sleep", sleeps.append)
    with pytest.raises(WeavzError) as exc:
        client.workspaces.list()
    assert exc.value.code == "NETWORK_ERROR" and exc.value.details is None
    assert len(calls) == 3 and sleeps == [0.5, 1.0]
    calls.clear()
    sleeps.clear()
    with pytest.raises(WeavzError):
        client.actions.execute("http", "send_request", workspace_id="workspace", input={})
    assert calls == ["POST"] and sleeps == []


def test_timeout_uses_sdk_error(client_factory):
    def handler(req):
        raise httpx.ReadTimeout("Timed out", request=req)
    client = client_factory(handler)
    with pytest.raises(WeavzError) as exc:
        client.workspaces.list()
    assert exc.value.code == "TIMEOUT" and exc.value.status == 0


@pytest.mark.parametrize("operation", [
    lambda client: client.workspaces.create(name="Example", slug="example"),
    lambda client: client.actions.execute("http", "send_request", workspace_id="workspace"),
    lambda client: client.connect.create_token(integration_name="slack", connection_name="Example", external_id="account", workspace_id="workspace"),
])
def test_post_server_errors_are_not_replayed(client_factory, monkeypatch, operation):
    calls, sleeps = [], []
    client = client_factory(lambda req: (calls.append(req), httpx.Response(503, json={"error": "Unavailable"}))[1], retries=2)
    monkeypatch.setattr("weavz_sdk.client.time.sleep", sleeps.append)
    with pytest.raises(WeavzError) as exc:
        operation(client)
    assert exc.value.status == 503 and len(calls) == 1 and sleeps == []


def test_action_rate_limit_can_retry_without_changing_the_request(client_factory, monkeypatch):
    calls = []
    def handler(req):
        calls.append(req)
        return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "Rate limited", "code": "RATE_LIMITED"}) if len(calls) == 1 else httpx.Response(200, json={"success": True, "output": "ok"})
    client = client_factory(handler, retries=1)
    monkeypatch.setattr("weavz_sdk.client.time.sleep", lambda _: None)
    assert client.actions.execute("http", "send_request", workspace_id="workspace", idempotency_key="request") == {"success": True, "output": "ok"}
    assert len(calls) == 2 and calls[0].content == calls[1].content


@pytest.mark.parametrize("value,expected", [("NaN", .5), ("inf", .5), ("-1", .5), ("bad", .5), ("0", 0), ("100000", 60)])
def test_retry_after_is_finite_and_bounded(client_factory, monkeypatch, value, expected):
    calls, sleeps = [], []
    def handler(req):
        calls.append(req)
        return httpx.Response(429, headers={"Retry-After": value}, json={"error": "Rate limited"}) if len(calls) == 1 else httpx.Response(200, json={"ok": True})
    client = client_factory(handler, retries=1)
    monkeypatch.setattr("weavz_sdk.client.time.sleep", sleeps.append)
    assert client.workspaces.list() == {"ok": True} and sleeps == [expected]


def test_invalid_json_is_an_sdk_error(client_factory):
    client = client_factory(lambda req: httpx.Response(200, text="not-json"))
    with pytest.raises(WeavzError) as exc:
        client.workspaces.list()
    assert exc.value.code == "INVALID_RESPONSE" and exc.value.status == 200


def test_error_shape_and_empty_success(client_factory):
    responses = iter([httpx.Response(400, headers={"Content-Type": "Application/Problem+JSON"}, json={"error": None, "code": None}), httpx.Response(204)])
    client = client_factory(lambda req: next(responses))
    with pytest.raises(WeavzError) as exc:
        client.workspaces.list()
    assert exc.value.code == "HTTP_ERROR" and str(exc.value) == "HTTP 400"
    assert client.workspaces.delete("workspace") is None


def test_nullable_patches_distinguish_omitted_and_null(client_factory):
    bodies = []
    client = client_factory(lambda req: (bodies.append(json.loads(req.content)), httpx.Response(200, json={}))[1])
    client.workspaces.update_integration("workspace", "integration", connection_id=None, enabled_actions=None, display_name=None, settings=None, oauth_app_id=None, oauth_app_mode=None)
    assert bodies[-1] == {"connectionId": None, "enabledActions": None, "displayName": None, "settings": None, "oauthAppId": None, "oauthAppMode": None}
    client.workspaces.update_integration("workspace", "integration")
    assert bodies[-1] == {}
    client.partials.update("partial", description=None, values={})
    assert bodies[-1] == {"description": None, "values": {}}
    client.end_users.update("customer", display_name=None, email=None, metadata=None)
    assert bodies[-1] == {"displayName": None, "email": None, "metadata": None}
    client.end_users.update("customer")
    assert bodies[-1] == {}


def test_pydantic_input_preserves_explicit_null_and_json_values(client_factory):
    class Input(BaseModel):
        sent_at: datetime = Field(alias="sentAt")
        nullable: str | None = None
        omitted: str | None = None
    bodies = []
    client = client_factory(lambda req: (bodies.append(json.loads(req.content)), httpx.Response(200, json={}))[1])
    client.actions.execute("custom", "send", workspace_id="workspace", input=Input(sentAt=datetime(2026, 1, 1, tzinfo=timezone.utc), nullable=None))
    assert bodies[-1]["input"] == {"sentAt": "2026-01-01T00:00:00Z", "nullable": None}


def test_workspace_model_keeps_current_auth_metadata():
    obj = WorkspaceIntegration.model_validate({"id": "integration", "workspaceId": "workspace", "integrationName": "slack", "alias": "support_slack", "connectionStrategy": "per_user", "authMethodKey": "bot", "oauthAppMode": "custom", "oauthAppId": "app", "connectionExternalId": "connection", "createdAt": "2026-01-01", "updatedAt": "2026-01-01"})
    assert obj.auth_method_key == "bot" and obj.connection_external_id == "connection"
    assert obj.model_dump(by_alias=True)["oauthAppId"] == "app"


@pytest.mark.parametrize("resource,path,terminal", [("connect", "/api/v1/connect/session/poll", {"status": "COMPLETED"}), ("approvals", "/api/v1/approvals/approval", {"approval": {"status": "approved"}})])
def test_wait_uses_remaining_io_budget(client_factory, resource, path, terminal):
    requests = []
    client = client_factory(lambda req: (requests.append(req), httpx.Response(200, json=terminal))[1])
    assert getattr(client, resource).wait("approval", timeout=0.1, interval=0.01) == terminal
    assert requests[0].url.path == path and 0 < requests[0].extensions["timeout"]["read"] <= 0.1


def test_wait_validation_and_deadline(client_factory, monkeypatch):
    now = [0.0]
    def handler(req):
        now[0] += 0.2
        return httpx.Response(200, json={"status": "PENDING"})
    client = client_factory(handler)
    monkeypatch.setattr("weavz_sdk.client.time.monotonic", lambda: now[0])
    monkeypatch.setattr("weavz_sdk.client.time.sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    with pytest.raises(WeavzError) as exc:
        client.connect.wait("token", timeout=0.5, interval=10)
    assert exc.value.code == "CONNECT_TIMEOUT" and now[0] == .5
    with pytest.raises(ValueError):
        client.connect.wait("token", interval=float("nan"))


def test_array_schema_places_enum_on_items():
    schema = props_to_json_schema({"colors": {"type": "STATIC_MULTI_SELECT_DROPDOWN", "required": True, "options": {"options": [{"value": "red"}, {"value": "blue"}]}}, "rows": {"type": "ARRAY"}})
    assert schema["properties"]["colors"]["items"] == {"enum": ["red", "blue"], "type": "string"}
    assert "enum" not in schema["properties"]["colors"] and schema["properties"]["rows"]["items"] == {}
    tool = WeavzActionTool("choose_colors", "Choose colors", schema, "example", "select", lambda _: {})
    converted = _langchain_args_schema(tool).model_json_schema()
    assert converted["properties"]["colors"]["items"]["enum"] == ["red", "blue"]


def test_mcp_adapter_keeps_bindings_defaults_and_caches(client_factory):
    requests = []
    def handler(req):
        requests.append(req)
        if req.url.path.endswith("/servers/server"):
            return httpx.Response(200, json={"server": {"workspaceId": "workspace", "endUserId": "customer"}, "tools": [{"toolType": "ACTION", "integrationName": "slack", "integrationAlias": "support_slack", "actionName": name, "connectionId": "connection", "inputDefaults": {"channel": "default-channel"}} for name in ["one", "two"]]})
        if req.url.path == "/api/v1/connections":
            return httpx.Response(200, json={"connection": {"integrationName": "slack", "externalId": "support-account", "authMethodKey": "bot", "workspaceId": "workspace", "endUserId": "customer"}})
        if req.url.path == "/api/v1/integrations":
            return httpx.Response(200, json={"integration": {"actions": {name: {"props": {"channel": {"required": True}}} for name in ["one", "two"]}}})
        return httpx.Response(200, json={"success": True, "output": "ok"})
    client = client_factory(handler)
    tools = create_mcp_server_action_tools(client, "server")
    assert tools[0].input_schema["required"] == []
    assert tools[0].execute({"channel": "caller-channel"})["output"] == "ok"
    body = json.loads(requests[-1].content)
    assert body["endUserId"] == "customer" and body["connectionExternalId"] == "support-account" and body["authMethodKey"] == "bot"
    assert body["integrationAlias"] == "support_slack" and body["input"] == {"channel": "caller-channel"}
    assert sum(req.url.path == "/api/v1/integrations" for req in requests) == 1
    assert sum(req.url.path == "/api/v1/connections" for req in requests) == 1


@pytest.mark.parametrize("connection", [{"integrationName": "slack", "workspaceId": "other"}, {"integrationName": "slack", "workspaceId": "workspace", "endUserId": "other"}, {"integrationName": "other"}])
def test_mcp_adapter_rejects_unrepresentable_credentials(connection):
    client = SimpleNamespace(mcp_servers=SimpleNamespace(get=lambda _: {"server": {"workspaceId": "workspace", "endUserId": "customer"}, "tools": [{"toolType": "ACTION", "integrationName": "slack", "actionName": "one", "connectionId": "connection"}]}), integrations=SimpleNamespace(get=lambda _: {"integration": {"actions": {"one": {}}}}), connections=SimpleNamespace(get=lambda _: {"connection": connection}))
    with pytest.raises(ValueError, match="different|binding"):
        create_mcp_server_action_tools(client, "server")
    client.mcp_servers.get = lambda _: {"server": {"workspaceId": "workspace"}, "tools": [{"toolType": "ACTION", "integrationName": "slack", "actionName": "one", "connectionId": "connection"}]}
    client.connections.get = lambda _: {"connection": {"integrationName": "slack", "endUserId": "customer"}}
    with pytest.raises(ValueError, match="explicit end-user binding"):
        create_mcp_server_action_tools(client, "server")


def test_pending_approval_is_preserved_and_duplicate_dispatch_rejected():
    pending = {"success": False, "approval": {"status": "pending", "id": "approval"}}
    tool = WeavzActionTool("support_slack_send", "Send", {"properties": {}}, "slack", "send", lambda _: pending)
    assert to_google_adk_function(tool)() == pending
    with pytest.raises(ValueError, match="Duplicate tool name"):
        create_tool_executor([tool, tool])
    assert to_openai_responses_tool(tool)["strict"] is False
    assert to_openai_chat_tool(tool)["function"]["strict"] is False


def test_full_json_schema_survives_google_conversion():
    schema = props_to_json_schema({
        "choice": {"type": "STATIC_DROPDOWN", "options": {"options": [{"value": 1}, {"value": 2}]}},
        "rows": {"type": "ARRAY", "properties": {"count": {"type": "NUMBER", "required": True}}},
        "config": {"type": "OBJECT", "properties": {"enabled": {"type": "CHECKBOX"}}},
        "payload": {"type": "JSON"}, "dynamic": {"type": "DYNAMIC"}, "file": {"type": "FILE"},
    })
    assert schema["properties"]["choice"]["type"] == "number"
    assert schema["properties"]["rows"]["items"]["required"] == ["count"]
    assert schema["properties"]["config"]["properties"]["enabled"]["type"] == "boolean"
    assert schema["properties"]["payload"]["type"] == ["object", "array", "string", "number", "boolean", "null"]
    assert schema["properties"]["dynamic"]["type"] == "object" and schema["properties"]["file"]["type"] == ["string", "object"]
    tool = WeavzActionTool("process_rows", "Process rows", schema, "example", "process", lambda _: {})
    declaration = to_google_function_declaration(tool)
    assert declaration["parametersJsonSchema"] is schema and "parameters" not in declaration


def test_computer_human_access_preserves_external_identity_and_sensitive_fragment(client_factory):
    from weavz_sdk import ComputerSessionAccess, ComputerSessionAccessRole
    from typing import get_args, get_type_hints
    from weavz_sdk.client import ComputerSessionsResource
    requests = []
    response = {"sessionId": "session", "role": "control", "viewerUrl": "https://api.example.com/viewer#token=fixture-only", "expiresAt": "2030-01-01T00:00:00Z", "frameOrigin": "https://app.example.com"}
    client = client_factory(lambda request: (requests.append(request), httpx.Response(200, json=response))[1])
    result = client.computer_sessions.create_access("session/a?b#c", workspace_id="workspace", end_user_id="customer/alice@example.test", role="control", ttl_seconds=120, frame_origin="https://app.example.com:443")
    assert len(requests) == 1
    assert requests[0].url.raw_path == b"/api/v1/computer-sessions/session%2Fa%3Fb%23c/access"
    assert requests[0].headers["authorization"] == "Bearer wvz_test"
    assert json.loads(requests[0].content) == {"workspaceId": "workspace", "endUserId": "customer/alice@example.test", "role": "control", "ttlSeconds": 120, "frameOrigin": "https://app.example.com:443"}
    assert result == response
    assert get_type_hints(ComputerSessionsResource.create_access)["return"] is ComputerSessionAccess
    assert set(get_args(ComputerSessionAccessRole)) == {"watch", "control"}
    assert not any(hasattr(client.computer_sessions, name) for name in ("viewer", "stream", "control"))


def test_computer_access_omits_unset_options_and_requires_customer_scope(client_factory):
    requests = []
    client = client_factory(lambda request: (requests.append(request), httpx.Response(200, json={}))[1])
    client.computer_sessions.create_access("session", workspace_id="workspace", end_user_id="external-user", role="watch")
    assert json.loads(requests[0].content) == {"workspaceId": "workspace", "endUserId": "external-user", "role": "watch"}
    with pytest.raises(TypeError):
        client.computer_sessions.create_access("session", role="control")
    assert len(requests) == 1


def test_approval_history_cursor_null_workspace_and_review_access(client_factory):
    requests = []
    bodies = [{"approvals": [], "total": 0, "nextCursor": "next-page"}, {"policy": {}}, {"approval": {"reviewAccess": {"canDecide": False, "code": "APPROVAL_DECISION_SCOPE_REQUIRED"}}}]
    client = client_factory(lambda request: (requests.append(request), httpx.Response(200, json=bodies.pop(0)))[1])
    page = client.approvals.list(status="history", workspace_id="workspace", cursor="opaque+cursor/=", limit=2)
    assert requests[0].url.params["status"] == "history"
    assert requests[0].url.params["cursor"] == "opaque+cursor/="
    assert page["nextCursor"] == "next-page"
    client.approval_policies.update("policy", workspace_id=None)
    assert json.loads(requests[1].content) == {"workspaceId": None}
    assert client.approvals.get("approval")["approval"]["reviewAccess"]["canDecide"] is False
