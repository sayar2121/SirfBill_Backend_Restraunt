from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from fastapi.staticfiles import StaticFiles
import os

# Create root uploads directories
# os.makedirs("uploads/reports", exist_ok=True)
# os.makedirs("uploads/profiles", exist_ok=True)
# os.makedirs("uploads/prescriptions", exist_ok=True)
# os.makedirs("uploads/banners", exist_ok=True)
# os.makedirs("uploads/doctors", exist_ok=True)
# os.makedirs("uploads/stories", exist_ok=True)

# Import models to ensure they are registered with SQLAlchemy
from models import Base, engine
# from graphql_api.schema import schema

import sqlalchemy as sa


# Create the tables automatically first time
Base.metadata.create_all(bind=engine)

# Auto-apply essential schema columns & performance indexes on startup
try:
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE shops ADD COLUMN IF NOT EXISTS account_holder_name VARCHAR;"))
        # Enable pg_trgm for high-speed sub-millisecond full-text and pattern search
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
        # High-performance GIN Trigram indexes on millions of rows
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_menu_items_name_trgm ON restaurant_menu_items USING gin (name gin_trgm_ops);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_menu_items_shortcode_trgm ON restaurant_menu_items USING gin (short_code gin_trgm_ops);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_menu_items_outlet_active ON restaurant_menu_items (outlet_id, is_active);"))

        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_customers_name_trgm ON restaurant_customers USING gin (name gin_trgm_ops);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_customers_phone_trgm ON restaurant_customers USING gin (phone gin_trgm_ops);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_customers_outlet_active ON restaurant_customers (outlet_id, is_active);"))

        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_orders_outlet_status ON restaurant_orders (outlet_id, status);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON restaurant_orders (customer_phone);"))

        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_name_trgm ON users USING gin (name gin_trgm_ops);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_phone_trgm ON users USING gin (phone gin_trgm_ops);"))
        conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_tenant_role ON users (tenant_id, role);"))
except Exception as e:
    print(f"Schema startup migration note: {e}")

# Legacy schema migrations note: Handled via Alembic in production
# try:
#     with engine.begin() as conn:
#         conn.execute(sa.text("ALTER TABLE shop_settings ADD COLUMN IF NOT EXISTS cin_number VARCHAR;"))
#         conn.execute(sa.text("ALTER TABLE shop_settings ADD COLUMN IF NOT EXISTS upi_id VARCHAR;"))
#         conn.execute(sa.text("ALTER TABLE inventory_items ALTER COLUMN expiry_date DROP NOT NULL;"))
# except Exception as e:
#     print(f"Schema migration note: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup before app starts (like connecting to DB, handled by sqlalchemy sync here)
    yield
    # Cleanup when app stops

app = FastAPI(title="SirfBill Restaurant Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5194", "http://192.168.0.222:5194", "https://sirfapi.vwings247.me", "*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/inventory", exist_ok=True)
os.makedirs("uploads/shop", exist_ok=True)
os.makedirs("uploads/kots", exist_ok=True)
os.makedirs("uploads/bills", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

os.makedirs("downloads", exist_ok=True)
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

from routes.user import router as user_router, admin_router as user_admin_router
# from routes.doctor import router as doctor_router
# from routes.appointment import router as appointment_router
# from routes.lab_catalog import router as lab_catalog_router
# from routes.lab_booking import router as lab_booking_router
# from routes.story import router as story_router
from routes.auth import router as auth_router
from routes.payment import router as payment_router
# from routes.dashboard import router as dashboard_router
# from routes.banner import router as banner_router
# from routes.settings import router as settings_router
from routes.shop_admin import router as shop_admin_router
from routes.shop_settings import router as shop_settings_router
from routes.pos_admin import router as pos_admin_router
# from routes.documents_admin import router as documents_admin_router
from routes.search import router as search_router
from routes.shop_orders import router as shop_orders_router
from routes.accounts import router as accounts_router
from routes.transactions import router as transactions_router
from routes.transaction_categories import router as transaction_categories_router
from routes.accounting_extended import router as accounting_extended_router
# from routes.lab_category import router as lab_category_router
# from routes.lab_template import router as lab_template_router
from routes.distributor_admin import router as distributor_admin_router
from routes.purchase_admin import router as purchase_admin_router

# Mount GraphQL Endpoint (Commented out for clean restaurant backend)
# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")


# Mount REST Routes
app.include_router(user_router)
app.include_router(user_admin_router)
# app.include_router(doctor_router)
# app.include_router(appointment_router)
# app.include_router(lab_catalog_router)
# app.include_router(lab_booking_router)
# app.include_router(story_router)
app.include_router(auth_router)
app.include_router(payment_router)
# app.include_router(dashboard_router)
# app.include_router(banner_router)

# app.include_router(settings_router)
app.include_router(shop_admin_router)
from routes.shop_admin import alias_router as shop_alias_router
app.include_router(shop_alias_router)
app.include_router(shop_settings_router)
app.include_router(pos_admin_router)
# app.include_router(documents_admin_router)
app.include_router(search_router)
app.include_router(shop_orders_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(transaction_categories_router)
app.include_router(accounting_extended_router)
# app.include_router(lab_category_router)
# app.include_router(lab_template_router)
app.include_router(distributor_admin_router)
app.include_router(purchase_admin_router)

# Printer Shop Routes (Commented out for Restaurant Backend)
# from routes.print_services import router as print_services_router
# from routes.print_jobs import router as print_jobs_router
# from routes.machines import router as machines_router
from routes.app_version import router as app_version_router

# app.include_router(print_services_router)
# app.include_router(print_jobs_router)
# app.include_router(machines_router)
app.include_router(app_version_router)

# --- Restaurant Domain Routers ---
from routes.restaurant_outlets import router as restaurant_outlets_router
from routes.restaurant_menu import router as restaurant_menu_router
from routes.restaurant_tables import router as restaurant_tables_router
from routes.restaurant_orders import router as restaurant_orders_router
from routes.restaurant_kitchen import router as restaurant_kitchen_router
from routes.restaurant_tenders import router as restaurant_tenders_router
from routes.restaurant_shifts import router as restaurant_shifts_router
from routes.restaurant_reports import router as restaurant_reports_router
from routes.restaurant_inventory import router as restaurant_inventory_router
from routes.restaurant_crm import router as restaurant_crm_router

app.include_router(restaurant_outlets_router)
app.include_router(restaurant_menu_router)
app.include_router(restaurant_tables_router)
app.include_router(restaurant_orders_router)
app.include_router(restaurant_kitchen_router)
app.include_router(restaurant_tenders_router)
app.include_router(restaurant_shifts_router)
app.include_router(restaurant_reports_router)
app.include_router(restaurant_inventory_router)
app.include_router(restaurant_crm_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to SirfBill Restaurant Backend"}


