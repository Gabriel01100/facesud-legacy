from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UnitType(str, enum.Enum):
    BRANCH = "branch"
    WARD = "ward"
    STAKE = "stake"


class UnitStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MembershipStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class OrganizationUnit(Base):
    __tablename__ = "community_organization_units"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("community_organization_units.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType, native_enum=False, length=16), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    administrative_area: Mapped[str | None] = mapped_column(String(120), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus, native_enum=False, length=16), nullable=False, default=UnitStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UnitMembership(Base):
    __tablename__ = "community_unit_memberships"
    __table_args__ = (
        Index(
            "uq_community_pending_account_unit", "account_id", "unit_id", unique=True,
            sqlite_where=text("status = 'pending'"), postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_community_membership_account_status", "account_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("identity_accounts.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("community_organization_units.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, native_enum=False, length=16), nullable=False, default=MembershipStatus.PENDING
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("identity_accounts.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
