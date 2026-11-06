"""Add subject ownership for default vs custom subjects.

Revision ID: 0002_subject_ownership
Revises: 0001_initial
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002_subject_ownership"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subjects",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_subjects_owner_id_users",
        "subjects",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("uq_subjects_name", "subjects", type_="unique")
    op.create_index("ix_subjects_owner_id", "subjects", ["owner_id"])
    op.execute(
        "CREATE UNIQUE INDEX uq_subjects_default_name_ci "
        "ON subjects (lower(name)) WHERE owner_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_subjects_owner_name_ci "
        "ON subjects (owner_id, lower(name)) WHERE owner_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_subjects_owner_name_ci")
    op.execute("DROP INDEX IF EXISTS uq_subjects_default_name_ci")
    op.drop_index("ix_subjects_owner_id", table_name="subjects")
    op.create_unique_constraint("uq_subjects_name", "subjects", ["name"])
    op.drop_constraint("fk_subjects_owner_id_users", "subjects", type_="foreignkey")
    op.drop_column("subjects", "owner_id")
