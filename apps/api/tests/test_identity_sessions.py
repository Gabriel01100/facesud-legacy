from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.identity.sessions import create_session, get_active_session, normalize_email, revoke_session
from app.models.base import Base
from app.models.identity import Account, AccountStatus


def test_normalize_email():
    assert normalize_email("  Person@Example.COM ") == "person@example.com"


def test_create_and_revoke_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="person@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session, raw_token, csrf_token = create_session(db, account_id=account.id, expires_at=expires_at)
        db.flush()

        assert session.token_hash != raw_token
        assert len(session.token_hash) == 64
        assert csrf_token
        assert get_active_session(db, raw_token) is not None
        assert revoke_session(db, raw_token)
        assert get_active_session(db, raw_token) is None
