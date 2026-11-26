from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.security import hash_password, new_opaque_token, token_digest
from app.identity.sessions import normalize_email
from app.models.identity import Account, AccountStatus, EmailVerificationToken, PasswordCredential

EMAIL_VERIFICATION_TTL = timedelta(hours=24)


def create_pending_account(
    db: Session, *, email: str, password: str, now: datetime | None = None
) -> tuple[Account, str] | None:
    normalized_email = normalize_email(email)
    current_time = now or datetime.now(timezone.utc)
    if db.scalar(select(Account.id).where(Account.email_normalized == normalized_email)) is not None:
        return None

    account = Account(email_normalized=normalized_email, status=AccountStatus.PENDING_EMAIL)
    db.add(account)
    db.flush()
    db.add(PasswordCredential(account_id=account.id, password_hash=hash_password(password)))
    raw_token = _issue_verification_token(db, account, now=current_time)
    db.flush()
    return account, raw_token


def issue_new_verification_token(
    db: Session, account: Account, *, now: datetime | None = None
) -> str:
    current_time = now or datetime.now(timezone.utc)
    for existing in db.scalars(
        select(EmailVerificationToken).where(
            EmailVerificationToken.account_id == account.id,
            EmailVerificationToken.used_at.is_(None),
        )
    ):
        existing.used_at = current_time
    return _issue_verification_token(db, account, now=current_time)


def _issue_verification_token(db: Session, account: Account, *, now: datetime) -> str:
    raw_token = new_opaque_token()
    db.add(
        EmailVerificationToken(
            account_id=account.id,
            token_hash=token_digest(raw_token),
            created_at=now,
            expires_at=now + EMAIL_VERIFICATION_TTL,
        )
    )
    return raw_token


def verify_email_token(db: Session, raw_token: str, *, now: datetime | None = None) -> Account | None:
    current_time = now or datetime.now(timezone.utc)
    token = db.scalar(
        select(EmailVerificationToken)
        .where(
            EmailVerificationToken.token_hash == token_digest(raw_token),
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > current_time,
        )
        .with_for_update()
    )
    if token is None:
        return None

    account = db.scalar(select(Account).where(Account.id == token.account_id).with_for_update())
    if account is None or account.status != AccountStatus.PENDING_EMAIL:
        return None

    token.used_at = current_time
    account.status = AccountStatus.ACTIVE
    db.flush()
    return account
