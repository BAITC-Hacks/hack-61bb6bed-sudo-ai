from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import current_user
from app.api.schemas import TeamInput
from app.domain.entities import User

router = APIRouter(prefix="/api/v1", tags=["team-management"])
Actor = Annotated[User, Depends(current_user)]


class InviteInput(BaseModel):
    token: str = Field(min_length=20, max_length=100)


@router.get("/teams/{team_id}")
async def detail(team_id: UUID, request: Request, user: Actor):
    return await request.app.state.teams.detail(team_id, user)


@router.patch("/teams/{team_id}")
async def edit(team_id: UUID, body: TeamInput, request: Request, user: Actor):
    return await request.app.state.teams.update(
        team_id, user, body.name, body.description, body.skill_slugs
    )


@router.post("/teams/{team_id}/invite")
async def invite(team_id: UUID, request: Request, user: Actor):
    return await request.app.state.teams.invite(team_id, user)


@router.post("/teams/join")
async def join(body: InviteInput, request: Request, user: Actor):
    return await request.app.state.teams.join(body.token, user)


@router.delete("/teams/{team_id}/members/{member_id}")
async def remove(team_id: UUID, member_id: UUID, request: Request, user: Actor):
    await request.app.state.teams.remove(team_id, member_id, user)
    return {"ok": True}


@router.post("/teams/{team_id}/captain/{member_id}")
async def transfer(team_id: UUID, member_id: UUID, request: Request, user: Actor):
    await request.app.state.teams.transfer(team_id, member_id, user)
    return {"ok": True}
