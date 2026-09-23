from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain.entities import Assessment, Brief, ProposalStatus, TaskStatus

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8000)]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DraftInput(InputModel):
    raw_text: Text


class PatchInput(InputModel):
    title: str | None = Field(default=None, max_length=200)
    raw_text: Text | None = None
    problem: str | None = Field(default=None, max_length=8000)
    goal: str | None = Field(default=None, max_length=8000)
    deliverable: str | None = Field(default=None, max_length=8000)
    success_criteria: str | None = Field(default=None, max_length=8000)
    target_users: str | None = Field(default=None, max_length=8000)
    constraints: str | None = Field(default=None, max_length=8000)
    timeline: str | None = Field(default=None, max_length=8000)
    resources: str | None = Field(default=None, max_length=8000)
    risk_context: str | None = Field(default=None, max_length=8000)
    skill_slugs: list[Slug] | None = Field(default=None, max_length=30)
    expected_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def no_nulls(self):
        if not self.model_fields_set - {"expected_revision"}:
            raise ValueError("Укажите хотя бы одно поле для изменения.")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name}: используйте пустую строку вместо null.")
        if self.skill_slugs is not None:
            self.skill_slugs = sorted(set(self.skill_slugs))
        return self


class AnswerInput(InputModel):
    field: Literal[
        "problem",
        "goal",
        "deliverable",
        "success_criteria",
        "target_users",
        "constraints",
        "timeline",
        "resources",
        "risk_context",
    ]
    answer: Text


class TeamInput(InputModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=3000)
    skill_slugs: list[Slug] = Field(default_factory=list, max_length=30)


class ProposalInput(InputModel):
    team_id: UUID
    pitch: Text
    approach: Text
    timeline: str = Field(min_length=1, max_length=300)


class View(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PublicTask(View):
    id: UUID
    brief: Brief
    skill_slugs: list[str]
    status: TaskStatus
    quality_score: int
    quality_level: str
    published_at: datetime | None
    created_at: datetime


class TaskView(PublicTask):
    business_id: UUID
    raw_text: str
    revision: int
    assessment: Assessment | None
    updated_at: datetime


class TeamView(View):
    id: UUID
    name: str
    description: str
    member_ids: list[UUID]
    skill_slugs: list[str]


class ProposalView(View):
    id: UUID
    task_id: UUID
    team_id: UUID
    pitch: str
    approach: str
    timeline: str
    status: ProposalStatus
    created_at: datetime
    updated_at: datetime


class MatchView(View):
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    source: str
    reason: str


class RecommendationView(View):
    task: PublicTask
    match: MatchView


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
