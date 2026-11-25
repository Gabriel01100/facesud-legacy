from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.security import verify_password
from app.identity.sessions import normalize_email
from app.models.identity import Account, AccountStatus, PasswordCredential

# A fixed dummy hash keeps the expensive password verification path similar
# when an email address does not exist.
_DUMMY_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MDEyMzQ1Njc4OWFiY2RlZg$kq9t8J6b3Vv0F5hJ0M5vJ1V6m9K6q9n5k4n1w2g3f4Q"


def authenticate_local_account(db: Session, email: str, password: str) -> Account | None:
    try:
        normalized_email = normalize_email(email)
    except ValueError:
        normalized_email = ""

    account = db.scalar(
        select(Account)
        .join(PasswordCredential)
        .where(Account.email_normalized == normalized_email)
    ) if normalized_email else None

    if account is None:
        verify_password(_DUMMY_PASSWORD_HASH, password[:1024])
        return None

    credential = account.password_credential
    if credential is None or not verify_password(credential.password_hash, password):
        return None

    if account.status != AccountStatus.ACTIVE:
        return None

    return account
