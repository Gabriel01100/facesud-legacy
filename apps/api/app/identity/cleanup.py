from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, or_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.identity.rate_limit import LOGIN_WINDOW, PASSWORD_RESET_WINDOW, REGISTRATION_WINDOW, RESEND_WINDOW
from app.identity.sessions import SESSION_IDLE_TTL
from app.models.identity import EmailVerificationToken, LoginRateLimit, PasswordResetToken, UserSession


def cleanup_identity_data(db: Session, *, now: datetime | None = None) -> tuple[int, int]:
    current_time = now or datetime.now(timezone.utc)
    idle_cutoff = current_time - SESSION_IDLE_TTL
    sessions_result = db.execute(
        delete(UserSession).where(
            or_(
                UserSession.revoked_at.is_not(None),
                UserSession.expires_at <= current_time,
                func.coalesce(UserSession.last_seen_at, UserSession.created_at) <= idle_cutoff,
            )
        )
    )
    token_retention_cutoff = current_time - timedelta(days=7)
    db.execute(
        delete(EmailVerificationToken).where(
            EmailVerificationToken.created_at < token_retention_cutoff,
            or_(
                EmailVerificationToken.used_at.is_not(None),
                EmailVerificationToken.expires_at <= current_time,
            ),
        )
    )
    db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.created_at < token_retention_cutoff,
            or_(
                PasswordResetToken.used_at.is_not(None),
                PasswordResetToken.expires_at <= current_time,
            ),
        )
    )
    rate_limit_retention = max(LOGIN_WINDOW, REGISTRATION_WINDOW, RESEND_WINDOW, PASSWORD_RESET_WINDOW)
    rate_limits_result = db.execute(
        delete(LoginRateLimit).where(
            LoginRateLimit.window_started_at <= current_time - rate_limit_retention
        )
    )
    db.flush()
    return sessions_result.rowcount or 0, rate_limits_result.rowcount or 0


def main() -> None:
    with SessionLocal() as db:
        deleted_sessions, deleted_buckets = cleanup_identity_data(db)
        db.commit()
    print(f"Deleted {deleted_sessions} expired/revoked sessions and {deleted_buckets} stale identity rate-limit buckets")


if __name__ == "__main__":
    main()
