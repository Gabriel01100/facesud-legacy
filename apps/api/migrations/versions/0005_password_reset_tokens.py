"""Add one-time password reset tokens.

Revision ID: 0005_password_reset_tokens
Revises: 0004_login_rate_limits
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_password_reset_tokens"
down_revision: Union[str, None] = "0004_login_rate_limits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "identity_password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_identity_password_reset_token_hash"),
    )
    op.create_index(
        "ix_identity_password_reset_tokens_account_id", "identity_password_reset_tokens", ["account_id"]
    )
    op.create_index(
        "ix_identity_password_reset_tokens_expires_at", "identity_password_reset_tokens", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_identity_password_reset_tokens_expires_at", table_name="identity_password_reset_tokens")
    op.drop_index("ix_identity_password_reset_tokens_account_id", table_name="identity_password_reset_tokens")
    op.drop_table("identity_password_reset_tokens")
