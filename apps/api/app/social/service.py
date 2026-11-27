import uuid
from datetime import datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.community import MembershipStatus, UnitMembership
from app.models.identity import Account, AccountStatus
from app.models.post import Post
from app.models.profile import UserProfile
from app.models.reaction import Reaction


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


def _visible_post(db: Session, *, post_id: uuid.UUID, viewer_id: uuid.UUID) -> tuple[Post, UnitMembership]:
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
    post = db.scalar(
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
    if post is None:
        raise SocialRuleError("Post not found.")
    return post, membership


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


def interaction_summaries(db: Session, *, post_ids: list[uuid.UUID], viewer_id: uuid.UUID) -> dict[uuid.UUID, dict]:
    if not post_ids:
        return {}
    comment_counts = dict(
        db.execute(
            select(Comment.post_id, func.count(Comment.id))
            .join(Account, Account.id == Comment.author_account_id)
            .join(UnitMembership, UnitMembership.account_id == Comment.author_account_id)
            .join(Post, Post.id == Comment.post_id)
            .where(
                Comment.post_id.in_(post_ids),
                Account.status == AccountStatus.ACTIVE,
                UnitMembership.status == MembershipStatus.APPROVED,
                UnitMembership.unit_id == Post.unit_id,
            )
            .group_by(Comment.post_id)
        ).all()
    )
    reaction_rows = db.execute(
        select(
            Reaction.post_id,
            func.count(Reaction.id),
            func.count(case((Reaction.account_id == viewer_id, 1))) > 0,
        )
        .join(Account, Account.id == Reaction.account_id)
        .join(UnitMembership, UnitMembership.account_id == Reaction.account_id)
        .join(Post, Post.id == Reaction.post_id)
        .where(
            Reaction.post_id.in_(post_ids),
            Account.status == AccountStatus.ACTIVE,
            UnitMembership.status == MembershipStatus.APPROVED,
            UnitMembership.unit_id == Post.unit_id,
        )
        .group_by(Reaction.post_id)
    ).all()
    summaries = {
        post_id: {"comment_count": int(comment_counts.get(post_id, 0)), "reaction_count": 0, "is_reacted": False}
        for post_id in post_ids
    }
    for post_id, count, reacted in reaction_rows:
        summaries[post_id]["reaction_count"] = int(count)
        summaries[post_id]["is_reacted"] = bool(reacted)
    return summaries


def list_post_comments(
    db: Session, *, post_id: uuid.UUID, viewer_id: uuid.UUID, limit: int = 50
) -> list[tuple[Comment, UserProfile | None]]:
    _visible_post(db, post_id=post_id, viewer_id=viewer_id)
    rows = db.execute(
        select(Comment, UserProfile)
        .join(Account, Account.id == Comment.author_account_id)
        .join(UnitMembership, UnitMembership.account_id == Comment.author_account_id)
        .join(Post, Post.id == Comment.post_id)
        .outerjoin(UserProfile, UserProfile.account_id == Comment.author_account_id)
        .where(
            Comment.post_id == post_id,
            Account.status == AccountStatus.ACTIVE,
            UnitMembership.status == MembershipStatus.APPROVED,
            UnitMembership.unit_id == Post.unit_id,
        )
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .limit(limit)
    )
    return list(rows)


def create_comment(
    db: Session, *, post_id: uuid.UUID, author_id: uuid.UUID, body: str
) -> tuple[Comment, UserProfile | None]:
    _visible_post(db, post_id=post_id, viewer_id=author_id)
    comment = Comment(post_id=post_id, author_account_id=author_id, body=body)
    db.add(comment)
    db.flush()
    profile = db.scalar(select(UserProfile).where(UserProfile.account_id == author_id))
    return comment, profile


def delete_own_comment(db: Session, *, comment_id: uuid.UUID, author_id: uuid.UUID) -> bool:
    comment = db.scalar(
        select(Comment).where(Comment.id == comment_id, Comment.author_account_id == author_id).with_for_update()
    )
    if comment is None:
        return False
    _visible_post(db, post_id=comment.post_id, viewer_id=author_id)
    db.delete(comment)
    db.flush()
    return True


def add_reaction(db: Session, *, post_id: uuid.UUID, account_id: uuid.UUID) -> None:
    _visible_post(db, post_id=post_id, viewer_id=account_id)
    values = {"post_id": post_id, "account_id": account_id}
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        statement = pg_insert(Reaction).values(**values).on_conflict_do_nothing(
            index_elements=["post_id", "account_id"]
        )
    elif dialect == "sqlite":
        statement = sqlite_insert(Reaction).values(**values).on_conflict_do_nothing(
            index_elements=["post_id", "account_id"]
        )
    else:
        existing = db.scalar(
            select(Reaction).where(
                Reaction.post_id == post_id, Reaction.account_id == account_id
            ).with_for_update()
        )
        if existing is None:
            db.add(Reaction(**values))
            db.flush()
        return
    db.execute(statement)


def remove_reaction(db: Session, *, post_id: uuid.UUID, account_id: uuid.UUID) -> None:
    _visible_post(db, post_id=post_id, viewer_id=account_id)
    reaction = db.scalar(
        select(Reaction).where(Reaction.post_id == post_id, Reaction.account_id == account_id).with_for_update()
    )
    if reaction is not None:
        db.delete(reaction)
        db.flush()
