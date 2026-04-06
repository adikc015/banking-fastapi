from fastapi import FastAPI
from fastapi import Request

from database import init_db
from routes import account, auth, loan, transaction
from utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger("audit")

app = FastAPI(
	title="Banking App API",
	description="Learning project for FastAPI with auth, accounts, transactions, fraud detection, and loans",
	version="1.0.0",
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(account.router, prefix="/accounts", tags=["Accounts"])
app.include_router(transaction.router, prefix="/transactions", tags=["Transactions"])
app.include_router(loan.router, prefix="/loans", tags=["Loans"])


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
	response = await call_next(request)
	client = request.client.host if request.client else "unknown"
	logger.info("%s %s | status=%s | client=%s", request.method, request.url.path, response.status_code, client)
	return response


@app.on_event("startup")
async def startup_event() -> None:
	await init_db()


@app.get("/")
async def root() -> dict[str, str]:
	return {"message": "Banking API is running", "docs": "/docs"}
