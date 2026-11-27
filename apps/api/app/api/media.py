import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_csrf
from app.api.schemas.media import PostMediaResponse
from app.core.config import settings
from app.core.database import get_db
from app.media.images import InvalidImageError
from app.media.service import MediaRuleError, read_post_image, upload_post_image
from app.media.storage import MediaStorageError, get_media_storage
from app.models.identity import UserSession

router = APIRouter(prefix="/api/v1/social", tags=["social media"])


def _media_response(asset) -> PostMediaResponse:
    return PostMediaResponse(
        id=asset.id,
        url=f"/api/v1/social/media/{asset.id}",
        content_type=asset.content_type,
        byte_size=asset.byte_size,
        width=asset.width,
        height=asset.height,
        created_at=asset.created_at,
    )


@router.post(
    "/posts/{post_id}/media",
    response_model=PostMediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_post_media(
    post_id: uuid.UUID,
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
        asset = upload_post_image(
            db, storage, post_id=post_id, account_id=session.account_id, raw_content=content
        )
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except MediaRuleError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
    except MediaStorageError:
        raise HTTPException(status_code=503, detail="Media storage is temporarily unavailable.") from None
    return _media_response(asset)


@router.get("/media/{media_id}")
def get_post_media(
    media_id: uuid.UUID,
    response: Response,
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
    storage=Depends(get_media_storage),
):
    try:
        asset, content = read_post_image(
            db, storage, media_id=media_id, account_id=session.account_id
        )
    except MediaRuleError:
        raise HTTPException(status_code=404, detail="Media not found.") from None
    except MediaStorageError:
        raise HTTPException(status_code=503, detail="Media storage is temporarily unavailable.") from None
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = f'inline; filename="{asset.id}.webp"'
    return Response(content=content, media_type="image/webp", headers=response.headers)
