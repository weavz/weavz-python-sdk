"""Optional task instructions in a personal or shared workspace library."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from weavz_sdk.models import SkillListResponse, SkillResponse, SkillScope
if TYPE_CHECKING:
    from weavz_sdk.client import WeavzClient


def _library(workspace_id: str, scope: SkillScope, end_user_id: str | None) -> dict[str, Any]:
    if scope not in ("end_user", "workspace"):
        raise ValueError("scope must be end_user or workspace")
    if scope == "end_user" and not end_user_id:
        raise ValueError("end_user_id is required for a personal skill library; use your customer's external identity")
    if scope == "workspace" and end_user_id is not None:
        raise ValueError("A shared workspace skill library does not have an end-user owner selector")
    value: dict[str, Any] = {"workspaceId": workspace_id, "scope": scope}
    if end_user_id is not None:
        value["endUserId"] = end_user_id
    return value


def _path(skill_id: str) -> str:
    if skill_id in (".", ".."):
        raise ValueError("Resource identifiers cannot be dot segments")
    return "/api/v1/skills/" + quote(skill_id, safe="")


class SkillsResource:
    def __init__(self, client: WeavzClient) -> None:
        self._client = client

    def list(self, workspace_id: str, *, scope: SkillScope = "end_user", end_user_id: str | None = None,
             query: str | None = None, tag: str | None = None, include_disabled: bool = False,
             limit: int = 25, offset: int = 0) -> SkillListResponse:
        """List metadata only. Get a selected skill to read its instructions."""
        params = {**_library(workspace_id, scope, end_user_id), "includeDisabled": include_disabled, "limit": limit, "offset": offset}
        if query is not None:
            params["query"] = query
        if tag is not None:
            params["tag"] = tag
        return SkillListResponse.model_validate(self._client.request("GET", "/api/v1/skills", params=params))

    def search(self, workspace_id: str, query: str, *, scope: SkillScope = "end_user", end_user_id: str | None = None,
               tag: str | None = None, limit: int = 25, offset: int = 0) -> SkillListResponse:
        return self.list(workspace_id, scope=scope, end_user_id=end_user_id, query=query, tag=tag, limit=limit, offset=offset)

    def get(self, skill_id: str, workspace_id: str, *, scope: SkillScope = "end_user", end_user_id: str | None = None) -> SkillResponse:
        """Explicitly read user-authored instructions. This does not run actions."""
        return SkillResponse.model_validate(self._client.request("GET", _path(skill_id), params=_library(workspace_id, scope, end_user_id)))

    def create(self, workspace_id: str, slug: str, name: str, markdown: str, *, scope: SkillScope = "end_user",
               end_user_id: str | None = None, description: str = "", tags: list[str] | None = None, enabled: bool = True) -> SkillResponse:
        payload = {**_library(workspace_id, scope, end_user_id), "slug": slug, "name": name, "markdown": markdown,
                   "description": description, "tags": tags or [], "enabled": enabled}
        return SkillResponse.model_validate(self._client.request("POST", "/api/v1/skills", json=payload))

    def update(self, skill_id: str, workspace_id: str, expected_version: int, *, scope: SkillScope = "end_user", end_user_id: str | None = None,
               slug: str | None = None, name: str | None = None, markdown: str | None = None, description: str | None = None,
               tags: list[str] | None = None, enabled: bool | None = None) -> SkillResponse:
        payload = {**_library(workspace_id, scope, end_user_id), "expectedVersion": expected_version}
        for key, value in {"slug": slug, "name": name, "markdown": markdown, "description": description, "tags": tags, "enabled": enabled}.items():
            if value is not None:
                payload[key] = value
        return SkillResponse.model_validate(self._client.request("PATCH", _path(skill_id), json=payload))

    def delete(self, skill_id: str, workspace_id: str, expected_version: int, *, scope: SkillScope = "end_user", end_user_id: str | None = None) -> dict[str, Any]:
        params = {**_library(workspace_id, scope, end_user_id), "expectedVersion": expected_version}
        return self._client.request("DELETE", _path(skill_id), params=params)
