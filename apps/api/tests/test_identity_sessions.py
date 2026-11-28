from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.identity.sessions import (
    AccountNotActiveError,
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


def test_pending_email_account_cannot_create_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="pending@example.com", status=AccountStatus.PENDING_EMAIL)
        db.add(account)
        db.flush()

        with pytest.raises(AccountNotActiveError):
            create_session(
                db,
                account_id=account.id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )


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


def test_create_session_rejects_expiration_beyond_absolute_lifetime():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="long-session@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        now = datetime.now(timezone.utc)

        with pytest.raises(ValueError, match="absolute session lifetime"):
            create_session(
                db,
                account_id=account.id,
                expires_at=now + timedelta(days=7, microseconds=1),
                now=now,
            )
    engine.dispose()


def test_create_session_accepts_exact_absolute_lifetime_boundary():
    from app.identity.sessions import SESSION_ABSOLUTE_TTL

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="boundary@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        now = datetime.now(timezone.utc)

        session, token, _ = create_session(
            db,
            account_id=account.id,
            expires_at=now + SESSION_ABSOLUTE_TTL,
            now=now,
        )

        assert session.expires_at == now + SESSION_ABSOLUTE_TTL
        assert get_active_session(db, token, now=now + SESSION_ABSOLUTE_TTL - timedelta(microseconds=1)) is not None
        assert get_active_session(db, token, now=now + SESSION_ABSOLUTE_TTL) is None
    engine.dispose()


def test_revoke_session_is_idempotent():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="revoke@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        now = datetime.now(timezone.utc)
        _, token, _ = create_session(
            db,
            account_id=account.id,
            expires_at=now + timedelta(hours=1),
            now=now,
        )

        assert revoke_session(db, token, now=now + timedelta(seconds=1)) is True
        assert revoke_session(db, token, now=now + timedelta(seconds=2)) is False
    engine.dispose()
