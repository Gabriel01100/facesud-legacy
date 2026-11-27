import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_csrf
from app.api.schemas.posts import FeedResponse, PostAuthorResponse, PostCreateRequest, PostResponse
from app.core.database import get_db
from app.models.identity import UserSession
from app.models.post import Post
from app.social.service import SocialRuleError, create_post, delete_own_post, list_unit_feed

router = APIRouter(prefix="/api/v1/social", tags=["social"])


def _post_response(post: Post, profile) -> PostResponse:
    return PostResponse(
        id=post.id,
        body=post.body,
        created_at=post.created_at,
        author=PostAuthorResponse(
            display_name=profile.display_name if profile and profile.display_name else None,
            username=profile.username if profile and profile.username else None,
        ),
    )


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    response: Response,
    limit: int = Query(default=20, ge=1, le=50),
    before: datetime | None = Query(default=None),
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        rows = list_unit_feed(db, viewer_id=session.account_id, limit=limit + 1, before=before)
    except SocialRuleError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from None
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [_post_response(post, profile) for post, profile in rows]
    return FeedResponse(items=items, next_before=items[-1].created_at if has_more and items else None)


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
        post = create_post(db, author_id=session.account_id, body=data.body)
    except SocialRuleError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from None
    return _post_response(post, None)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_post(
    post_id: uuid.UUID,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    if not delete_own_post(db, post_id=post_id, author_id=session.account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
