import pytest
from sqlalchemy.exc import IntegrityError

from app.models import User


def test_email_must_be_lowercase(db):
    db.add(User(name="A", email="A@B.CO", password_hash="x"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_role_check(db):
    db.add(User(name="A", email="a@b.co", password_hash="x", role="teacher"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_message_content_not_empty(db):
    from app.models import LearningSession, Message, Subject, User

    user = User(name="U", email="u@e.co", password_hash="x")
    db.add(user)
    db.flush()
    subject = Subject(name="S1", description="d")
    db.add(subject)
    db.flush()
    session = LearningSession(user_id=user.id, subject_id=subject.id)
    db.add(session)
    db.flush()
    db.add(Message(session_id=session.id, sender="student", content="", message_type="question"))
    with pytest.raises(IntegrityError):
        db.flush()
