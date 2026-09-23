import logging
from dataclasses import replace
from uuid import UUID

from app.application.ports import Analyzer, UnitOfWorkFactory
from app.domain.entities import (
    DomainError,
    Proposal,
    ProposalStatus,
    Role,
    Task,
    TaskStatus,
    Team,
    User,
    now,
)
from app.domain.scoring import QUESTIONS, match_skills

logger = logging.getLogger(__name__)
PUBLISH_FIELDS = ("title", "problem", "goal", "deliverable", "success_criteria", "timeline")


def require_role(user: User, role: Role) -> None:
    if user.role != role:
        raise DomainError("forbidden", "Эта операция недоступна вашей роли.", 403)


def owned(task: Task | None, user: User) -> Task:
    if task is None:
        raise DomainError("not_found", "Задача не найдена.", 404)
    require_role(user, Role.BUSINESS)
    if task.business_id != user.id:
        raise DomainError("forbidden", "Изменять задачу может только её владелец.", 403)
    return task


def editable(task: Task) -> None:
    if task.status != TaskStatus.DRAFT:
        raise DomainError("invalid_status", "Изменять можно только черновик.", 409)


def member(team: Team | None, user: User) -> Team:
    require_role(user, Role.STUDENT)
    if team is None:
        raise DomainError("not_found", "Команда не найдена.", 404)
    if user.id not in team.member_ids:
        raise DomainError("forbidden", "Вы не участник этой команды.", 403)
    return team


class ChallengeService:
    def __init__(self, uow: UnitOfWorkFactory, analyzer: Analyzer):
        self.uow = uow
        self.analyzer = analyzer

    async def ready(self) -> None:
        async with self.uow() as tx:
            await tx.repo.ping()

    async def demo_users(self) -> list[User]:
        async with self.uow() as tx:
            return await tx.repo.users()

    async def skills(self) -> list[dict]:
        async with self.uow() as tx:
            return await tx.repo.skills()

    async def create(self, user: User, raw_text: str) -> Task:
        require_role(user, Role.BUSINESS)
        task = Task(business_id=user.id, raw_text=raw_text)
        async with self.uow() as tx:
            await tx.repo.save_task(task)
            await tx.commit()
        return task

    async def update(self, task_id: UUID, user: User, changes: dict) -> Task:
        async with self.uow() as tx:
            task = owned(await tx.repo.task(task_id, lock=True), user)
            editable(task)
            expected = changes.pop("expected_revision", None)
            if expected is not None and task.revision != expected:
                raise DomainError("stale_revision", "Карточка уже изменена. Обновите её.", 409)
            if "skill_slugs" in changes:
                await tx.repo.validate_skills(changes["skill_slugs"])
                task.skill_slugs = changes.pop("skill_slugs")
            if "raw_text" in changes:
                task.raw_text = changes.pop("raw_text")
            task.brief = replace(task.brief, **changes)
            task.revision += 1
            task.updated_at = now()
            # A score for a previous version must never appear as a current score.
            task.assessment = None
            task.quality_score = 0
            task.quality_level = "Draft"
            await tx.repo.save_task(task)
            await tx.commit()
        return task

    async def analyze(self, task_id: UUID, user: User, improve: bool = False) -> Task:
        async with self.uow() as tx:
            snapshot = owned(await tx.repo.task(task_id), user)
            editable(snapshot)
            if not improve and snapshot.assessment and snapshot.assessment.source == "openai":
                return snapshot
        # No connection or row lock held during a slow external request.
        brief, assessment = await self.analyzer.analyze(snapshot.raw_text, snapshot.brief, improve)
        async with self.uow() as tx:
            task = owned(await tx.repo.task(task_id, lock=True), user)
            editable(task)
            if task.revision != snapshot.revision:
                raise DomainError("stale_analysis", "Карточка изменена во время анализа.", 409)
            task.brief = brief
            task.assessment = assessment
            task.quality_score = assessment.total
            task.quality_level = assessment.level
            task.revision += 1
            task.updated_at = now()
            await tx.repo.save_task(task)
            await tx.repo.add_score(task, "improve" if improve else "analyze")
            await tx.commit()
        return task

    async def answer(self, task_id: UUID, user: User, field: str, answer: str) -> Task:
        if field not in QUESTIONS:
            raise DomainError("invalid_field", "Неизвестное поле интервью.", 422)
        async with self.uow() as tx:
            task = owned(await tx.repo.task(task_id, lock=True), user)
            editable(task)
            setattr(task.brief, field, answer)
            task.revision += 1
            task.assessment = None
            task.quality_score = 0
            task.quality_level = "Draft"
            task.updated_at = now()
            await tx.repo.save_task(task)
            await tx.repo.add_answer(task_id, field, answer)
            await tx.commit()
        return await self.analyze(task_id, user)

    async def publish(self, task_id: UUID, user: User) -> Task:
        async with self.uow() as tx:
            task = owned(await tx.repo.task(task_id, lock=True), user)
            if task.status == TaskStatus.PUBLISHED:
                return task
            editable(task)
            missing = [name for name in PUBLISH_FIELDS if not getattr(task.brief, name).strip()]
            if missing:
                raise DomainError("incomplete_brief", "Заполните поля: " + ", ".join(missing), 422)
            if task.assessment is None:
                raise DomainError(
                    "analysis_required", "Проанализируйте текущую версию карточки.", 409
                )
            task.status = TaskStatus.PUBLISHED
            task.published_at = task.updated_at = now()
            task.revision += 1
            await tx.repo.save_task(task)
            await tx.commit()
        logger.info("task_published", extra={"task_id": str(task_id)})
        return task

    async def detail(self, task_id: UUID, user: User | None) -> Task:
        async with self.uow() as tx:
            task = await tx.repo.task(task_id)
        if task is None or (
            task.status == TaskStatus.DRAFT and (user is None or task.business_id != user.id)
        ):
            raise DomainError("not_found", "Задача не найдена.", 404)
        return task

    async def catalog(self, **filters) -> tuple[list[Task], int]:
        async with self.uow() as tx:
            return await tx.repo.tasks(**filters)

    async def business_tasks(self, user: User, **pagination) -> tuple[list[Task], int]:
        require_role(user, Role.BUSINESS)
        return await self.catalog(owner=user.id, **pagination)

    async def history(self, task_id: UUID, user: User) -> list[dict]:
        async with self.uow() as tx:
            owned(await tx.repo.task(task_id), user)
            return await tx.repo.history(task_id)

    async def create_team(self, user: User, name: str, description: str, skills: list[str]) -> Team:
        require_role(user, Role.STUDENT)
        team = Team(name, description, member_ids=[user.id], skill_slugs=skills)
        async with self.uow() as tx:
            await tx.repo.validate_skills(skills)
            await tx.repo.save_team(team)
            await tx.commit()
        return team

    async def my_teams(self, user: User) -> list[Team]:
        require_role(user, Role.STUDENT)
        async with self.uow() as tx:
            return await tx.repo.teams(user.id)

    async def apply(self, task_id: UUID, user: User, team_id: UUID, **content) -> Proposal:
        async with self.uow() as tx:
            member(await tx.repo.team(team_id), user)
            # Same lock order as selection: a late application cannot escape rejection.
            task = await tx.repo.task(task_id, lock=True)
            if task is None:
                raise DomainError("not_found", "Задача не найдена.", 404)
            if task.status != TaskStatus.PUBLISHED:
                raise DomainError("applications_closed", "Задача не принимает отклики.", 409)
            if await tx.repo.has_proposal(task_id, team_id):
                raise DomainError("duplicate_proposal", "Команда уже откликнулась.", 409)
            proposal = Proposal(task_id=task_id, team_id=team_id, **content)
            await tx.repo.save_proposal(proposal)
            await tx.commit()
        return proposal

    async def proposals(self, user: User, task_id: UUID | None = None, **page):
        async with self.uow() as tx:
            if task_id:
                owned(await tx.repo.task(task_id), user)
                return await tx.repo.proposals(task_id=task_id, **page)
            require_role(user, Role.STUDENT)
            return await tx.repo.proposals(member_id=user.id, **page)

    async def proposal_team(self, proposal_id: UUID, user: User) -> Team:
        async with self.uow() as tx:
            proposal = await tx.repo.proposal(proposal_id)
            if proposal is None:
                raise DomainError("not_found", "Отклик не найден.", 404)
            owned(await tx.repo.task(proposal.task_id), user)
            team = await tx.repo.team(proposal.team_id)
            assert team is not None
            return team

    async def select(self, proposal_id: UUID, user: User) -> Proposal:
        require_role(user, Role.BUSINESS)
        async with self.uow() as tx:
            initial = await tx.repo.proposal(proposal_id)
            if initial is None:
                raise DomainError("not_found", "Отклик не найден.", 404)
            task = owned(await tx.repo.task(initial.task_id, lock=True), user)
            proposal = await tx.repo.proposal(proposal_id)
            assert proposal is not None
            if (
                task.status == TaskStatus.TEAM_SELECTED
                and proposal.status == ProposalStatus.SELECTED
            ):
                return proposal
            if task.status != TaskStatus.PUBLISHED or proposal.status != ProposalStatus.SUBMITTED:
                raise DomainError(
                    "selection_closed", "Команда уже выбрана или задача закрыта.", 409
                )
            await tx.repo.select_proposal(proposal)
            task.status = TaskStatus.TEAM_SELECTED
            task.updated_at = now()
            task.revision += 1
            await tx.repo.save_task(task)
            await tx.commit()
        logger.info(
            "team_selected", extra={"task_id": str(task.id), "team_id": str(proposal.team_id)}
        )
        return proposal

    async def recommendations(self, user: User, team_id: UUID, limit: int, offset: int):
        async with self.uow() as tx:
            team = member(await tx.repo.team(team_id), user)
            tasks, total = await tx.repo.tasks(limit=limit, offset=offset)
        return [
            {"task": task, "match": match_skills(task.skill_slugs, team.skill_slugs)}
            for task in tasks
        ], total
