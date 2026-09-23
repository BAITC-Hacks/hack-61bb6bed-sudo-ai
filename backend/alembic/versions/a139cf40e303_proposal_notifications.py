"""Persistent business notification read state."""

import sqlalchemy as sa

from alembic import op

revision = "a139cf40e303"
down_revision = "f028bf30d202"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "proposals", sa.Column("business_read_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    op.drop_column("proposals", "business_read_at")
