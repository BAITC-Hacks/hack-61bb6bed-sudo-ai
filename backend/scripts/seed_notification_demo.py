"""One local demo proposal for the business demo account; safe to run again."""

import asyncio

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import Settings
from app.domain.entities import ProposalStatus, TaskStatus, now
from app.infrastructure.db.models import ProposalRow, SkillRow, TaskRow, TaskSkillRow, UserRow
from app.infrastructure.db.session import create_database
from scripts.seed_student_matching import ident
from scripts.seed_student_matching import seed as seed_matching


async def seed(factory):
    async with factory() as session:
        owner = await session.scalar(
            select(UserRow).where(UserRow.email == "business.demo@example.com")
        )
        if not owner:
            raise RuntimeError("Run seed_login_demo.py first")
        owner_id = owner.id
    await seed_matching(factory)
    task_id, proposal_id = ident("notification:store"), ident("notification:proposal")
    async with factory() as session:
        await session.execute(
            insert(TaskRow)
            .values(
                id=task_id,
                business_id=owner_id,
                raw_text="Демонстрационная задача для просмотра отклика команды.",
                title="Интернет-магазин: каталог и заказы · демо",
                problem="Заказы учебного магазина принимаются вручную в переписке.",
                goal="Проверить оформление заказов через сайт на тестовых данных.",
                deliverable="Прототип каталога, корзины и API заказов с документацией.",
                success_criteria=("20 тестовых заказов проходят от корзины до сохранения в базе."),
                target_users="Покупатели и менеджер учебного магазина.",
                constraints="Без реальных оплат; только синтетические данные.",
                timeline="3 недели на прототип.",
                resources="Тестовый каталог из 30 товаров.",
                risk_context="Не использовать персональные данные реальных покупателей.",
                status=TaskStatus.PUBLISHED,
                published_at=now(),
                quality_score=0,
                quality_level="Draft",
            )
            .on_conflict_do_nothing()
        )
        for skill_id in await session.scalars(
            select(SkillRow.id).where(SkillRow.slug.in_(["react", "fastapi", "postgresql"]))
        ):
            await session.execute(
                insert(TaskSkillRow)
                .values(task_id=task_id, skill_id=skill_id)
                .on_conflict_do_nothing()
            )
        await session.execute(
            insert(ProposalRow)
            .values(
                id=proposal_id,
                task_id=task_id,
                team_id=ident("team:api"),
                pitch=(
                    "Демо-отклик. Мы — API Crew: работаем с Python, FastAPI "
                    "и PostgreSQL. Поможем превратить ручной приём заказов в"
                    " понятный процесс на сайте."
                ),
                approach=(
                    "1. Уточним каталог и сценарий заказа.\n2. Подготовим "
                    "базу товаров и API заказов.\n3. Подключим каталог и "
                    "корзину совместно с фронтенд-участником.\n4. Проверим 20"
                    " тестовых заказов и передадим инструкцию запуска."
                ),
                timeline="3 недели: проектирование, разработка, тестирование и демонстрация.",
                status=ProposalStatus.SUBMITTED,
            )
            .on_conflict_do_nothing()
        )
        await session.commit()
    print(f"Demo notification ready. Task: {task_id}")


async def main():
    settings = Settings()
    if settings.app_env == "production":
        raise RuntimeError("Demo notifications are only available outside production")
    engine, factory = create_database(settings.database_url)
    try:
        await seed(factory)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
