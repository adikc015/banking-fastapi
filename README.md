# Banking App (FastAPI Learning Project)

This project is structured to help you learn FastAPI by building a realistic banking backend.

## Features Implemented (Phase 1)

- JWT Authentication (register/login)
- Role-based users: admin, customer
- KYC simulation (Aadhaar/PAN)
- Multiple bank accounts per user (savings/current)
- Minimum balance rule
- Interest calculation for savings accounts
- Transactions: deposit, withdraw, transfer
- Atomic transaction flows with DB transaction handling
- Basic concurrency safety (`SELECT ... FOR UPDATE` style flow)
- Fraud detection (sliding window):
  - large amount
  - multiple rapid transactions
  - location mismatch
- Loan apply + EMI calculation + admin approval
- Notification hooks via FastAPI background tasks (simulated email/SMS logs)
- Admin dashboard APIs:
  - list users
  - list all transactions
  - view fraud alerts
  - approve/reject loans
- Audit logging to `logs/app.log`
- Async SQLAlchemy setup

## Step-by-Step Learning Path

### Step 1: Run the app

```bash
uvicorn main:app --reload
```

Open:
- Docs: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

### Step 2: Learn authentication flow

1. Call `POST /auth/register` (customer)
2. Call `POST /auth/login` using OAuth2 form fields:
   - `username` = email
   - `password` = your password
3. Copy token and use **Authorize** button in Swagger UI.

### Step 3: KYC verification

Call `POST /auth/kyc` with:
- Aadhaar: 12 digits
- PAN: 10 chars, alpha-numeric style

### Step 4: Account lifecycle

1. Create savings/current account: `POST /accounts/`
2. List your accounts: `GET /accounts/`
3. Apply interest on savings: `POST /accounts/{account_id}/interest`

### Step 5: Transactions + DAA concepts

Try:
- `POST /transactions/deposit`
- `POST /transactions/withdraw`
- `POST /transactions/transfer`

Observe:
- ACID behavior from single DB transaction blocks
- Rollback behavior when validation fails
- Concurrency idea via row locking and consistent lock order

### Step 6: Fraud detection

Perform rapid transfers with high amount or varying location.
Then check:
- `GET /transactions/admin/fraud` (admin token)

### Step 7: Loan flow

1. Customer applies: `POST /loans/apply`
2. Admin lists pending: `GET /loans/admin/pending`
3. Admin reviews: `POST /loans/{loan_id}/review`

EMI formula used:

EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

Where:
- P = principal
- r = monthly interest rate
- n = number of months

## Next Phases (Recommended)

- Add Alembic migrations for production-safe schema evolution
- Add Redis caching for balance snapshots and read-heavy endpoints
- Replace in-memory fraud history with persistent + stream processing
- Add Celery + broker (Redis/RabbitMQ) for real async email/SMS
- Add test suite (pytest + httpx + async fixtures)
- Split to microservices:
  - Auth Service
  - Transaction Service
  - Notification Service

## Project Structure

- `main.py` - app entrypoint
- `database.py` - async SQLAlchemy engine/session/base
- `models/` - ORM models
- `schemas/` - Pydantic request/response models
- `routes/` - API routers by domain
- `services/` - business logic modules
- `utils/` - security, logging, helper utilities

