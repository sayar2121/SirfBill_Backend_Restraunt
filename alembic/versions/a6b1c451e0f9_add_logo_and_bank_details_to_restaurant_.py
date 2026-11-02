"""add logo and bank details to restaurant_outlets

Revision ID: a6b1c451e0f9
Revises: ea660d6e9480
Create Date: 2026-10-27 20:39:06.032886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b1c451e0f9'
down_revision: Union[str, Sequence[str], None] = 'ea660d6e9480'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to restaurant_outlets if not existing
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS logo_url VARCHAR;"))
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS upi_id VARCHAR(100);"))
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100);"))
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS bank_account_no VARCHAR(50);"))
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS bank_ifsc VARCHAR(30);"))
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS bank_branch VARCHAR(100);"))
    conn.execute(sa.text("ALTER TABLE restaurant_outlets ADD COLUMN IF NOT EXISTS bank_account_name VARCHAR(150);"))
    conn.execute(sa.text("ALTER TABLE restaurant_orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'CASH';"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('restaurant_outlets', 'bank_account_name')
    op.drop_column('restaurant_outlets', 'bank_branch')
    op.drop_column('restaurant_outlets', 'bank_ifsc')
    op.drop_column('restaurant_outlets', 'bank_account_no')
    op.drop_column('restaurant_outlets', 'bank_name')
    op.drop_column('restaurant_outlets', 'upi_id')
    op.drop_column('restaurant_outlets', 'logo_url')
