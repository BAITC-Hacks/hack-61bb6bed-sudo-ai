"""Transactional account/session storage. Raw session and invite tokens are never stored."""

import asyncio
import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert

from app.domain.entities import DomainError, Role, User, now
from app.infrastructure.db.models import RateLimitRow, SessionRow, UserRow

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
DUMMY_HASH = HASHER.hash("not-a-user-password-constant-time-check")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def user_entity(row: UserRow) -> User:
    return User(row.id, row.name, row.email, row.role)


def verify_password(encoded: str | None, password: str) -> bool:
    try:
        return HASHER.verify(encoded or DUMMY_HASH, password) and encoded is not None
    except VerificationError:
        return False


class Accounts:
    def __init__(self, factory, session_days: int):
        self.factory = factory
        self.session_days = session_days

    async def throttle(self, key: str, maximum: int = 10, seconds: int = 900):
        stamp = now()
        async with self.factory() as session:
            stmt = insert(RateLimitRow).values(
                key=digest(key),
                attempts=1,
                resets_at=stamp + timedelta(seconds=seconds),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[RateLimitRow.key],
                set_={
                    "attempts": case(
                        (RateLimitRow.resets_at < stamp, 1), else_=RateLimitRow.attempts + 1
                    ),
                    "resets_at": case(
                        (RateLimitRow.resets_at < stamp, stamp + timedelta(seconds=seconds)),
                        else_=RateLimitRow.resets_at,
                    ),
                },
            ).returning(RateLimitRow.attempts)
            attempts = await session.scalar(stmt)
            await session.commit()
        if attempts > maximum:
            raise DomainError("rate_limited", "Слишком много попыток. Попробуйте позже.", 429)

    async def register(self, name: str, email: str, password: str, role: Role) -> User:
        encoded = await asyncio.to_thread(HASHER.hash, password)
        async with self.factory() as session:
            if await session.scalar(select(UserRow.id).where(UserRow.email == email)):
                raise DomainError("email_exists", "Этот email уже зарегистрирован.", 409)
            row = UserRow(name=name, email=email, password_hash=encoded, role=role)
            session.add(row)
            await session.commit()
            return user_entity(row)

    async def login(self, email: str, password: str):
        await self.throttle("login:" + email)
        async with self.factory() as session:
            row = await session.scalar(select(UserRow).where(UserRow.email == email))
            encoded = row.password_hash if row else None
            if not await asyncio.to_thread(verify_password, encoded, password):
                raise DomainError("invalid_credentials", "Неверный email или пароль.", 401)
            # Lock and re-check after hashing: a concurrent password change invalidates this login.
            row = await session.scalar(
                select(UserRow)
                .where(UserRow.email == email)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if row.password_hash != encoded:
                raise DomainError("invalid_credentials", "Пароль изменён. Войдите снова.", 401)
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            session.add(
                SessionRow(
                    token_hash=digest(token),
                    csrf_hash=digest(csrf),
                    user_id=row.id,
                    expires_at=now() + timedelta(days=self.session_days),
                )
            )
            await session.execute(delete(SessionRow).where(SessionRow.expires_at < now()))
            await session.commit()
            return user_entity(row), token, csrf

    async def authenticate(self, token: str, csrf: str | None, unsafe: bool) -> User:
        async with self.factory() as session:
            record = await session.get(SessionRow, digest(token))
            if record is None or record.expires_at <= now():
                raise DomainError("session_expired", "Сессия завершена. Войдите снова.", 401)
            if unsafe and (not csrf or not secrets.compare_digest(record.csrf_hash, digest(csrf))):
                raise DomainError("csrf_failed", "Обновите страницу и повторите действие.", 403)
            row = await session.get(UserRow, record.user_id)
            return user_entity(row)

    async def logout(self, token: str):
        async with self.factory() as session:
            await session.execute(delete(SessionRow).where(SessionRow.token_hash == digest(token)))
            await session.commit()

    async def profile(self, user_id: UUID, name: str) -> User:
        async with self.factory() as session:
            row = await session.get(UserRow, user_id)
            row.name = name
            await session.commit()
            return user_entity(row)

    async def change_password(self, user_id: UUID, current: str, new: str):
        await self.throttle("password:" + str(user_id))
        async with self.factory() as session:
            row = await session.scalar(
                select(UserRow).where(UserRow.id == user_id).with_for_update()
            )
            if not await asyncio.to_thread(verify_password, row.password_hash, current):
                raise DomainError("invalid_password", "Текущий пароль неверен.", 400)
            row.password_hash = await asyncio.to_thread(HASHER.hash, new)
            await session.execute(delete(SessionRow).where(SessionRow.user_id == user_id))
            await session.commit()
