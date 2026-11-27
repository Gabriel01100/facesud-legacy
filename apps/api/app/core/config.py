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
    community_reviewer_emails: str = ""
    media_storage_backend: str = "local"
    media_storage_path: str = "/var/lib/facesud/media"
    media_max_upload_bytes: int = 5_242_880
    media_max_image_pixels: int = 20_000_000
    media_max_post_images: int = 4
    media_s3_bucket: str | None = None
    media_s3_region: str = "us-east-1"
    media_s3_endpoint_url: str | None = None
    media_s3_access_key_id: str | None = None
    media_s3_secret_access_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def community_reviewers(self) -> set[str]:
        return {email.strip().lower() for email in self.community_reviewer_emails.split(",") if email.strip()}

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
            if self.media_storage_backend.strip().lower() != "s3":
                raise ValueError("Production requires private S3-compatible media storage")
            if not all((self.media_s3_bucket, self.media_s3_access_key_id, self.media_s3_secret_access_key)):
                raise ValueError("Production media storage requires bucket and credentials")
            if self.media_s3_endpoint_url and not self.media_s3_endpoint_url.startswith("https://"):
                raise ValueError("Production custom media storage endpoint must use HTTPS")
            if self.media_max_upload_bytes > 10_485_760 or self.media_max_upload_bytes < 1024:
                raise ValueError("MEDIA_MAX_UPLOAD_BYTES must be between 1 KiB and 10 MiB")
            if self.media_max_image_pixels > 40_000_000 or self.media_max_image_pixels < 1_000_000:
                raise ValueError("MEDIA_MAX_IMAGE_PIXELS must be between 1 MP and 40 MP")
        return self


settings = Settings()
