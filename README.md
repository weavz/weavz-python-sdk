# Weavz Python SDK

[![PyPI version](https://img.shields.io/pypi/v/weavz-io-sdk?label=PyPI)](https://pypi.org/project/weavz-io-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/weavz-io-sdk)](https://pypi.org/project/weavz-io-sdk/)
[![PyPI downloads](https://img.shields.io/pypi/dm/weavz-io-sdk?label=downloads)](https://pypi.org/project/weavz-io-sdk/)
[![GitHub release](https://img.shields.io/github/v/release/weavz/weavz-python-sdk?label=release)](https://github.com/weavz/weavz-python-sdk/releases)
[![Release workflow](https://github.com/weavz/weavz-python-sdk/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/weavz/weavz-python-sdk/actions/workflows/release.yml)
[![License](https://img.shields.io/pypi/l/weavz-io-sdk?label=license)](https://github.com/weavz/weavz-python-sdk/blob/main/LICENSE)

Official Python SDK for [Weavz](https://weavz.io), governed app access for SaaS and AI products.

Weavz gives your product one API for connection management, end-user identity, hosted connect flows, action execution, triggers, MCP servers, approval rules, saved inputs, Filesystem, State KV, Sandbox execution, and 1,000+ integrations.

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
- Approval rules for review before selected actions run
- Saved inputs for reusable action values, with optional advanced defaults and locked fields
- Triggers and webhooks that forward integration events into your product

## Quick Start

This example creates a workspace and writes a file to its shared Filesystem. Use end-user scope when files should be private to each user.

```python
from weavz_sdk import WeavzClient

client = WeavzClient(api_key="wvz_your_api_key")

workspace = client.workspaces.create(
    name="Production",
    slug="production",
)["workspace"]

client.workspaces.add_integration(
    workspace["id"],
    integration_name="storage",
    integration_alias="files",
    connection_strategy="fixed",
    settings={"persistence": {"scope": "workspace"}},
)

result = client.actions.execute_typed(
    "storage",
    "write_file",
    workspace_id=workspace["id"],
    integration_alias="files",
    input={
        "path": "hello.txt",
        "content": "Hello from Weavz",
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
    headers={"Origin": "https://app.example.com"},
)
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `api_key` | Yes | - | Weavz API key with the `wvz_` prefix |
| `base_url` | No | `https://platform.weavz.io` | API base URL |
| `timeout` | No | `310.0` | Positive finite timeout in seconds for connection and request I/O |
| `max_retries` | No | `2` | Non-negative retry count for rate limits and retryable read/update failures |
| `headers` | No | `None` | Additional HTTP headers. The configured API-key authorization is preserved. |

Network failures and server errors do not automatically replay action-execution POST requests. Rate-limit responses can be retried. Retry delays are bounded to 60 seconds. `connect.wait()` and `approvals.wait()` validate their polling settings, cap each request's I/O timeout to the remaining polling budget, and stop polling at the deadline.

Successful responses containing invalid JSON raise `WeavzError` with code `INVALID_RESPONSE`. Network timeouts use `TIMEOUT`; other transport failures use `NETWORK_ERROR`. Raw requests must use the configured API origin so API credentials are not sent to another service.

Use the context manager to close the underlying HTTP client automatically:

```python
with WeavzClient(api_key="wvz_your_api_key") as client:
    result = client.connections.list()
    print(result["connections"])
```

## MCP Workspaces

An MCP Workspace includes one endpoint automatically. Add apps, choose whose accounts they use, then connect an AI client. No separate server creation is needed. New endpoints use Code Mode and OAuth, admit organization members and pre-added end users, and do not default to the creator's private credentials.

```python
workspace = client.mcp_workspaces.create(name="Support")["workspace"]
endpoint = workspace["mcpServer"]["mcpEndpoint"]

# Optional: intentionally change endpoint settings.
client.mcp_workspaces.configure_mcp(workspace["id"], mode="TOOLS")
```

The existing `workspaces` resource remains an alias. Several end users can share an endpoint with separate OAuth sessions or scoped access tokens. Existing endpoint URLs and permissions remain valid; older additional endpoints are compatibility connections. Use a separate MCP Workspace for a separate tool surface. Primary endpoint deletion is blocked; delete its workspace explicitly when that is intended.

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

For nullable update fields, omit the argument to leave it unchanged, or pass `None` to clear it:

```python
# Replace these IDs with the integration and end user you want to update.
integration_id = "00000000-0000-4000-8000-000000000001"
end_user_id = "00000000-0000-4000-8000-000000000002"
client.workspaces.update_integration(
    workspace["id"],
    integration_id,
    display_name=None,
    enabled_actions=None,
)
client.end_users.update(end_user_id, email=None)
```

Pydantic action inputs serialize aliases and JSON-compatible values, including dates. Fields explicitly set to `None` remain JSON `null`; fields not set are omitted.

### Hosted Connect

Create a hosted connect session on your backend when an end user needs to connect Slack, Google, GitHub, or another integration account. Keep your API key on the backend. Set `Origin` to a fixed frontend origin from your application's allowlist so OAuth completion messages return to your app. Return the connect URL only to the end user authorized for that connection, and open it from their **Connect** click.

```python
with WeavzClient(
    api_key="wvz_your_api_key",
    headers={"Origin": "https://app.example.com"},
) as connect_client:
    session = connect_client.connect.create_token(
        integration_name="slack",
        connection_name="Acme Slack",
        external_id="acme_slack",
        workspace_id=workspace["id"],
        end_user_id="user_123",
    )

    print(f"Send the user here: {session['connectUrl']}")

    completed = connect_client.connect.wait(
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

### MCP Workspaces For Agents

Each MCP Workspace includes an endpoint. Connect an OAuth-capable client to its URL. For a programmatic agent, issue private access for an existing external end user:

```python
access = client.mcp_workspaces.create_access_token(
    workspace["id"], end_user_id="user_123",
    scopes=["mcp:tools", "mcp:code"], expires_in=60 * 60,
)
# Deliver access["mcpEndpoint"] and access["accessToken"] privately to this user's agent.
# Send accessToken as Authorization: Bearer to the MCP endpoint.
```

You can also run Code Mode directly through the SDK:

```python
code_run = client.mcp_servers.execute_code(
    workspace["mcpServer"]["id"],
    """
return await weavz.files.write_file({
  path: "summary.json",
  content: JSON.stringify({ status: "ready" })
})
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

### Approval Rules

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

- [Approval rules guide](https://weavz.io/docs/guides/human-gates)
- [Approvals API reference](https://weavz.io/docs/api-reference/approvals)

### Saved Inputs

Saved inputs reuse action values. They are optional and manually selected by default; use advanced locking only when a field must not be overridden. SDK names remain `partials`.

```python
partial = client.partials.create(
    workspace["id"],
    "slack",
    "Support channel",
    integration_alias="customer_slack",
    action_name="send_channel_message",
    values={"channel": "C0123456789"},
    enforced_keys=[],
    is_default=False,
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

MCP-derived action tools retain the server's end-user binding, explicit connection selection, aliases, partials, and input defaults. They execute through the SDK action API and its approval policies; they do not call the MCP protocol or evaluate policies restricted to MCP sources. Pending approval responses remain available to your agent. Duplicate tool names are rejected rather than dispatching to the wrong action.


MCP is the primary hosted agent access path. The SDK also includes small dependency-free adapters that convert configured workspace actions into common AI tool shapes.

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

## Skills

Skills store optional reusable task instructions. Search returns metadata; get a selected skill to read its instructions. Saving a skill does not execute it or grant app access.

```python
workspace_id = "11111111-1111-4111-8111-111111111111"
created = client.skills.create(
    workspace_id,
    "customer-call-brief",
    "Prepare a customer call brief",
    "# Customer call brief\nSummarize the connected records and cite sources.",
    end_user_id="customer_123",
)
matches = client.skills.search(workspace_id, "brief", end_user_id="customer_123")
selected = client.skills.get(created.skill.id, workspace_id, end_user_id="customer_123")
client.skills.update(
    selected.skill.id,
    workspace_id,
    selected.skill.version,
    end_user_id="customer_123",
    description="Prepare a sourced brief before a customer meeting.",
)
```

For shared instructions, set `scope="workspace"` and omit `end_user_id`. Create a separate shared copy; an existing skill's owner and scope are immutable. Updates and deletion require the current version and return `SKILL_CONFLICT` for a stale version. See the [Skills guide](https://weavz.io/docs/guides/skills).

## Human Computer Access

Start and operate computers through [Computer Control actions](https://weavz.io/integrations/computer-control). For an existing session, your application backend can issue a short-lived link for a person to watch or take over.

Authenticate the person and authorize access to that session before issuing a link. Derive the workspace, session and external end-user ID from your application's validated user context. Keep the Weavz API key on your backend.

```python
access = client.computer_sessions.create_access(
    "7df5c03e-4df5-4b5f-95a7-5277d8f972db",
    workspace_id="550e8400-e29b-41d4-a716-446655440000",
    end_user_id="customer_123",
    role="watch",
    ttl_seconds=120,
    frame_origin="https://app.example.com",
)
# Deliver access["viewerUrl"] privately to the authorized browser.
```

`watch` allows observation. Use `control` for an authorized person to take over through the viewer; it does not grant agent tool control. Request a lifetime of 1–300 seconds; the link expires no later than the computer session. Omit `frame_origin` when opening the viewer directly; when embedding, provide the exact HTTPS origin without a path or wildcard.

`viewerUrl` is a sensitive credential. Preserve its fragment when opening it, deliver it only to the intended person, and keep it out of logs, analytics and agent or tool context. See the [Computer Control guide](https://weavz.io/docs/guides/computer-control) for setup, embedding and control handoff.

## Resource Map

| Resource | Purpose |
| --- | --- |
| `client.workspaces` | Workspace management and workspace integrations |
| `client.connections` | Connection CRUD and resolution |
| `client.connect` | Hosted connect session creation, polling, and waiting |
| `client.actions` | Integration action execution and generated input validation |
| `client.triggers` | Trigger enablement, listing, testing, and disabling |
| `client.mcp_servers` | MCP servers, tools, tokens, Code Mode execution, declarations |
| `client.skills` | Personal and shared task instructions, metadata search and versioned editing |
| `client.computer_sessions` | Short-lived human watch or control links for existing Computer Control sessions |
| `client.integrations` | Integration metadata, property options, OAuth status |
| `client.end_users` | End-user identity, connect tokens, invites |
| `client.partials` | Saved inputs and enforced fields |
| `client.approval_policies` | Approval rule management |
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

## Current capabilities in 0.3.0

The 0.3.0 SDK adds the Skills resource for optional, reusable task instructions and `client.computer_sessions.create_access()` for issuing a short-lived human watch or control link to an existing Computer Control session. Skills do not run tasks or grant app access; session access does not start or provision a computer. See [Skills](#skills) and [Human Computer Access](#human-computer-access) for setup and safe handling.

## Migrating to 0.2.0

Google function declarations now use `parametersJsonSchema` so JSON values, file inputs, nested arrays, and numeric choices keep their full schemas. Pass the returned declaration directly to Google GenAI. If your code reads the old `parameters` key, read `parametersJsonSchema` instead.

Nullable update arguments now distinguish omission from `None`: omit a field to leave it unchanged, or pass `None` to clear it. Pydantic action inputs retain explicit null values and omit fields not set by the caller. For actions whose required inputs are supplied by saved partials, use `execute()` so the API can apply them; `execute_typed()` validates the provided input against the complete generated action model before making a request.

MCP-derived adapters fail when a configured connection belongs to another integration, workspace or end user, or requires an end-user binding missing from the server. Set an explicit matching binding before creating the tools. They no longer silently fall back to another account.

## Testing

Run the offline client, adapter, and generated-model regressions:

```bash
python -m pip install -e . pytest
python -m pytest
```

Live integration suites are opt-in. Set `TEST_API_KEY` to an organization-scoped API key for a dedicated test organization and `TEST_API_URL` to its API URL. These suites create customer resources and clean up their own resources. They do not create an account or delete your supplied key. Without `TEST_API_KEY`, live suites are skipped while offline checks run.
