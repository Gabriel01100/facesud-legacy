import hashlib
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.identity.sessions import normalize_email
from app.models.identity import LoginRateLimit

LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_EMAIL_IP_LIMIT = 5
LOGIN_IP_LIMIT = 30

REGISTRATION_WINDOW = timedelta(hours=1)
REGISTRATION_EMAIL_IP_LIMIT = 2
REGISTRATION_IP_LIMIT = 5

RESEND_WINDOW = timedelta(hours=1)
RESEND_EMAIL_IP_LIMIT = 3
RESEND_IP_LIMIT = 10

PASSWORD_RESET_WINDOW = timedelta(hours=1)
PASSWORD_RESET_EMAIL_IP_LIMIT = 3
PASSWORD_RESET_IP_LIMIT = 10


def _bucket_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _upsert_attempt(
    db: Session, bucket_hash: str, *, now: datetime, window: timedelta
) -> tuple[int, datetime]:
    table = LoginRateLimit.__table__
    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        insert = pg_insert(table)
    elif dialect == "sqlite":
        insert = sqlite_insert(table)
    else:
        raise RuntimeError(f"Unsupported database for identity rate limiting: {dialect}")

    reset = table.c.window_started_at <= now - window
    statement = insert.values(
        bucket_hash=bucket_hash,
        window_started_at=now,
        attempts=1,
    ).on_conflict_do_update(
        index_elements=[table.c.bucket_hash],
        set_={
            "window_started_at": case((reset, now), else_=table.c.window_started_at),
            "attempts": case((reset, 1), else_=table.c.attempts + 1),
        },
    ).returning(table.c.attempts, table.c.window_started_at)

    attempts, window_started_at = db.execute(statement).one()
    return attempts, _as_utc(window_started_at)


def _consume_scoped_attempts(
    db: Session,
    *,
    scope: str,
    ip_address: str,
    email: str,
    window: timedelta,
    email_ip_limit: int,
    ip_limit: int,
    now: datetime | None = None,
) -> int | None:
    current_time = _as_utc(now or datetime.now(timezone.utc))
    try:
        normalized_email = normalize_email(email)
    except ValueError:
        normalized_email = email.strip().casefold()[:320]

    email_ip_key = _bucket_hash(f"{scope}:email-ip:{ip_address}:{normalized_email}")
    ip_key = _bucket_hash(f"{scope}:ip:{ip_address}")

    email_attempts, email_window = _upsert_attempt(
        db, email_ip_key, now=current_time, window=window
    )
    ip_attempts, ip_window = _upsert_attempt(
        db, ip_key, now=current_time, window=window
    )

    retry_after = 0
    if email_attempts > email_ip_limit:
        retry_after = max(
            retry_after,
            math.ceil((email_window + window - current_time).total_seconds()),
        )
    if ip_attempts > ip_limit:
        retry_after = max(
            retry_after,
            math.ceil((ip_window + window - current_time).total_seconds()),
        )
    return max(1, retry_after) if retry_after else None


def consume_login_attempt(
    db: Session,
    *,
    ip_address: str,
    email: str,
    now: datetime | None = None,
) -> int | None:
    return _consume_scoped_attempts(
        db,
        scope="login",
        ip_address=ip_address,
        email=email,
        window=LOGIN_WINDOW,
        email_ip_limit=LOGIN_EMAIL_IP_LIMIT,
        ip_limit=LOGIN_IP_LIMIT,
        now=now,
    )


def consume_registration_attempt(
    db: Session,
    *,
    ip_address: str,
    email: str,
    now: datetime | None = None,
) -> int | None:
    return _consume_scoped_attempts(
        db,
        scope="register",
        ip_address=ip_address,
        email=email,
        window=REGISTRATION_WINDOW,
        email_ip_limit=REGISTRATION_EMAIL_IP_LIMIT,
        ip_limit=REGISTRATION_IP_LIMIT,
        now=now,
    )


def consume_resend_attempt(
    db: Session,
    *,
    ip_address: str,
    email: str,
    now: datetime | None = None,
) -> int | None:
    return _consume_scoped_attempts(
        db,
        scope="resend",
        ip_address=ip_address,
        email=email,
        window=RESEND_WINDOW,
        email_ip_limit=RESEND_EMAIL_IP_LIMIT,
        ip_limit=RESEND_IP_LIMIT,
        now=now,
    )


def clear_login_attempts(db: Session, *, ip_address: str, email: str) -> None:
    try:
        normalized_email = normalize_email(email)
    except ValueError:
        normalized_email = email.strip().casefold()[:320]
    keys = [
        _bucket_hash(f"login:email-ip:{ip_address}:{normalized_email}"),
        _bucket_hash(f"login:ip:{ip_address}"),
    ]
    db.execute(delete(LoginRateLimit).where(LoginRateLimit.bucket_hash.in_(keys)))


def consume_password_reset_attempt(
    db: Session,
    *,
    ip_address: str,
    email: str,
    now: datetime | None = None,
) -> int | None:
    return _consume_scoped_attempts(
        db,
        scope="password-reset",
        ip_address=ip_address,
        email=email,
        window=PASSWORD_RESET_WINDOW,
        email_ip_limit=PASSWORD_RESET_EMAIL_IP_LIMIT,
        ip_limit=PASSWORD_RESET_IP_LIMIT,
        now=now,
    )
