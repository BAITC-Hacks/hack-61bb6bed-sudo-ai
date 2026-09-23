"""Student skills and opt-in open teams."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f028bf30d202"
down_revision = "e018af20c101"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("student_profile", postgresql.JSONB(), nullable=True))
    op.add_column(
        "teams", sa.Column("open_to_join", sa.Boolean(), server_default=sa.false(), nullable=False)
    )


def downgrade():
    op.drop_column("teams", "open_to_join")
    op.drop_column("users", "student_profile")
