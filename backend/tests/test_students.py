import pytest

from app.domain.entities import TaskStatus
from app.infrastructure.db.models import TaskRow
from scripts.seed_demo_data import ALPHA_ID, BUSINESS_ID, STUDENT_ID
from scripts.seed_student_matching import ident, seed


@pytest.mark.integration
async def test_profile_matching_and_open_team_permissions(client):
    await seed(client.app.state.accounts.factory)
    actor = {"X-Demo-User": str(STUDENT_ID)}
    business = {"X-Demo-User": str(BUSINESS_ID)}
    assert (await client.get("/api/v1/students/profile", headers=actor)).json() is None
    profile = {
        "direction": "frontend",
        "skill_slugs": ["react", "typescript"],
        "experience": "practice",
        "interests": "",
    }
    assert (
        await client.put("/api/v1/students/profile", headers=business, json=profile)
    ).status_code == 403
    assert (
        await client.put(
            "/api/v1/students/profile", headers=actor, json={**profile, "skill_slugs": ["invented"]}
        )
    ).status_code == 422
    assert (
        await client.put("/api/v1/students/profile", headers=actor, json=profile)
    ).status_code == 200
    assert (await client.get("/api/v1/students/profile", headers=actor)).json() == profile
    matches = (await client.get("/api/v1/students/matches", headers=actor)).json()
    assert matches["tasks"][0]["task"]["id"] == str(ident("task:store"))
    assert all(t["task"]["status"] == "published" for t in matches["tasks"])
    team = next(t for t in matches["teams"] if t["id"] == str(ident("team:api")))
    assert "fastapi" in team["added_by_team"] and "react" in team["added_by_you"]
    assert "email" not in str(team)
    assert (
        await client.post(f"/api/v1/students/teams/{ALPHA_ID}/join", headers=actor)
    ).status_code == 403
    path = f"/api/v1/students/teams/{team['id']}"
    assert (
        await client.put(path + "/recruitment", headers=actor, json={"open_to_join": False})
    ).status_code == 403
    assert (await client.post(path + "/join", headers=business)).status_code == 403
    for _ in range(2):
        assert (await client.post(path + "/join", headers=actor)).status_code == 200
    matches = (await client.get("/api/v1/students/matches", headers=actor)).json()
    assert team["id"] not in [t["id"] for t in matches["teams"]]
    async with client.app.state.accounts.factory() as session:
        row = await session.get(TaskRow, ident("task:store"))
        row.status = TaskStatus.TEAM_SELECTED
        await session.commit()
    assert not (await client.get("/api/v1/students/matches", headers=actor)).json()["tasks"]
