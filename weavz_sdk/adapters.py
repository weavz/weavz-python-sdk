"""Framework adapter helpers for turning Weavz actions into AI tools.

The helpers are dependency-free by default. Framework-specific objects are
created lazily only when the optional framework package is installed.
"""

from __future__ import annotations

import re
import inspect
import keyword
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import Field, create_model

from weavz_sdk.client import WeavzClient

JsonSchema = dict[str, Any]


@dataclass(frozen=True)
class WeavzActionTool:
    name: str
    description: str
    input_schema: JsonSchema
    integration_name: str
    action_name: str
    execute: Callable[[dict[str, Any]], Any]
    integration_alias: str | None = None


def _safe_tool_name(name: str) -> str:
    safe = re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9_-]", "_", name))
    if not re.match(r"^[a-zA-Z_]", safe):
        safe = f"_{safe}"
    return safe[:64]


def _safe_python_identifier(name: str) -> str:
    safe = re.sub(r"\W|^(?=\d)", "_", name)
    safe = re.sub(r"_+", "_", safe).strip("_") or "input"
    if keyword.iskeyword(safe):
        safe = f"{safe}_"
    return safe


def _map_property_type(prop_type: str | None) -> str | list[str]:
    if prop_type == "NUMBER":
        return "number"
    if prop_type == "CHECKBOX":
        return "boolean"
    if prop_type in {"ARRAY", "STATIC_MULTI_SELECT_DROPDOWN", "MULTI_SELECT_DROPDOWN"}:
        return "array"
    if prop_type == "JSON":
        return ["object", "array", "string", "number", "boolean", "null"]
    if prop_type == "FILE":
        return ["string", "object"]
    if prop_type in {"OBJECT", "DYNAMIC", "CUSTOM_AUTH", "OAUTH2"}:
        return "object"
    return "string"


def props_to_json_schema(props: dict[str, Any] | None = None) -> JsonSchema:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, prop_value in (props or {}).items():
        prop = prop_value if isinstance(prop_value, dict) else {}
        schema: dict[str, Any] = {
            "type": _map_property_type(prop.get("type")),
            "description": prop.get("description") or prop.get("displayName") or name,
        }
        refreshers = prop.get("refreshers")
        if isinstance(refreshers, list) and refreshers:
            schema["description"] = f"{schema['description']}. Depends on: {', '.join(refreshers)}."

        options = prop.get("options")
        nested = prop.get("properties")
        if schema["type"] == "array":
            schema["items"] = props_to_json_schema(nested) if isinstance(nested, dict) and nested else {}
        elif schema["type"] == "object" and isinstance(nested, dict) and nested:
            schema.update(props_to_json_schema(nested))
        if isinstance(options, dict) and isinstance(options.get("options"), list):
            values = [option["value"] for option in options["options"] if isinstance(option, dict) and "value" in option]
            if values:
                target = schema["items"] if schema["type"] == "array" else schema
                target["enum"] = values
                types = []
                for value in values:
                    kind = ("null" if value is None else "boolean" if isinstance(value, bool) else "number" if isinstance(value, (int, float)) else "string" if isinstance(value, str) else "array" if isinstance(value, list) else "object")
                    if kind not in types:
                        types.append(kind)
                target["type"] = types[0] if len(types) == 1 else types

        properties[name] = schema
        if prop.get("required"):
            required.append(name)

    return {"type": "object", "properties": properties, "required": required}


def create_action_tool(
    client: WeavzClient,
    *,
    integration_name: str,
    action_name: str,
    workspace_id: str,
    integration_alias: str | None = None,
    connection_external_id: str | None = None,
    auth_method_key: str | None = None,
    end_user_id: str | None = None,
    input_defaults: dict[str, Any] | None = None,
    partial_ids: list[str] | None = None,
    name: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> WeavzActionTool:
    integration = metadata or client.integrations.get(integration_name)["integration"]
    action = integration.get("actions", {}).get(action_name)
    if not isinstance(action, dict):
        raise ValueError(f"Action not found: {integration_name}/{action_name}")

    tool_name = _safe_tool_name(name or f"{integration_alias or integration_name}__{action_name}")
    tool_description = (
        description
        or action.get("description")
        or f"{integration.get('displayName', integration_name)}: {action.get('displayName', action_name)}"
    )
    input_schema = props_to_json_schema(action.get("props"))

    defaults = dict(input_defaults or {})
    if defaults:
        input_schema["required"] = [key for key in input_schema["required"] if key not in defaults]

    def execute(input: dict[str, Any]) -> Any:
        return client.actions.execute(
            integration_name,
            action_name,
            workspace_id=workspace_id,
            input={**defaults, **input},
            connection_external_id=connection_external_id,
            auth_method_key=auth_method_key,
            end_user_id=end_user_id,
            integration_alias=integration_alias,
            partial_ids=partial_ids,
        )

    return WeavzActionTool(
        name=tool_name,
        description=tool_description,
        input_schema=input_schema,
        integration_name=integration_name,
        action_name=action_name,
        integration_alias=integration_alias,
        execute=execute,
    )


def create_mcp_server_action_tools(client: WeavzClient, server_id: str) -> list[WeavzActionTool]:
    """Build direct API tools from an MCP server's action configuration.

    Execution uses the SDK action API and its approval policies, rather than
    calling the MCP protocol or evaluating MCP-only approval sources.
    """
    payload = client.mcp_servers.get(server_id)
    server = payload["server"]
    workspace_id = server.get("workspaceId")
    if not workspace_id:
        raise ValueError("Adapter tools require an MCP server scoped to a workspace")

    metadata_by_integration: dict[str, dict[str, Any]] = {}
    connections_by_id: dict[str, dict[str, Any]] = {}
    tools: list[WeavzActionTool] = []
    for mcp_tool in payload.get("tools", []):
        if mcp_tool.get("toolType") != "ACTION":
            continue
        integration_name = mcp_tool["integrationName"]
        if integration_name not in metadata_by_integration:
            metadata_by_integration[integration_name] = client.integrations.get(integration_name)["integration"]
        connection = None
        connection_id = mcp_tool.get("connectionId")
        if connection_id:
            if connection_id not in connections_by_id:
                connections_by_id[connection_id] = client.connections.get(connection_id)["connection"]
            connection = connections_by_id[connection_id]
            if connection.get("integrationName") != integration_name:
                raise ValueError("The MCP tool connection belongs to a different integration")
            if connection.get("workspaceId") not in (None, workspace_id):
                raise ValueError("The MCP tool connection belongs to a different workspace")
            if connection.get("endUserId") and connection["endUserId"] != server.get("endUserId"):
                raise ValueError("The MCP tool connection requires the same explicit end-user binding as the server")
        tools.append(
            create_action_tool(
                client,
                integration_name=integration_name,
                action_name=mcp_tool["actionName"],
                workspace_id=workspace_id,
                integration_alias=mcp_tool.get("integrationAlias"),
                connection_external_id=connection.get("externalId") if connection else None,
                auth_method_key=connection.get("authMethodKey") if connection else None,
                end_user_id=server.get("endUserId") or None,
                input_defaults=mcp_tool.get("inputDefaults") or None,
                partial_ids=mcp_tool.get("partialIds") or None,
                name=f"{mcp_tool.get('integrationAlias') or integration_name}__{mcp_tool['actionName']}",
                description=mcp_tool.get("description") or None,
                metadata=metadata_by_integration[integration_name],
            )
        )
    _tools_by_name(tools)
    return tools


def _action_tool_output(result: Any) -> Any:
    return result["output"] if isinstance(result, dict) and "output" in result else result


def _tools_by_name(tools: list[WeavzActionTool]) -> dict[str, WeavzActionTool]:
    by_name: dict[str, WeavzActionTool] = {}
    for tool in tools:
        if tool.name in by_name:
            raise ValueError(f"Duplicate tool name: {tool.name}")
        by_name[tool.name] = tool
    return by_name


def to_openai_responses_tool(tool: WeavzActionTool) -> dict[str, Any]:
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.input_schema,
        "strict": False,
    }


def to_openai_chat_tool(tool: WeavzActionTool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
            "strict": False,
        },
    }


def to_anthropic_tool(tool: WeavzActionTool) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
    }


def to_google_function_declaration(tool: WeavzActionTool) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "parametersJsonSchema": tool.input_schema,
    }


def _python_type_from_schema(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        return Any
    if schema_type == "boolean":
        return bool
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "array":
        return list[Any]
    if schema_type == "object":
        return dict[str, Any]
    return str


def _langchain_args_schema(tool: WeavzActionTool) -> Any:
    properties = tool.input_schema.get("properties") or {}
    required = set(tool.input_schema.get("required") or [])
    fields: dict[str, tuple[Any, Any]] = {}

    for name, raw_schema in properties.items():
        prop_schema = raw_schema if isinstance(raw_schema, dict) else {}
        annotation = _python_type_from_schema(prop_schema)
        default = ... if name in required else None
        fields[name] = (annotation, Field(
            default=default,
            description=prop_schema.get("description"),
            json_schema_extra={key: value for key, value in prop_schema.items() if key != "description"},
        ))

    model_name = re.sub(r"[^A-Za-z0-9]", "", tool.name.title()) or "WeavzTool"
    if model_name[0].isdigit():
        model_name = f"Weavz{model_name}"
    return create_model(f"{model_name}Input", **fields)


def to_google_adk_function(tool: WeavzActionTool) -> Callable[..., Any]:
    """Return a callable that Google ADK can wrap as a FunctionTool.

    The generated callable exposes a real inspect.Signature so ADK can infer
    the function schema while execution still routes through Weavz.
    """
    properties = tool.input_schema.get("properties") or {}
    required = set(tool.input_schema.get("required") or [])
    parameters: list[inspect.Parameter] = []
    aliases: dict[str, str] = {}

    for original_name, raw_schema in properties.items():
        prop_schema = raw_schema if isinstance(raw_schema, dict) else {}
        param_name = _safe_python_identifier(original_name)
        base_name = param_name
        suffix = 2
        while param_name in aliases:
            param_name = f"{base_name}_{suffix}"
            suffix += 1
        aliases[param_name] = original_name
        parameters.append(
            inspect.Parameter(
                param_name,
                inspect.Parameter.KEYWORD_ONLY,
                default=inspect._empty if original_name in required else None,
                annotation=_python_type_from_schema(prop_schema),
            )
        )

    def run(**kwargs: Any) -> Any:
        input_payload = {
            original_name: kwargs[param_name]
            for param_name, original_name in aliases.items()
            if param_name in kwargs and kwargs[param_name] is not None
        }
        result = tool.execute(input_payload)
        return _action_tool_output(result)

    run.__name__ = _safe_python_identifier(tool.name)
    run.__doc__ = tool.description
    run.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    return run


def to_google_adk_tool(tool: WeavzActionTool) -> Any:
    try:
        from google.adk.tools import FunctionTool
    except ImportError as exc:
        raise ImportError("Install google-adk to create Google ADK FunctionTool instances") from exc

    return FunctionTool(func=to_google_adk_function(tool))


def to_langchain_tool(tool: WeavzActionTool) -> Any:
    try:
        from langchain_core.tools import StructuredTool
    except ImportError as exc:
        raise ImportError("Install langchain-core to create LangChain tools") from exc

    return StructuredTool.from_function(
        name=tool.name,
        description=tool.description,
        args_schema=_langchain_args_schema(tool),
        func=lambda **kwargs: _action_tool_output(tool.execute(kwargs)),
    )


def create_tool_executor(tools: list[WeavzActionTool]) -> Callable[[str, dict[str, Any]], Any]:
    by_name = _tools_by_name(tools)

    def execute(name: str, input: dict[str, Any]) -> Any:
        if name not in by_name:
            raise ValueError(f"Unknown tool: {name}")
        return by_name[name].execute(input)

    return execute
