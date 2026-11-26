from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.identity.cleanup import cleanup_identity_data
from app.identity.sessions import (
    MAX_ACTIVE_SESSIONS,
    SESSION_ABSOLUTE_TTL,
    SESSION_IDLE_TTL,
    SESSION_TOUCH_INTERVAL,
    AccountNotActiveError,
    create_session,
    get_active_session,
    touch_session,
)
from app.models.base import Base
from app.models.identity import Account, AccountStatus, UserSession


def test_session_policy_constants():
    assert SESSION_ABSOLUTE_TTL == timedelta(days=7)
    assert SESSION_IDLE_TTL == timedelta(minutes=30)
    assert MAX_ACTIVE_SESSIONS == 5
    assert SESSION_TOUCH_INTERVAL == timedelta(minutes=1)


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
        assert get_active_session(db, token, now=start + SESSION_IDLE_TTL) is None


def test_last_seen_updates_only_after_more_than_one_minute():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="touch@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        start = datetime.now(timezone.utc)
        session, _, _ = create_session(
            db,
            account_id=account.id,
            expires_at=start + SESSION_ABSOLUTE_TTL,
            now=start,
        )
        assert touch_session(db, session, now=start + timedelta(minutes=1)) is False
        assert session.last_seen_at == start
        assert touch_session(db, session, now=start + timedelta(minutes=1, seconds=1)) is True
        assert session.last_seen_at == start + timedelta(minutes=1, seconds=1)


def test_create_session_revalidates_account_status_after_lock():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="disabled@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.commit()
        account_id = account.id
        account.status = AccountStatus.DISABLED
        db.commit()

        with pytest.raises(AccountNotActiveError):
            create_session(
                db,
                account_id=account_id,
                expires_at=datetime.now(timezone.utc) + SESSION_ABSOLUTE_TTL,
            )
    engine.dispose()


def test_cleanup_removes_revoked_expired_idle_sessions_and_old_rate_limit_buckets():
    from app.models.identity import LoginRateLimit

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized="cleanup@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        now = datetime.now(timezone.utc)
        db.add_all([
            UserSession(
                account_id=account.id, token_hash="1" * 64, csrf_token_hash="a" * 64,
                created_at=now - timedelta(days=9), last_seen_at=now - timedelta(days=9),
                expires_at=now + timedelta(days=1),
            ),
            UserSession(
                account_id=account.id, token_hash="2" * 64, csrf_token_hash="b" * 64,
                created_at=now - timedelta(days=8), last_seen_at=now - timedelta(days=8),
                expires_at=now - timedelta(days=1),
            ),
        ])
        db.add(LoginRateLimit(bucket_hash="c" * 64, window_started_at=now - timedelta(hours=1), attempts=8))
        db.flush()
        assert cleanup_identity_data(db, now=now) == (2, 1)
        assert db.scalar(select(UserSession)) is None
        assert db.scalar(select(LoginRateLimit)) is None
    engine.dispose()


def test_concurrent_session_creation_respects_account_session_limit():
    import os
    from concurrent.futures import ThreadPoolExecutor
    from uuid import uuid4

    database_url = os.getenv("IDENTITY_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Requires the PostgreSQL identity integration database")

    engine = create_engine(database_url, pool_size=10, max_overflow=0)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(email_normalized=f"concurrency-{uuid4()}@example.com", status=AccountStatus.ACTIVE)
        db.add(account)
        db.commit()
        account_id = account.id

    def create_one_session(_index: int) -> None:
        now = datetime.now(timezone.utc)
        with Session(engine) as db:
            create_session(
                db,
                account_id=account_id,
                expires_at=now + SESSION_ABSOLUTE_TTL,
                now=now,
            )
            db.commit()

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(create_one_session, range(8)))
        with Session(engine) as db:
            active_count = len(list(db.scalars(
                select(UserSession).where(
                    UserSession.account_id == account_id,
                    UserSession.revoked_at.is_(None),
                )
            )))
        assert active_count == MAX_ACTIVE_SESSIONS
    finally:
        engine.dispose()
