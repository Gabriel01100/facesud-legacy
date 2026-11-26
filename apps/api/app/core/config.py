from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FaceSud API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://facesud:facesud_dev@db:5432/facesud"
    redis_url: str = "redis://:facesud_dev@redis:6379/0"
    cors_origins: str = "http://localhost:5173"
    frontend_base_url: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True
    email_from: str | None = None
    smtp_timeout_seconds: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def secure_cookies(self) -> bool:
        return self.app_env.strip().lower() not in {"development", "test"}

    @property
    def session_cookie_name(self) -> str:
        if self.secure_cookies:
            return "__Host-facesud_session"
        return "facesud_session"

    @property
    def email_delivery_configured(self) -> bool:
        return bool(self.smtp_host and self.email_from and self.frontend_base_url)

    @model_validator(mode="after")
    def validate_environment_configuration(self):
        if self.app_env.strip().lower() in {"production", "prod"}:
            placeholders = ("facesud_dev", "localhost", "example", "changeme")
            configured = f"{self.database_url} {self.redis_url} {self.cors_origins} {self.frontend_base_url} {self.smtp_host or ''} {self.email_from or ''}".lower()
            if any(value in configured for value in placeholders):
                raise ValueError("Production configuration contains development/example values")
            if not self.allowed_origins or any(not origin.startswith("https://") for origin in self.allowed_origins):
                raise ValueError("Production CORS origins must use HTTPS")
            if not self.frontend_base_url.startswith("https://"):
                raise ValueError("Production frontend URL must use HTTPS")
            if not urlsplit(self.redis_url).password:
                raise ValueError("Production REDIS_URL must include a password")
            if not all((self.smtp_host, self.smtp_username, self.smtp_password, self.email_from)):
                raise ValueError("Production requires authenticated SMTP credentials and EMAIL_FROM")
            if "mailpit" in (self.smtp_host or "").lower() or ".local" in (self.email_from or "").lower():
                raise ValueError("Production cannot use local Mailpit SMTP settings")
            if not self.smtp_starttls:
                raise ValueError("Production SMTP must use STARTTLS")
        return self


settings = Settings()
