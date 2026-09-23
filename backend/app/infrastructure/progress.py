"""Account milestones derived from persisted actions, never client-provided XP."""

from sqlalchemy import exists, select

from app.domain.entities import ProposalStatus, Role, TaskStatus
from app.infrastructure.db.models import ProposalRow, ScoreRow, TaskRow, TeamMemberRow


async def account_progress(factory, actor):
    if actor.role == Role.BUSINESS:
        owned = TaskRow.business_id == actor.id
        checks = [
            ("idea", "Первая идея", "Создайте черновик", 20, select(TaskRow.id).where(owned)),
            (
                "analysis",
                "Разбор задачи",
                "Проанализируйте карточку",
                30,
                select(ScoreRow.id).join(TaskRow, TaskRow.id == ScoreRow.task_id).where(owned),
            ),
            (
                "published",
                "Открыты для команд",
                "Опубликуйте задачу",
                50,
                select(TaskRow.id).where(
                    owned, TaskRow.status.in_([TaskStatus.PUBLISHED, TaskStatus.TEAM_SELECTED])
                ),
            ),
            (
                "selected",
                "Партнёрство",
                "Выберите команду",
                100,
                select(TaskRow.id).where(owned, TaskRow.status == TaskStatus.TEAM_SELECTED),
            ),
        ]
    else:
        teams = select(TeamMemberRow.team_id).where(TeamMemberRow.user_id == actor.id)
        checks = [
            ("team", "В команде", "Создайте команду или присоединитесь", 20, teams),
            (
                "proposal",
                "Первое предложение",
                "Отправьте отклик от команды",
                80,
                select(ProposalRow.id).where(ProposalRow.team_id.in_(teams)),
            ),
            (
                "selected",
                "Команда выбрана",
                "Получите выбор бизнеса",
                100,
                select(ProposalRow.id).where(
                    ProposalRow.team_id.in_(teams), ProposalRow.status == ProposalStatus.SELECTED
                ),
            ),
        ]
    async with factory() as session:
        flags = (await session.execute(select(*(exists(query) for *_, query in checks)))).one()
    achievements = [
        dict(id=key, title=title, description=description, xp=xp, unlocked=bool(done))
        for (key, title, description, xp, _), done in zip(checks, flags, strict=True)
    ]
    xp = sum(item["xp"] for item in achievements if item["unlocked"])
    levels = [(0, "Старт"), (20, "Инициатор"), (100, "Практик"), (200, "Партнёр")]
    level = max(i for i, (threshold, _) in enumerate(levels) if xp >= threshold)
    return dict(
        xp=xp,
        level=level + 1,
        title=levels[level][1],
        level_start=levels[level][0],
        next_level_xp=levels[level + 1][0] if level < 3 else None,
        achievements=achievements,
    )
