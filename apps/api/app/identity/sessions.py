import hmac
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.security import new_session_secrets, token_digest
from app.models.identity import Account, AccountStatus, UserSession


def normalize_email(email: str) -> str:
    normalized = email.strip().casefold()
    if not normalized or len(normalized) > 320 or "@" not in normalized:
        raise ValueError("A valid email address is required")
    return normalized


def create_session(
    db: Session,
    *,
    account_id: UUID,
    expires_at: datetime,
) -> tuple[UserSession, str, str]:
    if expires_at.tzinfo is None:
        raise ValueError("Session expiration must be timezone-aware")
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("Session expiration must be in the future")

    raw_session_token, raw_csrf_token = new_session_secrets()
    session = UserSession(
        account_id=account_id,
        token_hash=token_digest(raw_session_token),
        csrf_token_hash=token_digest(raw_csrf_token),
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    return session, raw_session_token, raw_csrf_token


def get_active_session(db: Session, raw_token: str, *, now: datetime | None = None) -> UserSession | None:
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
    return db.scalar(statement)


def verify_csrf_token(session: UserSession, raw_token: str) -> bool:
    return hmac.compare_digest(session.csrf_token_hash, token_digest(raw_token))


def revoke_session(db: Session, raw_token: str, *, now: datetime | None = None) -> bool:
    session = db.scalar(select(UserSession).where(UserSession.token_hash == token_digest(raw_token)))
    if session is None or session.revoked_at is not None:
        return False
    session.revoked_at = now or datetime.now(timezone.utc)
    db.flush()
    return True
