import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_csrf
from app.api.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.core.config import settings
from app.core.database import get_db
from app.media.images import InvalidImageError
from app.media.storage import MediaStorageError, get_media_storage
from app.models.community import MembershipStatus, OrganizationUnit, UnitMembership
from app.models.identity import UserSession
from app.profiles.avatar_service import (
    AvatarRuleError,
    delete_profile_avatar,
    get_profile_avatar,
    read_profile_avatar,
    replace_profile_avatar,
)
from app.profiles.service import get_profile_for_owner, update_profile_for_owner

router = APIRouter(prefix="/api/v1/profile", tags=["profiles"])


def _response(profile, account, db: Session) -> ProfileResponse:
    approved_unit = db.scalar(
        select(OrganizationUnit)
        .join(UnitMembership, UnitMembership.unit_id == OrganizationUnit.id)
        .where(
            UnitMembership.account_id == account.id,
            UnitMembership.status == MembershipStatus.APPROVED,
        )
    )
    avatar = get_profile_avatar(db, account.id)
    return ProfileResponse(
        display_name=profile.display_name if profile is not None else None,
        username=profile.username if profile is not None else None,
        bio=profile.bio if profile is not None else None,
        account_created_at=account.created_at,
        avatar_url="/api/v1/profile/me/avatar" if avatar is not None else None,
        community_unit=(
            {"name": approved_unit.name, "kind": approved_unit.unit_type.value}
            if approved_unit is not None else None
        ),
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
    return _response(profile, account, db)


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
    return _response(profile, account, db)


@router.post("/me/avatar", status_code=status.HTTP_201_CREATED)
async def upload_my_avatar(
    file: UploadFile = File(...),
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
    storage=Depends(get_media_storage),
):
    content = await file.read(settings.media_max_upload_bytes + 1)
    await file.close()
    if len(content) > settings.media_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Image exceeds the upload size limit.")
    try:
        replace_profile_avatar(db, storage, account_id=session.account_id, raw_content=content)
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except AvatarRuleError:
        raise HTTPException(status_code=404, detail="Profile not found.") from None
    except MediaStorageError:
        raise HTTPException(status_code=503, detail="Media storage is temporarily unavailable.") from None
    return {"avatar_url": "/api/v1/profile/me/avatar"}


@router.get("/me/avatar")
def get_my_avatar(
    response: Response,
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
    storage=Depends(get_media_storage),
):
    try:
        avatar, content = read_profile_avatar(db, storage, account_id=session.account_id)
    except AvatarRuleError:
        raise HTTPException(status_code=404, detail="Profile avatar not found.") from None
    except MediaStorageError:
        raise HTTPException(status_code=503, detail="Media storage is temporarily unavailable.") from None
    return Response(
        content=content,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, no-store",
            "Vary": "Cookie",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{avatar.id}.webp"',
        },
    )


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
def remove_my_avatar(
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
    storage=Depends(get_media_storage),
):
    try:
        delete_profile_avatar(db, storage, account_id=session.account_id)
    except AvatarRuleError:
        raise HTTPException(status_code=404, detail="Profile not found.") from None
    except MediaStorageError:
        raise HTTPException(status_code=503, detail="Media storage is temporarily unavailable.") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"Cache-Control": "no-store", "Vary": "Cookie"})
