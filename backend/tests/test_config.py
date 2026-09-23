import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_demo_auth_cannot_be_enabled_in_production():
    with pytest.raises(ValidationError, match="Demo authentication"):
        Settings(app_env="production", demo_auth_enabled=True)


def test_postgres_is_required():
    with pytest.raises(ValidationError, match="postgresql"):
        Settings(database_url="sqlite:///not-supported")


async def test_disabled_demo_has_no_identity_backdoor():
    app = create_app(Settings(app_env="production", demo_auth_enabled=False, openai_api_key=""))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (await client.get("/api/v1/demo/users")).status_code == 404
            response = await client.post(
                "/api/v1/tasks/draft",
                json={"raw_text": "An idea"},
                headers={"X-Demo-User": "11111111-1111-4111-8111-111111111111"},
            )
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "demo_disabled"
