"""Persist generated interview plans."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e018af20c101"
down_revision = "dabbc2819b60"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("interview_plan_json", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("tasks", "interview_plan_json")
