from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_allowed_origin, require_csrf
from app.api.schemas.identity import AuthenticatedAccount, LoginRequest
from app.core.config import settings
from app.core.database import get_db
from app.identity.authentication import authenticate_local_account
from app.identity.sessions import create_session, revoke_session

router = APIRouter(prefix="/api/v1/auth", tags=["identity"])

SESSION_ABSOLUTE_TTL = timedelta(days=7)


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
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
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=int(SESSION_ABSOLUTE_TTL.total_seconds()),
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    secure = settings.app_env.lower() == "production"
    for name, httponly in (
        (settings.session_cookie_name, True),
        (settings.csrf_cookie_name, False),
    ):
        response.delete_cookie(
            key=name,
            path="/",
            secure=secure,
            httponly=httponly,
            samesite="lax",
        )


@router.post("/login", response_model=AuthenticatedAccount)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthenticatedAccount:
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
    _set_auth_cookies(response, raw_session_token, raw_csrf_token)
    response.headers["Cache-Control"] = "no-store"
    return AuthenticatedAccount(id=account.id, email=account.email_normalized)


@router.get("/me", response_model=AuthenticatedAccount)
def me(
    response: Response,
    session=Depends(get_current_session),
) -> AuthenticatedAccount:
    response.headers["Cache-Control"] = "no-store"
    account = session.account
    return AuthenticatedAccount(id=account.id, email=account.email_normalized)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    session=Depends(require_csrf),
    db: Session = Depends(get_db),
) -> Response:
    require_allowed_origin(request)
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        revoke_session(db, raw_token)
        db.commit()
    _clear_auth_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
