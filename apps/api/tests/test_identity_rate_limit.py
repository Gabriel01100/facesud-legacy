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


def test_registration_rate_limit_is_scoped_by_ip_and_email():
    from app.identity.rate_limit import (
        REGISTRATION_EMAIL_IP_LIMIT,
        REGISTRATION_WINDOW,
        consume_registration_attempt,
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start = datetime.now(timezone.utc)
        for _ in range(REGISTRATION_EMAIL_IP_LIMIT):
            assert consume_registration_attempt(
                db, ip_address="192.0.2.10", email="person@example.com", now=start
            ) is None
        retry_after = consume_registration_attempt(
            db, ip_address="192.0.2.10", email="person@example.com", now=start
        )
        assert retry_after is not None and retry_after >= int(REGISTRATION_WINDOW.total_seconds())
    engine.dispose()


def test_registration_ip_limit_is_shared_across_email_addresses():
    from app.identity.rate_limit import REGISTRATION_IP_LIMIT, consume_registration_attempt

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start = datetime.now(timezone.utc)
        for index in range(REGISTRATION_IP_LIMIT):
            assert consume_registration_attempt(
                db, ip_address="192.0.2.11", email=f"user{index}@example.com", now=start
            ) is None
        assert consume_registration_attempt(
            db, ip_address="192.0.2.11", email="another@example.com", now=start
        ) is not None
    engine.dispose()


def test_resend_rate_limit_is_separate_from_registration_and_login():
    from app.identity.rate_limit import (
        RESEND_EMAIL_IP_LIMIT,
        consume_registration_attempt,
        consume_resend_attempt,
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start = datetime.now(timezone.utc)
        for _ in range(RESEND_EMAIL_IP_LIMIT):
            assert consume_resend_attempt(
                db, ip_address="192.0.2.12", email="person@example.com", now=start
            ) is None
        assert consume_resend_attempt(
            db, ip_address="192.0.2.12", email="person@example.com", now=start
        ) is not None
        assert consume_registration_attempt(
            db, ip_address="192.0.2.12", email="person@example.com", now=start
        ) is None
    engine.dispose()
