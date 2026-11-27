import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.media.images import InvalidImageError, normalize_image
from app.media.storage import MediaStorage, MediaStorageError
from app.models.identity import Account, AccountStatus
from app.models.profile_avatar import ProfileAvatar


class AvatarRuleError(Exception):
    pass


def get_profile_avatar(db: Session, account_id: uuid.UUID) -> ProfileAvatar | None:
    return db.scalar(select(ProfileAvatar).where(ProfileAvatar.account_id == account_id))


def replace_profile_avatar(
    db: Session,
    storage: MediaStorage,
    *,
    account_id: uuid.UUID,
    raw_content: bytes,
) -> ProfileAvatar:
    account = db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None or account.status != AccountStatus.ACTIVE:
        raise AvatarRuleError("Profile not found.")

    normalized, width, height = normalize_image(raw_content)
    key = f"{uuid.uuid4().hex}.webp"
    storage.put(key, normalized, "image/webp")
    db.info.setdefault("media_pending_uploads", []).append((storage, key))

    avatar = db.scalar(
        select(ProfileAvatar).where(ProfileAvatar.account_id == account_id).with_for_update()
    )
    old_key = avatar.storage_key if avatar is not None else None
    if avatar is None:
        avatar = ProfileAvatar(account_id=account_id, storage_key=key)
        db.add(avatar)
    else:
        avatar.storage_key = key

    avatar.content_type = "image/webp"
    avatar.byte_size = len(normalized)
    avatar.width = width
    avatar.height = height
    if old_key is not None:
        db.info.setdefault("media_pending_deletes", []).append((storage, old_key))

    try:
        db.flush()
    except Exception:
        storage.delete(key)
        db.info["media_pending_uploads"] = [
            item for item in db.info.get("media_pending_uploads", []) if item[1] != key
        ]
        raise
    return avatar


def delete_profile_avatar(db: Session, storage: MediaStorage, *, account_id: uuid.UUID) -> bool:
    account = db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None or account.status != AccountStatus.ACTIVE:
        raise AvatarRuleError("Profile not found.")

    avatar = db.scalar(
        select(ProfileAvatar).where(ProfileAvatar.account_id == account_id).with_for_update()
    )
    if avatar is None:
        return False

    db.info.setdefault("media_pending_deletes", []).append((storage, avatar.storage_key))
    db.delete(avatar)
    return True


def read_profile_avatar(
    db: Session,
    storage: MediaStorage,
    *,
    account_id: uuid.UUID,
) -> tuple[ProfileAvatar, bytes]:
    account = db.scalar(select(Account).where(Account.id == account_id))
    if account is None or account.status != AccountStatus.ACTIVE:
        raise AvatarRuleError("Profile not found.")
    avatar = db.scalar(select(ProfileAvatar).where(ProfileAvatar.account_id == account_id))
    if avatar is None:
        raise AvatarRuleError("Profile avatar not found.")
    try:
        content = storage.get(avatar.storage_key)
    except MediaStorageError:
        raise
    return avatar, content
