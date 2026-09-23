from dataclasses import asdict, fields
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import (
    Assessment,
    Brief,
    CriterionScore,
    DomainError,
    Proposal,
    ProposalStatus,
    Question,
    Task,
    TaskStatus,
    Team,
    User,
    now,
)
from app.infrastructure.db.models import (
    AnswerRow,
    ProposalRow,
    ScoreRow,
    SkillRow,
    TaskRow,
    TaskSkillRow,
    TeamMemberRow,
    TeamRow,
    TeamSkillRow,
    UserRow,
)


def assessment_from_json(value: dict | None) -> Assessment | None:
    if value is None:
        return None
    return Assessment(
        **{
            **value,
            "scores": {key: CriterionScore(**item) for key, item in value["scores"].items()},
            "next_questions": [Question(**item) for item in value["next_questions"]],
        }
    )


def task_entity(row: TaskRow, skills: list[str]) -> Task:
    return Task(
        id=row.id,
        business_id=row.business_id,
        raw_text=row.raw_text,
        brief=Brief(**{item.name: getattr(row, item.name) for item in fields(Brief)}),
        skill_slugs=skills,
        status=row.status,
        quality_score=row.quality_score,
        quality_level=row.quality_level,
        revision=row.revision,
        assessment=assessment_from_json(row.assessment_json),
        created_at=row.created_at,
        updated_at=row.updated_at,
        published_at=row.published_at,
    )


def proposal_entity(row: ProposalRow) -> Proposal:
    return Proposal(**{item.name: getattr(row, item.name) for item in fields(Proposal)})


class PostgresRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ping(self) -> None:
        # Readiness requires an accessible, migrated schema, not just a TCP connection.
        await self.session.execute(select(TaskRow.id).limit(1))

    async def user(self, user_id: UUID) -> User | None:
        row = await self.session.get(UserRow, user_id)
        return User(row.id, row.name, row.email, row.role) if row else None

    async def users(self) -> list[User]:
        rows = await self.session.scalars(select(UserRow).order_by(UserRow.name))
        return [User(row.id, row.name, row.email, row.role) for row in rows]

    async def skills(self) -> list[dict]:
        rows = await self.session.scalars(select(SkillRow).order_by(SkillRow.name))
        return [{"slug": row.slug, "name": row.name} for row in rows]

    async def validate_skills(self, slugs: list[str]) -> None:
        existing = set(
            await self.session.scalars(select(SkillRow.slug).where(SkillRow.slug.in_(slugs)))
        )
        if unknown := set(slugs) - existing:
            raise DomainError(
                "unknown_skills", "Неизвестные навыки: " + ", ".join(sorted(unknown)), 422
            )

    async def _task_skills(self, ids: list[UUID]) -> dict[UUID, list[str]]:
        result: dict[UUID, list[str]] = {task_id: [] for task_id in ids}
        if not ids:
            return result
        rows = await self.session.execute(
            select(TaskSkillRow.task_id, SkillRow.slug)
            .join(SkillRow)
            .where(TaskSkillRow.task_id.in_(ids))
            .order_by(SkillRow.slug)
        )
        for task_id, slug in rows:
            result[task_id].append(slug)
        return result

    async def task(self, task_id: UUID, lock: bool = False) -> Task | None:
        stmt = (
            select(TaskRow).where(TaskRow.id == task_id).execution_options(populate_existing=True)
        )
        if lock:
            stmt = stmt.with_for_update()
        row = await self.session.scalar(stmt)
        if row is None:
            return None
        return task_entity(row, (await self._task_skills([row.id]))[row.id])

    async def save_task(self, task: Task) -> None:
        row = await self.session.get(TaskRow, task.id)
        if row is None:
            row = TaskRow(id=task.id)
            self.session.add(row)
        for name in (
            "business_id",
            "raw_text",
            "status",
            "quality_score",
            "quality_level",
            "revision",
            "created_at",
            "updated_at",
            "published_at",
        ):
            setattr(row, name, getattr(task, name))
        for name, value in asdict(task.brief).items():
            setattr(row, name, value)
        row.assessment_json = asdict(task.assessment) if task.assessment else None
        await self.session.flush()
        await self.session.execute(delete(TaskSkillRow).where(TaskSkillRow.task_id == task.id))
        skill_ids = await self.session.scalars(
            select(SkillRow.id).where(SkillRow.slug.in_(task.skill_slugs))
        )
        self.session.add_all(
            TaskSkillRow(task_id=task.id, skill_id=skill_id) for skill_id in skill_ids
        )
        await self.session.flush()

    async def tasks(
        self,
        *,
        owner: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str = "quality",
        skill: str | None = None,
        q: str | None = None,
    ) -> tuple[list[Task], int]:
        condition = (
            TaskRow.business_id == owner if owner else TaskRow.status == TaskStatus.PUBLISHED
        )
        stmt = select(TaskRow).where(condition)
        if q:
            stmt = stmt.where(
                or_(
                    TaskRow.title.icontains(q, autoescape=True),
                    TaskRow.problem.icontains(q, autoescape=True),
                )
            )
        if skill:
            stmt = stmt.where(
                TaskRow.id.in_(
                    select(TaskSkillRow.task_id).join(SkillRow).where(SkillRow.slug == skill)
                )
            )
        total = await self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        newest = TaskRow.created_at.desc() if owner else TaskRow.published_at.desc()
        order = TaskRow.quality_score.desc() if sort == "quality" else newest
        rows = list(
            await self.session.scalars(stmt.order_by(order, TaskRow.id).limit(limit).offset(offset))
        )
        skills = await self._task_skills([row.id for row in rows])
        return [task_entity(row, skills[row.id]) for row in rows], total or 0

    async def add_score(self, task: Task, reason: str) -> None:
        assert task.assessment is not None
        self.session.add(
            ScoreRow(
                task_id=task.id,
                revision=task.revision,
                score=task.quality_score,
                reason=reason,
                feedback=asdict(task.assessment),
            )
        )

    async def history(self, task_id: UUID) -> list[dict]:
        rows = await self.session.scalars(
            select(ScoreRow).where(ScoreRow.task_id == task_id).order_by(ScoreRow.revision)
        )
        return [
            {
                "revision": row.revision,
                "score": row.score,
                "reason": row.reason,
                "assessment": row.feedback,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def add_answer(self, task_id: UUID, field: str, answer: str) -> None:
        self.session.add(AnswerRow(task_id=task_id, field=field, answer=answer))

    async def team(self, team_id: UUID) -> Team | None:
        row = await self.session.get(TeamRow, team_id)
        if row is None:
            return None
        members = list(
            await self.session.scalars(
                select(TeamMemberRow.user_id).where(TeamMemberRow.team_id == team_id)
            )
        )
        skills = list(
            await self.session.scalars(
                select(SkillRow.slug)
                .join(TeamSkillRow)
                .where(TeamSkillRow.team_id == team_id)
                .order_by(SkillRow.slug)
            )
        )
        return Team(row.name, row.description, row.id, members, skills)

    async def teams(self, user_id: UUID) -> list[Team]:
        ids = await self.session.scalars(
            select(TeamMemberRow.team_id).where(TeamMemberRow.user_id == user_id)
        )
        # Demo membership is small; the catalog uses a batched skill query.
        result = []
        for team_id in ids:
            team = await self.team(team_id)
            if team:
                result.append(team)
        return result

    async def save_team(self, team: Team) -> None:
        self.session.add(
            TeamRow(
                id=team.id,
                name=team.name,
                description=team.description,
                owner_id=team.member_ids[0] if team.member_ids else None,
            )
        )
        await self.session.flush()
        self.session.add_all(
            TeamMemberRow(team_id=team.id, user_id=user_id) for user_id in team.member_ids
        )
        skill_ids = await self.session.scalars(
            select(SkillRow.id).where(SkillRow.slug.in_(team.skill_slugs))
        )
        self.session.add_all(
            TeamSkillRow(team_id=team.id, skill_id=skill_id) for skill_id in skill_ids
        )

    async def proposal(self, proposal_id: UUID) -> Proposal | None:
        row = await self.session.scalar(
            select(ProposalRow)
            .where(ProposalRow.id == proposal_id)
            .execution_options(populate_existing=True)
        )
        return proposal_entity(row) if row else None

    async def proposals(
        self,
        *,
        task_id: UUID | None = None,
        member_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Proposal], int]:
        stmt = select(ProposalRow)
        if task_id:
            stmt = stmt.where(ProposalRow.task_id == task_id)
        if member_id:
            stmt = stmt.where(
                ProposalRow.team_id.in_(
                    select(TeamMemberRow.team_id).where(TeamMemberRow.user_id == member_id)
                )
            )
        total = await self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = await self.session.scalars(
            stmt.order_by(ProposalRow.created_at, ProposalRow.id).limit(limit).offset(offset)
        )
        return [proposal_entity(row) for row in rows], total or 0

    async def has_proposal(self, task_id: UUID, team_id: UUID) -> bool:
        return bool(
            await self.session.scalar(
                select(ProposalRow.id).where(
                    ProposalRow.task_id == task_id,
                    ProposalRow.team_id == team_id,
                )
            )
        )

    async def save_proposal(self, proposal: Proposal) -> None:
        self.session.add(ProposalRow(**asdict(proposal)))
        await self.session.flush()

    async def select_proposal(self, proposal: Proposal) -> None:
        stamp = now()
        await self.session.execute(
            update(ProposalRow)
            .where(
                ProposalRow.task_id == proposal.task_id,
                ProposalRow.id != proposal.id,
            )
            .values(status=ProposalStatus.REJECTED, updated_at=stamp)
        )
        await self.session.execute(
            update(ProposalRow)
            .where(ProposalRow.id == proposal.id)
            .values(
                status=ProposalStatus.SELECTED,
                updated_at=stamp,
            )
        )
        proposal.status = ProposalStatus.SELECTED
        proposal.updated_at = stamp
