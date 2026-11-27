import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_csrf
from app.api.schemas.posts import FeedResponse, PostAuthorResponse, PostCreateRequest, PostResponse
from app.api.schemas.media import PostMediaResponse
from app.core.database import get_db
from app.models.identity import UserSession
from app.models.post import Post
from app.models.media import MediaAsset
from app.media.service import list_post_media, delete_post_images_for_owner
from app.media.storage import get_media_storage
from app.models.profile import UserProfile
from app.social.service import (
    SocialRuleError, create_post, delete_own_post, interaction_summaries, list_unit_feed,
)

router = APIRouter(prefix="/api/v1/social", tags=["social"])


def _post_response(
    post: Post, profile: UserProfile | None, viewer_id: uuid.UUID, summary: dict | None = None,
    images: list[MediaAsset] | None = None,
) -> PostResponse:
    return PostResponse(
        id=post.id,
        body=post.body,
        created_at=post.created_at,
        is_mine=post.author_account_id == viewer_id,
        author=PostAuthorResponse(
            display_name=profile.display_name if profile and profile.display_name else None,
            username=profile.username if profile and profile.username else None,
        ),
        comment_count=(summary or {}).get("comment_count", 0),
        reaction_count=(summary or {}).get("reaction_count", 0),
        is_reacted=(summary or {}).get("is_reacted", False),
        images=[
            PostMediaResponse(
                id=asset.id,
                url=f"/api/v1/social/media/{asset.id}",
                content_type=asset.content_type,
                byte_size=asset.byte_size,
                width=asset.width,
                height=asset.height,
                created_at=asset.created_at,
            )
            for asset in (images or [])
        ],
    )


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    response: Response,
    limit: int = Query(default=20, ge=1, le=50),
    before: datetime | None = Query(default=None),
    before_id: uuid.UUID | None = Query(default=None),
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        rows = list_unit_feed(
            db, viewer_id=session.account_id, limit=limit + 1, before=before, before_id=before_id
        )
    except SocialRuleError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from None
    has_more = len(rows) > limit
    rows = rows[:limit]
    summaries = interaction_summaries(
        db, post_ids=[post.id for post, _ in rows], viewer_id=session.account_id
    )
    media_by_post = list_post_media(db, [post.id for post, _ in rows])
    items = [
        _post_response(post, profile, session.account_id, summaries.get(post.id), media_by_post.get(post.id, []))
        for post, profile in rows
    ]
    last_item = items[-1] if items else None
    return FeedResponse(
        items=items,
        next_before=last_item.created_at if has_more and last_item else None,
        next_before_id=last_item.id if has_more and last_item else None,
    )


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def add_post(
    data: PostCreateRequest,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        post, profile = create_post(db, author_id=session.account_id, body=data.body)
    except SocialRuleError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from None
    return _post_response(post, profile, session.account_id)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_post(
    post_id: uuid.UUID,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
    storage=Depends(get_media_storage),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    deleted_media = delete_post_images_for_owner(
        db, storage, post_id=post_id, account_id=session.account_id
    )
    if not deleted_media or not delete_own_post(db, post_id=post_id, author_id=session.account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
