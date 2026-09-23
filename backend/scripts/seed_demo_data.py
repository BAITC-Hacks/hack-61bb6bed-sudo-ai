"""Idempotent synthetic demo data. Run: python -m scripts.seed_demo_data."""

import asyncio
import logging
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.dialects.postgresql import insert

from app.core.config import Settings
from app.core.logging import configure_logging
from app.domain.entities import Brief, Role, Task, TaskStatus, Team, now
from app.domain.scoring import assess
from app.infrastructure.db.models import SkillRow, UserRow
from app.infrastructure.db.session import PostgresUnitOfWork, create_database

BUSINESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_BUSINESS_ID = UUID("22222222-2222-4222-8222-222222222222")
STUDENT_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_STUDENT_ID = UUID("44444444-4444-4444-8444-444444444444")
ALPHA_ID = UUID("55555555-5555-4555-8555-555555555555")
BETA_ID = UUID("66666666-6666-4666-8666-666666666666")
SKILLS = {
    "python": "Python",
    "fastapi": "FastAPI",
    "react": "React",
    "postgresql": "PostgreSQL",
    "llm": "LLM",
    "docker": "Docker",
    "data-analysis": "Data Analysis",
    "computer-vision": "Computer Vision",
    "cybersecurity": "Cybersecurity",
}


async def seed(factory, with_tasks: bool = True) -> None:
    async with factory() as session:
        for user_id, name, role in [
            (BUSINESS_ID, "Demo Business", Role.BUSINESS),
            (OTHER_BUSINESS_ID, "Other Business", Role.BUSINESS),
            (STUDENT_ID, "Demo Student", Role.STUDENT),
            (OTHER_STUDENT_ID, "Other Student", Role.STUDENT),
        ]:
            await session.execute(
                insert(UserRow)
                .values(
                    id=user_id,
                    name=name,
                    email=f"{user_id}@example.test",
                    role=role,
                )
                .on_conflict_do_nothing()
            )
        for slug, name in SKILLS.items():
            await session.execute(
                insert(SkillRow)
                .values(
                    id=uuid5(NAMESPACE_URL, f"sana:skill:{slug}"),
                    name=name,
                    slug=slug,
                )
                .on_conflict_do_nothing()
            )
        await session.commit()
    async with PostgresUnitOfWork(factory) as tx:
        for team in [
            Team(
                "Team Alpha",
                "Python, web и AI прототипы",
                ALPHA_ID,
                [STUDENT_ID],
                ["python", "fastapi", "react", "postgresql", "llm", "docker"],
            ),
            Team(
                "Team Beta",
                "Аналитика и компьютерное зрение",
                BETA_ID,
                [OTHER_STUDENT_ID],
                ["python", "data-analysis", "computer-vision"],
            ),
        ]:
            if await tx.repo.team(team.id) is None:
                await tx.repo.save_team(team)
        if with_tasks:
            examples = [
                (
                    "support",
                    "AI-классификация обращений",
                    "llm",
                    "Операторы вручную сортируют 500 обращений в день и тратят на это 4 часа.",
                    "Классифицировать не менее 80% тестовых обращений; ответ API быстрее 5 секунд.",
                ),
                (
                    "demand",
                    "Прогнозирование спроса",
                    "data-analysis",
                    "Магазин теряет продажи: каждую неделю заканчиваются 20 популярных товаров.",
                    "Ошибка прогноза MAPE менее 20% на отложенной выборке за 4 недели.",
                ),
                (
                    "warehouse",
                    "Контроль склада по изображениям",
                    "computer-vision",
                    "Инвентаризация 200 коробок занимает у кладовщика 2 часа ежедневно.",
                    "Точность подсчёта коробок не менее 90% на 100 синтетических изображениях.",
                ),
            ]
            for slug, title, skill, problem, success in examples:
                task_id = uuid5(NAMESPACE_URL, f"sana:task:{slug}")
                if await tx.repo.task(task_id):
                    continue
                brief = Brief(
                    title=title,
                    problem=problem,
                    goal="Сократить ручную работу сотрудников и проверить пользу автоматизации.",
                    deliverable="Рабочий прототип API, инструкция запуска и отчёт с метриками.",
                    success_criteria=success,
                    target_users="Сотрудники операционного отдела.",
                    constraints=(
                        "Использовать только синтетические данные; внешние интеграции не нужны."
                    ),
                    timeline="3 недели: прототип, проверка метрик и демонстрация.",
                    resources=(
                        "Синтетический тестовый набор и 2 консультации с представителем бизнеса."
                    ),
                    risk_context=(
                        "Исключить персональные данные, спорные результаты проверяет человек."
                    ),
                )
                assessment = assess(brief, warning="Demo: базовая оценка без OpenAI.")
                task = Task(
                    BUSINESS_ID,
                    problem,
                    id=task_id,
                    brief=brief,
                    skill_slugs=["python", skill],
                    status=TaskStatus.PUBLISHED,
                    quality_score=assessment.total,
                    quality_level=assessment.level,
                    assessment=assessment,
                    published_at=now(),
                )
                await tx.repo.save_task(task)
                await tx.repo.add_score(task, "demo_seed")
        await tx.commit()


async def main():
    settings = Settings()
    if settings.app_env == "production":
        raise RuntimeError("Demo seed is disabled in production")
    engine, factory = create_database(settings.database_url)
    try:
        await seed(factory)
        logging.getLogger(__name__).info("demo_seed_complete")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
