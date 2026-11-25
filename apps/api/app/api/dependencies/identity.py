from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.identity.sessions import get_active_session
from app.models.identity import UserSession


def get_current_session(
    request: Request,
    db: Session = Depends(get_db),
) -> UserSession:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    session = get_active_session(db, raw_token)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return session


def require_allowed_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin not in settings.allowed_origins:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed")


def require_csrf(
    request: Request,
    session: UserSession = Depends(get_current_session),
) -> UserSession:
    from app.identity.sessions import verify_csrf_token

    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("x-csrf-token")
    if (
        not csrf_cookie
        or not csrf_header
        or csrf_cookie != csrf_header
        or not verify_csrf_token(session, csrf_header)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return session
