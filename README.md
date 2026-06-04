# weavz-sdk

Python SDK for the [Weavz](https://weavz.io) API — integration and MCP infrastructure for connection management, MCP servers, triggers, and action execution.

## Installation

```bash
pip install weavz-sdk
```

## Quick Start

```python
from weavz_sdk import WeavzClient

client = WeavzClient(api_key="wvz_your_api_key")
workspace_id = "550e8400-e29b-41d4-a716-446655440000"

# List connections
result = client.connections.list()
print(result["connections"])

# Expose configured Slack tools to MCP Code Mode through the `slack` alias
client.workspaces.add_integration(
    workspace_id,
    integration_name="slack",
    integration_alias="slack",
    connection_strategy="per_user",
)

# Execute an action through the configured alias
result = client.actions.execute(
    "slack",
    "send_channel_message",
    input={"channel": "#general", "text": "Hello from Weavz!"},
    workspace_id=workspace_id,
    integration_alias="slack",
)

# Create an OAuth-enabled MCP server
result = client.mcp_servers.create(
    name="My MCP Server",
    mode="CODE",
    workspace_id=workspace_id,
    auth_mode="oauth",
    settings={"codeMode": {"approvalWaitSeconds": 30}},
)
print(result["mcpEndpoint"])

# For provisioned clients, enable bearer auth and issue one token per end user:
bearer_server = client.mcp_servers.create(
    name="Provisioned MCP Server",
    mode="CODE",
    workspace_id=workspace_id,
    auth_mode="oauth_and_bearer",
)["server"]
bearer_token = client.mcp_servers.create_bearer_token(
    bearer_server["id"],
    end_user_id="user_123",
)["bearerToken"]

run = client.mcp_servers.execute_code(
    result["server"]["id"],
    'return await weavz.slack.send_channel_message({ channel: "C123", text: "Hello" })',
)

# If Human Gates returns approval_required, approve it and fetch the stored run:
approved = client.mcp_servers.execute_code(
    result["server"]["id"],
    approval_id="apr_9b36d3f761d84bb2b6f9a0c4b9d1f7e0",
    wait_for_approval_seconds=30,
)
```

## Resources

The client provides namespaced access to all API resources:

| Resource | Methods |
|----------|---------|
| `client.workspaces` | `list()`, `create()`, `get()`, `update()`, `delete()`, `list_integrations()`, `add_integration()`, `update_integration()`, `remove_integration()` |
| `client.connections` | `list()`, `get()`, `create()`, `delete()`, `resolve()` |
| `client.actions` | `execute()` |
| `client.triggers` | `list()`, `enable()`, `disable()`, `test()` |
| `client.mcp_servers` | `list()`, `create()`, `get()`, `update()`, `delete()`, `regenerate_token()`, `create_bearer_token()`, `create_access_token()`, `create_end_user_token()`, `create_oauth_token()`, `add_tool()`, `update_tool()`, `delete_tool()`, `execute_code()`, `get_declarations()` |
| `client.api_keys` | `list()`, `create()`, `delete()` |
| `client.integrations` | `list()`, `list_summary()`, `get()`, `resolve_options()`, `resolve_property()`, `oauth_status()` |
| `client.connect` | `create_token()`, `poll()`, `wait()`, `get_session()` |
| `client.end_users` | `create()`, `list()`, `get()`, `update()`, `delete()`, `create_connect_token()`, `invite()` |
| `client.partials` | `list()`, `get()`, `create()`, `update()`, `delete()`, `set_default()` |
| `client.approval_policies` | `list()`, `create()`, `get()`, `update()`, `delete()`, `test()` |
| `client.approvals` | `list()`, `get()`, `approve()`, `reject()`, `cancel()`, `wait()` |

## Building SaaS on Weavz

Org-wide API keys can provision the integration control plane for your own product: create workspaces, register end users, create hosted connect sessions, expose MCP servers, configure workspace integrations, and execute actions.

```python
workspace = client.workspaces.create(name="Production", slug="production")["workspace"]

client.workspaces.add_integration(
    workspace["id"],
    integration_name="slack",
    integration_alias="customer_slack",
    connection_strategy="per_user",
)
```

## AI Framework Adapters

MCP is the primary hosted agent surface. These adapters are a local compatibility layer for SaaS builders who need configured workspace actions as framework-native tools while keeping framework packages optional.

```python
from weavz_sdk import create_mcp_server_action_tools, to_openai_responses_tool, to_anthropic_tool, to_google_adk_tool

tools = create_mcp_server_action_tools(client, "660e8400-e29b-41d4-a716-446655440000")
openai_tools = [to_openai_responses_tool(tool) for tool in tools]
anthropic_tools = [to_anthropic_tool(tool) for tool in tools]
google_adk_tools = [to_google_adk_tool(tool) for tool in tools]  # Requires google-adk
```

## Error Handling

```python
from weavz_sdk import WeavzClient, WeavzError

client = WeavzClient(api_key="wvz_...")

try:
    client.actions.execute(
        "slack",
        "send_channel_message",
        workspace_id="550e8400-e29b-41d4-a716-446655440000",
        input={},
    )
except WeavzError as e:
    print(e.code)    # 'ACTION_FAILED'
    print(e.status)  # 400
    print(e.details) # additional context
```

## Context Manager

```python
with WeavzClient(api_key="wvz_...") as client:
    result = client.connections.list()
```

## License

MIT
