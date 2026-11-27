import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.community import MembershipStatus, UnitMembership
from app.models.identity import Account, AccountStatus
from app.models.post import Post
from app.models.profile import UserProfile


class SocialRuleError(Exception):
    pass


def _approved_membership(db: Session, account_id: uuid.UUID) -> UnitMembership:
    membership = db.scalar(
        select(UnitMembership)
        .where(UnitMembership.account_id == account_id, UnitMembership.status == MembershipStatus.APPROVED)
        .with_for_update()
    )
    if membership is None:
        raise SocialRuleError("An approved community membership is required.")
    return membership


def create_post(db: Session, *, author_id: uuid.UUID, body: str) -> tuple[Post, UserProfile | None]:
    account = db.scalar(select(Account).where(Account.id == author_id).with_for_update())
    if account is None or account.status != AccountStatus.ACTIVE:
        raise SocialRuleError("An active account is required.")
    membership = _approved_membership(db, author_id)
    post = Post(author_account_id=author_id, unit_id=membership.unit_id, body=body)
    db.add(post)
    db.flush()
    profile = db.scalar(select(UserProfile).where(UserProfile.account_id == author_id))
    return post, profile


def list_unit_feed(
    db: Session, *, viewer_id: uuid.UUID, limit: int, before: datetime | None = None,
    before_id: uuid.UUID | None = None,
):
    viewer = db.scalar(select(Account).where(Account.id == viewer_id))
    if viewer is None or viewer.status != AccountStatus.ACTIVE:
        raise SocialRuleError("An active account is required.")
    membership = db.scalar(
        select(UnitMembership).where(
            UnitMembership.account_id == viewer_id, UnitMembership.status == MembershipStatus.APPROVED
        )
    )
    if membership is None:
        raise SocialRuleError("An approved community membership is required.")
    if (before is None) != (before_id is None):
        raise SocialRuleError("Both cursor values must be provided together.")

    query = (
        select(Post, UserProfile)
        .join(Account, Account.id == Post.author_account_id)
        .outerjoin(UserProfile, UserProfile.account_id == Post.author_account_id)
        .join(UnitMembership, UnitMembership.account_id == Post.author_account_id)
        .where(
            Post.unit_id == membership.unit_id,
            UnitMembership.unit_id == membership.unit_id,
            UnitMembership.status == MembershipStatus.APPROVED,
            Account.status == AccountStatus.ACTIVE,
        )
    )
    if before is not None and before_id is not None:
        query = query.where(
            or_(Post.created_at < before, and_(Post.created_at == before, Post.id < before_id))
        )
    return list(db.execute(query.order_by(Post.created_at.desc(), Post.id.desc()).limit(limit)))


def delete_own_post(db: Session, *, post_id: uuid.UUID, author_id: uuid.UUID) -> bool:
    post = db.scalar(
        select(Post).where(Post.id == post_id, Post.author_account_id == author_id).with_for_update()
    )
    if post is None:
        return False
    db.delete(post)
    db.flush()
    return True
