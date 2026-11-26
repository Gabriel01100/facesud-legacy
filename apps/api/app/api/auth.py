from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_allowed_origin, require_csrf
from app.api.schemas.identity import AuthenticatedAccount, CsrfTokenResponse, LoginRequest, LoginResponse
from app.core.config import settings
from app.core.database import get_db
from app.identity.authentication import authenticate_local_account
from app.identity.sessions import (
    SESSION_ABSOLUTE_TTL,
    create_session,
    revoke_session,
    rotate_csrf_token,
    touch_session,
)
from app.models.identity import UserSession

router = APIRouter(prefix="/api/v1/auth", tags=["identity"])


def _set_session_cookie(response: Response, session_token: str) -> None:
    secure = settings.app_env.lower() == "production"
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=int(SESSION_ABSOLUTE_TTL.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    secure = settings.app_env.lower() == "production"
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=secure,
        httponly=True,
        samesite="lax",
    )


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    require_allowed_origin(request)
    account = authenticate_local_account(db, data.email, data.password)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect, or the account is not active.",
        )

    now = datetime.now(timezone.utc)
    _, raw_session_token, raw_csrf_token = create_session(
        db,
        account_id=account.id,
        expires_at=now + SESSION_ABSOLUTE_TTL,
        now=now,
    )
    db.commit()
    _set_session_cookie(response, raw_session_token)
    response.headers["Cache-Control"] = "no-store"
    return LoginResponse(id=account.id, email=account.email_normalized, csrf_token=raw_csrf_token)


@router.get("/me", response_model=AuthenticatedAccount)
def me(
    response: Response,
    session: UserSession = Depends(get_current_session),
) -> AuthenticatedAccount:
    response.headers["Cache-Control"] = "no-store"
    account = session.account
    return AuthenticatedAccount(id=account.id, email=account.email_normalized)


@router.post("/csrf", response_model=CsrfTokenResponse)
def refresh_csrf_token(
    request: Request,
    response: Response,
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> CsrfTokenResponse:
    # A fresh token can be fetched after a page reload without exposing the
    # HttpOnly session cookie or relying on a CSRF cookie shared across hosts.
    require_allowed_origin(request)
    raw_token = rotate_csrf_token(db, session)
    touch_session(db, session)
    response.headers["Cache-Control"] = "no-store"
    return CsrfTokenResponse(csrf_token=raw_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> Response:
    require_allowed_origin(request)
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        revoke_session(db, raw_token)
        db.commit()
    _clear_session_cookie(response)
    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
