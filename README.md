# Weavz Python SDK

Official Python SDK for [Weavz](https://weavz.io), the stateful agent runtime for SaaS and AI products.

Weavz gives your product one API for connection management, end-user identity, hosted connect flows, action execution, triggers, MCP servers, Human Gates, input partials, Filesystem, State KV, Sandbox execution, and 500+ integrations.

## Links

- [Weavz](https://weavz.io)
- [Dashboard](https://dashboard.weavz.io)
- [Documentation](https://weavz.io/docs)
- [Python SDK docs](https://weavz.io/docs/sdks/python)
- [API reference](https://weavz.io/docs/api-reference)
- [Integration catalog](https://weavz.io/integrations)

## Installation

```bash
pip install weavz-io-sdk
```

The SDK supports Python 3.10 and newer.

```python
from weavz_sdk import WeavzClient

client = WeavzClient(api_key="wvz_your_api_key")
```

## What You Can Build

- Hosted OAuth and credential connection flows for your customers
- Multi-tenant workspaces with per-user, fixed, or fallback connection strategies
- Validated action execution across integrations such as Slack, GitHub, Google Sheets, HubSpot, Notion, Stripe, and more
- Remote MCP servers for Claude, ChatGPT, Codex, Cursor, and custom agents
- Code Mode MCP servers where agents search, inspect, and call workspace integrations dynamically
- Tool Mode MCP servers with a small explicit tool list
- Filesystem and State KV for durable files, checkpoints, cursors, and lightweight agent state
- Sandbox workflows that run JavaScript, Python, or Shell through the runtime
- Human Gates for approvals before sensitive actions run
- Input partials for defaults, locked fields, and reusable action configuration
- Triggers and webhooks that forward integration events into your product

## Quick Start

This example creates a workspace, enables a built-in integration, and executes an action through the SDK.

```python
from weavz_sdk import WeavzClient

client = WeavzClient(api_key="wvz_your_api_key")

workspace = client.workspaces.create(
    name="Production",
    slug="production",
)["workspace"]

client.workspaces.add_integration(
    workspace["id"],
    integration_name="hash-encode",
    integration_alias="hash",
)

result = client.actions.execute(
    "hash-encode",
    "hash",
    workspace_id=workspace["id"],
    integration_alias="hash",
    input={
        "text": "hello from weavz",
        "algorithm": "sha256",
        "encoding": "hex",
    },
)

if result["success"]:
    print(result["output"])

client.close()
```

For a guided Slack setup, see the [Quick Start](https://weavz.io/docs/getting-started/quick-start).

## Configuration

```python
client = WeavzClient(
    api_key="wvz_your_api_key",
    base_url="https://platform.weavz.io",
    timeout=310.0,
    max_retries=2,
)
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `api_key` | Yes | - | Weavz API key with the `wvz_` prefix |
| `base_url` | No | `https://platform.weavz.io` | API base URL |
| `timeout` | No | `310.0` | Request timeout in seconds |
| `max_retries` | No | `2` | Retry count for transient failures |

Use the context manager to close the underlying HTTP client automatically:

```python
with WeavzClient(api_key="wvz_your_api_key") as client:
    result = client.connections.list()
    print(result["connections"])
```

## Core Product Flows

### Workspaces And Integration Aliases

Workspaces scope connections, integration configuration, MCP servers, partials, triggers, and end-user access. Add integrations to a workspace under purpose-readable aliases so agents and logs show stable names.

```python
workspace = client.workspaces.create(
    name="Acme Customer",
    slug="acme-customer",
)["workspace"]

client.workspaces.add_integration(
    workspace["id"],
    integration_name="slack",
    integration_alias="customer_slack",
    connection_strategy="per_user",
    enabled_actions=["send_channel_message"],
)
```

Read more:

- [Organizations and workspaces](https://weavz.io/docs/concepts/organizations-and-workspaces)
- [Workspace integrations](https://weavz.io/docs/concepts/integration-selectors)
- [Integration aliases](https://weavz.io/docs/guides/integration-aliases)

### Hosted Connect

Create a hosted connect session when an end user needs to connect Slack, Google, GitHub, or another integration account.

```python
session = client.connect.create_token(
    integration_name="slack",
    connection_name="Acme Slack",
    external_id="acme_slack",
    workspace_id=workspace["id"],
    end_user_id="user_123",
)

print(f"Send the user here: {session['connectUrl']}")

completed = client.connect.wait(
    session["token"],
    timeout=120.0,
    interval=1.0,
)

if completed["status"] == "COMPLETED":
    print(completed["connectionId"])
```

Read more:

- [Connections](https://weavz.io/docs/concepts/connections)
- [Hosted connect API](https://weavz.io/docs/api-reference/oauth)
- [Setting up connections](https://weavz.io/docs/guides/setting-up-connections)

### Execute Actions

Execute integration actions directly from your backend or product workflows.

```python
run = client.actions.execute(
    "slack",
    "send_channel_message",
    workspace_id=workspace["id"],
    integration_alias="customer_slack",
    end_user_id="user_123",
    input={
        "channel": "#support",
        "text": "New customer escalation received.",
    },
    idempotency_key="ticket_123_notify_slack",
)

if run.get("status") == "approval_required":
    print("Approval required:", run["approval"]["id"])
else:
    print("Action output:", run["output"])
```

Read more:

- [Actions](https://weavz.io/docs/concepts/actions)
- [Executing actions](https://weavz.io/docs/guides/executing-actions)
- [Actions API reference](https://weavz.io/docs/api-reference/actions)

### MCP Servers For Agents

Create remote MCP servers that expose workspace integrations to AI agents. Code Mode is the best default for broad agent workspaces; Tool Mode is useful for small explicit tool surfaces.

```python
result = client.mcp_servers.create(
    name="Acme Agent Workspace",
    mode="CODE",
    workspace_id=workspace["id"],
    auth_mode="oauth_and_bearer",
    end_user_access="restricted",
    settings={
        "codeMode": {
            "approvalWaitSeconds": 30,
        },
    },
)

server = result["server"]
mcp_endpoint = result["mcpEndpoint"]

token_result = client.mcp_servers.create_bearer_token(
    server["id"],
    end_user_id="user_123",
    scopes=["mcp:tools", "mcp:code"],
    expires_in=60 * 60 * 24 * 30,
)

print(mcp_endpoint, token_result["bearerToken"])
```

You can also run Code Mode directly through the SDK:

```python
code_run = client.mcp_servers.execute_code(
    server["id"],
    """
const parsed = await weavz.datetime.parse_date({
  dateString: "June 18, 2026 9am",
  timezone: "America/New_York"
})

return { parsed }
""",
)
```

Code Mode responses include `structuredContent.timings` for total execution and per-action latency.
For Agent Browser workflows, batch several browser actions inside one Code Mode script instead of
calling `execute_code()` once per click or screenshot.

Read more:

- [MCP servers](https://weavz.io/docs/concepts/mcp-servers)
- [MCP Code Mode](https://weavz.io/docs/guides/mcp-code-mode)
- [MCP Tool Mode](https://weavz.io/docs/guides/mcp-tool-mode)
- [Weavz MCP App](https://weavz.io/docs/guides/weavz-mcp-app)

### Human Gates

Human Gates let you require approval before sensitive actions execute.

```python
policy = client.approval_policies.create(
    workspace_id=workspace["id"],
    name="Approve external messages",
    sources=["sdk", "mcp_code", "mcp_tools"],
    decision="require_approval",
    risk_mode="always",
    approvers=[{"type": "org_role", "roles": ["owner", "admin"]}],
    timeout_seconds=3600,
    default_on_timeout="reject",
    approval_access_mode="dashboard_and_hosted_link",
)["policy"]

guarded = client.actions.execute(
    "slack",
    "send_channel_message",
    workspace_id=workspace["id"],
    integration_alias="customer_slack",
    end_user_id="user_123",
    input={"channel": "#general", "text": "Launch update"},
)

if guarded.get("status") == "approval_required":
    client.approvals.approve(
        guarded["approval"]["id"],
        reason="Message reviewed",
    )
```

Read more:

- [Human Gates guide](https://weavz.io/docs/guides/human-gates)
- [Approvals API reference](https://weavz.io/docs/api-reference/approvals)

### Input Partials

Input partials let you reuse defaults and lock enforced fields so agents or callers only provide the fields they should control.

```python
partial = client.partials.create(
    workspace["id"],
    "slack",
    "Support channel default",
    action_name="send_channel_message",
    values={"channel": "#support"},
    enforced_keys=["channel"],
)["partial"]

client.actions.execute(
    "slack",
    "send_channel_message",
    workspace_id=workspace["id"],
    integration_alias="customer_slack",
    partial_ids=[partial["id"]],
    input={"text": "A new ticket needs attention."},
)
```

Read more:

- [Input partials](https://weavz.io/docs/concepts/input-partials)
- [Using input partials](https://weavz.io/docs/guides/using-input-partials)

### Triggers

Enable triggers to receive integration events in your own webhook endpoint.

```python
trigger = client.triggers.enable(
    integration_name="github",
    trigger_name="new_push",
    workspace_id=workspace["id"],
    integration_alias="customer_github",
    callback_url="https://yourapp.example.com/webhooks/weavz/github",
    callback_metadata={"customerId": "acme"},
)["triggerSource"]

print(trigger["id"])
```

Read more:

- [Triggers](https://weavz.io/docs/concepts/triggers)
- [Setting up triggers](https://weavz.io/docs/guides/setting-up-triggers)

## Generated Integration Input Models

The SDK includes generated Pydantic models and lookup helpers for integration action inputs.

```python
from weavz_sdk.integrations import (
    INTEGRATION_ACTIONS,
    SlackSendChannelMessageInput,
    get_action_names,
    validate_action_input,
)

print(get_action_names("slack"))
print(INTEGRATION_ACTIONS["slack"])

input_data = SlackSendChannelMessageInput(
    channel="#general",
    text="Typed input from Python",
)

validated = validate_action_input(
    "slack",
    "send_channel_message",
    input_data,
)

result = client.actions.execute_typed(
    "slack",
    "send_channel_message",
    workspace_id=workspace["id"],
    integration_alias="customer_slack",
    input=validated,
)
```

The model naming pattern is `{IntegrationName}{ActionName}Input` in PascalCase. Use `execute()` for dynamic or future integrations and `execute_typed()` when you want generated-model validation before the request is sent.

## AI Framework Adapters

MCP is the primary hosted agent surface. The SDK also includes small dependency-free adapters that convert configured workspace actions into common AI tool shapes.

```python
from weavz_sdk import (
    create_mcp_server_action_tools,
    to_anthropic_tool,
    to_openai_responses_tool,
)

tools = create_mcp_server_action_tools(client, server["id"])

openai_tools = [to_openai_responses_tool(tool) for tool in tools]
anthropic_tools = [to_anthropic_tool(tool) for tool in tools]
```

Optional framework adapters are created lazily when the matching package is installed.

## Resource Map

| Resource | Purpose |
| --- | --- |
| `client.workspaces` | Workspace management and workspace integrations |
| `client.connections` | Connection CRUD and resolution |
| `client.connect` | Hosted connect session creation, polling, and waiting |
| `client.actions` | Integration action execution and generated input validation |
| `client.triggers` | Trigger enablement, listing, testing, and disabling |
| `client.mcp_servers` | MCP servers, tools, tokens, Code Mode execution, declarations |
| `client.integrations` | Integration metadata, property options, OAuth status |
| `client.end_users` | End-user identity, connect tokens, invites |
| `client.partials` | Input partial presets and enforced fields |
| `client.approval_policies` | Human Gates policy management |
| `client.approvals` | Approval inbox, decisions, and waiting |
| `client.api_keys` | Customer-facing API key management |

## Error Handling

```python
from weavz_sdk import WeavzError

try:
    client.actions.execute(
        "slack",
        "send_channel_message",
        workspace_id=workspace["id"],
        integration_alias="customer_slack",
        input={"channel": "#general", "text": "Hello"},
    )
except WeavzError as error:
    print(error.code)
    print(error.status)
    print(error.details)
```

## Publishing And Development

This public repository is a release mirror. SDK development happens in the main Weavz monorepo under `sdks/python/`, then this repository is updated from that source directory for releases.

For local checks in this repository:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest
python -m pytest tests/test_generated_integrations.py
```

Live integration tests require a running Weavz API stack.

## License

[MIT](LICENSE)
