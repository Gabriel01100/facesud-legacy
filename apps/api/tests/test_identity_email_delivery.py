from email.message import EmailMessage
from types import SimpleNamespace

from app.identity import email as email_module


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = None
        self.message = None
        self.ehlo_count = 0
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def ehlo(self):
        self.ehlo_count += 1

    def starttls(self, context):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message):
        self.message = message


def test_local_verification_email_uses_mailpit_without_starttls_or_auth(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(email_module.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(
        email_module,
        "settings",
        SimpleNamespace(
            email_delivery_configured=True,
            smtp_host="mailpit",
            smtp_port=1025,
            smtp_timeout_seconds=10,
            smtp_starttls=False,
            smtp_username=None,
            smtp_password=None,
            email_from="FaceSud <no-reply@facesud.local>",
            frontend_base_url="http://localhost:5173",
        ),
    )

    email_module.send_verification_email("person@example.com", "opaque-token")

    smtp = FakeSMTP.instances[-1]
    assert smtp.host == "mailpit"
    assert smtp.port == 1025
    assert smtp.started_tls is False
    assert smtp.logged_in is None
    assert smtp.message["To"] == "person@example.com"
    assert "http://localhost:5173/verify-email?token=opaque-token" in smtp.message.get_content()


def test_production_style_email_uses_starttls_and_smtp_auth(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(email_module.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_module.ssl, "create_default_context", lambda: "tls-context")
    monkeypatch.setattr(
        email_module,
        "settings",
        SimpleNamespace(
            email_delivery_configured=True,
            smtp_host="smtp.example.net",
            smtp_port=587,
            smtp_timeout_seconds=10,
            smtp_starttls=True,
            smtp_username="facesud",
            smtp_password="smtp-secret",
            email_from="FaceSud <no-reply@example.net>",
            frontend_base_url="https://facesud.example.net",
        ),
    )

    email_module.send_verification_email("person@example.com", "opaque-token")

    smtp = FakeSMTP.instances[-1]
    assert smtp.started_tls is True
    assert smtp.ehlo_count == 2
    assert smtp.logged_in == ("facesud", "smtp-secret")


def test_password_reset_email_uses_shared_delivery_transport(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(email_module.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(
        email_module,
        "settings",
        SimpleNamespace(
            email_delivery_configured=True,
            smtp_host="mailpit",
            smtp_port=1025,
            smtp_timeout_seconds=10,
            smtp_starttls=False,
            smtp_username=None,
            smtp_password=None,
            email_from="FaceSud <no-reply@facesud.local>",
            frontend_base_url="http://localhost:5173",
        ),
    )

    email_module.send_password_reset_email("person@example.com", "reset-token")

    assert "http://localhost:5173/reset-password?token=reset-token" in FakeSMTP.instances[-1].message.get_content()
