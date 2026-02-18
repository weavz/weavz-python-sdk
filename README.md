# weavz-sdk

Python SDK for the [Weavz](https://weavz.io) API — an embedded iPaaS for connection management, MCP servers, triggers, and action execution.

## Installation

```bash
pip install weavz-sdk
```

## Quick Start

```python
from weavz_sdk import WeavzClient

client = WeavzClient(api_key="wvz_your_api_key")

# List connections
result = client.connections.list()
print(result["connections"])

# Execute an action
result = client.actions.execute(
    "slack",
    "send_channel_message",
    input={"channel": "#general", "text": "Hello from Weavz!"},
    connection_external_id="my-slack",
    workspace_id="your-workspace-id",
)

# Create an MCP server
result = client.mcp_servers.create(
    name="My MCP Server",
    mode="TOOLS",
    workspace_id="your-workspace-id",
)
print(result["bearerToken"])
```

## Resources

The client provides namespaced access to all API resources:

| Resource | Methods |
|----------|---------|
| `client.workspaces` | `list()`, `create()`, `get()`, `delete()`, `list_integrations()`, `add_integration()`, `update_integration()`, `remove_integration()` |
| `client.connections` | `list()`, `create()`, `delete()`, `resolve()` |
| `client.actions` | `execute()` |
| `client.triggers` | `list()`, `enable()`, `disable()`, `test()` |
| `client.mcp_servers` | `list()`, `create()`, `get()`, `update()`, `delete()`, `regenerate_token()`, `add_tool()`, `update_tool()`, `delete_tool()`, `execute_code()` |
| `client.api_keys` | `list()`, `create()`, `delete()` |
| `client.members` | `list()`, `create()`, `update()`, `delete()` |
| `client.integrations` | `list()`, `get()`, `resolve_options()`, `resolve_property()`, `oauth_status()` |
| `client.end_users` | `create()`, `list()`, `get()`, `update()`, `delete()`, `create_connect_token()`, `invite()` |
| `client.partials` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.invitations` | `send()`, `list()`, `revoke()`, `accept()` |

## Error Handling

```python
from weavz_sdk import WeavzClient, WeavzError

client = WeavzClient(api_key="wvz_...")

try:
    client.actions.execute("slack", "send_channel_message", input={})
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
