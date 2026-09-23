import pytest

from scripts.seed_demo_data import BUSINESS_ID, OTHER_BUSINESS_ID, STUDENT_ID

pytestmark = pytest.mark.integration


async def test_progress_scoped_and_repeat_safe(client):
    assert (await client.get("/api/v1/me/progress")).status_code == 401
    owner = {"X-Demo-User": str(BUSINESS_ID)}
    other = {"X-Demo-User": str(OTHER_BUSINESS_ID)}
    assert (await client.get("/api/v1/me/progress", headers=owner)).json()["xp"] == 0
    for _ in range(2):
        result = await client.post(
            "/api/v1/tasks/draft", headers=owner, json={"raw_text": "Тестовая идея для бизнеса"}
        )
        assert result.status_code == 201
    task_id = result.json()["id"]
    for _ in range(2):
        progress = (await client.get("/api/v1/me/progress", headers=owner)).json()
        assert progress["xp"] == 20
        assert progress["level"] == 2
        assert (await client.get("/api/v1/me/progress", headers=other)).json()["xp"] == 0
    await client.post(f"/api/v1/tasks/{task_id}/analyze", headers=owner)
    assert (await client.get("/api/v1/me/progress", headers=owner)).json()["xp"] == 50


async def test_student_progress_uses_membership(client):
    response = await client.get("/api/v1/me/progress", headers={"X-Demo-User": str(STUDENT_ID)})
    data = response.json()
    assert data["xp"] == 20  # Seeded student belongs to Team Alpha.
    assert [a["id"] for a in data["achievements"]] == ["team", "proposal", "selected"]
