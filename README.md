# SirfBill Backend (Restaurant Edition)

A high-performance, multi-tenant, production-ready backend API tailored for **Restaurants, Cafes, Quick Service Restaurants (QSR), Cloud Kitchens, Bars, and Fine Dining Outlets**. Engineered with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Pydantic**.

---

## 🚀 Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Database:** [PostgreSQL 15](https://www.postgresql.org/)
- **ORM & Migrations:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/)
- **Receipt & Thermal Engine:** ReportLab / Jinja2 Thermal HTML templates (80mm & 58mm thermal rolls, 3-inch POS printers, high-fidelity PDF output)
- **Authentication & Security:** JWT (JSON Web Tokens), role-based access control (Admin, Waiter, Cashier, Kitchen Staff), and SMS OTP integration
- **Containerization:** Docker & Docker Compose (Production & Portainer ready)

---

## 🍽️ Key Modules & Capabilities

### 1. 🪑 Dine-in Table Management & Floor Plans
- **Multi-Floor / Section Support:** Organize tables across sections (e.g., *Main Hall, AC Hall, Rooftop, Balcony, Bar*).
- **Table Operations:** Real-time table states (`VACANT`, `OCCUPIED`, `RESERVED`, `CLEANING`).
- **Live Seating & Order Linking:** Direct table-to-order binding with one-click bill settlement and automatic status release upon payment completion.

### 2. 🧾 Restaurant POS & Order Lifecycle
- **Multiple Order Types:** Full support for **Dine-in**, **Takeaway**, and **Delivery**.
- **Order State Machine:** Smooth transitions across states (`DRAFT` → `OPEN` → `SENT_TO_KITCHEN` → `COMPLETED` / `CANCELLED`).
- **Dynamic Cart & Item Increments:** Add new items or increment quantities on live orders with server-authoritative calculations and version-based optimistic locking concurrency control.
- **GST & Pricing Calculations:** Comprehensive SGST/CGST/IGST tax calculation, pre-tax line item rates, discount logic, rounding adjustments, and GST tax breakup breakdowns on bills.

### 3. 🍳 Kitchen Display System (KDS) & KOT Management
- **Kitchen Order Tickets (KOT):** Auto-generated numerical KOTs (`KOT-XXXXXX`) formatted specifically for kitchen thermal printers and display systems.
- **Station-based Routing:** Organize items by prep stations (*Kitchen, Tandoor, Bar, Desserts*).
- **Kitchen Ticket States:** `NEW`, `PREPARING`, `READY`, and `SERVED` tracking with special chef instructions and item notes.

### 4. 📋 Menu Management, Categories & Modifiers
- **Categorization:** Menu items grouped into rich categories with custom emoji/icons, descriptions, and sort priorities.
- **Menu Items:** Full menu item models supporting variants, pricing, preparation station routing, active flags, and badges (*Chef's Special, Bestseller, Spicy, Veg/Non-Veg*).
- **Modifiers & Add-ons:** Customizable options (extra cheese, spice levels, preparation choices) linked directly to order lines.

### 5. 💳 Tenders, Settlements & Split Payments
- **Payment Modes:** Cash, UPI / QR, Credit/Debit Cards, Split Tenders, and Due / Credit accounts.
- **Settlement Endpoint:** Finalizes payments, updates order paid status (`COMPLETED`), records payment tenders, computes change due, and frees up dining tables.
- **Thermal Printing Integration:** Instant 80mm/58mm thermal invoice and KOT generation with customizable outlet branding, GSTIN, FSSAI, UPI QR, and bank details.

### 6. ⏱️ Shift Management & Day Closing
- **Cashier Shifts:** Open and close cashier shifts with starting cash in drawer, recorded sales by payment method, expected cash, actual counted cash, and variance tracking.
- **Shift Handover:** Generates X-Reports and Z-Reports for end-of-day reconciliation.

### 7. 📦 Restaurant Inventory & Recipe Engine
- **Ingredients & Stock Ledgers:** Track raw materials (vegetables, dairy, spices, packaging) with minimum stock alerts.
- **Recipe Consumption:** Map menu items to recipes to automatically deduct ingredient stocks when orders are prepared.
- **Stock Movements:** Audit trails for inward purchases, kitchen consumption, and spoilage/wastage write-offs.

### 8. 👥 Restaurant CRM & Guest Loyalty
- **Guest Profiles:** Track customer visit history, total spent, order preferences, and contact numbers.
- **Walk-in & Guest Fallbacks:** Seamless handling for both named customers and walk-in counter guests.

### 9. 📊 Restaurant Analytics & Reporting
- **Sales Reports:** Real-time daily, monthly, and custom range revenue analytics.
- **Order Breakdown:** Payment mode distribution (Cash vs. UPI vs. Card), table turnover rates, hourly rush hours, and item-wise sales volume.

### 10. 🏢 Multi-Tenant Outlet & Shop Settings
- **Multi-Branch Support:** Single tenant with multiple restaurant outlets/branches.
- **Branding & Legal:** Store Name, Logo, Address, Contact, FSSAI Number, GSTIN, CIN, and Bank Details (including account holder name & IFSC).
- **Dynamic UPI Payment:** Instant UPI QR generation on customer receipts directly linked to outlet UPI ID.

---

## 📂 Project Structure

```text
SirfBill_Backend_Restraunt/
├── main.py                     # Application entry point & router aggregator
├── dependencies.py             # Auth dependencies & database session injection
├── Dockerfile                  # Container build instructions (Port 8030)
├── docker-compose.yml          # Production multi-container setup (DB, Backend, pgAdmin)
├── .env                        # Environment configurations (Credentials & Secrets)
├── requirements.txt            # Python dependencies
│
├── alembic/                    # Database migrations
│   ├── env.py                  # Alembic environment runner
│   └── versions/               # Schema migration scripts
│
├── models/                     # SQLAlchemy ORM Models
│   ├── database.py             # Engine, SessionLocal & Base configuration
│   ├── restaurant_outlet.py    # Outlets / Branches
│   ├── restaurant_table.py     # Dining tables & sections
│   ├── restaurant_menu.py      # Menu categories & items
│   ├── restaurant_modifier.py  # Menu modifiers & add-on options
│   ├── restaurant_order.py     # Orders & order headers
│   ├── restaurant_order_line.py# Order items, variants & instructions
│   ├── restaurant_kitchen.py   # Kitchen order tickets (KOT)
│   ├── restaurant_tender.py    # Payment tenders & settlements
│   ├── restaurant_shift.py     # Cashier shifts & drawer closing
│   ├── restaurant_ingredient.py# Raw ingredients & stock
│   ├── restaurant_recipe.py    # Recipe mapping & ingredient usage
│   ├── restaurant_stock_ledger.py # Stock audit & inventory ledger
│   ├── restaurant_customer.py  # Guest profiles & loyalty
│   ├── shop.py                 # Multi-tenant shops / organizations
│   ├── shop_settings.py        # Store branding, GSTIN, FSSAI, bank details
│   ├── account.py              # Financial bank/cash accounts
│   ├── transaction.py          # Accounting income & expense ledgers
│   └── user.py                 # Admin, Cashier, Waiter & Kitchen users
│
├── routes/                     # REST API Endpoints (FastAPI Routers)
│   ├── auth.py                 # Authentication, staff login & token issuance
│   ├── restaurant_outlets.py   # Outlet management endpoints
│   ├── restaurant_tables.py    # Table status, seating & floor plans
│   ├── restaurant_menu.py      # Categories & menu item CRUD
│   ├── restaurant_orders.py    # Order creation, live tables, append & settle
│   ├── restaurant_kitchen.py   # KOT management & kitchen status updates
│   ├── restaurant_tenders.py   # Payment settlement & receipt generation
│   ├── restaurant_shifts.py    # Cash drawer & shift reconciliation
│   ├── restaurant_inventory.py # Raw materials, recipes & stock audits
│   ├── restaurant_reports.py   # Sales reports, daily revenue & metrics
│   ├── restaurant_crm.py       # Customer directory & order history
│   ├── shop_settings.py        # Store settings, UPI, FSSAI & bill layout
│   ├── distributor_admin.py    # Vendor & supplier management
│   ├── purchase_admin.py       # Purchase orders & stock entry
│   └── accounts.py             # Accounting accounts & transactions
│
├── schemas/                    # Pydantic Schemas (Request/Response Validation)
│   ├── restaurant_order.py     # Order and line schemas
│   ├── restaurant_menu.py      # Menu & category schemas
│   ├── restaurant_table.py     # Dining table schemas
│   ├── restaurant_kitchen.py   # KOT schemas
│   ├── restaurant_tender.py    # Payment & settlement schemas
│   └── shop_settings.py        # Store settings validation
│
├── utils/                      # Helper Utilities
│   ├── restaurant_thermal_printer.py # 80mm/58mm thermal receipt PDF generator
│   └── pdf_generator.py        # General billing & report PDF generators
│
├── templates/                  # Thermal Receipt HTML & Jinja2 Templates
│   └── thermal_bill_template.html # High-fidelity thermal bill template
│
└── uploads/                    # Persistent storage for uploaded media & receipts
    ├── shop/                   # Brand logos & payment QR codes
    ├── bills/                  # Generated bill PDFs
    └── kots/                   # Kitchen ticket print files
```

---

## ⚙️ Environment Configuration (`.env`)

Create a `.env` file in the root directory:

```env
# Database Settings
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sirfbill_restaurant

# Security & Secrets
JWT_SECRET=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMS / OTP Gateway (Optional)
APITXT_AUTH_KEY=your_apitxt_key

# Payment Gateway (Optional)
RAZORPAY_KEY_ID=rzp_live_xxx
RAZORPAY_KEY_SECRET=xxx

# pgAdmin (Docker Dashboard)
PGADMIN_EMAIL=admin@sirfbill.com
PGADMIN_PASSWORD=admin123
```

---

## 🐳 Running with Docker

The service can be run fully containerized alongside PostgreSQL and pgAdmin:

### 1. Start Services
```bash
docker compose up -d --build
```

- **Backend API:** `http://localhost:8030`
- **pgAdmin 4 Dashboard:** `http://localhost:8031`
- **PostgreSQL:** Port `5432`

### 2. View Logs
```bash
docker compose logs -f backend
```

### 3. Stop Services
```bash
docker compose down
```

---

## 💻 Running Locally (Development Mode)

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Start Development Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📖 API Documentation

Once the backend is running, access the interactive API docs:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) (or [http://localhost:8030/docs](http://localhost:8030/docs) in Docker)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🛡️ License
Private and Proprietary. All rights reserved.
