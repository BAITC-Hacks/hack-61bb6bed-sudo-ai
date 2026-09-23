from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.entities import ProposalStatus, Role, TaskStatus


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def enum_type(enum, name):
    return Enum(enum, name=name, values_callable=lambda values: [item.value for item in values])


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserRow(Timestamps, Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    role: Mapped[Role] = mapped_column(enum_type(Role, "user_role"), index=True)
    student_profile: Mapped[dict | None] = mapped_column(JSONB)
    password_hash: Mapped[str | None] = mapped_column(String(255))


class TeamRow(Timestamps, Base):
    __tablename__ = "teams"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    open_to_join: Mapped[bool] = mapped_column(Boolean, server_default="false", default=False)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class SessionRow(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InviteRow(Base):
    __tablename__ = "team_invites"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RateLimitRow(Base):
    __tablename__ = "rate_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer)
    resets_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class TeamMemberRow(Base):
    __tablename__ = "team_members"
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SkillRow(Base):
    __tablename__ = "skills"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(80), unique=True)


class TeamSkillRow(Base):
    __tablename__ = "team_skills"
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True
    )


class TaskRow(Timestamps, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("quality_score BETWEEN 0 AND 100", name="quality_range"),
        CheckConstraint("revision > 0", name="positive_revision"),
        CheckConstraint(
            "quality_level IN ('Draft', 'Basic', 'Ready', 'Strong', 'Excellent')",
            name="quality_level",
        ),
        Index("ix_tasks_catalog_quality", "status", text("quality_score DESC"), "id"),
        Index("ix_tasks_catalog_newest", "status", text("published_at DESC"), "id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    raw_text: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(200), default="")
    problem: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    deliverable: Mapped[str] = mapped_column(Text, default="")
    success_criteria: Mapped[str] = mapped_column(Text, default="")
    target_users: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    timeline: Mapped[str] = mapped_column(Text, default="")
    resources: Mapped[str] = mapped_column(Text, default="")
    risk_context: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(enum_type(TaskStatus, "task_status"), index=True)
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    quality_level: Mapped[str] = mapped_column(String(16), default="Draft")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    assessment_json: Mapped[dict | None] = mapped_column(JSONB)
    interview_plan_json: Mapped[dict | None] = mapped_column(JSONB)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskSkillRow(Base):
    __tablename__ = "task_skills"
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True
    )


class ScoreRow(Base):
    """One immutable score snapshot per evaluated revision, including all criterion scores."""

    __tablename__ = "task_score_history"
    __table_args__ = (
        UniqueConstraint("task_id", "revision"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    revision: Mapped[int]
    score: Mapped[int]
    reason: Mapped[str] = mapped_column(String(40))
    feedback: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnswerRow(Base):
    __tablename__ = "interview_answers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    field: Mapped[str] = mapped_column(String(40))
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProposalRow(Timestamps, Base):
    business_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __tablename__ = "proposals"
    __table_args__ = (
        UniqueConstraint("task_id", "team_id"),
        Index(
            "uq_proposals_one_selected",
            "task_id",
            unique=True,
            postgresql_where=text("status = 'selected'"),
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="RESTRICT"), index=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), index=True)
    pitch: Mapped[str] = mapped_column(Text)
    approach: Mapped[str] = mapped_column(Text)
    timeline: Mapped[str] = mapped_column(String(300))
    status: Mapped[ProposalStatus] = mapped_column(enum_type(ProposalStatus, "proposal_status"))
