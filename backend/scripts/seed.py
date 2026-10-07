# scripts/seed.py -- Phase 0 (guide Sec 0.4 Step 5)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Subject

SUBJECTS = [
    ("Python Programming", "Variables, control flow, functions, data structures and common pitfalls."),
    ("Basic Mathematics", "Fractions, algebra basics, and number sense."),
    ("Introduction to Databases", "Tables, keys, SQL queries and normalization."),
]

with SessionLocal() as db, db.begin():
    for name, description in SUBJECTS:
        if not db.scalar(select(Subject).where(Subject.name == name)):
            db.add(Subject(name=name, description=description))
print("seed done")
