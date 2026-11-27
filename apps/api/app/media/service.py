import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.media.images import InvalidImageError, normalize_image
from app.media.storage import MediaStorage, MediaStorageError
from app.models.community import MembershipStatus, UnitMembership
from app.models.identity import Account, AccountStatus
from app.models.media import MediaAsset
from app.models.post import Post


class MediaRuleError(Exception):
    def __init__(self, message: str, status_code: int = 404):
        super().__init__(message)
        self.status_code = status_code


def _visible_post_for_member(db: Session, *, post_id: uuid.UUID, account_id: uuid.UUID, lock: bool = False) -> Post:
    account = db.scalar(select(Account).where(Account.id == account_id))
    if account is None or account.status != AccountStatus.ACTIVE:
        raise MediaRuleError("Post not found.")
    membership = db.scalar(
        select(UnitMembership).where(
            UnitMembership.account_id == account_id,
            UnitMembership.status == MembershipStatus.APPROVED,
        )
    )
    if membership is None:
        raise MediaRuleError("Post not found.")
    query = (
        select(Post)
        .join(Account, Account.id == Post.author_account_id)
        .join(
            UnitMembership,
            and_(
                UnitMembership.account_id == Post.author_account_id,
                UnitMembership.unit_id == Post.unit_id,
                UnitMembership.status == MembershipStatus.APPROVED,
            ),
        )
        .where(
            Post.id == post_id,
            Post.unit_id == membership.unit_id,
            Account.status == AccountStatus.ACTIVE,
        )
    )
    if lock:
        query = query.with_for_update()
    post = db.scalar(query)
    if post is None:
        raise MediaRuleError("Post not found.")
    return post


def upload_post_image(
    db: Session,
    storage: MediaStorage,
    *,
    post_id: uuid.UUID,
    account_id: uuid.UUID,
    raw_content: bytes,
) -> MediaAsset:
    post = _visible_post_for_member(db, post_id=post_id, account_id=account_id, lock=True)
    if post.author_account_id != account_id:
        raise MediaRuleError("Post not found.")
    current_count = db.scalar(select(func.count(MediaAsset.id)).where(MediaAsset.post_id == post_id)) or 0
    if current_count >= settings.media_max_post_images:
        raise MediaRuleError("The post has reached its image limit.", status_code=409)
    try:
        normalized, width, height = normalize_image(raw_content)
    except InvalidImageError:
        raise
    key = f"{uuid.uuid4().hex}.webp"
    storage.put(key, normalized, "image/webp")
    asset = MediaAsset(
        owner_account_id=account_id,
        post_id=post_id,
        storage_key=key,
        purpose="post_image",
        content_type="image/webp",
        byte_size=len(normalized),
        width=width,
        height=height,
    )
    db.add(asset)
    try:
        db.flush()
    except Exception:
        storage.delete(key)
        raise
    return asset


def list_post_media(db: Session, post_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[MediaAsset]]:
    if not post_ids:
        return {}
    assets = db.scalars(
        select(MediaAsset)
        .where(MediaAsset.post_id.in_(post_ids), MediaAsset.purpose == "post_image")
        .order_by(MediaAsset.created_at.asc(), MediaAsset.id.asc())
    ).all()
    result: dict[uuid.UUID, list[MediaAsset]] = {post_id: [] for post_id in post_ids}
    for asset in assets:
        result[asset.post_id].append(asset)
    return result


def read_post_image(
    db: Session,
    storage: MediaStorage,
    *,
    media_id: uuid.UUID,
    account_id: uuid.UUID,
) -> tuple[MediaAsset, bytes]:
    asset = db.scalar(
        select(MediaAsset).where(MediaAsset.id == media_id, MediaAsset.purpose == "post_image")
    )
    if asset is None:
        raise MediaRuleError("Media not found.")
    _visible_post_for_member(db, post_id=asset.post_id, account_id=account_id)
    try:
        content = storage.get(asset.storage_key)
    except MediaStorageError:
        raise
    return asset, content


def delete_post_images_for_owner(
    db: Session,
    storage: MediaStorage,
    *,
    post_id: uuid.UUID,
    account_id: uuid.UUID,
) -> bool:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.author_account_id == account_id))
    if post is None:
        return False
    assets = db.scalars(select(MediaAsset).where(MediaAsset.post_id == post_id)).all()
    for asset in assets:
        storage.delete(asset.storage_key)
    return True
