import httpx
import pytest
from sqlalchemy import select

from app.infrastructure.accounts import digest
from app.infrastructure.db.models import SessionRow, UserRow

pytestmark = pytest.mark.integration
PASSWORD = "long-test-password-123"


async def register(client, email="owner@example.com", role="business"):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Test Account",
            "password": PASSWORD,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def csrf(client):
    return {"X-CSRF-Token": client.cookies["sana_csrf"]}


async def test_registration_real_sessions_hashes_and_logout(client):
    client.app.state.settings.demo_auth_enabled = False
    user = await register(client, "OWNER@example.com")
    assert user["email"] == "owner@example.com"
    assert "password_hash" not in user
    assert (await client.get("/api/v1/auth/me")).json()["id"] == user["id"]
    async with client.app.state.engine.connect() as conn:
        encoded = await conn.scalar(
            select(UserRow.password_hash).where(UserRow.email == user["email"])
        )
        assert encoded.startswith("$argon2id$") and PASSWORD not in encoded
        session_hash = await conn.scalar(select(SessionRow.token_hash))
        assert session_hash == digest(client.cookies["sana_session"])
    assert (
        await client.post("/api/v1/tasks/draft", headers=csrf(client), json={"raw_text": "Идея"})
    ).status_code == 201
    assert (await client.post("/api/v1/auth/logout", headers=csrf(client))).status_code == 200
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    login = await client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    assert login.status_code == 200
    assert "httponly" in login.headers.get_list("set-cookie")[0].lower()


async def test_csrf_and_cross_origin_cannot_change_account(client):
    await register(client)
    for headers in [{}, {"X-CSRF-Token": "forged"}]:
        response = await client.patch(
            "/api/v1/auth/profile", headers=headers, json={"name": "Hacked"}
        )
        assert response.status_code == 403
    response = await client.patch(
        "/api/v1/auth/profile",
        headers={**csrf(client), "Origin": "https://evil.example"},
        json={"name": "Hacked"},
    )
    assert response.status_code == 403
    response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example"},
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    assert response.status_code == 403
    response = await client.patch(
        "/api/v1/auth/profile", headers=csrf(client), json={"name": "My Name"}
    )
    assert response.json()["name"] == "My Name"


async def test_registration_validation_and_duplicate_email(client):
    for payload in [
        {"password": "short"},
        {"email": "not-an-email"},
        {"role": "admin"},
        {"name": "   "},
    ]:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Name",
                "email": "valid@example.com",
                "role": "business",
                "password": PASSWORD,
                **payload,
            },
        )
        assert response.status_code == 422
    await register(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Copy",
            "email": "OWNER@example.com",
            "role": "student",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 409


async def test_password_change_revokes_every_session(client):
    await register(client)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=client.app), base_url="http://test"
    ) as other:
        await other.post(
            "/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}
        )
        response = await client.post(
            "/api/v1/auth/password",
            headers=csrf(client),
            json={
                "current_password": PASSWORD,
                "new_password": "new-long-password-456",
            },
        )
        assert response.status_code == 200
        assert (await other.get("/api/v1/auth/me")).status_code == 401
        assert (await client.get("/api/v1/auth/me")).status_code == 401
        assert (
            await client.post(
                "/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}
            )
        ).status_code == 401
        assert (
            await client.post(
                "/api/v1/auth/login",
                json={"email": "owner@example.com", "password": "new-long-password-456"},
            )
        ).status_code == 200


async def test_login_rate_limit(client):
    results = []
    for _ in range(12):
        results.append(
            (
                await client.post(
                    "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong"}
                )
            ).status_code
        )
    assert results[:10] == [401] * 10
    assert results[-1] == 429


async def test_real_account_cannot_use_demo_header_to_impersonate(client):
    await register(client, role="student")
    response = await client.post(
        "/api/v1/tasks/draft",
        headers={**csrf(client), "X-Demo-User": "11111111-1111-4111-8111-111111111111"},
        json={"raw_text": "Idea"},
    )
    assert response.status_code == 403


async def test_team_invites_membership_and_ownership(client):
    captain = await register(client, "captain@example.com", "student")
    response = await client.post(
        "/api/v1/teams", headers=csrf(client), json={"name": "Real Team", "skill_slugs": ["python"]}
    )
    assert response.status_code == 201
    team_id = response.json()["id"]
    invitation = (
        await client.post(f"/api/v1/teams/{team_id}/invite", headers=csrf(client))
    ).json()["url"]
    token = invitation.split("#")[1]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=client.app), base_url="http://test"
    ) as member:
        person = await register(member, "member@example.com", "student")
        assert (await member.get(f"/api/v1/teams/{team_id}")).status_code == 403
        response = await member.post(
            "/api/v1/teams/join", headers=csrf(member), json={"token": token}
        )
        assert response.status_code == 200
        assert len(response.json()["members"]) == 2
        assert (
            await member.post("/api/v1/teams/join", headers=csrf(member), json={"token": token})
        ).status_code == 404
        assert (
            await member.patch(
                f"/api/v1/teams/{team_id}", headers=csrf(member), json={"name": "Forged"}
            )
        ).status_code == 403
        assert (
            await client.delete(
                f"/api/v1/teams/{team_id}/members/{captain['id']}", headers=csrf(client)
            )
        ).status_code == 409
        response = await client.post(
            f"/api/v1/teams/{team_id}/captain/{person['id']}", headers=csrf(client)
        )
        assert response.status_code == 200
        assert (
            await member.patch(
                f"/api/v1/teams/{team_id}",
                headers=csrf(member),
                json={"name": "Updated", "skill_slugs": ["react"]},
            )
        ).status_code == 200
        assert (
            await client.post(f"/api/v1/teams/{team_id}/invite", headers=csrf(client))
        ).status_code == 403
        assert (
            await member.delete(
                f"/api/v1/teams/{team_id}/members/{captain['id']}", headers=csrf(member)
            )
        ).status_code == 200
        assert (await client.get(f"/api/v1/teams/{team_id}")).status_code == 403
