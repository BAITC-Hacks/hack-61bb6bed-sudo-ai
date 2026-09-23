"""Small repeatable review dataset; never seed production or call external AI."""

import asyncio
import os
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.dialects.postgresql import insert

from app.core.config import Settings
from app.infrastructure.db.models import SkillRow
from app.infrastructure.db.session import create_database
from scripts.seed_demo_data import SKILLS
from scripts.seed_login_demo import seed as seed_logins
from scripts.seed_notification_demo import seed as seed_notification


async def seed(factory):
    # Only the skill dictionary from the larger seed: no old test accounts/tasks.
    async with factory() as session:
        for slug, name in SKILLS.items():
            await session.execute(
                insert(SkillRow)
                .values(id=uuid5(NAMESPACE_URL, f"sana:skill:{slug}"), slug=slug, name=name)
                .on_conflict_do_nothing()
            )
        await session.commit()
    await seed_logins(factory)
    await seed_notification(factory)


async def main():
    settings = Settings()
    if (
        settings.app_env != "development"
        or os.getenv("REVIEW_DEMO_ENABLED", "true").lower() != "true"
    ):
        print("Review demo disabled; no records changed.")
        return
    engine, factory = create_database(settings.database_url)
    try:
        await seed(factory)
        print("Review demo ready: two logins, three teams, four tasks, one proposal.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
