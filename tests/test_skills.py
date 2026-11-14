import json

import httpx
import pytest

from weavz_sdk import Skill, SkillMetadata, WeavzClient, WeavzError

WORKSPACE = "11111111-1111-4111-8111-111111111111"
SKILL = {"id": "skill", "workspaceId": WORKSPACE, "scope": "end_user", "slug": "brief", "name": "Brief", "description": "",
         "tags": [], "enabled": True, "version": 1, "createdAt": "2026-11-14T00:00:00Z", "updatedAt": "2026-11-14T00:00:00Z"}


@pytest.fixture
def fixture():
    clients = []

    def make(response, status=200):
        requests = []
        def handler(request):
            requests.append(request)
            return httpx.Response(status, json=response)
        client = WeavzClient("wvz_fixture", base_url="https://api.example.test", max_retries=0)
        headers = client._http.headers
        client._http.close()
        client._http = httpx.Client(base_url="https://api.example.test", headers=headers, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client, requests
    yield make
    for client in clients:
        client.close()


def test_metadata_search_is_typed_and_preserves_external_identity(fixture):
    client, requests = fixture({"skills": [SKILL], "pagination": {"limit": 5, "offset": 10, "total": 30}, "permissions": {"canWrite": True}})
    result = client.skills.search(WORKSPACE, "account % brief", end_user_id="customer/alice@example.test", limit=5, offset=10)
    assert isinstance(result.skills[0], SkillMetadata)
    assert not hasattr(result.skills[0], "markdown")
    assert requests[0].url.params["endUserId"] == "customer/alice@example.test"
    assert requests[0].url.params["query"] == "account % brief"
    assert requests[0].url.params["offset"] == "10"


def test_explicit_shared_read_encodes_identifier(fixture):
    client, requests = fixture({"skill": {**SKILL, "scope": "workspace", "markdown": "# Instructions"}, "permissions": {"canWrite": False}})
    result = client.skills.get("skill/a?b#c", WORKSPACE, scope="workspace")
    assert isinstance(result.skill, Skill)
    assert result.skill.markdown == "# Instructions"
    assert requests[0].url.raw_path.startswith(b"/api/v1/skills/skill%2Fa%3Fb%23c?")
    assert "endUserId" not in requests[0].url.params


def test_create_and_sparse_update_keep_markdown_in_the_body(fixture):
    client, requests = fixture({"skill": {**SKILL, "markdown": "# Private instructions"}, "permissions": {"canWrite": True}})
    client.skills.create(WORKSPACE, "brief", "Brief", "# Private instructions", end_user_id="customer-123")
    assert requests[0].method == "POST"
    assert json.loads(requests[0].content)["markdown"] == "# Private instructions"
    assert requests[0].url.query == b""
    client.skills.update("skill", WORKSPACE, 4, end_user_id="customer-123", enabled=False, tags=[], description="")
    assert requests[1].method == "PATCH"
    assert json.loads(requests[1].content) == {"workspaceId": WORKSPACE, "scope": "end_user", "endUserId": "customer-123", "expectedVersion": 4, "enabled": False, "tags": [], "description": ""}


def test_delete_requires_version_and_conflicts_remain_errors(fixture):
    client, requests = fixture({"deleted": True, "id": "skill"})
    assert client.skills.delete("skill", WORKSPACE, 7, scope="workspace")["deleted"] is True
    assert requests[0].method == "DELETE"
    assert requests[0].url.params["expectedVersion"] == "7"
    other, calls = fixture({"error": "Changed", "code": "SKILL_CONFLICT"}, 409)
    with pytest.raises(WeavzError):
        other.skills.update("skill", WORKSPACE, 1, scope="workspace", name="Old draft")
    assert len(calls) == 1


@pytest.mark.parametrize("kwargs", [{}, {"scope": "workspace", "end_user_id": "customer"}])
def test_library_identity_choices_are_explicit(fixture, kwargs):
    client, requests = fixture({})
    with pytest.raises(ValueError):
        client.skills.list(WORKSPACE, **kwargs)
    assert requests == []
