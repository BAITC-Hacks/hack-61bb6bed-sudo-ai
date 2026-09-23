"""Local-only, idempotent synthetic profiles and open demo teams."""

import asyncio
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.dialects.postgresql import insert

from app.core.config import Settings
from app.domain.entities import Role, TaskStatus, now
from app.infrastructure.db.models import (
    SkillRow,
    TaskRow,
    TaskSkillRow,
    TeamMemberRow,
    TeamRow,
    TeamSkillRow,
    UserRow,
)
from app.infrastructure.db.session import create_database


def ident(value):
    return uuid5(NAMESPACE_URL, "sana:matching-demo:" + value)


async def seed(factory):
    async with factory() as session:
        # Actual stack options are shared with task and team editors.
        for slug, name in {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "nodejs": "Node.js",
            "figma": "Figma",
            "html-css": "HTML / CSS",
            "vue": "Vue",
            "java": "Java",
            "go": "Go",
        }.items():
            await session.execute(
                insert(SkillRow)
                .values(id=ident("skill:" + slug), slug=slug, name=name)
                .on_conflict_do_nothing()
            )
        from sqlalchemy import select

        skills = {r.slug: r.id for r in await session.scalars(select(SkillRow))}
        examples = [
            (
                "interface",
                "Алия · демо",
                "Frontend Lab · демо",
                "Интерфейсы на React. Ищем участника для API и данных.",
                "frontend",
                ["react", "typescript", "figma"],
            ),
            (
                "api",
                "Тимур · демо",
                "API Crew · демо",
                "Создаём API и базы данных. Будем рады фронтенд-разработчику.",
                "backend",
                ["python", "fastapi", "postgresql"],
            ),
            (
                "data",
                "Дана · демо",
                "Data Studio · демо",
                "Аналитика и AI. Нужна помощь с интерфейсами и интеграцией.",
                "data",
                ["python", "data-analysis", "llm"],
            ),
        ]
        for key, name, team_name, description, direction, stack in examples:
            uid, tid = ident("user:" + key), ident("team:" + key)
            await session.execute(
                insert(UserRow)
                .values(
                    id=uid,
                    name=name,
                    email=key + ".matching@example.test",
                    role=Role.STUDENT,
                    student_profile={
                        "direction": direction,
                        "skill_slugs": stack,
                        "experience": "practice",
                        "interests": "Учебные проекты",
                    },
                )
                .on_conflict_do_nothing()
            )
            await session.execute(
                insert(TeamRow)
                .values(
                    id=tid,
                    name=team_name,
                    description="Демонстрационная команда. " + description,
                    owner_id=uid,
                    open_to_join=True,
                )
                .on_conflict_do_nothing()
            )
            await session.execute(
                insert(TeamMemberRow).values(team_id=tid, user_id=uid).on_conflict_do_nothing()
            )
            for slug in stack:
                await session.execute(
                    insert(TeamSkillRow)
                    .values(team_id=tid, skill_id=skills[slug])
                    .on_conflict_do_nothing()
                )
        bid = ident("business")
        await session.execute(
            insert(UserRow)
            .values(
                id=bid,
                name="Учебный бизнес · демо",
                email="business.matching@example.test",
                role=Role.BUSINESS,
            )
            .on_conflict_do_nothing()
        )
        for key, title, stack, result in [
            (
                "store",
                "Витрина интернет-магазина · демо",
                ["react", "typescript", "figma"],
                "Адаптивный каталог, фильтры и корзина на тестовых товарах.",
            ),
            (
                "orders",
                "API заказов для магазина · демо",
                ["python", "fastapi", "postgresql"],
                "API создания и просмотра заказов с тестами и документацией.",
            ),
            (
                "analytics",
                "Аналитика продаж · демо",
                ["python", "data-analysis", "llm"],
                "Отчёт по синтетическим продажам и прототип помощника аналитика.",
            ),
        ]:
            tid = ident("task:" + key)
            await session.execute(
                insert(TaskRow)
                .values(
                    id=tid,
                    business_id=bid,
                    raw_text="Демонстрационная учебная задача.",
                    title=title,
                    problem="Учебный магазин ведёт процессы вручную. Нужен прототип.",
                    goal="Проверить прототип на синтетических данных.",
                    deliverable=result,
                    success_criteria="Сценарий проходит 20 тестов. Есть инструкция запуска.",
                    target_users="Сотрудники и покупатели учебного магазина.",
                    constraints="Только синтетические данные; без реальных оплат.",
                    timeline="Учебный прототип за 3 недели.",
                    resources="Тестовый набор данных и обратная связь на демонстрации.",
                    risk_context="Не использовать реальные персональные данные.",
                    status=TaskStatus.PUBLISHED,
                    published_at=now(),
                    quality_score=0,
                    quality_level="Draft",
                )
                .on_conflict_do_nothing()
            )
            for slug in stack:
                await session.execute(
                    insert(TaskSkillRow)
                    .values(task_id=tid, skill_id=skills[slug])
                    .on_conflict_do_nothing()
                )
        await session.commit()


async def main():
    settings = Settings()
    if settings.app_env == "production":
        raise RuntimeError("Synthetic matching data is for local development only")
    engine, factory = create_database(settings.database_url)
    try:
        await seed(factory)
        print("Demo profiles, open teams and tasks ready.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
