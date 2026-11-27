import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=2, max_length=60)
    username: str | None = Field(default=None, min_length=3, max_length=24)
    bio: str | None = Field(default=None, max_length=280)

    @field_validator("display_name", "bio")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().removeprefix("@").lower()
        if not re.fullmatch(r"[a-z0-9_]{3,24}", normalized):
            raise ValueError("Username must contain 3-24 lowercase letters, numbers or underscores.")
        return normalized

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one profile field must be provided.")
        return self


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str | None
    username: str | None
    bio: str | None
    account_created_at: datetime
    avatar_url: str | None = None
    community_unit: dict[str, str] | None = None
