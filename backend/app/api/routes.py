from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import current_user, optional_user, service
from app.api.schemas import (
    AnswerInput,
    DraftInput,
    Page,
    PatchInput,
    ProposalInput,
    ProposalView,
    PublicTask,
    RecommendationView,
    TaskView,
    TeamInput,
    TeamView,
)
from app.application.service import ChallengeService
from app.domain.entities import DomainError, User

router = APIRouter(prefix="/api/v1")
Service = Annotated[ChallengeService, Depends(service)]
Actor = Annotated[User, Depends(current_user)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@router.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def ready(svc: Service):
    await svc.ready()
    return {"status": "ok", "database": "ok"}


@router.get("/demo/users", tags=["demo"])
async def demo_users(request: Request, svc: Service):
    if not request.app.state.settings.demo_auth_enabled:
        raise DomainError("not_found", "Не найдено.", 404)
    return await svc.demo_users()


@router.get("/skills", tags=["teams"])
async def skills(svc: Service):
    return await svc.skills()


@router.post("/tasks/draft", response_model=TaskView, status_code=201, tags=["tasks"])
async def create_draft(body: DraftInput, actor: Actor, svc: Service):
    return await svc.create(actor, body.raw_text)


@router.get("/tasks", response_model=Page[PublicTask], tags=["catalog"])
async def catalog(
    svc: Service,
    limit: Limit = 20,
    offset: Offset = 0,
    sort: Literal["quality", "newest"] = "quality",
    skill: str | None = None,
    q: str | None = Query(default=None, max_length=200),
):
    items, total = await svc.catalog(limit=limit, offset=offset, sort=sort, skill=skill, q=q)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/tasks/{task_id}", response_model=TaskView | PublicTask, tags=["tasks"])
async def detail(
    task_id: UUID, svc: Service, actor: Annotated[User | None, Depends(optional_user)]
):
    task = await svc.detail(task_id, actor)
    if actor and actor.id == task.business_id:
        return TaskView.model_validate(task)
    return PublicTask.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskView, tags=["tasks"])
async def edit(task_id: UUID, body: PatchInput, actor: Actor, svc: Service):
    return await svc.update(task_id, actor, body.model_dump(exclude_unset=True))


@router.post("/tasks/{task_id}/analyze", response_model=TaskView, tags=["builder"])
async def analyze(task_id: UUID, actor: Actor, svc: Service):
    return await svc.analyze(task_id, actor)


@router.post("/tasks/{task_id}/improve", response_model=TaskView, tags=["builder"])
async def improve(task_id: UUID, actor: Actor, svc: Service):
    return await svc.analyze(task_id, actor, improve=True)


@router.post("/tasks/{task_id}/answer", response_model=TaskView, tags=["builder"])
async def answer(task_id: UUID, body: AnswerInput, actor: Actor, svc: Service):
    return await svc.answer(task_id, actor, body.field, body.answer)


@router.get("/tasks/{task_id}/score-history", tags=["builder"])
async def history(task_id: UUID, actor: Actor, svc: Service):
    return await svc.history(task_id, actor)


@router.post("/tasks/{task_id}/publish", response_model=TaskView, tags=["tasks"])
async def publish(task_id: UUID, actor: Actor, svc: Service):
    return await svc.publish(task_id, actor)


@router.post(
    "/tasks/{task_id}/apply", response_model=ProposalView, status_code=201, tags=["proposals"]
)
async def apply(task_id: UUID, body: ProposalInput, actor: Actor, svc: Service):
    return await svc.apply(task_id, actor, **body.model_dump())


@router.get("/business/tasks", response_model=Page[TaskView], tags=["business"])
async def business_tasks(actor: Actor, svc: Service, limit: Limit = 20, offset: Offset = 0):
    items, total = await svc.business_tasks(actor, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get(
    "/business/tasks/{task_id}/proposals", response_model=Page[ProposalView], tags=["business"]
)
async def proposals(
    task_id: UUID, actor: Actor, svc: Service, limit: Limit = 20, offset: Offset = 0
):
    items, total = await svc.proposals(actor, task_id, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/business/proposals/{proposal_id}/team", response_model=TeamView, tags=["business"])
async def proposal_team(proposal_id: UUID, actor: Actor, svc: Service):
    return await svc.proposal_team(proposal_id, actor)


@router.get("/my-proposals", response_model=Page[ProposalView], tags=["proposals"])
async def my_proposals(actor: Actor, svc: Service, limit: Limit = 20, offset: Offset = 0):
    items, total = await svc.proposals(actor, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/proposals/{proposal_id}/select", response_model=ProposalView, tags=["business"])
async def select(proposal_id: UUID, actor: Actor, svc: Service):
    return await svc.select(proposal_id, actor)


@router.post("/teams", response_model=TeamView, status_code=201, tags=["teams"])
async def create_team(body: TeamInput, actor: Actor, svc: Service):
    return await svc.create_team(actor, body.name, body.description, sorted(set(body.skill_slugs)))


@router.get("/teams/me", response_model=list[TeamView], tags=["teams"])
async def my_teams(actor: Actor, svc: Service):
    return await svc.my_teams(actor)


@router.get("/recommendations", response_model=Page[RecommendationView], tags=["catalog"])
async def recommendations(
    team_id: UUID, actor: Actor, svc: Service, limit: Limit = 20, offset: Offset = 0
):
    items, total = await svc.recommendations(actor, team_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
