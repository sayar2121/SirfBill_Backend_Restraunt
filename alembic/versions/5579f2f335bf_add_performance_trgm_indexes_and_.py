"""add_performance_trgm_indexes_and_cleanups

Revision ID: 5579f2f335bf
Revises: b7c3d18e9f21
Create Date: 2026-11-10 12:19:28.401935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5579f2f335bf'
down_revision: Union[str, Sequence[str], None] = 'b7c3d18e9f21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with pg_trgm extension and performance GIN search indexes."""
    conn = op.get_bind()
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
    
    # Menu Items search indexes
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_menu_items_name_trgm ON restaurant_menu_items USING gin (name gin_trgm_ops);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_menu_items_shortcode_trgm ON restaurant_menu_items USING gin (short_code gin_trgm_ops);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_menu_items_outlet_active ON restaurant_menu_items (outlet_id, is_active);"))

    # Customers search indexes
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_customers_name_trgm ON restaurant_customers USING gin (name gin_trgm_ops);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_customers_phone_trgm ON restaurant_customers USING gin (phone gin_trgm_ops);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_customers_outlet_active ON restaurant_customers (outlet_id, is_active);"))

    # Orders lookup indexes
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_orders_outlet_status ON restaurant_orders (outlet_id, status);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON restaurant_orders (customer_phone);"))

    # Users search indexes
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_name_trgm ON users USING gin (name gin_trgm_ops);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_phone_trgm ON users USING gin (phone gin_trgm_ops);"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_tenant_role ON users (tenant_id, role);"))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_users_tenant_role;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_users_phone_trgm;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_users_name_trgm;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_orders_customer_phone;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_orders_outlet_status;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_customers_outlet_active;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_customers_phone_trgm;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_customers_name_trgm;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_menu_items_outlet_active;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_menu_items_shortcode_trgm;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_menu_items_name_trgm;"))
