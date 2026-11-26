from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import Account
from app.models.profile import UserProfile


def get_profile_for_owner(db: Session, account_id: UUID) -> tuple[UserProfile | None, Account]:
    account = db.scalar(select(Account).where(Account.id == account_id))
    if account is None:
        raise LookupError("Account not found")
    profile = db.scalar(select(UserProfile).where(UserProfile.account_id == account_id))
    return profile, account


def update_profile_for_owner(
    db: Session,
    account_id: UUID,
    *,
    changes: dict[str, str | None],
) -> tuple[UserProfile, Account]:
    # Serialize first-time profile creation and username changes for this account.
    account = db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None:
        raise LookupError("Account not found")

    profile = db.scalar(select(UserProfile).where(UserProfile.account_id == account_id).with_for_update())
    if profile is None:
        profile = UserProfile(account_id=account_id)
        db.add(profile)

    for field, value in changes.items():
        setattr(profile, field, value)

    db.flush()
    return profile, account
