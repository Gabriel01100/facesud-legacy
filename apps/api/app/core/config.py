from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FaceSud API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://facesud:facesud_dev@db:5432/facesud"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def reject_development_defaults_in_production(self):
        if self.app_env.lower() == "production":
            placeholders = ("facesud_dev", "localhost", "example", "changeme")
            configured = f"{self.database_url} {self.redis_url} {self.cors_origins}".lower()
            if any(value in configured for value in placeholders):
                raise ValueError("Production configuration contains development/example values")
        return self


settings = Settings()
