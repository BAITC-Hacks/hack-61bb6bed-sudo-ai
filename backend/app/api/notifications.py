from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, update

from app.api.deps import current_user
from app.domain.entities import DomainError, Role, User, now
from app.infrastructure.db.models import ProposalRow, TaskRow, TeamRow

router = APIRouter(prefix="/api/v1/business/notifications", tags=["notifications"])
Actor = Annotated[User, Depends(current_user)]


def business(actor):
    if actor.role != Role.BUSINESS:
        raise DomainError("forbidden", "Уведомления доступны владельцу бизнеса.", 403)


@router.get("")
async def notifications(
    request: Request,
    actor: Actor,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    business(actor)
    async with request.app.state.accounts.factory() as session:
        scope = TaskRow.business_id == actor.id
        total = await session.scalar(
            select(func.count()).select_from(ProposalRow).join(TaskRow).where(scope)
        )
        unread = await session.scalar(
            select(func.count())
            .select_from(ProposalRow)
            .join(TaskRow)
            .where(scope, ProposalRow.business_read_at.is_(None))
        )
        rows = await session.execute(
            select(ProposalRow, TaskRow.title, TeamRow.name)
            .join(TaskRow)
            .join(TeamRow, TeamRow.id == ProposalRow.team_id)
            .where(scope)
            .order_by(ProposalRow.created_at.desc(), ProposalRow.id)
            .offset(offset)
            .limit(limit)
        )
        return {
            "items": [
                {
                    "id": p.id,
                    "task_id": p.task_id,
                    "task_title": title,
                    "team_name": name,
                    "created_at": p.created_at,
                    "read": p.business_read_at is not None,
                }
                for p, title, name in rows
            ],
            "total": total,
            "unread_count": unread,
        }


@router.post("/{proposal_id}/read")
async def mark_read(proposal_id: UUID, request: Request, actor: Actor):
    business(actor)
    async with request.app.state.accounts.factory() as session:
        owned = select(TaskRow.id).where(TaskRow.business_id == actor.id)
        result = await session.execute(
            update(ProposalRow)
            .where(ProposalRow.id == proposal_id, ProposalRow.task_id.in_(owned))
            .values(business_read_at=func.coalesce(ProposalRow.business_read_at, now()))
            .returning(ProposalRow.id)
        )
        if result.scalar_one_or_none() is None:
            raise DomainError("not_found", "Уведомление не найдено.", 404)
        await session.commit()
        return {"ok": True}
