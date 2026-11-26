from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AccountStatus(str, enum.Enum):
    PENDING_EMAIL = "pending_email"
    ACTIVE = "active"
    DISABLED = "disabled"


class Account(Base):
    __tablename__ = "identity_accounts"
    __table_args__ = (UniqueConstraint("email_normalized", name="uq_identity_accounts_email_normalized"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_normalized: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, native_enum=False, length=32), nullable=False, default=AccountStatus.PENDING_EMAIL
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    password_credential: Mapped[PasswordCredential | None] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    external_identities: Mapped[list[ExternalIdentity]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[UserSession]] = relationship(back_populates="account", cascade="all, delete-orphan")
    email_verification_tokens: Mapped[list[EmailVerificationToken]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class PasswordCredential(Base):
    __tablename__ = "identity_password_credentials"

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("identity_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account: Mapped[Account] = relationship(back_populates="password_credential")


class ExternalIdentity(Base):
    __tablename__ = "identity_external_identities"
    __table_args__ = (UniqueConstraint("provider", "subject", name="uq_identity_provider_subject"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("identity_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    account: Mapped[Account] = relationship(back_populates="external_identities")


class UserSession(Base):
    __tablename__ = "identity_sessions"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_identity_sessions_token_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("identity_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped[Account] = relationship(back_populates="sessions")


class EmailVerificationToken(Base):
    __tablename__ = "identity_email_verification_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_identity_email_verification_token_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("identity_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped[Account] = relationship(back_populates="email_verification_tokens")


class LoginRateLimit(Base):
    __tablename__ = "identity_login_rate_limits"

    bucket_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
