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
)

# Create an MCP server
result = client.mcp_servers.create(name="My MCP Server", mode="TOOLS")
print(result["bearerToken"])
```

## Resources

The client provides namespaced access to all API resources:

| Resource | Methods |
|----------|---------|
| `client.projects` | `list()`, `create()`, `get()`, `delete()` |
| `client.connections` | `list()`, `create()`, `delete()`, `resolve()` |
| `client.actions` | `execute()` |
| `client.triggers` | `list()`, `enable()`, `disable()`, `test()` |
| `client.mcp_servers` | `list()`, `create()`, `get()`, `update()`, `delete()`, `regenerate_token()`, `add_tool()`, `update_tool()`, `delete_tool()`, `execute_code()` |
| `client.api_keys` | `list()`, `create()`, `delete()` |
| `client.members` | `list()`, `create()`, `update()`, `delete()` |
| `client.connection_policies` | `list()`, `create()`, `update()`, `delete()` |
| `client.pieces` | `list()`, `get()`, `resolve_options()`, `resolve_property()`, `oauth_status()` |
| `client.billing` | `plans()`, `plan()`, `usage()`, `addons()`, `purchase_addon()` |
| `client.activity` | `list()` |

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
