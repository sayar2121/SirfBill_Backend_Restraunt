"""add account_holder_name to shops

Revision ID: b7c3d18e9f21
Revises: a6b1c451e0f9
Create Date: 2026-11-02 10:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c3d18e9f21'
down_revision: Union[str, Sequence[str], None] = 'a6b1c451e0f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS account_holder_name VARCHAR;"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('shops', 'account_holder_name')

