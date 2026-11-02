"""add_icon_emoji_to_categories

Revision ID: ea660d6e9480
Revises: 043a726c5d77
Create Date: 2026-10-26 10:41:27.227138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea660d6e9480'
down_revision: Union[str, Sequence[str], None] = '043a726c5d77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        ALTER TABLE restaurant_menu_categories
        ADD COLUMN IF NOT EXISTS icon_emoji VARCHAR(50) DEFAULT '🍽️';
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('restaurant_menu_categories', 'icon_emoji')
