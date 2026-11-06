# scripts/seed.py -- Phase 0 (guide Sec 0.4 Step 5)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.services.subject_seed import seed_default_subjects

with SessionLocal() as db, db.begin():
    created = seed_default_subjects(db)
print(f"seed done ({created} new default subjects)")
