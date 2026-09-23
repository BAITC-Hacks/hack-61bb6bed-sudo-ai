import pytest

from scripts.seed_demo_data import ALPHA_ID
from tests.test_workflow import BUSINESS, OTHER, PITCH, STUDENT, published

pytestmark = pytest.mark.integration


async def test_proposal_notifications_are_private_and_read_state_persists(client):
    task_id = await published(client)
    url = "/api/v1/business/notifications"
    assert (await client.get(url, headers=BUSINESS)).json()["unread_count"] == 0
    response = await client.post(
        f"/api/v1/tasks/{task_id}/apply", headers=STUDENT, json={**PITCH, "team_id": str(ALPHA_ID)}
    )
    assert response.status_code == 201
    proposal_id = response.json()["id"]
    feed = (await client.get(url, headers=BUSINESS)).json()
    assert feed["unread_count"] == 1 and feed["total"] == 1
    assert feed["items"][0]["task_id"] == task_id
    assert feed["items"][0]["team_name"] == "Team Alpha"
    assert (await client.get(url, headers=OTHER)).json()["total"] == 0
    assert (await client.get(url, headers=STUDENT)).status_code == 403
    assert (await client.post(f"{url}/{proposal_id}/read", headers=OTHER)).status_code == 404
    for _ in range(2):
        assert (await client.post(f"{url}/{proposal_id}/read", headers=BUSINESS)).status_code == 200
    feed = (await client.get(url, headers=BUSINESS)).json()
    assert feed["unread_count"] == 0 and feed["items"][0]["read"] is True
    assert (await client.get(url + "?offset=20", headers=BUSINESS)).json()["items"] == []
