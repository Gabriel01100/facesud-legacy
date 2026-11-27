import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.community import MembershipStatus, UnitType


class UnitCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=120)
    unit_type: UnitType
    country_code: str = Field(min_length=2, max_length=2)
    parent_id: uuid.UUID | None = None
    administrative_area: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=120)

    @field_validator("name", "administrative_area", "locality")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", normalized):
            raise ValueError("Country code must use ISO 3166-1 alpha-2.")
        return normalized


class UnitResponse(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None
    unit_type: UnitType
    name: str
    country_code: str
    administrative_area: str | None
    locality: str | None


class MembershipRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit_id: uuid.UUID


class MembershipReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: MembershipStatus
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("decision")
    @classmethod
    def allowed_decision(cls, value):
        if value not in {MembershipStatus.APPROVED, MembershipStatus.REJECTED}:
            raise ValueError("Decision must be approved or rejected.")
        return value


class MembershipResponse(BaseModel):
    id: uuid.UUID
    unit: UnitResponse
    status: MembershipStatus
    requested_at: datetime
    reviewed_at: datetime | None
    provisional: bool = True


class ReviewQueueItem(BaseModel):
    id: uuid.UUID
    unit: UnitResponse
    status: MembershipStatus
    requested_at: datetime
    account_reference: str
