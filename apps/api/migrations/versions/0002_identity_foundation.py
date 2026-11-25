"""Create the initial Identity persistence foundation.

Revision ID: 0002_identity_foundation
Revises: 0001_initial_empty
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_identity_foundation"
down_revision: Union[str, None] = "0001_initial_empty"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    account_status = sa.Enum(
        "PENDING_EMAIL", "ACTIVE", "DISABLED", name="accountstatus", native_enum=False, length=32
    )
    op.create_table(
        "identity_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email_normalized", sa.String(length=320), nullable=False),
        sa.Column("status", account_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email_normalized", name="uq_identity_accounts_email_normalized"),
    )

    op.create_table(
        "identity_password_credentials",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_id"),
    )

    op.create_table(
        "identity_external_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "subject", name="uq_identity_provider_subject"),
    )
    op.create_index("ix_identity_external_identities_account_id", "identity_external_identities", ["account_id"])

    op.create_table(
        "identity_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_identity_sessions_token_hash"),
    )
    op.create_index("ix_identity_sessions_account_id", "identity_sessions", ["account_id"])
    op.create_index("ix_identity_sessions_expires_at", "identity_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_identity_sessions_expires_at", table_name="identity_sessions")
    op.drop_index("ix_identity_sessions_account_id", table_name="identity_sessions")
    op.drop_table("identity_sessions")
    op.drop_index("ix_identity_external_identities_account_id", table_name="identity_external_identities")
    op.drop_table("identity_external_identities")
    op.drop_table("identity_password_credentials")
    op.drop_table("identity_accounts")
