"""Create a separate local demo login without changing existing accounts."""

import asyncio

from sqlalchemy import select

from app.core.config import Settings
from app.domain.entities import Role
from app.infrastructure.accounts import Accounts
from app.infrastructure.db.models import UserRow
from app.infrastructure.db.session import create_database


async def main():
    settings = Settings()
    if settings.app_env == "production":
        raise RuntimeError("Demo login seed is only available outside production")
    engine, factory = create_database(settings.database_url)
    try:
        async with factory() as session:
            exists = await session.scalar(
                select(UserRow.id).where(UserRow.email == "business.demo@example.com")
            )
        if not exists:
            await Accounts(factory, settings.session_days).register(
                "Демо Бизнес", "business.demo@example.com", "Sana-Demo-Business-2026", Role.BUSINESS
            )
        print("Local business demo account ready (existing accounts unchanged).")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
