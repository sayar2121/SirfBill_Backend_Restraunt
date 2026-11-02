# SirfBill Backend (Printer & Billing Edition)

A high-performance, production-ready backend API built for **Printing Press, Photocopy, Digital Printing & Retail Billing Stores**. Engineered with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and **Strawberry GraphQL**.

---

## 🚀 Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Database:** [PostgreSQL 15](https://www.postgresql.org/)
- **ORM & Migrations:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/)
- **GraphQL:** [Strawberry GraphQL](https://strawberry.rocks/)
- **PDF & Document Engine:** WeasyPrint / ReportLab
- **Authentication:** JWT (JSON Web Tokens) & APITXT (SMS OTP)
- **Containerization:** Docker & Docker Compose (Portainer Ready)

---

## 🛠️ Key Modules & Capabilities

### 1. 🖨️ Printing Press & Services Management
- **Print Services:** Configure pricing for various paper types (A4, A3, Glossy, Bond), single/double-sided, color mode (B&W, Color), and finishing options (Binding, Lamination).
- **Print Jobs & Queue:** Track job statuses (`PENDING`, `PROCESSING`, `PRINTED`, `DELIVERED`), assign jobs to operators, and link them to customer bills.
- **Machine Fleet:** Monitor printer machines/presses, track print counts, status, and maintenance logs.

### 2. 🧾 Point of Sale (POS) & Counter Billing
- **Fast Billing:** Quick counter checkout with Barcode/SKU scan or service selection.
- **Flexible Payments:** Cash, UPI, Card, Split payments, and Credit / Due balance tracking.
- **GST & Non-GST Billing:** Automatic SGST/CGST/IGST calculation, custom discounts, and round-offs.
- **PDF & Thermal Receipts:** Instant receipt generation with business details, customizable footer, and dynamic UPI QR code.

### 3. 📦 Inventory & Stock Control
- **Product Catalog:** Manage stationery, paper reams, toner cartridges, inks, flex rolls, and raw materials.
- **Stock Flexibility:** Supports full pack sizes and loose quantities.
- **Printing-Friendly:** Expiry dates are optional (allowing non-perishable store items like papers, cartridges, and boards).
- **Racks & Categories:** Organize inventory by shelf/rack numbers and departmental categories.

### 4. 🏢 Distributor & Purchase Management
- **Vendor Directory:** Maintain distributor contacts, GSTIN, phone numbers, and addresses.
- **Purchase Bills:** Inward purchase recording that automatically updates inventory stock levels.
- **Expense Integration:** Purchases automatically log into accounting ledgers as vendor expenses.

### 5. 💰 Finance & Accounting Ledger
- **Accounts & Ledgers:** Cash in Hand, Bank Accounts, UPI Wallets.
- **Transactions:** Daily income and expense tracking categorized by type (Electricity, Rent, Paper Purchase, Maintenance).
- **Financial Reports:** Summary of daily revenue, cash vs. digital split, and net margins.

### 6. ⚙️ Shop Customization & Settings
- **Legal & Identity:** Store Name, Tagline, Address, Phone, **CIN Number** (Corporate Identity Number), and **GSTIN**.
- **Bank & UPI Integration:** Bank account numbers, IFSC, and automated QR code URL generation for customer payment.
- **Branding:** Custom invoice header logos and footer terms & conditions.

---

## 📂 Project Structure

```text
SirfBill_Backend(Printer)/
├── main.py                     # Application entry point & route aggregator
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
├── graphql_api/                # Strawberry GraphQL API
│   ├── schema.py               # Root schema
│   ├── queries/                # GraphQL query resolvers
│   ├── mutations/              # GraphQL mutation resolvers
│   └── types/                  # GraphQL type definitions
│
├── models/                     # SQLAlchemy ORM Models
│   ├── database.py             # Engine, SessionLocal & Base configuration
│   ├── shop.py                 # Multi-tenant shops / branches
│   ├── shop_settings.py        # Store branding, CIN number, GSTIN, bank details
│   ├── shop_bill.py            # POS Invoices & invoice items
│   ├── inventory.py            # Store items & stock levels
│   ├── print_service.py        # Print specifications & rates
│   ├── print_job.py            # Printing job orders & statuses
│   ├── machine.py              # Printers / machines
│   ├── distributor.py          # Vendors / Suppliers
│   ├── purchase.py             # Purchase bills & inward items
│   ├── account.py              # Bank & Cash accounts
│   ├── transaction.py          # Income & Expense records
│   ├── user.py                 # Admin & staff users
│   └── enums.py                # Database enum definitions
│
├── routes/                     # REST API Endpoints (FastAPI Routers)
│   ├── auth.py                 # Authentication & Token issuance
│   ├── pos_admin.py            # Billing, checkout & invoice generation
│   ├── shop_admin.py           # Inventory management & Excel bulk import
│   ├── print_services.py       # Print rates & service endpoints
│   ├── print_jobs.py           # Print job workflow endpoints
│   ├── machines.py             # Printer machinery endpoints
│   ├── purchase_admin.py       # Distributor purchase bills
│   ├── distributor_admin.py    # Vendor management
│   ├── accounts.py             # Financial accounts
│   ├── transactions.py         # Transaction records
│   ├── shop_settings.py        # Store branding & bill customization
│   └── search.py               # Universal search
│
├── schemas/                    # Pydantic Schemas (Request/Response Validation)
│   ├── shop_settings.py        # Settings validation (CIN, GST, Bank)
│   ├── inventory.py            # Inventory validation & empty date parsing
│   ├── purchase.py             # Purchase bill schemas
│   ├── print_service.py        # Print service schemas
│   └── ...
│
└── uploads/                    # Persistent storage for uploaded media & PDFs
    ├── shop/                   # Logos, payment QR codes
    └── reports/                # Generated statements & export files
```

---

## ⚙️ Environment Configuration (`.env`)

Create a `.env` file in the root directory:

```env
# Database Settings
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432
DB_NAME=sirfbill_printer

# Security & Secrets
JWT_SECRET=your_super_secret_jwt_key

# SMS / OTP Gateway
APITXT_AUTH_KEY=your_apitxt_key

# Payment Gateway (Optional)
RAZORPAY_KEY_ID=rzp_live_xxx
RAZORPAY_KEY_SECRET=xxx

# pgAdmin (Docker Dashboard)
PGADMIN_EMAIL=admin@sirfbill.com
PGADMIN_PASSWORD=admin123
```

---

## 🐳 Running with Docker (Recommended)

This setup uses dedicated ports to run cleanly alongside existing stacks (freeing ports `8028` and `8029`):
- **Backend API:** `http://localhost:8030`
- **pgAdmin 4:** `http://localhost:8031`
- **PostgreSQL Database:** Port `5432` (internal network: `sirfbill_printer_net`)
- **Database Name:** `sirfbill_printer`

### 1. Start Services
```bash
docker compose up -d --build
```

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
python3 -m venv venv
source venv/bin/activate
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
- **Swagger UI:** [http://localhost:8030/docs](http://localhost:8030/docs) (or [http://localhost:8000/docs](http://localhost:8000/docs) in local dev)
- **ReDoc:** [http://localhost:8030/redoc](http://localhost:8030/redoc)
- **GraphQL Explorer:** [http://localhost:8030/graphql](http://localhost:8030/graphql)

---

## 🛡️ License
Private and Proprietary. All rights reserved.
