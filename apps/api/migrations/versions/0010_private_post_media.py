"""Add private post media metadata.

Revision ID: 0010_private_post_media
Revises: 0009_social_interactions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010_private_post_media"
down_revision: Union[str, None] = "0009_social_interactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=80), nullable=False),
        sa.Column("purpose", sa.String(length=24), server_default="post_image", nullable=False),
        sa.Column("content_type", sa.String(length=64), server_default="image/webp", nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("purpose = 'post_image'", name="ck_media_assets_supported_purpose"),
        sa.CheckConstraint("byte_size > 0", name="ck_media_assets_positive_size"),
        sa.CheckConstraint("width > 0 AND height > 0", name="ck_media_assets_positive_dimensions"),
        sa.ForeignKeyConstraint(["owner_account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["social_posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
    )
    op.create_index("ix_media_assets_post_created", "media_assets", ["post_id", "created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_media_assets_post_created", table_name="media_assets")
    op.drop_table("media_assets")
