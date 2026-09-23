import asyncio
from dataclasses import replace
from uuid import UUID

import pytest

from app.domain.scoring import assess
from scripts.seed_demo_data import (
    ALPHA_ID,
    BETA_ID,
    BUSINESS_ID,
    OTHER_BUSINESS_ID,
    OTHER_STUDENT_ID,
    STUDENT_ID,
)

pytestmark = pytest.mark.integration
PREFIX = "/api/v1"
BUSINESS = {"X-Demo-User": str(BUSINESS_ID)}
STUDENT = {"X-Demo-User": str(STUDENT_ID)}
OTHER = {"X-Demo-User": str(OTHER_BUSINESS_ID)}
STUDENT2 = {"X-Demo-User": str(OTHER_STUDENT_ID)}
BRIEF = {
    "title": "Классификация обращений",
    "problem": "500 заявок в день сортируются вручную",
    "goal": "Снизить время сортировки",
    "deliverable": "Прототип REST API",
    "success_criteria": "Точность не менее 80% на тестовой выборке",
    "timeline": "3 недели",
    "skill_slugs": ["python", "llm"],
}
PITCH = {
    "pitch": "Создадим прототип",
    "approach": "Сначала проверим данные",
    "timeline": "3 недели",
}


async def draft(client):
    response = await client.post(
        f"{PREFIX}/tasks/draft", headers=BUSINESS, json={"raw_text": "Нужен AI"}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def published(client):
    task_id = await draft(client)
    response = await client.patch(f"{PREFIX}/tasks/{task_id}", headers=BUSINESS, json=BRIEF)
    assert response.status_code == 200, response.text
    response = await client.post(f"{PREFIX}/tasks/{task_id}/analyze", headers=BUSINESS)
    assert response.status_code == 200, response.text
    response = await client.post(f"{PREFIX}/tasks/{task_id}/publish", headers=BUSINESS)
    assert response.status_code == 200, response.text
    return task_id


async def apply(client, task_id, headers=STUDENT, team_id=ALPHA_ID):
    return await client.post(
        f"{PREFIX}/tasks/{task_id}/apply", headers=headers, json={**PITCH, "team_id": str(team_id)}
    )


async def test_full_workflow_and_private_data(client):
    task_id = await draft(client)
    assert (await client.get(f"{PREFIX}/tasks/{task_id}")).status_code == 404
    assert (await client.get(f"{PREFIX}/tasks")).json()["total"] == 0
    answer = await client.post(
        f"{PREFIX}/tasks/{task_id}/answer",
        headers=BUSINESS,
        json={"field": "problem", "answer": BRIEF["problem"]},
    )
    assert answer.status_code == 200, answer.text
    assert answer.json()["assessment"]["source"] == "local_fallback"
    await client.patch(f"{PREFIX}/tasks/{task_id}", headers=BUSINESS, json=BRIEF)
    improved = await client.post(f"{PREFIX}/tasks/{task_id}/improve", headers=BUSINESS)
    assert improved.status_code == 200
    assert (
        await client.post(f"{PREFIX}/tasks/{task_id}/publish", headers=BUSINESS)
    ).status_code == 200
    public = (await client.get(f"{PREFIX}/tasks/{task_id}")).json()
    assert "raw_text" not in public and "assessment" not in public
    catalog = (await client.get(f"{PREFIX}/tasks?skill=python&limit=1")).json()
    assert catalog["total"] == 1 and len(catalog["items"]) == 1
    assert "raw_text" not in catalog["items"][0]
    rec = await client.get(f"{PREFIX}/recommendations?team_id={ALPHA_ID}", headers=STUDENT)
    assert rec.json()["items"][0]["match"]["score"] == 100
    proposal = await apply(client, task_id)
    assert proposal.status_code == 201, proposal.text
    proposal2 = await apply(client, task_id, STUDENT2, BETA_ID)
    assert proposal2.status_code == 201
    proposal_id = proposal.json()["id"]
    assert (
        await client.get(f"{PREFIX}/business/tasks/{task_id}/proposals", headers=BUSINESS)
    ).json()["total"] == 2
    assert (
        await client.get(f"{PREFIX}/business/proposals/{proposal_id}/team", headers=BUSINESS)
    ).json()["name"] == "Team Alpha"
    selected = await client.post(f"{PREFIX}/proposals/{proposal_id}/select", headers=BUSINESS)
    assert selected.status_code == 200 and selected.json()["status"] == "selected"
    assert (await client.get(f"{PREFIX}/my-proposals", headers=STUDENT2)).json()["items"][0][
        "status"
    ] == "rejected"
    assert (await client.get(f"{PREFIX}/tasks/{task_id}")).json()["status"] == "team_selected"
    assert (await client.get(f"{PREFIX}/tasks")).json()["total"] == 0
    assert (
        await client.post(f"{PREFIX}/proposals/{proposal_id}/select", headers=BUSINESS)
    ).status_code == 200
    history = (await client.get(f"{PREFIX}/tasks/{task_id}/score-history", headers=BUSINESS)).json()
    assert len(history) == 2


async def test_access_and_publication_rules(client):
    task_id = await draft(client)
    assert (
        await client.patch(f"{PREFIX}/tasks/{task_id}", headers=OTHER, json=BRIEF)
    ).status_code == 403
    assert (
        await client.post(f"{PREFIX}/tasks/{task_id}/analyze", headers=STUDENT)
    ).status_code == 403
    assert (
        await client.post(f"{PREFIX}/tasks/{task_id}/publish", headers=BUSINESS)
    ).status_code == 422
    assert (await apply(client, task_id)).status_code == 409
    await client.patch(f"{PREFIX}/tasks/{task_id}", headers=BUSINESS, json=BRIEF)
    assert (
        await client.post(f"{PREFIX}/tasks/{task_id}/publish", headers=BUSINESS)
    ).status_code == 409
    assert (
        await client.get(f"{PREFIX}/business/tasks/{task_id}/proposals", headers=OTHER)
    ).status_code == 403
    assert (
        await client.post(f"{PREFIX}/tasks/draft", json={"raw_text": "Идея"})
    ).status_code == 401


async def test_duplicate_membership_and_closed_state(client):
    task_id = await published(client)
    assert (await apply(client, task_id, STUDENT, BETA_ID)).status_code == 403
    proposal = await apply(client, task_id)
    assert (await apply(client, task_id)).status_code == 409
    proposal_id = proposal.json()["id"]
    assert (
        await client.post(f"{PREFIX}/proposals/{proposal_id}/select", headers=OTHER)
    ).status_code == 403
    assert (
        await client.post(f"{PREFIX}/proposals/{proposal_id}/select", headers=STUDENT)
    ).status_code == 403
    assert (
        await client.patch(f"{PREFIX}/tasks/{task_id}", headers=BUSINESS, json=BRIEF)
    ).status_code == 409
    await client.post(f"{PREFIX}/proposals/{proposal_id}/select", headers=BUSINESS)
    assert (await apply(client, task_id, STUDENT2, BETA_ID)).status_code == 409


async def test_concurrent_selection_has_exactly_one_winner(client):
    task_id = await published(client)
    ids = [
        (await apply(client, task_id)).json()["id"],
        (await apply(client, task_id, STUDENT2, BETA_ID)).json()["id"],
    ]
    responses = await asyncio.gather(
        *[
            client.post(f"{PREFIX}/proposals/{proposal_id}/select", headers=BUSINESS)
            for proposal_id in ids
        ]
    )
    assert sorted(item.status_code for item in responses) == [200, 409]
    proposals = (
        await client.get(f"{PREFIX}/business/tasks/{task_id}/proposals", headers=BUSINESS)
    ).json()["items"]
    assert sorted(item["status"] for item in proposals) == ["rejected", "selected"]


async def test_concurrent_duplicate_application(client):
    task_id = await published(client)
    responses = await asyncio.gather(apply(client, task_id), apply(client, task_id))
    assert sorted(item.status_code for item in responses) == [201, 409]


async def test_edit_invalidates_score_and_enforces_revision(client):
    task_id = await draft(client)
    analysis = (await client.post(f"{PREFIX}/tasks/{task_id}/analyze", headers=BUSINESS)).json()
    assert analysis["quality_score"] > 0
    response = await client.patch(
        f"{PREFIX}/tasks/{task_id}",
        headers=BUSINESS,
        json={"goal": "Новая цель", "expected_revision": 1},
    )
    assert response.status_code == 409
    response = await client.patch(
        f"{PREFIX}/tasks/{task_id}",
        headers=BUSINESS,
        json={"goal": "Новая цель", "expected_revision": analysis["revision"]},
    )
    assert response.status_code == 200
    assert response.json()["assessment"] is None and response.json()["quality_score"] == 0


async def test_stale_ai_response_does_not_overwrite_edit(client):
    started, release = asyncio.Event(), asyncio.Event()

    class SlowAnalyzer:
        async def analyze(self, raw_text, brief, improve):
            started.set()
            await release.wait()
            result = replace(brief, problem="Старый результат")
            return result, assess(result)

    task_id = await draft(client)
    client.app.state.service.analyzer = SlowAnalyzer()
    pending = asyncio.create_task(
        client.post(f"{PREFIX}/tasks/{task_id}/analyze", headers=BUSINESS)
    )
    await asyncio.wait_for(started.wait(), timeout=3)
    await client.patch(
        f"{PREFIX}/tasks/{task_id}", headers=BUSINESS, json={"problem": "Новая правка"}
    )
    release.set()
    assert (await pending).status_code == 409
    response = await client.get(f"{PREFIX}/tasks/{task_id}", headers=BUSINESS)
    assert response.json()["brief"]["problem"] == "Новая правка"


async def test_invalid_input_and_team_creation(client):
    task_id = await draft(client)
    for body in [{"title": None}, {"status": "published"}, {"skill_slugs": ["unknown"]}, {}]:
        assert (
            await client.patch(f"{PREFIX}/tasks/{task_id}", headers=BUSINESS, json=body)
        ).status_code == 422
    assert (await client.get(f"{PREFIX}/tasks?limit=1000")).status_code == 422
    response = await client.post(
        f"{PREFIX}/teams",
        headers=STUDENT,
        json={"name": "Gamma", "skill_slugs": ["python", "python"]},
    )
    assert response.status_code == 201
    assert response.json()["member_ids"] == [str(STUDENT_ID)]
    assert response.json()["skill_slugs"] == ["python"]
    assert UUID(response.json()["id"])
    assert (await client.get(f"{PREFIX}/ready")).status_code == 200
