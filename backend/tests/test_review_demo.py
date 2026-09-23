from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select, text

from app.domain.entities import now
from app.infrastructure.db.models import ProposalRow, TaskRow, TeamRow, UserRow
from scripts import seed_review_demo


@pytest.mark.integration
async def test_fresh_review_dataset_is_small_repeatable_and_preserves_changes(client):
    factory = client.app.state.accounts.factory
    # client fixture only permits the dedicated *_test database.
    async with factory() as session:
        await session.execute(text("TRUNCATE users, skills CASCADE"))
        await session.commit()
    await seed_review_demo.seed(factory)
    async with factory() as session:
        for model, count in [(UserRow, 6), (TeamRow, 3), (TaskRow, 4), (ProposalRow, 1)]:
            assert await session.scalar(select(func.count()).select_from(model)) == count
        student = await session.scalar(
            select(UserRow).where(UserRow.email == "student.demo@example.com")
        )
        assert student.student_profile is None
        student.student_profile = {
            "direction": "backend",
            "skill_slugs": ["python"],
            "experience": "practice",
            "interests": "",
        }
        proposal = await session.scalar(select(ProposalRow))
        proposal.business_read_at = now()
        await session.commit()
    await seed_review_demo.seed(factory)
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(ProposalRow)) == 1
        assert (await session.scalar(select(ProposalRow))).business_read_at is not None
        student = await session.scalar(
            select(UserRow).where(UserRow.email == "student.demo@example.com")
        )
        assert student.student_profile["direction"] == "backend"


@pytest.mark.parametrize("environment,enabled", [("production", "true"), ("development", "false")])
async def test_review_seed_can_be_disabled(monkeypatch, environment, enabled):
    monkeypatch.setattr(seed_review_demo, "Settings", lambda: SimpleNamespace(app_env=environment))
    monkeypatch.setenv("REVIEW_DEMO_ENABLED", enabled)
    seed = AsyncMock()
    monkeypatch.setattr(seed_review_demo, "seed", seed)
    await seed_review_demo.main()
    seed.assert_not_called()
