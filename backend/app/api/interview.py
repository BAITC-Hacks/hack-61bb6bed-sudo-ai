from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update

from app.api.deps import current_user
from app.domain.entities import DomainError, Role, TaskStatus, User
from app.infrastructure.db.models import TaskRow
from app.infrastructure.interview import FIELDS, FieldName

router = APIRouter(prefix="/api/v1/tasks", tags=["interview"])
Actor = Annotated[User, Depends(current_user)]


class CoachInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: FieldName
    answer: str = Field(default="", max_length=8000)
    clarification: str = Field(default="", max_length=8000)
    expected_revision: int = Field(ge=1)


async def context(request, task_id, actor):
    async with request.app.state.accounts.factory() as session:
        row = await session.scalar(select(TaskRow).where(TaskRow.id == task_id))
        if row is None:
            raise DomainError("not_found", "Задача не найдена.", 404)
        if actor.role != Role.BUSINESS or row.business_id != actor.id:
            raise DomainError("forbidden", "Доступ только автору задачи.", 403)
        if row.status != TaskStatus.DRAFT:
            raise DomainError("invalid_status", "Интервью доступно только для черновика.", 409)
        return row, dict(
            raw_text=row.raw_text, brief={f: getattr(row, f) for f in FIELDS}, fields=FIELDS
        )


@router.post("/{task_id}/interview")
async def plan(task_id: UUID, request: Request, actor: Actor):
    row, data = await context(request, task_id, actor)
    if row.interview_plan_json:
        return row.interview_plan_json
    await request.app.state.accounts.throttle(
        "interview:" + str(actor.id), maximum=60, seconds=3600
    )
    result = await request.app.state.interview.plan(data)
    if result["source"] == "openai":
        async with request.app.state.accounts.factory() as session:
            await session.execute(
                update(TaskRow)
                .where(TaskRow.id == task_id, TaskRow.interview_plan_json.is_(None))
                .values(interview_plan_json=result)
            )
            await session.commit()
            saved = await session.scalar(
                select(TaskRow.interview_plan_json).where(TaskRow.id == task_id)
            )
            return saved
    return result


@router.post("/{task_id}/coach")
async def coach(task_id: UUID, body: CoachInput, request: Request, actor: Actor):
    row, data = await context(request, task_id, actor)
    if row.revision != body.expected_revision:
        raise DomainError("stale_revision", "Карточка изменилась. Обновите страницу.", 409)
    await request.app.state.accounts.throttle(
        "interview:" + str(actor.id), maximum=60, seconds=3600
    )
    result = await request.app.state.interview.coach({**data, **body.model_dump()})
    return {**result, "revision": row.revision, "field": body.field}
