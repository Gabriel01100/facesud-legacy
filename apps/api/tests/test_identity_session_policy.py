from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.identity.sessions import (
    MAX_ACTIVE_SESSIONS,
    SESSION_ABSOLUTE_TTL,
    SESSION_IDLE_TTL,
    create_session,
    get_active_session,
)
from app.models.base import Base
from app.models.identity import Account, AccountStatus, UserSession


def test_session_policy_constants():
    assert SESSION_ABSOLUTE_TTL == timedelta(days=7)
    assert SESSION_IDLE_TTL == timedelta(minutes=30)
    assert MAX_ACTIVE_SESSIONS == 5


def test_sixth_session_revokes_oldest_active_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="sessions@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        start = datetime.now(timezone.utc)

        issued = []
        for index in range(MAX_ACTIVE_SESSIONS + 1):
            _, token, _ = create_session(
                db,
                account_id=account.id,
                expires_at=start + SESSION_ABSOLUTE_TTL,
                now=start + timedelta(seconds=index),
            )
            issued.append(token)

        db.flush()
        assert get_active_session(db, issued[0], now=start + timedelta(seconds=6)) is None
        assert get_active_session(db, issued[-1], now=start + timedelta(seconds=6)) is not None
        active_count = db.scalar(
            select(UserSession).where(
                UserSession.account_id == account.id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > start + timedelta(seconds=6),
            ).count()
        ) if False else None
        assert sum(get_active_session(db, token, now=start + timedelta(seconds=7)) is not None for token in issued) == MAX_ACTIVE_SESSIONS


def test_idle_session_is_revoked_after_thirty_minutes():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="idle@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        start = datetime.now(timezone.utc)
        _, token, _ = create_session(
            db,
            account_id=account.id,
            expires_at=start + SESSION_ABSOLUTE_TTL,
            now=start,
        )
        assert get_active_session(db, token, now=start + SESSION_IDLE_TTL + timedelta(seconds=1)) is None
