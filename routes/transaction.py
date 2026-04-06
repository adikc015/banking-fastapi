from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.account import Account
from models.transaction import Transaction
from models.user import User, UserRole
from schemas.transaction import DepositRequest, TransactionOut, TransferRequest, WithdrawRequest
from services.notification_service import send_transaction_alert
from services.payment_service import deposit, transfer, withdraw
from utils.rate_limiter import limiter
from utils.security import get_current_user

router = APIRouter()


async def _validate_account_owner(db: AsyncSession, account_id: int, user_id: int) -> None:
	query = select(Account).where(Account.id == account_id, Account.user_id == user_id)
	result = await db.execute(query)
	account = result.scalar_one_or_none()
	if account is None:
		raise HTTPException(status_code=404, detail="Account not found or not owned by current user")


@router.post("/deposit", response_model=TransactionOut)
@limiter.limit("15/minute")
async def deposit_money(
	request: Request,
	payload: DepositRequest,
	background_tasks: BackgroundTasks,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Transaction:
	await _validate_account_owner(db, payload.account_id, current_user.id)
	tx = await deposit(db, payload.account_id, payload.amount, payload.location)
	background_tasks.add_task(send_transaction_alert, current_user.email, f"Deposit successful: {payload.amount}")
	return tx


@router.post("/withdraw", response_model=TransactionOut)
@limiter.limit("15/minute")
async def withdraw_money(
	request: Request,
	payload: WithdrawRequest,
	background_tasks: BackgroundTasks,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Transaction:
	await _validate_account_owner(db, payload.account_id, current_user.id)
	tx = await withdraw(db, payload.account_id, payload.amount, payload.location)
	background_tasks.add_task(send_transaction_alert, current_user.email, f"Withdraw successful: {payload.amount}")
	return tx


@router.post("/transfer", response_model=TransactionOut)
@limiter.limit("10/minute")
async def transfer_money(
	request: Request,
	payload: TransferRequest,
	background_tasks: BackgroundTasks,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Transaction:
	await _validate_account_owner(db, payload.from_account_id, current_user.id)
	tx = await transfer(
		db,
		from_account_id=payload.from_account_id,
		to_account_id=payload.to_account_id,
		amount=payload.amount,
		location=payload.location,
	)
	background_tasks.add_task(
		send_transaction_alert,
		current_user.email,
		f"Transfer successful: {payload.amount} to account {payload.to_account_id}",
	)
	return tx


@router.get("/", response_model=list[TransactionOut])
async def my_transactions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Transaction]:
	account_rows = await db.execute(select(Account.id).where(Account.user_id == current_user.id))
	account_ids = [item[0] for item in account_rows.all()]
	if not account_ids:
		return []

	query = select(Transaction).where(
		(Transaction.from_account_id.in_(account_ids)) | (Transaction.to_account_id.in_(account_ids))
	)
	rows = await db.execute(query.order_by(Transaction.id.desc()))
	return list(rows.scalars().all())


@router.get("/admin/all", response_model=list[TransactionOut])
async def all_transactions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Transaction]:
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=403, detail="Admin access required")

	rows = await db.execute(select(Transaction).order_by(Transaction.id.desc()))
	return list(rows.scalars().all())


@router.get("/admin/fraud", response_model=list[TransactionOut])
async def fraud_alerts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Transaction]:
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=403, detail="Admin access required")

	rows = await db.execute(select(Transaction).where(Transaction.status == "flagged").order_by(Transaction.id.desc()))
	return list(rows.scalars().all())
