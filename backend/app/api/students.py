from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.deps import current_user
from app.api.schemas import PublicTask
from app.domain.entities import DomainError, Role, TaskStatus, User
from app.infrastructure.db.models import (
    SkillRow,
    TaskRow,
    TeamMemberRow,
    TeamRow,
    TeamSkillRow,
    UserRow,
)
from app.infrastructure.db.repository import PostgresRepository, task_entity

router = APIRouter(prefix="/api/v1/students", tags=["student-matching"])
Actor = Annotated[User, Depends(current_user)]


class StudentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    direction: Literal["frontend", "backend", "fullstack", "data", "design", "security"]
    skill_slugs: list[str] = Field(min_length=1, max_length=30)
    experience: Literal["beginner", "practice", "experienced"]
    interests: str = Field(default="", max_length=500)


def student(actor):
    if actor.role != Role.STUDENT:
        raise DomainError("forbidden", "Доступно только студентам.", 403)


@router.get("/profile")
async def profile(request: Request, actor: Actor):
    student(actor)
    async with request.app.state.accounts.factory() as session:
        return (await session.get(UserRow, actor.id)).student_profile


@router.put("/profile")
async def save_profile(body: StudentProfile, request: Request, actor: Actor):
    student(actor)
    async with request.app.state.accounts.factory() as session:
        await PostgresRepository(session).validate_skills(body.skill_slugs)
        row = await session.get(UserRow, actor.id)
        row.student_profile = {**body.model_dump(), "skill_slugs": sorted(set(body.skill_slugs))}
        await session.commit()
        return row.student_profile


@router.get("/matches")
async def matches(request: Request, actor: Actor):
    student(actor)
    async with request.app.state.accounts.factory() as session:
        profile = (await session.get(UserRow, actor.id)).student_profile
        if not profile:
            return {"profile": None, "tasks": [], "teams": []}
        own = set(profile["skill_slugs"])
        repo = PostgresRepository(session)
        rows = list(
            await session.scalars(select(TaskRow).where(TaskRow.status == TaskStatus.PUBLISHED))
        )
        skills = await repo._task_skills([r.id for r in rows])
        tasks = []
        for row in rows:
            required = set(skills[row.id])
            overlap = sorted(own & required)
            if overlap:
                tasks.append(
                    {
                        "task": PublicTask.model_validate(task_entity(row, skills[row.id])),
                        "matched_skills": overlap,
                        "missing_skills": sorted(required - own),
                        "coverage": round(100 * len(overlap) / len(required)),
                    }
                )
        tasks.sort(
            key=lambda item: (-item["coverage"], -item["task"].quality_score, str(item["task"].id))
        )
        my_teams = select(TeamMemberRow.team_id).where(TeamMemberRow.user_id == actor.id)
        teams = []
        for team in await session.scalars(
            select(TeamRow).where(TeamRow.open_to_join.is_(True), ~TeamRow.id.in_(my_teams))
        ):
            team_skills = set(
                await session.scalars(
                    select(SkillRow.slug).join(TeamSkillRow).where(TeamSkillRow.team_id == team.id)
                )
            )
            added_by_team, added_by_you = sorted(team_skills - own), sorted(own - team_skills)
            if not added_by_team or not added_by_you:
                continue
            members = list(
                await session.scalars(
                    select(UserRow.name)
                    .join(TeamMemberRow, TeamMemberRow.user_id == UserRow.id)
                    .where(TeamMemberRow.team_id == team.id)
                )
            )
            teams.append(
                {
                    "id": team.id,
                    "name": team.name,
                    "description": team.description,
                    "members": members,
                    "added_by_team": added_by_team,
                    "added_by_you": added_by_you,
                    "shared_skills": sorted(own & team_skills),
                }
            )
        teams.sort(
            key=lambda item: (
                -(len(item["added_by_you"]) + len(item["added_by_team"])),
                str(item["id"]),
            )
        )
        return {"profile": profile, "tasks": tasks[:12], "teams": teams[:12]}


@router.post("/teams/{team_id}/join")
async def join_open_team(team_id: UUID, request: Request, actor: Actor):
    student(actor)
    async with request.app.state.accounts.factory() as session:
        team = await session.scalar(select(TeamRow).where(TeamRow.id == team_id).with_for_update())
        if not team or not team.open_to_join:
            raise DomainError("not_open", "Вступление в эту команду закрыто.", 403)
        if not await session.get(TeamMemberRow, (team_id, actor.id)):
            session.add(TeamMemberRow(team_id=team_id, user_id=actor.id))
            await session.commit()
        return {"id": team_id}


class Recruitment(BaseModel):
    open_to_join: bool


@router.put("/teams/{team_id}/recruitment")
async def recruitment(team_id: UUID, body: Recruitment, request: Request, actor: Actor):
    student(actor)
    async with request.app.state.accounts.factory() as session:
        team = await session.scalar(select(TeamRow).where(TeamRow.id == team_id).with_for_update())
        if not team or team.owner_id != actor.id:
            raise DomainError("forbidden", "Изменять набор может только капитан.", 403)
        team.open_to_join = body.open_to_join
        await session.commit()
        return {"open_to_join": team.open_to_join}
