"""Add text posts scoped to approved community units.

Revision ID: 0008_social_posts
Revises: 0007_community_foundation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008_social_posts"
down_revision: Union[str, None] = "0007_community_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "social_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["community_organization_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_social_posts_unit_created", "social_posts", ["unit_id", "created_at", "id"])
    op.create_index("ix_social_posts_author_created", "social_posts", ["author_account_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_social_posts_author_created", table_name="social_posts")
    op.drop_index("ix_social_posts_unit_created", table_name="social_posts")
    op.drop_table("social_posts")
