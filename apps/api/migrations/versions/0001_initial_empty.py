"""Initial empty schema baseline.

This migration intentionally creates no business tables. It establishes the
Alembic revision chain for the executable foundation.
"""
from typing import Sequence, Union

revision: str = "0001_initial_empty"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
