from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_csrf
from app.api.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.core.database import get_db
from app.models.identity import UserSession
from app.profiles.service import get_profile_for_owner, update_profile_for_owner

router = APIRouter(prefix="/api/v1/profile", tags=["profiles"])


def _response(profile, account) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id if profile is not None else account.id,
        display_name=profile.display_name if profile is not None else None,
        username=profile.username if profile is not None else None,
        bio=profile.bio if profile is not None else None,
        created_at=profile.created_at if profile is not None else account.created_at,
        updated_at=profile.updated_at if profile is not None else None,
        account_created_at=account.created_at,
        avatar_url=None,
        community_unit=None,
    )


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    response: Response,
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        profile, account = get_profile_for_owner(db, session.account_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required") from None
    return _response(profile, account)


@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdateRequest,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    try:
        profile, account = update_profile_for_owner(
            db,
            session.account_id,
            changes=data.model_dump(exclude_unset=True),
        )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required") from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username is unavailable.",
        ) from None
    return _response(profile, account)
