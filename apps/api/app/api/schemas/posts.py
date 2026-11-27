import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Post content cannot be empty.")
        return normalized


class PostAuthorResponse(BaseModel):
    display_name: str | None
    username: str | None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    body: str
    created_at: datetime
    author: PostAuthorResponse
    is_mine: bool


class FeedResponse(BaseModel):
    items: list[PostResponse]
    next_before: datetime | None
    next_before_id: uuid.UUID | None
