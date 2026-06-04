from __future__ import annotations

import pytest
from pydantic import ValidationError

from weavz_sdk import WeavzClient
from weavz_sdk.integrations import (
    HttpSendRequestInput,
    get_action_input_model,
    get_action_names,
    require_action_input_model,
    validate_action_input,
)


def test_generated_action_lookup_helpers() -> None:
    assert "send_request" in get_action_names("http")
    assert get_action_input_model("http", "send_request") is HttpSendRequestInput
    assert require_action_input_model("http", "send_request") is HttpSendRequestInput


def test_generated_action_validation_returns_pydantic_model() -> None:
    validated = validate_action_input(
        "http",
        "send_request",
        {
            "method": "GET",
            "url": "https://example.com",
            "headers": {},
            "queryParams": {},
            "authType": "NONE",
        },
    )

    assert isinstance(validated, HttpSendRequestInput)
    assert validated.model_dump(by_alias=True)["method"] == "GET"


def test_generated_action_validation_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        validate_action_input("http", "send_request", {"method": "GET"})


def test_python_client_execute_typed_validates_before_post(monkeypatch: pytest.MonkeyPatch) -> None:
    client = WeavzClient(api_key="wvz_test", base_url="http://example.invalid")
    captured: dict[str, object] = {}

    def fake_post(path: str, json: object = None, headers: dict[str, str] | None = None) -> dict[str, bool]:
        captured["path"] = path
        captured["json"] = json
        captured["headers"] = headers
        return {"ok": True}

    monkeypatch.setattr(client.actions, "_post", fake_post)

    try:
        result = client.actions.execute_typed(
            "http",
            "send_request",
            workspace_id="00000000-0000-0000-0000-000000000000",
            input=HttpSendRequestInput(
                method="GET",
                url="https://example.com",
                headers={},
                queryParams={},
                authType="NONE",
            ),
        )
    finally:
        client.close()

    assert result == {"ok": True}
    assert captured["path"] == "/api/v1/actions/execute"
    assert captured["headers"] == {"X-Weavz-Source": "sdk"}
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["integrationName"] == "http"
    assert body["actionName"] == "send_request"
    assert body["input"]["method"] == "GET"
