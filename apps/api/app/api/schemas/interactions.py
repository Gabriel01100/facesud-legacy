import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=1000)

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Comment content cannot be empty.")
        return normalized


class CommentAuthorResponse(BaseModel):
    display_name: str | None
    username: str | None


class CommentResponse(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    author: CommentAuthorResponse
    is_mine: bool


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    has_more: bool
