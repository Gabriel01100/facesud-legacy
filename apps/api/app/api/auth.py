import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_allowed_origin
from app.api.schemas.identity import (
    AuthenticatedAccount,
    CsrfTokenResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
from app.core.config import settings
from app.core.database import get_db
from app.identity.authentication import authenticate_local_account
from app.identity.email import EmailDeliveryError, send_verification_email
from app.identity.rate_limit import clear_login_attempts, consume_login_attempt
from app.identity.registration import (
    create_pending_account,
    issue_new_verification_token,
    verify_email_token,
)
from app.identity.sessions import (
    SESSION_ABSOLUTE_TTL,
    AccountNotActiveError,
    create_session,
    get_active_session,
    normalize_email,
    revoke_session,
    rotate_csrf_token,
    touch_session,
    verify_csrf_token,
)
from app.models.identity import Account, AccountStatus, UserSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["identity"])
GENERIC_REGISTRATION_MESSAGE = (
    "Si la dirección puede registrarse, recibirás un correo con los próximos pasos."
)
GENERIC_VERIFICATION_MESSAGE = "El enlace no es válido, venció o ya fue utilizado."


def _set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=int(SESSION_ABSOLUTE_TTL.total_seconds()),
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.secure_cookies,
        httponly=True,
        samesite="lax",
    )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    require_allowed_origin(request)
    response.headers["Cache-Control"] = "no-store"
    if not settings.email_delivery_configured:
        raise HTTPException(status_code=503, detail="Email delivery is not configured.")

    try:
        created = create_pending_account(db, email=str(data.email), password=data.password)
        if created is None:
            return MessageResponse(message=GENERIC_REGISTRATION_MESSAGE)
        account, raw_token = created
        db.commit()
    except IntegrityError:
        db.rollback()
        return MessageResponse(message=GENERIC_REGISTRATION_MESSAGE)

    try:
        send_verification_email(account.email_normalized, raw_token)
    except EmailDeliveryError:
        logger.warning("Verification email could not be delivered for a new registration")
    return MessageResponse(message=GENERIC_REGISTRATION_MESSAGE)


@router.post("/email-verification/resend", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def resend_verification(
    data: ResendVerificationRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    require_allowed_origin(request)
    response.headers["Cache-Control"] = "no-store"
    if not settings.email_delivery_configured:
        raise HTTPException(status_code=503, detail="Email delivery is not configured.")

    normalized_email = normalize_email(str(data.email))
    account = db.scalar(
        select(Account).where(
            Account.email_normalized == normalized_email,
            Account.status == AccountStatus.PENDING_EMAIL,
        )
    )
    if account is not None:
        raw_token = issue_new_verification_token(db, account)
        db.commit()
        try:
            send_verification_email(account.email_normalized, raw_token)
        except EmailDeliveryError:
            logger.warning("Verification email resend failed")
    return MessageResponse(message=GENERIC_REGISTRATION_MESSAGE)


@router.post("/email-verification/verify", response_model=MessageResponse)
def verify_email(
    data: VerifyEmailRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    require_allowed_origin(request)
    response.headers["Cache-Control"] = "no-store"
    account = verify_email_token(db, data.token)
    if account is None:
        raise HTTPException(status_code=400, detail=GENERIC_VERIFICATION_MESSAGE)
    db.commit()
    return MessageResponse(message="Correo verificado. Ya podés iniciar sesión.")


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    require_allowed_origin(request)
    ip_address = request.client.host if request.client else "unknown"
    retry_after = consume_login_attempt(db, ip_address=ip_address, email=str(data.email))
    # Persist attempts before doing the expensive Argon2 verification.
    db.commit()
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    account = authenticate_local_account(db, str(data.email), data.password)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect, or the account is not active.",
        )

    clear_login_attempts(db, ip_address=ip_address, email=str(data.email))
    incoming_token = request.cookies.get(settings.session_cookie_name)
    if incoming_token:
        revoke_session(db, incoming_token)

    now = datetime.now(timezone.utc)
    try:
        _, raw_session_token, raw_csrf_token = create_session(
            db,
            account_id=account.id,
            expires_at=now + SESSION_ABSOLUTE_TTL,
            now=now,
        )
    except AccountNotActiveError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect, or the account is not active.",
        ) from None

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
    require_allowed_origin(request)
    raw_token = rotate_csrf_token(db, session)
    touch_session(db, session)
    response.headers["Cache-Control"] = "no-store"
    return CsrfTokenResponse(csrf_token=raw_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    require_allowed_origin(request)
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        session = get_active_session(db, raw_token, touch=False)
        if session is not None:
            csrf_header = request.headers.get("x-csrf-token")
            if not csrf_header or not verify_csrf_token(session, csrf_header):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
        revoke_session(db, raw_token)
        db.commit()

    _clear_session_cookie(response)
    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
