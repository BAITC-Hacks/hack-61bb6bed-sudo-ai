import os

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.infrastructure.db.models import Base
from app.infrastructure.db.session import create_database
from app.main import create_app
from scripts.seed_demo_data import seed


@pytest.fixture
async def client():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a migrated PostgreSQL database ending in _test")
    if not (make_url(url).database or "").endswith("_test"):
        raise RuntimeError("Tests may only reset a database whose name ends in _test")
    engine, factory = create_database(url)
    async with engine.begin() as conn:
        names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE {names} CASCADE"))
    await seed(factory, with_tasks=False)
    await engine.dispose()
    settings = Settings(
        database_url=url, app_env="test", openai_api_key="", openai_model="", demo_auth_enabled=True
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as api:
            api.app = app
            yield api
