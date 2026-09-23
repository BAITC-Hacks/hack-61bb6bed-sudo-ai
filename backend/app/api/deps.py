from uuid import UUID

from fastapi import Header, Request

from app.application.service import ChallengeService
from app.domain.entities import DomainError, User


def service(request: Request) -> ChallengeService:
    return request.app.state.service


async def optional_user(
    request: Request,
    x_demo_user: UUID | None = Header(default=None),
) -> User | None:
    if token := request.cookies.get("sana_session"):
        return await request.app.state.accounts.authenticate(
            token,
            request.headers.get("X-CSRF-Token"),
            request.method not in {"GET", "HEAD", "OPTIONS"},
        )
    if x_demo_user is None:
        return None
    if not request.app.state.settings.demo_auth_enabled:
        raise DomainError("demo_disabled", "Demo-авторизация отключена.", 401)
    async with request.app.state.uow() as tx:
        user = await tx.repo.user(x_demo_user)
    if user is None:
        raise DomainError("invalid_identity", "Demo-пользователь не найден.", 401)
    return user


async def current_user(request: Request, x_demo_user: UUID | None = Header(default=None)) -> User:
    user = await optional_user(request, x_demo_user)
    if user is None:
        raise DomainError("identity_required", "Войдите в аккаунт.", 401)
    return user
