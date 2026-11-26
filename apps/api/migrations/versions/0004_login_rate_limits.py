"""Add persistent login rate-limit buckets.

Revision ID: 0004_login_rate_limits
Revises: 0003_email_verification
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_login_rate_limits"
down_revision: Union[str, None] = "0003_email_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "identity_login_rate_limits",
        sa.Column("bucket_hash", sa.String(length=64), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("bucket_hash"),
    )


def downgrade() -> None:
    op.drop_table("identity_login_rate_limits")
