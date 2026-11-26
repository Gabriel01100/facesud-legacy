"""Add private user profile records.

Revision ID: 0006_user_profiles
Revises: 0005_password_reset_tokens
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_user_profiles"
down_revision: Union[str, None] = "0005_password_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profiles_user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=60), nullable=True),
        sa.Column("username", sa.String(length=24), nullable=True),
        sa.Column("bio", sa.String(length=280), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", name="uq_profiles_user_profiles_account_id"),
        sa.UniqueConstraint("username", name="uq_profiles_user_profiles_username"),
    )


def downgrade() -> None:
    op.drop_table("profiles_user_profiles")
