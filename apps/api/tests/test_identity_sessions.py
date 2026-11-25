from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.identity.sessions import (
    create_session,
    get_active_session,
    normalize_email,
    revoke_session,
    verify_csrf_token,
)
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
        assert verify_csrf_token(session, csrf_token)
        assert not verify_csrf_token(session, "incorrect-csrf-token")
        assert get_active_session(db, raw_token) is not None
        assert revoke_session(db, raw_token)
        assert get_active_session(db, raw_token) is None


def test_pending_email_account_cannot_use_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="pending@example.com", status=AccountStatus.PENDING_EMAIL)
        db.add(account)
        db.flush()

        _, raw_token, _ = create_session(
            db,
            account_id=account.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert get_active_session(db, raw_token) is None


def test_expired_session_is_not_active():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="expired@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        _, raw_token, _ = create_session(
            db,
            account_id=account.id,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=1),
        )
        assert get_active_session(db, raw_token, now=datetime.now(timezone.utc) + timedelta(seconds=2)) is None
