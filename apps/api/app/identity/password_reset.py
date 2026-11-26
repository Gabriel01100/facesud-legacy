from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.identity.security import hash_password, new_opaque_token, token_digest, verify_password
from app.models.identity import (
    Account,
    AccountStatus,
    PasswordCredential,
    PasswordResetToken,
    UserSession,
)

PASSWORD_RESET_TTL = timedelta(minutes=30)


def issue_password_reset_token(
    db: Session, account: Account, *, now: datetime | None = None
) -> str:
    current_time = now or datetime.now(timezone.utc)
    for existing in db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.account_id == account.id,
            PasswordResetToken.used_at.is_(None),
        )
    ):
        existing.used_at = current_time

    raw_token = new_opaque_token()
    db.add(
        PasswordResetToken(
            account_id=account.id,
            token_hash=token_digest(raw_token),
            created_at=current_time,
            expires_at=current_time + PASSWORD_RESET_TTL,
        )
    )
    db.flush()
    return raw_token


def reset_password(
    db: Session, *, raw_token: str, new_password: str, now: datetime | None = None
) -> bool:
    current_time = now or datetime.now(timezone.utc)
    token = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_digest(raw_token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > current_time,
        )
        .with_for_update()
    )
    if token is None:
        return False

    new_password_hash = hash_password(new_password)
    account = db.scalar(
        select(Account)
        .where(Account.id == token.account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is None or account.status != AccountStatus.ACTIVE:
        return False

    credential = db.scalar(
        select(PasswordCredential)
        .where(PasswordCredential.account_id == account.id)
        .with_for_update()
    )
    if credential is None:
        return False

    credential.password_hash = new_password_hash
    credential.password_changed_at = current_time
    token.used_at = current_time
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.account_id == account.id,
            PasswordResetToken.id != token.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=current_time)
    )
    db.execute(
        update(UserSession)
        .where(UserSession.account_id == account.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=current_time)
    )
    db.flush()
    return True


def change_password(
    db: Session,
    *,
    account_id,
    current_password: str,
    new_password: str,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(timezone.utc)
    credential_snapshot = db.get(PasswordCredential, account_id)
    if credential_snapshot is None or not verify_password(credential_snapshot.password_hash, current_password):
        return False

    new_password_hash = hash_password(new_password)
    account = db.scalar(
        select(Account)
        .where(Account.id == account_id, Account.status == AccountStatus.ACTIVE)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is None:
        return False

    credential = db.scalar(
        select(PasswordCredential)
        .where(PasswordCredential.account_id == account_id)
        .with_for_update()
    )
    if credential is None or credential.password_hash != credential_snapshot.password_hash:
        return False

    credential.password_hash = new_password_hash
    credential.password_changed_at = current_time
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.account_id == account_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=current_time)
    )
    db.execute(
        update(UserSession)
        .where(UserSession.account_id == account_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=current_time)
    )
    db.flush()
    return True
