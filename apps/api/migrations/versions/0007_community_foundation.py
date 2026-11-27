"""Add organization units and provisional community membership requests.

Revision ID: 0007_community_foundation
Revises: 0006_user_profiles
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_community_foundation"
down_revision: Union[str, None] = "0006_user_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    unit_type = sa.Enum("branch", "ward", "stake", name="unittype", native_enum=False, length=16)
    unit_status = sa.Enum("active", "inactive", name="unitstatus", native_enum=False, length=16)
    membership_status = sa.Enum("pending", "approved", "rejected", "revoked", name="membershipstatus", native_enum=False, length=16)
    op.create_table(
        "community_organization_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("unit_type", unit_type, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("administrative_area", sa.String(120), nullable=True),
        sa.Column("locality", sa.String(120), nullable=True),
        sa.Column("status", unit_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["community_organization_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_organization_units_parent_id", "community_organization_units", ["parent_id"])
    op.create_table(
        "community_unit_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", membership_status, nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["identity_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["community_organization_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_account_id"], ["identity_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_membership_account_status", "community_unit_memberships", ["account_id", "status"])
    op.create_index(
        "uq_community_pending_account",
        "community_unit_memberships",
        ["account_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "uq_community_approved_account",
        "community_unit_memberships",
        ["account_id"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
        sqlite_where=sa.text("status = 'approved'"),
    )


def downgrade() -> None:
    op.drop_index("uq_community_approved_account", table_name="community_unit_memberships")
    op.drop_index("uq_community_pending_account", table_name="community_unit_memberships")
    op.drop_index("ix_community_membership_account_status", table_name="community_unit_memberships")
    op.drop_table("community_unit_memberships")
    op.drop_index("ix_community_organization_units_parent_id", table_name="community_organization_units")
    op.drop_table("community_organization_units")
