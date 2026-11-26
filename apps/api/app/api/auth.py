import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_allowed_origin, require_csrf
from app.api.schemas.identity import (
    AuthenticatedAccount,
    CsrfTokenResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
from app.core.config import settings
from app.core.database import get_db
from app.identity.authentication import authenticate_local_account
from app.identity.email import EmailDeliveryError, send_password_reset_email, send_verification_email
from app.identity.rate_limit import (
    clear_login_attempts,
    consume_login_attempt,
    consume_password_reset_attempt,
    consume_registration_attempt,
    consume_resend_attempt,
)
from app.identity.registration import (
    create_pending_account,
    issue_new_verification_token,
    verify_email_token,
)
from app.identity.password_reset import (
    change_password as change_account_password,
    issue_password_reset_token,
    reset_password,
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

    ip_address = request.client.host if request.client else "unknown"
    retry_after = consume_registration_attempt(db, ip_address=ip_address, email=str(data.email))
    db.commit()
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

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

    ip_address = request.client.host if request.client else "unknown"
    retry_after = consume_resend_attempt(db, ip_address=ip_address, email=str(data.email))
    db.commit()
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification email requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

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


@router.post("/password-reset/request", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    data: PasswordResetRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    require_allowed_origin(request)
    response.headers["Cache-Control"] = "no-store"
    if not settings.email_delivery_configured:
        raise HTTPException(status_code=503, detail="Email delivery is not configured.")

    ip_address = request.client.host if request.client else "unknown"
    retry_after = consume_password_reset_attempt(
        db, ip_address=ip_address, email=str(data.email)
    )
    db.commit()
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    normalized_email = normalize_email(str(data.email))
    account = db.scalar(
        select(Account).where(
            Account.email_normalized == normalized_email,
            Account.status == AccountStatus.ACTIVE,
        )
    )
    if account is not None:
        raw_token = issue_password_reset_token(db, account)
        db.commit()
        try:
            send_password_reset_email(account.email_normalized, raw_token)
        except EmailDeliveryError:
            logger.warning("Password reset email could not be delivered")
    return MessageResponse(
        message="Si la cuenta existe y puede restablecerse, recibirás un correo con los próximos pasos."
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    data: PasswordResetConfirmRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    require_allowed_origin(request)
    response.headers["Cache-Control"] = "no-store"
    ip_address = request.client.host if request.client else "unknown"
    retry_after = consume_password_reset_attempt(
        db, ip_address=ip_address, email="reset-confirmation"
    )
    db.commit()
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    if not reset_password(db, raw_token=data.token, new_password=data.new_password):
        raise HTTPException(status_code=400, detail="The reset link is invalid, expired, or already used.")
    db.commit()
    return MessageResponse(message="Tu contraseña fue actualizada. Iniciá sesión nuevamente.")


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChangeRequest,
    request: Request,
    response: Response,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> Response:
    response.headers["Cache-Control"] = "no-store"
    changed = change_account_password(
        db,
        account_id=session.account_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    if not changed:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    db.commit()
    _clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
