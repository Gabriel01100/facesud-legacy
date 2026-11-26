import hmac
import unicodedata
from datetime import datetime, timedelta, timezone
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.security import new_opaque_token, new_session_secrets, token_digest
from app.models.identity import Account, AccountStatus, UserSession

SESSION_ABSOLUTE_TTL = timedelta(days=7)
SESSION_IDLE_TTL = timedelta(minutes=30)
SESSION_TOUCH_INTERVAL = timedelta(minutes=1)
MAX_ACTIVE_SESSIONS = 5


class AccountNotActiveError(RuntimeError):
    pass


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def normalize_email(email: str) -> str:
    candidate = unicodedata.normalize("NFC", email.strip())
    if not candidate or len(candidate) > 320:
        raise ValueError("A valid email address is required")
    try:
        validated = validate_email(candidate, check_deliverability=False, allow_smtputf8=True)
    except EmailNotValidError as exc:
        raise ValueError("A valid email address is required") from exc
    normalized = unicodedata.normalize("NFC", validated.normalized).casefold()
    if len(normalized) > 320:
        raise ValueError("A valid email address is required")
    return normalized


def create_session(
    db: Session,
    *,
    account_id: UUID,
    expires_at: datetime,
    now: datetime | None = None,
) -> tuple[UserSession, str, str]:
    current_time = now or datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        raise ValueError("Session expiration must be timezone-aware")
    if _utc(expires_at) <= _utc(current_time):
        raise ValueError("Session expiration must be in the future")
    if _utc(expires_at) > _utc(current_time) + SESSION_ABSOLUTE_TTL:
        raise ValueError("Session expiration exceeds the absolute session lifetime")

    account = db.scalar(
        select(Account)
        .where(Account.id == account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is None or account.status != AccountStatus.ACTIVE:
        raise AccountNotActiveError("Account is not active")

    active_sessions = list(
        db.scalars(
            select(UserSession).where(
                UserSession.account_id == account_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > current_time,
            )
        )
    )
    active_sessions = [
        item for item in active_sessions
        if current_time - _utc(item.last_seen_at or item.created_at) < SESSION_IDLE_TTL
    ]
    active_sessions.sort(key=lambda item: _utc(item.created_at))

    while len(active_sessions) >= MAX_ACTIVE_SESSIONS:
        oldest = active_sessions.pop(0)
        oldest.revoked_at = current_time

    raw_session_token, raw_csrf_token = new_session_secrets()
    session = UserSession(
        account_id=account_id,
        token_hash=token_digest(raw_session_token),
        csrf_token_hash=token_digest(raw_csrf_token),
        created_at=current_time,
        last_seen_at=current_time,
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    return session, raw_session_token, raw_csrf_token


def get_active_session(
    db: Session,
    raw_token: str,
    *,
    now: datetime | None = None,
    touch: bool = True,
) -> UserSession | None:
    current_time = now or datetime.now(timezone.utc)
    statement = (
        select(UserSession)
        .join(Account)
        .where(
            UserSession.token_hash == token_digest(raw_token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > current_time,
            Account.status == AccountStatus.ACTIVE,
        )
    )
    session = db.scalar(statement)
    if session is None:
        return None

    last_activity = _utc(session.last_seen_at or session.created_at)
    if _utc(current_time) - last_activity >= SESSION_IDLE_TTL:
        session.revoked_at = current_time
        db.flush()
        return None

    if touch:
        touch_session(db, session, now=current_time)
    return session


def touch_session(db: Session, session: UserSession, *, now: datetime | None = None) -> bool:
    current_time = now or datetime.now(timezone.utc)
    last_activity = _utc(session.last_seen_at or session.created_at)
    if _utc(current_time) - last_activity <= SESSION_TOUCH_INTERVAL:
        return False
    session.last_seen_at = current_time
    db.flush()
    return True


def rotate_csrf_token(db: Session, session: UserSession) -> str:
    raw_token = new_opaque_token()
    session.csrf_token_hash = token_digest(raw_token)
    db.flush()
    return raw_token


def verify_csrf_token(session: UserSession, raw_token: str) -> bool:
    return hmac.compare_digest(session.csrf_token_hash, token_digest(raw_token))


def revoke_session(db: Session, raw_token: str, *, now: datetime | None = None) -> bool:
    session = db.scalar(select(UserSession).where(UserSession.token_hash == token_digest(raw_token)))
    if session is None or session.revoked_at is not None:
        return False
    session.revoked_at = now or datetime.now(timezone.utc)
    db.flush()
    return True
