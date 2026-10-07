# scripts/create_admin.py -- Phase 0 (guide Sec 0.4 Step 5)
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.auth.passwords import hash_password
from app.database.session import SessionLocal
from app.models import LearnerProfile, User

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--name", default="Administrator")
args = parser.parse_args()
password = getpass.getpass("Password: ")

with SessionLocal() as db, db.begin():
    user = db.scalar(select(User).where(User.email == args.email.lower()))
    if user is None:
        user = User(name=args.name, email=args.email.lower(), password_hash=hash_password(password), role="admin")
        db.add(user)
        db.flush()
        db.add(LearnerProfile(user_id=user.id))
    else:
        user.role = "admin"
print("admin ready")
