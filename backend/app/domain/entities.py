from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class Role(StrEnum):
    BUSINESS = "business"
    STUDENT = "student"


class TaskStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    TEAM_SELECTED = "team_selected"


class ProposalStatus(StrEnum):
    SUBMITTED = "submitted"
    SELECTED = "selected"
    REJECTED = "rejected"


def now() -> datetime:
    return datetime.now(UTC)


@dataclass
class User:
    id: UUID
    name: str
    email: str
    role: Role


@dataclass
class Brief:
    title: str = ""
    problem: str = ""
    goal: str = ""
    deliverable: str = ""
    success_criteria: str = ""
    target_users: str = ""
    constraints: str = ""
    timeline: str = ""
    resources: str = ""
    risk_context: str = ""


@dataclass
class CriterionScore:
    score: int
    maximum: int
    reason: str


@dataclass
class Question:
    field: str
    question: str


@dataclass
class Assessment:
    total: int
    level: str
    source: str
    scores: dict[str, CriterionScore]
    missing_fields: list[str]
    next_questions: list[Question]
    warning: str | None = None


@dataclass
class Task:
    business_id: UUID
    raw_text: str
    id: UUID = field(default_factory=uuid4)
    brief: Brief = field(default_factory=Brief)
    skill_slugs: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.DRAFT
    quality_score: int = 0
    quality_level: str = "Draft"
    revision: int = 1
    assessment: Assessment | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)
    published_at: datetime | None = None


@dataclass
class Team:
    name: str
    description: str
    id: UUID = field(default_factory=uuid4)
    member_ids: list[UUID] = field(default_factory=list)
    skill_slugs: list[str] = field(default_factory=list)


@dataclass
class Proposal:
    task_id: UUID
    team_id: UUID
    pitch: str
    approach: str
    timeline: str
    id: UUID = field(default_factory=uuid4)
    status: ProposalStatus = ProposalStatus.SUBMITTED
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)
