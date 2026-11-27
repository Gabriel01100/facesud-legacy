"""Add private profile avatar metadata.

Revision ID: 0011_profile_avatars
Revises: 0010_private_post_media
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011_profile_avatars"
down_revision: Union[str, None] = "0010_private_post_media"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profiles_avatars",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=64), server_default="image/webp", nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", name="uq_profiles_avatars_account_id"),
        sa.UniqueConstraint("storage_key", name="uq_profiles_avatars_storage_key"),
        sa.CheckConstraint("byte_size > 0", name="ck_profiles_avatars_positive_size"),
        sa.CheckConstraint("width > 0 AND height > 0", name="ck_profiles_avatars_positive_dimensions"),
    )


def downgrade() -> None:
    op.drop_table("profiles_avatars")
