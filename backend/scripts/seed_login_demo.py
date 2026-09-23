"""Create a separate local demo login without changing existing accounts."""

import asyncio

from sqlalchemy import select

from app.core.config import Settings
from app.domain.entities import Role
from app.infrastructure.accounts import Accounts
from app.infrastructure.db.models import UserRow
from app.infrastructure.db.session import create_database


async def seed(factory, session_days=7):
    accounts = (
        ("Демо Бизнес", "business.demo@example.com", "Sana-Demo-Business-2026", Role.BUSINESS),
        ("Демо Студент", "student.demo@example.com", "Sana-Demo-Student-2026", Role.STUDENT),
    )
    for name, email, password, role in accounts:
        async with factory() as session:
            exists = await session.scalar(select(UserRow.id).where(UserRow.email == email))
        if not exists:
            await Accounts(factory, session_days).register(name, email, password, role)
    print("Local business and student demo accounts ready (existing accounts unchanged).")


async def main():
    settings = Settings()
    if settings.app_env == "production":
        raise RuntimeError("Demo login seed is only available outside production")
    engine, factory = create_database(settings.database_url)
    try:
        await seed(factory, settings.session_days)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
