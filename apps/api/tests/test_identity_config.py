import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cookie_security_is_enabled_outside_development_and_test():
    assert Settings(app_env="development").session_cookie_name == "facesud_session"
    assert Settings(app_env="test").session_cookie_name == "facesud_session"
    for environment in ("staging", "preview", "production", "Production"):
        config = Settings(
            app_env=environment,
            redis_url="redis://:strong-password@redis.internal:6379/0",
            database_url="postgresql+psycopg://user:strong-password@db.internal/facesud",
            cors_origins="https://facesud.org",
            frontend_base_url="https://facesud.org",
            smtp_host="smtp.mailprovider.net",
            smtp_port=587,
            smtp_username="facesud",
            smtp_password="smtp-secret",
            smtp_starttls=True,
            email_from="FaceSud <no-reply@facesud.org>",
        )
        assert config.secure_cookies
        assert config.session_cookie_name == "__Host-facesud_session"


def test_production_rejects_redis_without_password():
    with pytest.raises(ValidationError, match="Production REDIS_URL must include a password"):
        Settings(
            app_env="production",
            redis_url="redis://redis.internal:6379/0",
            database_url="postgresql+psycopg://user:strong-password@db.internal/facesud",
            cors_origins="https://facesud.org",
            frontend_base_url="https://facesud.org",
        )


def test_local_mailpit_settings_enable_email_delivery_without_tls():
    config = Settings(
        app_env="development",
        smtp_host="mailpit",
        smtp_port=1025,
        smtp_starttls=False,
        email_from="FaceSud <no-reply@facesud.local>",
    )
    assert config.email_delivery_configured
    assert config.smtp_starttls is False


def test_production_requires_authenticated_starttls_smtp():
    with pytest.raises(ValidationError, match="authenticated SMTP credentials"):
        Settings(
            app_env="production",
            redis_url="redis://:strong-password@redis.internal:6379/0",
            database_url="postgresql+psycopg://user:strong-password@db.internal/facesud",
            cors_origins="https://facesud.org",
            frontend_base_url="https://facesud.org",
        )


def test_production_rejects_placeholder_sender_domain():
    with pytest.raises(ValidationError, match="development/example values"):
        Settings(
            app_env="production",
            redis_url="redis://:strong-password@redis.internal:6379/0",
            database_url="postgresql+psycopg://user:strong-password@db.internal/facesud",
            cors_origins="https://facesud.org",
            frontend_base_url="https://facesud.org",
            smtp_host="smtp.mailprovider.net",
            smtp_port=587,
            smtp_username="facesud",
            smtp_password="smtp-secret",
            smtp_starttls=True,
            email_from="FaceSud <no-reply@example.net>",
        )


def test_production_rejects_local_mailpit_transport():
    with pytest.raises(ValidationError, match="cannot use local Mailpit"):
        Settings(
            app_env="production",
            redis_url="redis://:strong-password@redis.internal:6379/0",
            database_url="postgresql+psycopg://user:strong-password@db.internal/facesud",
            cors_origins="https://facesud.org",
            frontend_base_url="https://facesud.org",
            smtp_host="mailpit",
            smtp_port=1025,
            smtp_username="facesud",
            smtp_password="smtp-secret",
            smtp_starttls=True,
            email_from="FaceSud <no-reply@facesud.local>",
        )
