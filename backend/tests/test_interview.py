from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Brief
from app.infrastructure.interview import FIELDS, Coach, InterviewAI
from scripts.seed_demo_data import BUSINESS_ID, OTHER_BUSINESS_ID


async def test_interview_fallback_is_explicit_and_does_not_invent_suggestions():
    ai = InterviewAI(None, "", 1)
    plan = await ai.plan({"raw_text": "Интернет-магазин"})
    assert plan["source"] == "local_fallback"
    assert {q["field"] for q in plan["questions"]} == set(FIELDS)
    coach = await ai.coach({"field": "timeline"})
    assert coach["suggestion"] == "" and coach["warning"]


async def test_coach_receives_business_context_and_unsaved_answer():
    output = Coach(
        question="Какие товары продаёте?",
        hint="Опишите ассортимент.",
        suggestion="Магазин обуви",
        followups=["Нужна ли доставка?"],
    )
    parse = AsyncMock(return_value=SimpleNamespace(status="completed", output_parsed=output))
    ai = InterviewAI(SimpleNamespace(responses=SimpleNamespace(parse=parse)), "test", 1)
    context = {
        "raw_text": "Нужен интернет-магазин",
        "brief": asdict(Brief(goal="Продажи онлайн")),
        "field": "problem",
        "answer": "Продаём обувь",
        "clarification": "Только в Алматы",
    }
    result = await ai.coach(context)
    assert result["source"] == "openai"
    assert "Алматы" in parse.call_args.kwargs["input"][1]["content"]
    assert parse.call_args.kwargs["store"] is False


@pytest.mark.integration
async def test_plan_cached_private_and_coach_does_not_edit_task(client):
    owner = {"X-Demo-User": str(BUSINESS_ID)}
    stranger = {"X-Demo-User": str(OTHER_BUSINESS_ID)}
    task = (
        await client.post(
            "/api/v1/tasks/draft", headers=owner, json={"raw_text": "Нужен интернет-магазин обуви"}
        )
    ).json()
    task_id = task["id"]
    plan = await InterviewAI(None, "", 1).plan({})
    plan["source"] = "openai"
    client.app.state.interview.plan = AsyncMock(return_value=plan)
    for _ in range(2):
        r = await client.post(f"/api/v1/tasks/{task_id}/interview", headers=owner)
        assert r.status_code == 200
    client.app.state.interview.plan.assert_awaited_once()
    assert (
        await client.post(f"/api/v1/tasks/{task_id}/interview", headers=stranger)
    ).status_code == 403
    client.app.state.interview.coach = AsyncMock(
        return_value={
            "question": "Какие товары?",
            "hint": "Уточните ассортимент",
            "suggestion": "Обувь",
            "followups": [],
            "source": "openai",
            "warning": None,
        }
    )
    body = {"field": "problem", "answer": "Обувь", "expected_revision": task["revision"]}
    r = await client.post(f"/api/v1/tasks/{task_id}/coach", headers=owner, json=body)
    assert r.status_code == 200
    assert (await client.get(f"/api/v1/tasks/{task_id}", headers=owner)).json()["brief"] == task[
        "brief"
    ]
    assert (
        await client.post(f"/api/v1/tasks/{task_id}/coach", headers=stranger, json=body)
    ).status_code == 403
    body["expected_revision"] += 1
    assert (
        await client.post(f"/api/v1/tasks/{task_id}/coach", headers=owner, json=body)
    ).status_code == 409
