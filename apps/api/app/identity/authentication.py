from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.security import DUMMY_PASSWORD_HASH, verify_password
from app.identity.sessions import normalize_email
from app.models.identity import Account, AccountStatus, PasswordCredential


def authenticate_local_account(db: Session, email: str, password: str) -> Account | None:
    try:
        normalized_email = normalize_email(email)
    except ValueError:
        normalized_email = ""

    account = (
        db.scalar(
            select(Account)
            .join(PasswordCredential)
            .where(Account.email_normalized == normalized_email)
        )
        if normalized_email
        else None
    )

    if account is None:
        verify_password(DUMMY_PASSWORD_HASH, password[:1024])
        return None

    credential = account.password_credential
    if credential is None or len(password) > 1024 or not verify_password(credential.password_hash, password):
        return None

    if account.status != AccountStatus.ACTIVE:
        return None

    return account
