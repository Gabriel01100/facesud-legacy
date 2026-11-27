import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import require_csrf, get_current_session
from app.api.schemas.interactions import (
    CommentAuthorResponse, CommentCreateRequest, CommentListResponse, CommentResponse,
)
from app.core.database import get_db
from app.models.identity import UserSession
from app.social.service import (
    SocialRuleError, add_reaction, create_comment, delete_own_comment, interaction_summaries,
    list_post_comments, remove_reaction,
)

router = APIRouter(prefix="/api/v1/social", tags=["social"])


def _rule_http_error(exc: SocialRuleError) -> HTTPException:
    if str(exc) == "Post not found.":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _comment_response(comment, profile, viewer_id: uuid.UUID) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        body=comment.body,
        created_at=comment.created_at,
        is_mine=comment.author_account_id == viewer_id,
        author=CommentAuthorResponse(
            display_name=profile.display_name if profile and profile.display_name else None,
            username=profile.username if profile and profile.username else None,
        ),
    )


def _summary(db: Session, post_id: uuid.UUID, viewer_id: uuid.UUID) -> dict:
    return interaction_summaries(db, post_ids=[post_id], viewer_id=viewer_id).get(
        post_id, {"comment_count": 0, "reaction_count": 0, "is_reacted": False}
    )


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
def get_comments(
    post_id: uuid.UUID,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        rows = list_post_comments(db, post_id=post_id, viewer_id=session.account_id, limit=limit + 1)
    except SocialRuleError as exc:
        raise _rule_http_error(exc) from None
    has_more = len(rows) > limit
    return CommentListResponse(
        items=[_comment_response(comment, profile, session.account_id) for comment, profile in rows[:limit]],
        has_more=has_more,
    )


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    post_id: uuid.UUID,
    data: CommentCreateRequest,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        comment, profile = create_comment(
            db, post_id=post_id, author_id=session.account_id, body=data.body
        )
    except SocialRuleError as exc:
        raise _rule_http_error(exc) from None
    return _comment_response(comment, profile, session.account_id)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_comment(
    comment_id: uuid.UUID,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        deleted = delete_own_comment(db, comment_id=comment_id, author_id=session.account_id)
    except SocialRuleError as exc:
        raise _rule_http_error(exc) from None
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")


@router.put("/posts/{post_id}/reaction", status_code=status.HTTP_200_OK)
def put_reaction(
    post_id: uuid.UUID,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        add_reaction(db, post_id=post_id, account_id=session.account_id)
        return _summary(db, post_id, session.account_id)
    except SocialRuleError as exc:
        raise _rule_http_error(exc) from None


@router.delete("/posts/{post_id}/reaction", status_code=status.HTTP_200_OK)
def delete_reaction(
    post_id: uuid.UUID,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        remove_reaction(db, post_id=post_id, account_id=session.account_id)
        return _summary(db, post_id, session.account_id)
    except SocialRuleError as exc:
        raise _rule_http_error(exc) from None
