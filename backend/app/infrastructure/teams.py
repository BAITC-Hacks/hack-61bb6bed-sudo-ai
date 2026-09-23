import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.application.service import require_role
from app.domain.entities import DomainError, Role, User, now
from app.infrastructure.accounts import digest
from app.infrastructure.db.models import (
    InviteRow,
    SkillRow,
    TeamMemberRow,
    TeamRow,
    TeamSkillRow,
    UserRow,
)
from app.infrastructure.db.repository import PostgresRepository


class TeamManagement:
    def __init__(self, factory, frontend_url: str):
        self.factory = factory
        self.frontend_url = frontend_url

    async def _team(self, session, team_id: UUID, user: User, owner: bool = False):
        require_role(user, Role.STUDENT)
        row = await session.scalar(select(TeamRow).where(TeamRow.id == team_id).with_for_update())
        if row is None:
            raise DomainError("not_found", "Команда не найдена.", 404)
        membership = await session.get(TeamMemberRow, (team_id, user.id))
        if not membership or (owner and row.owner_id != user.id):
            raise DomainError("forbidden", "У вас нет прав на это действие.", 403)
        return row

    async def detail(self, team_id: UUID, user: User):
        async with self.factory() as session:
            row = await self._team(session, team_id, user)
            members = (
                await session.scalars(
                    select(UserRow)
                    .join(TeamMemberRow)
                    .where(TeamMemberRow.team_id == team_id)
                    .order_by(UserRow.name)
                )
            ).all()
            team = await PostgresRepository(session).team(team_id)
            return {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "owner_id": row.owner_id,
                "skill_slugs": team.skill_slugs,
                "members": [{"id": m.id, "name": m.name} for m in members],
            }

    async def update(
        self, team_id: UUID, user: User, name: str, description: str, slugs: list[str]
    ):
        async with self.factory() as session:
            row = await self._team(session, team_id, user, owner=True)
            await PostgresRepository(session).validate_skills(slugs)
            row.name, row.description = name, description
            await session.execute(delete(TeamSkillRow).where(TeamSkillRow.team_id == team_id))
            skills = await session.scalars(select(SkillRow.id).where(SkillRow.slug.in_(slugs)))
            session.add_all(TeamSkillRow(team_id=team_id, skill_id=skill) for skill in skills)
            await session.commit()
        return await self.detail(team_id, user)

    async def invite(self, team_id: UUID, user: User):
        token = secrets.token_urlsafe(32)
        async with self.factory() as session:
            await self._team(session, team_id, user, owner=True)
            await session.execute(delete(InviteRow).where(InviteRow.team_id == team_id))
            session.add(
                InviteRow(
                    token_hash=digest(token), team_id=team_id, expires_at=now() + timedelta(days=7)
                )
            )
            await session.commit()
        return {
            "url": self.frontend_url.rstrip("/") + "/join#" + token,
            "message": "Одноразовая ссылка действует 7 дней. Новая ссылка заменяет предыдущую.",
        }

    async def join(self, token: str, user: User):
        require_role(user, Role.STUDENT)
        async with self.factory() as session:
            invitation = await session.get(InviteRow, digest(token))
            if invitation is None:
                raise DomainError(
                    "invalid_invite", "Приглашение недействительно или уже использовано.", 404
                )
            team_id = invitation.team_id
            # Same lock order as invite creation/removal: team, then invitation.
            await session.scalar(select(TeamRow).where(TeamRow.id == team_id).with_for_update())
            invitation = await session.scalar(
                select(InviteRow)
                .where(InviteRow.token_hash == digest(token))
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if invitation is None or invitation.expires_at <= now():
                raise DomainError(
                    "invalid_invite", "Срок приглашения истёк или ссылка использована.", 409
                )
            await session.execute(
                insert(TeamMemberRow)
                .values(team_id=team_id, user_id=user.id)
                .on_conflict_do_nothing()
            )
            await session.delete(invitation)
            await session.commit()
        return await self.detail(team_id, user)

    async def remove(self, team_id: UUID, member_id: UUID, user: User):
        async with self.factory() as session:
            row = await self._team(session, team_id, user)
            if member_id == row.owner_id:
                raise DomainError("owner_required", "Сначала передайте управление командой.", 409)
            if row.owner_id != user.id and member_id != user.id:
                raise DomainError("forbidden", "Удалять участников может только капитан.", 403)
            await session.execute(
                delete(TeamMemberRow).where(
                    TeamMemberRow.team_id == team_id, TeamMemberRow.user_id == member_id
                )
            )
            await session.commit()

    async def transfer(self, team_id: UUID, member_id: UUID, user: User):
        async with self.factory() as session:
            row = await self._team(session, team_id, user, owner=True)
            if await session.get(TeamMemberRow, (team_id, member_id)) is None:
                raise DomainError(
                    "not_member", "Новый капитан должен быть участником команды.", 422
                )
            row.owner_id = member_id
            await session.commit()
