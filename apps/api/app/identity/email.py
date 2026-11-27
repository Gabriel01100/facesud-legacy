import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


def _send_message(message: EmailMessage) -> None:
    if not settings.email_delivery_configured:
        raise EmailDeliveryError("Transactional email is not configured")

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        ) as smtp:
            smtp.ehlo()
            if settings.smtp_starttls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception("Transactional email delivery failed")
        raise EmailDeliveryError("Could not deliver transactional email") from exc


def send_verification_email(recipient: str, raw_token: str) -> None:
    query = urlencode({"token": raw_token})
    verification_url = f"{settings.frontend_base_url.rstrip('/')}/verify-email?{query}"

    message = EmailMessage()
    message["Subject"] = "Verificá tu correo electrónico para FaceSud"
    message["From"] = settings.email_from
    message["To"] = recipient
    message.set_content(
        "Para verificar tu dirección de correo electrónico en FaceSud, abrí este enlace:\n\n"
        f"{verification_url}\n\n"
        "El enlace vence en 24 horas. Si no solicitaste esta cuenta, podés ignorar este mensaje."
    )
    _send_message(message)


def send_password_reset_email(recipient: str, raw_token: str) -> None:
    query = urlencode({"token": raw_token})
    reset_url = f"{settings.frontend_base_url.rstrip('/')}/reset-password?{query}"

    message = EmailMessage()
    message["Subject"] = "Restablecé tu contraseña de FaceSud"
    message["From"] = settings.email_from
    message["To"] = recipient
    message.set_content(
        "Recibimos una solicitud para restablecer la contraseña de tu cuenta de FaceSud. "
        "Si la realizaste, abrí este enlace:\n\n"
        f"{reset_url}\n\n"
        "El enlace vence en 30 minutos y solo puede utilizarse una vez. "
        "Si no solicitaste este cambio, ignorá este mensaje; tu contraseña seguirá igual."
    )
    _send_message(message)
