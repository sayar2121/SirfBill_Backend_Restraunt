"""add_price_and_badge_to_menu_items

Revision ID: 043a726c5d77
Revises: 37fabd7fce72
Create Date: 2026-10-26 10:08:30.587218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '043a726c5d77'
down_revision: Union[str, Sequence[str], None] = '37fabd7fce72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure price and badge columns exist on restaurant_menu_items
    op.execute("""
        ALTER TABLE restaurant_menu_items 
        ADD COLUMN IF NOT EXISTS price NUMERIC(10, 2) DEFAULT 0.00,
        ADD COLUMN IF NOT EXISTS badge VARCHAR(50);
    """)

    # Populate item price from existing item prices if price is 0 or null
    op.execute("""
        UPDATE restaurant_menu_items m
        SET price = p.price
        FROM restaurant_item_prices p
        WHERE p.item_id = m.id AND (m.price IS NULL OR m.price = 0);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('restaurant_menu_items', 'badge')
    op.drop_column('restaurant_menu_items', 'price')
