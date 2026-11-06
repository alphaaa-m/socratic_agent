"""Idempotent default-subject catalog. Course outlines are deferred to Phase 7."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Subject

# Shared defaults for every account. Names are the public catalog identifiers.
DEFAULT_SUBJECTS = (
    ("Python", "Variables, control flow, functions, data structures and common pitfalls."),
    ("Basic Mathematics", "Fractions, algebra basics, and number sense."),
    ("Databases", "Tables, keys, SQL queries and normalization."),
    ("OOP", "Classes, objects, inheritance, encapsulation and polymorphism."),
    ("Machine Learning", "Supervised learning, features, models and evaluation."),
    ("DSA", "Arrays, lists, stacks, queues, trees, graphs and algorithm analysis."),
)

# Preserve existing default rows created by the earlier three-subject seed.
_LEGACY_DEFAULT_NAMES = {
    "Python Programming": "Python",
    "Introduction to Databases": "Databases",
}


def seed_default_subjects(db: Session) -> int:
    """Insert missing default subjects. Safe to run more than once."""
    for old_name, new_name in _LEGACY_DEFAULT_NAMES.items():
        already_renamed = db.scalar(
            select(Subject.id).where(Subject.owner_id.is_(None), Subject.name == new_name)
        )
        legacy = db.scalar(
            select(Subject).where(Subject.owner_id.is_(None), Subject.name == old_name)
        )
        if legacy is not None and already_renamed is None:
            legacy.name = new_name

    created = 0
    for name, description in DEFAULT_SUBJECTS:
        existing = db.scalar(
            select(Subject).where(
                Subject.owner_id.is_(None),
                func.lower(Subject.name) == name.lower(),
            )
        )
        if existing is None:
            db.add(Subject(name=name, description=description, owner_id=None, is_active=True))
            created += 1
        elif existing.name != name:
            existing.name = name
    return created
