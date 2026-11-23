# TIMBANG - Purchase, Inventory and Seller-Contribution Tracking for Junkshops

Full-stack Django (templates for the frontend) with PostgreSQL / Supabase.

## Features
**Standard features (Project Development 1)**
- Account registration with validation and hashed passwords
- Login / logout
- Role-based dashboards (Owner and Staff)
- User profile (view and edit own profile)

**Core feature: Transaction Recording**
A junkshop records each purchase from a seller. The user picks a seller, adds one or more
materials with quantities, and the system looks up each material's current buying price,
computes every subtotal and the total payable, and saves the transaction.

| Action | Who | Notes |
|---|---|---|
| Add / view sellers | Owner, Staff | Contact number is optional but unique |
| Record a purchase (Create) | Owner, Staff | Saved with the user who recorded it |
| View transactions (Read) | Owner sees all; Staff see only their own | List and detail pages |
| Void a transaction (Delete) | Owner only | Requires a reason; can be done once |

Transactions are never edited or deleted. Corrections are made by voiding (SDD BR-22),
so the audit trail is kept.

**Business rules enforced** (from the SDD)
- At least one line item; each quantity greater than zero; a material only once per transaction
- Only active sellers and active materials can be used; a material needs a current price
- The unit price is copied from the current price onto each line, so later price changes never alter it
- Subtotals and the total are computed by the system, rounded to two decimals
- The transaction date cannot be in the future
- A void needs a reason and can happen only once
- Saving a transaction and its lines happens in one database transaction (all or nothing)

**Data model** (follows the SDD ERD): `User` -> `Seller`, `Transaction`;
`Seller` -> `Transaction`; `Transaction` -> `TransactionItem`;
`Material` -> `MaterialPrice`, `TransactionItem`; `MaterialPrice` -> `TransactionItem`.

## Setup
1. Create and activate a virtual environment, then install packages:
   ```
   python -m venv venv
   venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your values (never commit `.env`).
   For Supabase use the **Session pooler** details: `DB_HOST=aws-0-<region>.pooler.supabase.com`,
   `DB_PORT=5432`, `DB_NAME=postgres`, `DB_USER=postgres.<project-ref>`, `DB_SSLMODE=require`.
3. Create the tables:
   ```
   python manage.py migrate
   ```
4. Run the app and register your first account (it becomes the Owner; later accounts are Staff):
   ```
   python manage.py runserver 8080
   ```
   Open http://127.0.0.1:8080/register/
5. Load sample materials and prices (needs an Owner account to exist first):
   ```
   python manage.py seed_materials
   ```
   The prices are examples only.

## Try the core feature
1. Log in as the Owner. Open **Sellers -> Add seller**.
2. Open **Record purchase**, choose the seller, add materials and weights, and save.
3. Check the detail page for unit prices, subtotals and the total payable.
4. Open the transaction as Owner and void it with a reason.
5. Register a second account (Staff). It sees only its own transactions and cannot void.

## Project structure
```
config/         settings and root URLs
accounts/       custom User model, registration, login, dashboards, profile
transactions/   Seller, Material, MaterialPrice, Transaction, TransactionItem,
                forms, views, services (save/void logic), seed command
templates/      base, partials, accounts/, dashboards/, transactions/
static/css/     timbang.css
```

## Git workflow
- `main`: stable code only; changes arrive through pull requests
- `develop`: integration branch, created from `main`
- `feature/<name>`: one branch per feature, created from `develop`
  (e.g. `feature/transaction-recording`)