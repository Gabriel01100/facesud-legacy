from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.identity.rate_limit import (
    LOGIN_EMAIL_IP_LIMIT,
    LOGIN_IP_LIMIT,
    LOGIN_WINDOW,
    consume_login_attempt,
)
from app.models.base import Base


def test_login_rate_limit_applies_per_email_and_ip_window():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start = datetime.now(timezone.utc)
        for _ in range(LOGIN_EMAIL_IP_LIMIT):
            assert consume_login_attempt(
                db, ip_address="192.0.2.1", email="person@example.com", now=start
            ) is None
        retry_after = consume_login_attempt(
            db, ip_address="192.0.2.1", email="person@example.com", now=start
        )
        assert retry_after is not None and retry_after >= int(LOGIN_WINDOW.total_seconds())
        db.rollback()
    engine.dispose()


def test_login_rate_limit_ip_bucket_is_shared_across_emails():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start = datetime.now(timezone.utc)
        for index in range(LOGIN_IP_LIMIT):
            assert consume_login_attempt(
                db, ip_address="192.0.2.2", email=f"user{index}@example.com", now=start
            ) is None
        assert consume_login_attempt(
            db, ip_address="192.0.2.2", email="another@example.com", now=start
        ) is not None
    engine.dispose()


def test_login_rate_limit_window_resets_after_fifteen_minutes():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start = datetime.now(timezone.utc)
        for _ in range(LOGIN_EMAIL_IP_LIMIT + 1):
            consume_login_attempt(db, ip_address="192.0.2.3", email="person@example.com", now=start)
        assert consume_login_attempt(
            db,
            ip_address="192.0.2.3",
            email="person@example.com",
            now=start + LOGIN_WINDOW + timedelta(seconds=1),
        ) is None
    engine.dispose()
