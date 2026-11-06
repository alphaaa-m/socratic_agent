"""Seed the shared default subject catalog.

Revision ID: 0003_seed_default_subjects
Revises: 0002_subject_ownership
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_seed_default_subjects"
down_revision = "0002_subject_ownership"
branch_labels = None
depends_on = None

DEFAULT_SUBJECTS = (
    ("Python", "Variables, control flow, functions, data structures and common pitfalls."),
    ("Basic Mathematics", "Fractions, algebra basics, and number sense."),
    ("Databases", "Tables, keys, SQL queries and normalization."),
    ("OOP", "Classes, objects, inheritance, encapsulation and polymorphism."),
    ("Machine Learning", "Supervised learning, features, models and evaluation."),
    ("DSA", "Arrays, lists, stacks, queues, trees, graphs and algorithm analysis."),
)


def upgrade() -> None:
    bind = op.get_bind()
    subjects = sa.table(
        "subjects",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_active", sa.Boolean()),
        sa.column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True)),
    )
    existing = {
        name.casefold(): subject_id
        for subject_id, name in bind.execute(
            sa.select(subjects.c.id, subjects.c.name).where(subjects.c.owner_id.is_(None))
        )
    }
    legacy_names = {"python programming": "Python", "introduction to databases": "Databases"}
    for old_name, new_name in legacy_names.items():
        if old_name in existing and new_name.casefold() not in existing:
            bind.execute(
                subjects.update().where(subjects.c.id == existing[old_name]).values(name=new_name)
            )
            existing[new_name.casefold()] = existing.pop(old_name)

    for name, description in DEFAULT_SUBJECTS:
        if name.casefold() not in existing:
            bind.execute(
                subjects.insert().values(
                    name=name, description=description, is_active=True, owner_id=None
                )
            )


def downgrade() -> None:
    # Default subjects are durable catalog data and may already have sessions.
    pass
