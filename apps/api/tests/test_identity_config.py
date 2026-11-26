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
            smtp_host="smtp.example.net",
            smtp_port=587,
            smtp_username="facesud",
            smtp_password="smtp-secret",
            smtp_starttls=True,
            email_from="FaceSud <no-reply@example.net>",
        )
        assert config.secure_cookies
        assert config.session_cookie_name == "__Host-facesud_session"


def test_production_rejects_redis_without_password():
    with pytest.raises(ValidationError, match="Redis URL must include a password"):
        Settings(
            app_env="production",
            redis_url="redis://redis.internal:6379/0",
            database_url="postgresql+psycopg://user:strong-password@db.internal/facesud",
            cors_origins="https://facesud.org",
            frontend_base_url="https://facesud.org",
        )
